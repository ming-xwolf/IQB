# 阿里巴巴Java面试 - 秒杀系统完整实现

## 🎯 解决方案概述

本文档提供双十一秒杀系统的完整代码实现，解决百万用户同时抢购的高并发场景，包括多级限流、分布式锁、库存管理等核心技术方案。

## 💡 关键技术点

- **多级限流策略**：IP、用户、接口三级限流防护
- **分布式锁机制**：Redis分布式锁保证数据一致性
- **库存原子操作**：Lua脚本实现原子性库存扣减
- **异步化处理**：提升系统吞吐量和响应速度

## 📝 题目3：秒杀系统的并发控制

### 分层限流秒杀控制器

```java
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.beans.factory.annotation.Autowired;

import javax.servlet.http.HttpServletRequest;
import java.time.Duration;
import java.util.concurrent.CompletableFuture;

/**
 * 分层限流秒杀系统控制器
 * 实现IP限流、用户限流、接口限流等多重防护
 */
@RestController
@RequestMapping("/seckill")
@Slf4j
public class SeckillController {
    
    @Autowired
    private SeckillService seckillService;
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    @Autowired
    private IpRateLimiter ipRateLimiter;
    
    @Autowired
    private LocalCacheManager localCache;
    
    /**
     * 秒杀商品接口
     * 多级限流策略：IP限流 -> 用户限流 -> 接口限流 -> 业务处理
     */
    @PostMapping("/purchase/{productId}")
    @RateLimited(rate = 50000, per = "1s") // 接口级限流：5万QPS
    public ResponseEntity<SeckillResult> purchase(
            @PathVariable Long productId,
            @RequestHeader("User-ID") Long userId,
            HttpServletRequest request) {
        
        long startTime = System.currentTimeMillis();
        
        try {
            // 1. IP级限流（防止单IP恶意请求）
            String clientIP = getClientIP(request);
            if (!ipRateLimiter.tryAcquire(clientIP, 20, Duration.ofSeconds(1))) {
                return ResponseEntity.status(429).body(
                    SeckillResult.failure("IP请求过于频繁，请稍后重试", "RATE_LIMIT_IP"));
            }
            
            // 2. 用户级限流（防止单用户重复提交）
            String userLimitKey = "seckill:user_limit:" + userId + ":" + productId;
            if (!redisTemplate.opsForValue().setIfAbsent(userLimitKey, "1", Duration.ofSeconds(1))) {
                return ResponseEntity.ok(SeckillResult.failure("请勿重复提交", "DUPLICATE_REQUEST"));
            }
            
            // 3. 预检查（快速失败，减少后续处理压力）
            if (!preCheck(productId)) {
                return ResponseEntity.ok(SeckillResult.failure("商品已售罄", "SOLD_OUT"));
            }
            
            // 4. 风控检查
            RiskCheckResult riskResult = checkUserRisk(userId, clientIP);
            if (!riskResult.isAllowed()) {
                return ResponseEntity.ok(SeckillResult.failure("风控拦截：" + riskResult.getReason(), "RISK_BLOCKED"));
            }
            
            // 5. 进入秒杀队列处理
            SeckillResult result = seckillService.processSeckill(productId, userId, clientIP);
            
            // 6. 记录处理时间
            long processingTime = System.currentTimeMillis() - startTime;
            recordMetrics(productId, processingTime, result.isSuccess());
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("秒杀处理异常 - 商品ID: {}, 用户ID: {}", productId, userId, e);
            return ResponseEntity.status(500).body(
                SeckillResult.failure("系统繁忙，请稍后重试", "SYSTEM_ERROR"));
        }
    }
    
    /**
     * 预检查机制（多级缓存 + 快速失败）
     */
    private boolean preCheck(Long productId) {
        // 1. 本地缓存快速检查（最快）
        Boolean localAvailable = localCache.get("stock:" + productId);
        if (Boolean.FALSE.equals(localAvailable)) {
            log.debug("本地缓存显示商品 {} 已售罄", productId);
            return false;
        }
        
        // 2. Redis分布式缓存检查
        String stockKey = "seckill:stock:" + productId;
        String stockStr = (String) redisTemplate.opsForValue().get(stockKey);
        
        if (stockStr == null) {
            // 缓存未命中，从数据库加载
            return reloadStockFromDB(productId);
        }
        
        long currentStock = Long.parseLong(stockStr);
        if (currentStock <= 0) {
            // 更新本地缓存
            localCache.put("stock:" + productId, false);
            log.debug("Redis缓存显示商品 {} 已售罄", productId);
            return false;
        }
        
        return true;
    }
    
    /**
     * 从数据库重新加载库存
     */
    private boolean reloadStockFromDB(Long productId) {
        try {
            SeckillProduct product = seckillService.getProductById(productId);
            if (product == null || product.getStock() <= 0) {
                localCache.put("stock:" + productId, false);
                return false;
            }
            
            // 更新Redis缓存
            String stockKey = "seckill:stock:" + productId;
            redisTemplate.opsForValue().set(stockKey, String.valueOf(product.getStock()), Duration.ofMinutes(5));
            
            return true;
        } catch (Exception e) {
            log.error("从数据库加载库存失败 - 商品ID: {}", productId, e);
            return false;
        }
    }
    
    /**
     * 用户风控检查
     */
    private RiskCheckResult checkUserRisk(Long userId, String clientIP) {
        // 1. 检查用户行为异常
        if (isAbnormalBehavior(userId)) {
            return RiskCheckResult.blocked("用户行为异常");
        }
        
        // 2. 检查IP黑名单
        if (isBlacklistedIP(clientIP)) {
            return RiskCheckResult.blocked("IP被列入黑名单");
        }
        
        // 3. 检查设备指纹
        if (isSuspiciousDevice(clientIP)) {
            return RiskCheckResult.blocked("设备异常");
        }
        
        return RiskCheckResult.allowed();
    }
    
    /**
     * 获取客户端真实IP
     */
    private String getClientIP(HttpServletRequest request) {
        String xForwardedFor = request.getHeader("X-Forwarded-For");
        if (xForwardedFor != null && !xForwardedFor.isEmpty() && !"unknown".equalsIgnoreCase(xForwardedFor)) {
            return xForwardedFor.split(",")[0].trim();
        }
        
        String xRealIP = request.getHeader("X-Real-IP");
        if (xRealIP != null && !xRealIP.isEmpty() && !"unknown".equalsIgnoreCase(xRealIP)) {
            return xRealIP;
        }
        
        return request.getRemoteAddr();
    }
    
    /**
     * 记录监控指标
     */
    private void recordMetrics(Long productId, long processingTime, boolean success) {
        // 记录处理时间
        Metrics.timer("seckill.processing.time", "product", String.valueOf(productId))
            .record(processingTime, TimeUnit.MILLISECONDS);
        
        // 记录成功/失败率
        Metrics.counter("seckill.requests", 
            "product", String.valueOf(productId),
            "result", success ? "success" : "failure")
            .increment();
    }
    
    // 辅助方法
    private boolean isAbnormalBehavior(Long userId) { return false; }
    private boolean isBlacklistedIP(String ip) { return false; }
    private boolean isSuspiciousDevice(String ip) { return false; }
}
```

### 秒杀核心业务服务

```java
import org.redisson.api.RLock;
import org.redisson.api.RedissonClient;
import org.springframework.data.redis.core.script.RedisScript;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

/**
 * 秒杀核心业务服务
 * 处理库存扣减、订单创建等核心逻辑
 */
@Service
@Slf4j
public class SeckillService {
    
    @Autowired
    private RedissonClient redisson;
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    @Autowired
    private OrderService orderService;
    
    @Autowired
    private MessageProducer messageProducer;
    
    @Autowired
    private ExecutorService seckillExecutor;
    
    // Lua脚本：原子性库存扣减
    private static final String STOCK_DEDUCTION_SCRIPT = """
        local stock_key = KEYS[1]
        local order_key = KEYS[2]
        local user_id = ARGV[1]
        local product_id = ARGV[2]
        local current_time = ARGV[3]
        
        -- 检查库存
        local current_stock = redis.call('get', stock_key)
        if not current_stock or tonumber(current_stock) <= 0 then
            return {0, '库存不足'}
        end
        
        -- 检查用户是否已经购买过
        local user_order_key = 'seckill:user_order:' .. user_id .. ':' .. product_id
        if redis.call('exists', user_order_key) == 1 then
            return {0, '用户已购买'}
        end
        
        -- 扣减库存
        local remaining_stock = redis.call('decr', stock_key)
        if remaining_stock < 0 then
            -- 库存不足，回滚
            redis.call('incr', stock_key)
            return {0, '库存不足'}
        end
        
        -- 创建预订单记录
        local order_id = product_id .. '_' .. user_id .. '_' .. current_time
        redis.call('hset', order_key, 
            'order_id', order_id,
            'user_id', user_id, 
            'product_id', product_id,
            'status', 'PENDING',
            'create_time', current_time
        )
        
        -- 设置用户购买记录
        redis.call('setex', user_order_key, 86400, order_id) -- 24小时过期
        
        return {1, order_id, remaining_stock}
        """;
    
    /**
     * 处理秒杀请求的核心方法
     */
    public SeckillResult processSeckill(Long productId, Long userId, String clientIP) {
        String lockKey = "seckill:lock:" + productId;
        RLock distributedLock = redisson.getLock(lockKey);
        
        try {
            // 尝试获取分布式锁，最多等待100ms，锁定500ms
            if (distributedLock.tryLock(100, 500, TimeUnit.MILLISECONDS)) {
                try {
                    return doSeckillWithLock(productId, userId, clientIP);
                } finally {
                    if (distributedLock.isHeldByCurrentThread()) {
                        distributedLock.unlock();
                    }
                }
            } else {
                return SeckillResult.failure("系统繁忙，请稍后重试", "SYSTEM_BUSY");
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return SeckillResult.failure("请求被中断", "INTERRUPTED");
        } catch (Exception e) {
            log.error("秒杀处理异常", e);
            return SeckillResult.failure("系统异常", "SYSTEM_ERROR");
        }
    }
    
    /**
     * 在分布式锁保护下执行秒杀逻辑
     */
    private SeckillResult doSeckillWithLock(Long productId, Long userId, String clientIP) {
        // 使用Lua脚本执行原子性操作
        String stockKey = "seckill:stock:" + productId;
        String orderKey = "seckill:order:" + productId + ":" + userId;
        
        Object[] result = (Object[]) redisTemplate.execute(
            RedisScript.of(STOCK_DEDUCTION_SCRIPT, Object[].class),
            Arrays.asList(stockKey, orderKey),
            String.valueOf(userId),
            String.valueOf(productId),
            String.valueOf(System.currentTimeMillis())
        );
        
        if (result == null || result.length < 2) {
            return SeckillResult.failure("系统异常", "SYSTEM_ERROR");
        }
        
        Integer success = (Integer) result[0];
        if (success != 1) {
            String errorMessage = (String) result[1];
            return SeckillResult.failure(errorMessage, "SECKILL_FAILED");
        }
        
        String orderId = (String) result[1];
        Integer remainingStock = result.length > 2 ? (Integer) result[2] : 0;
        
        // 异步处理订单创建（提高响应速度）
        handleOrderCreationAsync(orderId, productId, userId, clientIP);
        
        // 库存预警
        if (remainingStock <= 10) {
            sendStockWarning(productId, remainingStock);
        }
        
        return SeckillResult.success("抢购成功，正在为您创建订单", orderId);
    }
    
    /**
     * 异步处理订单创建
     */
    private void handleOrderCreationAsync(String orderId, Long productId, Long userId, String clientIP) {
        CompletableFuture.supplyAsync(() -> {
            try {
                // 1. 获取商品信息
                SeckillProduct product = getProductById(productId);
                if (product == null) {
                    throw new RuntimeException("商品不存在");
                }
                
                // 2. 创建订单对象
                SeckillOrder order = SeckillOrder.builder()
                    .orderId(orderId)
                    .userId(userId)
                    .productId(productId)
                    .productName(product.getName())
                    .price(product.getPrice())
                    .quantity(1)
                    .clientIP(clientIP)
                    .status(OrderStatus.PENDING)
                    .createTime(System.currentTimeMillis())
                    .build();
                
                // 3. 调用订单服务创建正式订单
                OrderCreateResult createResult = orderService.createOrder(order);
                
                if (createResult.isSuccess()) {
                    // 更新Redis中的订单状态
                    updateOrderStatus(orderId, OrderStatus.CREATED);
                    
                    // 发送订单创建成功消息
                    messageProducer.sendOrderCreatedMessage(order);
                    
                    log.info("订单创建成功 - 订单ID: {}, 用户ID: {}", orderId, userId);
                    return createResult;
                } else {
                    throw new RuntimeException("订单创建失败: " + createResult.getErrorMessage());
                }
                
            } catch (Exception e) {
                log.error("异步创建订单失败 - 订单ID: {}", orderId, e);
                
                // 回滚库存
                rollbackStock(productId);
                
                // 更新订单状态为失败
                updateOrderStatus(orderId, OrderStatus.FAILED);
                
                // 发送订单创建失败通知
                sendOrderFailureNotification(orderId, userId, e.getMessage());
                
                throw new RuntimeException("订单创建失败", e);
            }
        }, seckillExecutor)
        .whenComplete((result, throwable) -> {
            if (throwable != null) {
                log.error("订单异步处理完成，但存在异常", throwable);
            } else {
                log.info("订单异步处理成功完成 - 订单ID: {}", orderId);
            }
        });
    }
    
    /**
     * 回滚库存
     */
    private void rollbackStock(Long productId) {
        String stockKey = "seckill:stock:" + productId;
        try {
            redisTemplate.opsForValue().increment(stockKey);
            log.info("库存回滚成功 - 商品ID: {}", productId);
        } catch (Exception e) {
            log.error("库存回滚失败 - 商品ID: {}", productId, e);
            // 发送告警消息
            sendCriticalAlert("库存回滚失败", "商品ID: " + productId + ", 错误: " + e.getMessage());
        }
    }
    
    /**
     * 更新订单状态
     */
    private void updateOrderStatus(String orderId, OrderStatus status) {
        try {
            String orderKey = "seckill:order:" + orderId;
            redisTemplate.opsForHash().put(orderKey, "status", status.name());
            redisTemplate.opsForHash().put(orderKey, "update_time", String.valueOf(System.currentTimeMillis()));
            
            log.debug("订单状态更新成功 - 订单ID: {}, 状态: {}", orderId, status);
        } catch (Exception e) {
            log.error("订单状态更新失败 - 订单ID: {}, 状态: {}", orderId, status, e);
        }
    }
    
    /**
     * 发送库存预警
     */
    private void sendStockWarning(Long productId, Integer remainingStock) {
        try {
            StockWarningMessage message = StockWarningMessage.builder()
                .productId(productId)
                .remainingStock(remainingStock)
                .timestamp(System.currentTimeMillis())
                .build();
            
            messageProducer.sendStockWarningMessage(message);
            
            log.warn("库存预警 - 商品ID: {}, 剩余库存: {}", productId, remainingStock);
        } catch (Exception e) {
            log.error("发送库存预警失败", e);
        }
    }
    
    /**
     * 发送订单失败通知
     */
    private void sendOrderFailureNotification(String orderId, Long userId, String errorMessage) {
        try {
            OrderFailureNotification notification = OrderFailureNotification.builder()
                .orderId(orderId)
                .userId(userId)
                .errorMessage(errorMessage)
                .timestamp(System.currentTimeMillis())
                .build();
            
            messageProducer.sendOrderFailureNotification(notification);
        } catch (Exception e) {
            log.error("发送订单失败通知异常", e);
        }
    }
    
    /**
     * 发送严重告警
     */
    private void sendCriticalAlert(String title, String content) {
        // 实现告警发送逻辑
    }
    
    /**
     * 根据商品ID获取商品信息
     */
    public SeckillProduct getProductById(Long productId) {
        // 实现商品查询逻辑
        return null;
    }
}
```

### 高性能本地缓存

```java
import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * 高性能本地缓存
 * 用于缓存热点数据，减少Redis访问压力
 */
@Component
@Slf4j
public class SeckillLocalCache {
    
    // 商品库存缓存
    private final Cache<String, Boolean> stockCache = Caffeine.newBuilder()
        .maximumSize(10000)
        .expireAfterWrite(5, TimeUnit.SECONDS) // 5秒过期，保证数据新鲜度
        .recordStats() // 开启统计
        .build();
    
    // 商品信息缓存
    private final Cache<Long, SeckillProduct> productCache = Caffeine.newBuilder()
        .maximumSize(1000)
        .expireAfterWrite(1, TimeUnit.MINUTES) // 1分钟过期
        .recordStats()
        .build();
    
    // 用户风控缓存
    private final Cache<Long, RiskLevel> userRiskCache = Caffeine.newBuilder()
        .maximumSize(100000)
        .expireAfterWrite(10, TimeUnit.MINUTES) // 10分钟过期
        .recordStats()
        .build();
    
    /**
     * 秒杀活动开始时预热缓存
     */
    @EventListener
    public void onSeckillStart(SeckillStartEvent event) {
        log.info("秒杀活动开始，开始预热本地缓存");
        
        List<SeckillProduct> products = event.getProducts();
        
        for (SeckillProduct product : products) {
            // 预热商品信息缓存
            productCache.put(product.getId(), product);
            
            // 预热库存状态缓存
            String stockKey = "stock:" + product.getId();
            stockCache.put(stockKey, product.getStock() > 0);
        }
        
        log.info("本地缓存预热完成，缓存商品数量: {}", products.size());
    }
    
    /**
     * 秒杀活动结束时清理缓存
     */
    @EventListener
    public void onSeckillEnd(SeckillEndEvent event) {
        log.info("秒杀活动结束，清理本地缓存");
        
        stockCache.invalidateAll();
        productCache.invalidateAll();
        userRiskCache.invalidateAll();
        
        log.info("本地缓存清理完成");
    }
    
    // 库存缓存操作
    public Boolean getStockStatus(String key) {
        return stockCache.getIfPresent(key);
    }
    
    public void putStockStatus(String key, Boolean available) {
        stockCache.put(key, available);
    }
    
    public void invalidateStock(String key) {
        stockCache.invalidate(key);
    }
    
    // 商品信息缓存操作
    public SeckillProduct getProduct(Long productId) {
        return productCache.getIfPresent(productId);
    }
    
    public void putProduct(Long productId, SeckillProduct product) {
        productCache.put(productId, product);
    }
    
    // 用户风控缓存操作
    public RiskLevel getUserRiskLevel(Long userId) {
        return userRiskCache.getIfPresent(userId);
    }
    
    public void putUserRiskLevel(Long userId, RiskLevel riskLevel) {
        userRiskCache.put(userId, riskLevel);
    }
    
    /**
     * 获取缓存统计信息
     */
    public CacheStats getCacheStats() {
        return CacheStats.builder()
            .stockCacheStats(stockCache.stats())
            .productCacheStats(productCache.stats())
            .userRiskCacheStats(userRiskCache.stats())
            .build();
    }
    
    /**
     * 定期输出缓存统计信息
     */
    @Scheduled(fixedRate = 30000) // 每30秒
    public void logCacheStats() {
        CacheStats stats = getCacheStats();
        
        log.info("本地缓存统计信息:");
        log.info("库存缓存 - 命中率: {:.2f}%, 大小: {}", 
            stats.getStockCacheStats().hitRate() * 100, stockCache.estimatedSize());
        log.info("商品缓存 - 命中率: {:.2f}%, 大小: {}", 
            stats.getProductCacheStats().hitRate() * 100, productCache.estimatedSize());
        log.info("风控缓存 - 命中率: {:.2f}%, 大小: {}", 
            stats.getUserRiskCacheStats().hitRate() * 100, userRiskCache.estimatedSize());
    }
}
```

### 秒杀结果和数据模型

```java
import lombok.Builder;
import lombok.Data;

/**
 * 秒杀结果模型
 */
@Data
@Builder
public class SeckillResult {
    private boolean success;
    private String message;
    private String orderId;
    private String errorCode;
    private long timestamp;
    private Object data;
    
    public static SeckillResult success(String message, String orderId) {
        return SeckillResult.builder()
            .success(true)
            .message(message)
            .orderId(orderId)
            .timestamp(System.currentTimeMillis())
            .build();
    }
    
    public static SeckillResult failure(String message, String errorCode) {
        return SeckillResult.builder()
            .success(false)
            .message(message)
            .errorCode(errorCode)
            .timestamp(System.currentTimeMillis())
            .build();
    }
}

/**
 * 秒杀商品模型
 */
@Data
@Builder
public class SeckillProduct {
    private Long id;
    private String name;
    private String description;
    private BigDecimal price;
    private BigDecimal originalPrice;
    private Integer stock;
    private Integer totalStock;
    private Long startTime;
    private Long endTime;
    private ProductStatus status;
    private String imageUrl;
    
    public boolean isActive() {
        long now = System.currentTimeMillis();
        return status == ProductStatus.ACTIVE && 
               now >= startTime && 
               now <= endTime && 
               stock > 0;
    }
}

/**
 * 秒杀订单模型
 */
@Data
@Builder
public class SeckillOrder {
    private String orderId;
    private Long userId;
    private Long productId;
    private String productName;
    private BigDecimal price;
    private Integer quantity;
    private String clientIP;
    private OrderStatus status;
    private Long createTime;
    private Long updateTime;
    private String remark;
}

/**
 * 风控检查结果
 */
@Data
@Builder
public class RiskCheckResult {
    private boolean allowed;
    private String reason;
    private RiskLevel riskLevel;
    
    public static RiskCheckResult allowed() {
        return RiskCheckResult.builder()
            .allowed(true)
            .riskLevel(RiskLevel.LOW)
            .build();
    }
    
    public static RiskCheckResult blocked(String reason) {
        return RiskCheckResult.builder()
            .allowed(false)
            .reason(reason)
            .riskLevel(RiskLevel.HIGH)
            .build();
    }
}

// 枚举定义
enum ProductStatus { ACTIVE, INACTIVE, SOLD_OUT }
enum OrderStatus { PENDING, CREATED, PAID, CANCELLED, FAILED }
enum RiskLevel { LOW, MEDIUM, HIGH }
```

## 🎯 面试要点总结

### 技术亮点
1. **多级限流**：IP、用户、接口三级防护，层层过滤恶意请求
2. **原子操作**：Lua脚本保证库存扣减的原子性
3. **异步处理**：订单创建异步化，提升系统响应速度
4. **本地缓存**：Caffeine缓存热点数据，减少Redis压力

### 系统优势
- **高并发支持**：支持百万级并发请求
- **数据一致性**：分布式锁 + Lua脚本保证数据一致性
- **快速响应**：多级缓存 + 异步处理，响应时间<100ms
- **容错能力**：完善的异常处理和库存回滚机制

### 回答要点
- **架构设计**：分层架构，职责清晰，易于扩展
- **性能优化**：缓存策略、异步处理、资源复用
- **安全防护**：风控检查、限流策略、防重复提交
- **监控告警**：完整的监控指标和告警机制

---

[← 返回Java高级面试题](../../questions/company-specific/alibaba/java-advanced.md) 