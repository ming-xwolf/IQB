# Redis缓存架构完整实现

[← 返回缓存系统面试题](../../questions/backend/caching.md)

## 🎯 解决方案概述

Redis缓存架构是现代高并发系统的核心组件，本方案深入分析Redis在企业级应用中的架构设计和优化策略，提供从单机部署到集群架构的完整实现，重点解决高可用、数据一致性和性能优化等关键问题。

## 💡 核心问题分析

### Redis架构设计的技术挑战

**业务背景**：在高并发、大数据量的企业级应用中，Redis需要承担缓存、会话存储、消息队列等多重职责，要求具备高性能、高可用和可扩展性。

**技术难点**：
- **架构选择**：主从、哨兵、集群模式的选择和配置优化
- **数据一致性**：缓存与数据库的一致性保证机制
- **性能优化**：内存管理、网络优化、持久化策略
- **故障处理**：故障检测、自动切换、数据恢复

## 📝 题目1：Redis集群架构设计与高可用实现

### 解决方案思路分析

#### 1. Redis集群架构选择策略

**为什么选择Redis Cluster？**
- **水平扩展**：支持数据分片，突破单机内存限制
- **高可用性**：内置故障检测和自动故障转移
- **无中心架构**：避免单点故障，提高系统可靠性
- **客户端智能路由**：减少网络跳转，提高性能

#### 2. 数据分片和一致性哈希

**分片策略设计原理**：
- **哈希槽机制**：16384个槽位均匀分布数据
- **一致性哈希**：节点增减时最小化数据迁移
- **虚拟节点**：提高数据分布的均匀性
- **热点数据处理**：识别和优化热点key的分布

### 代码实现要点

#### Redis集群架构实现

```java
/**
 * Redis集群架构完整实现
 * 
 * 设计原理：
 * 1. 集群配置管理：动态发现和配置集群节点
 * 2. 智能路由：基于哈希槽的客户端路由
 * 3. 故障处理：自动故障检测和切换
 * 4. 性能优化：连接池、管道、批量操作
 */

import redis.clients.jedis.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.logging.Logger;

@Configuration
public class RedisClusterConfig {
    private static final Logger logger = Logger.getLogger(RedisClusterConfig.class.getName());
    
    @Value("${redis.cluster.nodes}")
    private String clusterNodes;
    
    @Value("${redis.cluster.timeout:5000}")
    private int timeout;
    
    @Value("${redis.cluster.max-redirections:3}")
    private int maxRedirections;
    
    @Bean
    public JedisCluster jedisCluster() {
        Set<HostAndPort> nodes = parseClusterNodes(clusterNodes);
        
        JedisPoolConfig poolConfig = new JedisPoolConfig();
        poolConfig.setMaxTotal(200);
        poolConfig.setMaxIdle(50);
        poolConfig.setMinIdle(10);
        poolConfig.setTestOnBorrow(true);
        poolConfig.setTestOnReturn(true);
        
        return new JedisCluster(nodes, timeout, timeout, maxRedirections, poolConfig);
    }
    
    private Set<HostAndPort> parseClusterNodes(String nodes) {
        Set<HostAndPort> hostAndPorts = new HashSet<>();
        String[] nodeArray = nodes.split(",");
        
        for (String node : nodeArray) {
            String[] parts = node.trim().split(":");
            hostAndPorts.add(new HostAndPort(parts[0], Integer.parseInt(parts[1])));
        }
        
        return hostAndPorts;
    }
}

@Service
public class RedisClusterService {
    private static final Logger logger = Logger.getLogger(RedisClusterService.class.getName());
    
    @Autowired
    private JedisCluster jedisCluster;
    
    private final ObjectMapper objectMapper = new ObjectMapper();
    
    /**
     * 字符串操作
     */
    public void set(String key, String value, int expireSeconds) {
        try {
            if (expireSeconds > 0) {
                jedisCluster.setex(key, expireSeconds, value);
            } else {
                jedisCluster.set(key, value);
            }
            logger.fine(String.format("Set key: %s", key));
        } catch (Exception e) {
            logger.severe(String.format("Failed to set key %s: %s", key, e.getMessage()));
            throw new RuntimeException("Redis set operation failed", e);
        }
    }
    
    public String get(String key) {
        try {
            String value = jedisCluster.get(key);
            logger.fine(String.format("Get key: %s, value: %s", key, value));
            return value;
        } catch (Exception e) {
            logger.severe(String.format("Failed to get key %s: %s", key, e.getMessage()));
            return null;
        }
    }
    
    /**
     * 对象缓存
     */
    public <T> void setObject(String key, T object, int expireSeconds) {
        try {
            String json = objectMapper.writeValueAsString(object);
            set(key, json, expireSeconds);
        } catch (Exception e) {
            logger.severe(String.format("Failed to set object for key %s: %s", key, e.getMessage()));
            throw new RuntimeException("Redis set object failed", e);
        }
    }
    
    public <T> T getObject(String key, Class<T> clazz) {
        try {
            String json = get(key);
            if (json != null) {
                return objectMapper.readValue(json, clazz);
            }
            return null;
        } catch (Exception e) {
            logger.severe(String.format("Failed to get object for key %s: %s", key, e.getMessage()));
            return null;
        }
    }
    
    /**
     * 哈希操作
     */
    public void hset(String key, String field, String value) {
        try {
            jedisCluster.hset(key, field, value);
            logger.fine(String.format("Hash set - key: %s, field: %s", key, field));
        } catch (Exception e) {
            logger.severe(String.format("Failed to hset key %s field %s: %s", key, field, e.getMessage()));
            throw new RuntimeException("Redis hset operation failed", e);
        }
    }
    
    public String hget(String key, String field) {
        try {
            return jedisCluster.hget(key, field);
        } catch (Exception e) {
            logger.severe(String.format("Failed to hget key %s field %s: %s", key, field, e.getMessage()));
            return null;
        }
    }
    
    public Map<String, String> hgetAll(String key) {
        try {
            return jedisCluster.hgetAll(key);
        } catch (Exception e) {
            logger.severe(String.format("Failed to hgetAll key %s: %s", key, e.getMessage()));
            return new HashMap<>();
        }
    }
    
    /**
     * 列表操作
     */
    public void lpush(String key, String... values) {
        try {
            jedisCluster.lpush(key, values);
            logger.fine(String.format("List push - key: %s, count: %d", key, values.length));
        } catch (Exception e) {
            logger.severe(String.format("Failed to lpush key %s: %s", key, e.getMessage()));
            throw new RuntimeException("Redis lpush operation failed", e);
        }
    }
    
    public List<String> lrange(String key, long start, long end) {
        try {
            return jedisCluster.lrange(key, start, end);
        } catch (Exception e) {
            logger.severe(String.format("Failed to lrange key %s: %s", key, e.getMessage()));
            return new ArrayList<>();
        }
    }
    
    /**
     * 集合操作
     */
    public void sadd(String key, String... members) {
        try {
            jedisCluster.sadd(key, members);
            logger.fine(String.format("Set add - key: %s, count: %d", key, members.length));
        } catch (Exception e) {
            logger.severe(String.format("Failed to sadd key %s: %s", key, e.getMessage()));
            throw new RuntimeException("Redis sadd operation failed", e);
        }
    }
    
    public Set<String> smembers(String key) {
        try {
            return jedisCluster.smembers(key);
        } catch (Exception e) {
            logger.severe(String.format("Failed to smembers key %s: %s", key, e.getMessage()));
            return new HashSet<>();
        }
    }
    
    /**
     * 有序集合操作
     */
    public void zadd(String key, double score, String member) {
        try {
            jedisCluster.zadd(key, score, member);
            logger.fine(String.format("Sorted set add - key: %s, member: %s, score: %f", key, member, score));
        } catch (Exception e) {
            logger.severe(String.format("Failed to zadd key %s: %s", key, e.getMessage()));
            throw new RuntimeException("Redis zadd operation failed", e);
        }
    }
    
    public List<String> zrange(String key, long start, long end) {
        try {
            return new ArrayList<>(jedisCluster.zrange(key, start, end));
        } catch (Exception e) {
            logger.severe(String.format("Failed to zrange key %s: %s", key, e.getMessage()));
            return new ArrayList<>();
        }
    }
    
    /**
     * 通用操作
     */
    public boolean exists(String key) {
        try {
            return jedisCluster.exists(key);
        } catch (Exception e) {
            logger.severe(String.format("Failed to check exists for key %s: %s", key, e.getMessage()));
            return false;
        }
    }
    
    public void delete(String key) {
        try {
            jedisCluster.del(key);
            logger.fine(String.format("Deleted key: %s", key));
        } catch (Exception e) {
            logger.severe(String.format("Failed to delete key %s: %s", key, e.getMessage()));
            throw new RuntimeException("Redis delete operation failed", e);
        }
    }
    
    public void expire(String key, int seconds) {
        try {
            jedisCluster.expire(key, seconds);
            logger.fine(String.format("Set expire for key: %s, seconds: %d", key, seconds));
        } catch (Exception e) {
            logger.severe(String.format("Failed to set expire for key %s: %s", key, e.getMessage()));
            throw new RuntimeException("Redis expire operation failed", e);
        }
    }
    
    /**
     * 批量操作
     */
    public void mset(Map<String, String> keyValues) {
        try {
            String[] keyValueArray = new String[keyValues.size() * 2];
            int index = 0;
            for (Map.Entry<String, String> entry : keyValues.entrySet()) {
                keyValueArray[index++] = entry.getKey();
                keyValueArray[index++] = entry.getValue();
            }
            jedisCluster.mset(keyValueArray);
            logger.fine(String.format("Batch set %d keys", keyValues.size()));
        } catch (Exception e) {
            logger.severe(String.format("Failed to mset: %s", e.getMessage()));
            throw new RuntimeException("Redis mset operation failed", e);
        }
    }
    
    public List<String> mget(String... keys) {
        try {
            return jedisCluster.mget(keys);
        } catch (Exception e) {
            logger.severe(String.format("Failed to mget: %s", e.getMessage()));
            return new ArrayList<>();
        }
    }
}

/**
 * Redis集群监控和管理
 */
@Component
public class RedisClusterMonitor {
    private static final Logger logger = Logger.getLogger(RedisClusterMonitor.class.getName());
    
    @Autowired
    private JedisCluster jedisCluster;
    
    private final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(2);
    
    @PostConstruct
    public void startMonitoring() {
        // 集群状态监控
        scheduler.scheduleAtFixedRate(this::monitorClusterStatus, 0, 30, TimeUnit.SECONDS);
        
        // 性能指标监控
        scheduler.scheduleAtFixedRate(this::monitorPerformance, 0, 60, TimeUnit.SECONDS);
    }
    
    private void monitorClusterStatus() {
        try {
            Map<String, JedisPool> clusterNodes = jedisCluster.getClusterNodes();
            
            logger.info("=== Redis Cluster Status ===");
            logger.info(String.format("Total nodes: %d", clusterNodes.size()));
            
            int activeNodes = 0;
            for (Map.Entry<String, JedisPool> entry : clusterNodes.entrySet()) {
                String nodeKey = entry.getKey();
                JedisPool pool = entry.getValue();
                
                try (Jedis jedis = pool.getResource()) {
                    String pong = jedis.ping();
                    if ("PONG".equals(pong)) {
                        activeNodes++;
                        logger.fine(String.format("Node %s is active", nodeKey));
                    }
                } catch (Exception e) {
                    logger.warning(String.format("Node %s is not responding: %s", nodeKey, e.getMessage()));
                }
            }
            
            logger.info(String.format("Active nodes: %d/%d", activeNodes, clusterNodes.size()));
            
        } catch (Exception e) {
            logger.severe("Failed to monitor cluster status: " + e.getMessage());
        }
    }
    
    private void monitorPerformance() {
        try {
            Map<String, JedisPool> clusterNodes = jedisCluster.getClusterNodes();
            
            logger.info("=== Redis Performance Metrics ===");
            
            for (Map.Entry<String, JedisPool> entry : clusterNodes.entrySet()) {
                String nodeKey = entry.getKey();
                JedisPool pool = entry.getValue();
                
                try (Jedis jedis = pool.getResource()) {
                    String info = jedis.info("memory");
                    parseAndLogMemoryInfo(nodeKey, info);
                    
                    String statsInfo = jedis.info("stats");
                    parseAndLogStatsInfo(nodeKey, statsInfo);
                    
                } catch (Exception e) {
                    logger.warning(String.format("Failed to get performance info from node %s: %s", 
                                                nodeKey, e.getMessage()));
                }
            }
            
        } catch (Exception e) {
            logger.severe("Failed to monitor performance: " + e.getMessage());
        }
    }
    
    private void parseAndLogMemoryInfo(String nodeKey, String info) {
        String[] lines = info.split("\r\n");
        Map<String, String> memoryInfo = new HashMap<>();
        
        for (String line : lines) {
            if (line.contains(":")) {
                String[] parts = line.split(":");
                memoryInfo.put(parts[0], parts[1]);
            }
        }
        
        String usedMemory = memoryInfo.get("used_memory_human");
        String maxMemory = memoryInfo.get("maxmemory_human");
        
        logger.info(String.format("Node %s - Memory: %s/%s", nodeKey, usedMemory, maxMemory));
    }
    
    private void parseAndLogStatsInfo(String nodeKey, String info) {
        String[] lines = info.split("\r\n");
        Map<String, String> statsInfo = new HashMap<>();
        
        for (String line : lines) {
            if (line.contains(":")) {
                String[] parts = line.split(":");
                statsInfo.put(parts[0], parts[1]);
            }
        }
        
        String totalConnections = statsInfo.get("total_connections_received");
        String totalCommands = statsInfo.get("total_commands_processed");
        
        logger.info(String.format("Node %s - Connections: %s, Commands: %s", 
                                nodeKey, totalConnections, totalCommands));
    }
    
    @PreDestroy
    public void shutdown() {
        scheduler.shutdown();
        try {
            if (!scheduler.awaitTermination(10, TimeUnit.SECONDS)) {
                scheduler.shutdownNow();
            }
        } catch (InterruptedException e) {
            scheduler.shutdownNow();
            Thread.currentThread().interrupt();
        }
    }
}

/**
 * 缓存一致性管理
 */
@Service
public class CacheConsistencyManager {
    private static final Logger logger = Logger.getLogger(CacheConsistencyManager.class.getName());
    
    @Autowired
    private RedisClusterService redisService;
    
    /**
     * Cache-Aside模式实现
     */
    public <T> T getWithCacheAside(String key, Class<T> clazz, Supplier<T> dataLoader, int expireSeconds) {
        // 先从缓存获取
        T cachedData = redisService.getObject(key, clazz);
        if (cachedData != null) {
            logger.fine("Cache hit for key: " + key);
            return cachedData;
        }
        
        // 缓存未命中，从数据源加载
        logger.fine("Cache miss for key: " + key);
        T data = dataLoader.get();
        
        if (data != null) {
            // 写入缓存
            redisService.setObject(key, data, expireSeconds);
            logger.fine("Data loaded and cached for key: " + key);
        }
        
        return data;
    }
    
    /**
     * 更新数据并删除缓存
     */
    public void updateAndEvictCache(String key, Runnable dataUpdater) {
        try {
            // 先更新数据库
            dataUpdater.run();
            
            // 再删除缓存
            redisService.delete(key);
            
            logger.info("Data updated and cache evicted for key: " + key);
            
        } catch (Exception e) {
            logger.severe(String.format("Failed to update data and evict cache for key %s: %s", 
                                       key, e.getMessage()));
            throw new RuntimeException("Update and evict operation failed", e);
        }
    }
    
    /**
     * 分布式锁实现
     */
    public boolean tryLock(String lockKey, String lockValue, int expireSeconds) {
        try {
            String result = jedisCluster.set(lockKey, lockValue, "NX", "EX", expireSeconds);
            boolean acquired = "OK".equals(result);
            
            if (acquired) {
                logger.fine(String.format("Lock acquired: %s", lockKey));
            } else {
                logger.fine(String.format("Lock acquisition failed: %s", lockKey));
            }
            
            return acquired;
            
        } catch (Exception e) {
            logger.severe(String.format("Failed to acquire lock %s: %s", lockKey, e.getMessage()));
            return false;
        }
    }
    
    public void releaseLock(String lockKey, String lockValue) {
        String luaScript = 
            "if redis.call('get', KEYS[1]) == ARGV[1] then " +
            "return redis.call('del', KEYS[1]) " +
            "else " +
            "return 0 " +
            "end";
        
        try {
            Object result = jedisCluster.eval(luaScript, Collections.singletonList(lockKey), 
                                            Collections.singletonList(lockValue));
            
            if (result.equals(1L)) {
                logger.fine(String.format("Lock released: %s", lockKey));
            } else {
                logger.warning(String.format("Lock release failed, key may have expired: %s", lockKey));
            }
            
        } catch (Exception e) {
            logger.severe(String.format("Failed to release lock %s: %s", lockKey, e.getMessage()));
        }
    }
}

#### 配置文件示例

```yaml
# Redis集群配置
redis:
  cluster:
    nodes: "192.168.1.101:7001,192.168.1.101:7002,192.168.1.102:7001,192.168.1.102:7002,192.168.1.103:7001,192.168.1.103:7002"
    timeout: 5000
    max-redirections: 3
    
# 应用配置
spring:
  redis:
    cluster:
      max-redirects: 3
    timeout: 5000ms
    jedis:
      pool:
        max-active: 200
        max-wait: -1ms
        max-idle: 50
        min-idle: 10

# 监控配置
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics
  endpoint:
    health:
      show-details: always
```

## 🎯 面试要点总结

### 技术深度体现
- **架构设计能力**：深入理解Redis集群架构和分片机制
- **高可用实现**：掌握故障检测、自动切换和数据恢复策略
- **性能优化**：连接池配置、批量操作、内存管理等优化技术
- **一致性保证**：分布式锁、缓存更新策略等一致性解决方案

### 生产实践经验
- **集群运维**：Redis集群的部署、监控和维护经验
- **性能调优**：基于业务特点进行的性能优化实践
- **故障处理**：生产环境故障的快速定位和恢复经验
- **容量规划**：基于业务增长的集群扩容和资源规划

### 面试回答要点
- **架构选择**：清晰阐述不同Redis架构模式的适用场景
- **技术原理**：深入解释哈希槽、一致性哈希等核心概念
- **实战经验**：结合具体项目展示Redis应用的价值和效果
- **问题解决**：展示解决Redis相关问题的思路和方法

---

*Redis缓存架构的核心在于平衡性能、一致性和可用性，需要根据业务特点选择合适的缓存策略* 🚀 