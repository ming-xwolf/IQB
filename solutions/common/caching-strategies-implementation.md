# 通用面试 - 缓存策略完整实现

[← 返回缓存技术面试题](../../questions/backend/caching.md)

## 🎯 解决方案概述

缓存策略是提升系统性能的关键技术，涉及多级缓存、缓存算法、一致性保证等核心问题。本方案深入分析各种缓存策略的设计原理和实现技术，展示在大规模分布式系统中的最佳实践。

## 💡 核心问题分析

### 缓存策略的技术挑战

**业务背景**：在高并发Web应用中，数据库访问成为性能瓶颈，需要通过多层缓存来提升响应速度

**技术难点**：
- 缓存命中率优化和热点数据识别
- 缓存一致性保证和数据同步策略
- 缓存穿透、雪崩、击穿等异常场景处理
- 多级缓存架构和缓存更新策略
- 内存管理和缓存淘汰算法

## 📝 题目解决方案

### 解决方案思路分析

#### 1. 缓存架构设计策略

**为什么采用多级缓存？**
- **L1本地缓存**：最快访问速度，适合热点数据
- **L2分布式缓存**：容量大，支持集群共享
- **L3数据库缓存**：持久化存储，数据安全性高
- **CDN边缘缓存**：地理分布，降低网络延迟

#### 2. 缓存算法选择原理

**不同算法的适用场景**：
- **LRU**：适合有明显访问时间局部性的场景
- **LFU**：适合有访问频率差异的场景
- **FIFO**：简单实现，适合缓存大小固定的场景
- **W-TinyLFU**：结合频率和时间，适合复杂访问模式

#### 3. 一致性保证策略

**缓存更新模式**：
- **Cache-Aside**：应用程序控制缓存更新
- **Write-Through**：同步写入缓存和数据库
- **Write-Behind**：异步写入，提高性能
- **Refresh-Ahead**：主动刷新即将过期的数据

### 代码实现要点

#### 多级缓存系统完整实现

```java
/**
 * 多级缓存系统完整实现
 * 
 * 设计原理：
 * 1. 支持多种缓存算法和淘汰策略
 * 2. 实现多级缓存穿透和数据同步
 * 3. 提供缓存预热和异常处理机制
 * 4. 支持监控统计和性能分析
 */

import java.util.concurrent.*;
import java.util.concurrent.locks.*;
import java.util.concurrent.atomic.*;
import java.time.LocalDateTime;
import java.time.Duration;

/**
 * 缓存项定义
 */
@Data
@AllArgsConstructor
public class CacheItem<V> {
    private V value;
    private long accessTime;
    private long createTime;
    private long accessCount;
    private long ttl; // Time To Live (milliseconds)
    
    public boolean isExpired() {
        return ttl > 0 && (System.currentTimeMillis() - createTime) > ttl;
    }
    
    public void updateAccess() {
        this.accessTime = System.currentTimeMillis();
        this.accessCount++;
    }
}

/**
 * LRU缓存实现
 */
public class LRUCache<K, V> {
    
    private final int capacity;
    private final ConcurrentHashMap<K, Node<K, V>> cache;
    private final Node<K, V> head;
    private final Node<K, V> tail;
    private final ReadWriteLock lock = new ReentrantReadWriteLock();
    private final AtomicLong hitCount = new AtomicLong(0);
    private final AtomicLong missCount = new AtomicLong(0);
    
    static class Node<K, V> {
        K key;
        V value;
        Node<K, V> prev;
        Node<K, V> next;
        long accessTime;
        
        Node() {}
        
        Node(K key, V value) {
            this.key = key;
            this.value = value;
            this.accessTime = System.currentTimeMillis();
        }
    }
    
    public LRUCache(int capacity) {
        this.capacity = capacity;
        this.cache = new ConcurrentHashMap<>(capacity);
        this.head = new Node<>();
        this.tail = new Node<>();
        head.next = tail;
        tail.prev = head;
    }
    
    /**
     * 获取缓存值
     */
    public V get(K key) {
        Node<K, V> node = cache.get(key);
        if (node == null) {
            missCount.incrementAndGet();
            return null;
        }
        
        hitCount.incrementAndGet();
        
        // 移动到头部（最近访问）
        lock.writeLock().lock();
        try {
            moveToHead(node);
            node.accessTime = System.currentTimeMillis();
        } finally {
            lock.writeLock().unlock();
        }
        
        return node.value;
    }
    
    /**
     * 存入缓存
     */
    public void put(K key, V value) {
        Node<K, V> existing = cache.get(key);
        
        lock.writeLock().lock();
        try {
            if (existing != null) {
                // 更新现有节点
                existing.value = value;
                existing.accessTime = System.currentTimeMillis();
                moveToHead(existing);
            } else {
                // 创建新节点
                Node<K, V> newNode = new Node<>(key, value);
                
                if (cache.size() >= capacity) {
                    // 淘汰最久未使用的节点
                    Node<K, V> tail = removeTail();
                    cache.remove(tail.key);
                }
                
                cache.put(key, newNode);
                addToHead(newNode);
            }
        } finally {
            lock.writeLock().unlock();
        }
    }
    
    /**
     * 移除缓存
     */
    public void remove(K key) {
        Node<K, V> node = cache.remove(key);
        if (node != null) {
            lock.writeLock().lock();
            try {
                removeNode(node);
            } finally {
                lock.writeLock().unlock();
            }
        }
    }
    
    private void addToHead(Node<K, V> node) {
        node.prev = head;
        node.next = head.next;
        head.next.prev = node;
        head.next = node;
    }
    
    private void removeNode(Node<K, V> node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }
    
    private void moveToHead(Node<K, V> node) {
        removeNode(node);
        addToHead(node);
    }
    
    private Node<K, V> removeTail() {
        Node<K, V> lastNode = tail.prev;
        removeNode(lastNode);
        return lastNode;
    }
    
    /**
     * 获取缓存统计信息
     */
    public CacheStats getStats() {
        long hits = hitCount.get();
        long misses = missCount.get();
        long total = hits + misses;
        double hitRate = total == 0 ? 0.0 : (double) hits / total;
        
        return new CacheStats(hits, misses, hitRate, cache.size(), capacity);
    }
}

/**
 * LFU缓存实现
 */
public class LFUCache<K, V> {
    
    private final int capacity;
    private final ConcurrentHashMap<K, Node<K, V>> cache;
    private final ConcurrentHashMap<Integer, FrequencyNode<K, V>> frequencies;
    private final AtomicInteger minFrequency = new AtomicInteger(1);
    private final ReadWriteLock lock = new ReentrantReadWriteLock();
    
    static class Node<K, V> {
        K key;
        V value;
        int frequency;
        Node<K, V> prev, next;
        
        Node(K key, V value) {
            this.key = key;
            this.value = value;
            this.frequency = 1;
        }
    }
    
    static class FrequencyNode<K, V> {
        int frequency;
        Node<K, V> head, tail;
        
        FrequencyNode(int frequency) {
            this.frequency = frequency;
            this.head = new Node<>(null, null);
            this.tail = new Node<>(null, null);
            head.next = tail;
            tail.prev = head;
        }
        
        void addNode(Node<K, V> node) {
            node.next = head.next;
            node.prev = head;
            head.next.prev = node;
            head.next = node;
        }
        
        void removeNode(Node<K, V> node) {
            node.prev.next = node.next;
            node.next.prev = node.prev;
        }
        
        Node<K, V> removeTail() {
            Node<K, V> lastNode = tail.prev;
            if (lastNode != head) {
                removeNode(lastNode);
                return lastNode;
            }
            return null;
        }
        
        boolean isEmpty() {
            return head.next == tail;
        }
    }
    
    public LFUCache(int capacity) {
        this.capacity = capacity;
        this.cache = new ConcurrentHashMap<>(capacity);
        this.frequencies = new ConcurrentHashMap<>();
    }
    
    public V get(K key) {
        Node<K, V> node = cache.get(key);
        if (node == null) {
            return null;
        }
        
        updateFrequency(node);
        return node.value;
    }
    
    public void put(K key, V value) {
        if (capacity <= 0) return;
        
        lock.writeLock().lock();
        try {
            Node<K, V> existing = cache.get(key);
            if (existing != null) {
                existing.value = value;
                updateFrequency(existing);
                return;
            }
            
            if (cache.size() >= capacity) {
                evictLFU();
            }
            
            Node<K, V> newNode = new Node<>(key, value);
            cache.put(key, newNode);
            
            FrequencyNode<K, V> freqNode = frequencies.computeIfAbsent(1, 
                k -> new FrequencyNode<>(1));
            freqNode.addNode(newNode);
            minFrequency.set(1);
            
        } finally {
            lock.writeLock().unlock();
        }
    }
    
    private void updateFrequency(Node<K, V> node) {
        int oldFreq = node.frequency;
        int newFreq = oldFreq + 1;
        
        FrequencyNode<K, V> oldFreqNode = frequencies.get(oldFreq);
        oldFreqNode.removeNode(node);
        
        if (oldFreqNode.isEmpty() && oldFreq == minFrequency.get()) {
            minFrequency.incrementAndGet();
        }
        
        node.frequency = newFreq;
        FrequencyNode<K, V> newFreqNode = frequencies.computeIfAbsent(newFreq, 
            k -> new FrequencyNode<>(newFreq));
        newFreqNode.addNode(node);
    }
    
    private void evictLFU() {
        FrequencyNode<K, V> minFreqNode = frequencies.get(minFrequency.get());
        Node<K, V> nodeToRemove = minFreqNode.removeTail();
        if (nodeToRemove != null) {
            cache.remove(nodeToRemove.key);
        }
    }
}

/**
 * 多级缓存管理器
 */
public class MultiLevelCacheManager<K, V> {
    
    private final LRUCache<K, V> l1Cache; // 本地缓存
    private final RedisCache<K, V> l2Cache; // 分布式缓存
    private final DatabaseCache<K, V> l3Cache; // 数据库缓存
    
    private final ScheduledExecutorService scheduler;
    private final CacheMetrics metrics;
    
    public MultiLevelCacheManager(int l1Size, RedisCache<K, V> l2Cache, 
                                 DatabaseCache<K, V> l3Cache) {
        this.l1Cache = new LRUCache<>(l1Size);
        this.l2Cache = l2Cache;
        this.l3Cache = l3Cache;
        this.scheduler = Executors.newScheduledThreadPool(2);
        this.metrics = new CacheMetrics();
        
        // 启动缓存预热和清理任务
        startBackgroundTasks();
    }
    
    /**
     * 获取数据 - 多级缓存穿透
     */
    public V get(K key) {
        long startTime = System.currentTimeMillis();
        
        try {
            // L1缓存查找
            V value = l1Cache.get(key);
            if (value != null) {
                metrics.recordHit("L1", System.currentTimeMillis() - startTime);
                return value;
            }
            
            // L2缓存查找
            value = l2Cache.get(key);
            if (value != null) {
                // 回填L1缓存
                l1Cache.put(key, value);
                metrics.recordHit("L2", System.currentTimeMillis() - startTime);
                return value;
            }
            
            // L3数据库查找
            value = l3Cache.get(key);
            if (value != null) {
                // 回填L1和L2缓存
                l1Cache.put(key, value);
                l2Cache.put(key, value);
                metrics.recordHit("L3", System.currentTimeMillis() - startTime);
                return value;
            }
            
            metrics.recordMiss(System.currentTimeMillis() - startTime);
            return null;
            
        } catch (Exception e) {
            metrics.recordError();
            throw new CacheException("缓存获取失败", e);
        }
    }
    
    /**
     * 写入数据 - 多级缓存更新
     */
    public void put(K key, V value) {
        try {
            // Write-Through模式：同步写入所有级别
            l1Cache.put(key, value);
            l2Cache.put(key, value);
            l3Cache.put(key, value);
            
            metrics.recordWrite();
            
        } catch (Exception e) {
            metrics.recordError();
            throw new CacheException("缓存写入失败", e);
        }
    }
    
    /**
     * 删除数据 - 多级缓存失效
     */
    public void evict(K key) {
        try {
            l1Cache.remove(key);
            l2Cache.remove(key);
            l3Cache.remove(key);
            
            metrics.recordEviction();
            
        } catch (Exception e) {
            metrics.recordError();
            throw new CacheException("缓存删除失败", e);
        }
    }
    
    /**
     * 缓存预热
     */
    public void warmUp(Collection<K> keys) {
        CompletableFuture.runAsync(() -> {
            for (K key : keys) {
                try {
                    V value = l3Cache.get(key);
                    if (value != null) {
                        l1Cache.put(key, value);
                        l2Cache.put(key, value);
                    }
                } catch (Exception e) {
                    // 记录错误但继续预热其他数据
                    System.err.println("预热失败: " + key + ", " + e.getMessage());
                }
            }
        });
    }
    
    /**
     * 启动后台任务
     */
    private void startBackgroundTasks() {
        // 定期清理过期数据
        scheduler.scheduleAtFixedRate(this::cleanupExpiredEntries, 
            1, 1, TimeUnit.MINUTES);
        
        // 定期输出统计信息
        scheduler.scheduleAtFixedRate(this::logCacheStats, 
            5, 5, TimeUnit.MINUTES);
    }
    
    private void cleanupExpiredEntries() {
        // L2和L3缓存的过期清理由各自实现
        // 这里可以添加L1缓存的过期清理逻辑
    }
    
    private void logCacheStats() {
        CacheStats l1Stats = l1Cache.getStats();
        System.out.printf("缓存统计 - L1命中率: %.2f%%, L2命中率: %.2f%%, L3命中率: %.2f%%%n",
            l1Stats.getHitRate() * 100,
            l2Cache.getHitRate() * 100,
            l3Cache.getHitRate() * 100);
    }
    
    /**
     * 获取综合统计信息
     */
    public CacheMetrics getMetrics() {
        return metrics;
    }
    
    /**
     * 关闭缓存管理器
     */
    public void shutdown() {
        scheduler.shutdown();
        try {
            if (!scheduler.awaitTermination(60, TimeUnit.SECONDS)) {
                scheduler.shutdownNow();
            }
        } catch (InterruptedException e) {
            scheduler.shutdownNow();
            Thread.currentThread().interrupt();
        }
    }
}

/**
 * 缓存统计信息
 */
@Data
@AllArgsConstructor
public class CacheStats {
    private long hitCount;
    private long missCount;
    private double hitRate;
    private int currentSize;
    private int maxSize;
    
    public long getTotalRequests() {
        return hitCount + missCount;
    }
}

/**
 * 缓存指标收集器
 */
public class CacheMetrics {
    private final AtomicLong l1Hits = new AtomicLong(0);
    private final AtomicLong l2Hits = new AtomicLong(0);
    private final AtomicLong l3Hits = new AtomicLong(0);
    private final AtomicLong misses = new AtomicLong(0);
    private final AtomicLong writes = new AtomicLong(0);
    private final AtomicLong evictions = new AtomicLong(0);
    private final AtomicLong errors = new AtomicLong(0);
    
    private final HistogramMetric responseTime = new HistogramMetric();
    
    public void recordHit(String level, long responseTimeMs) {
        switch (level) {
            case "L1": l1Hits.incrementAndGet(); break;
            case "L2": l2Hits.incrementAndGet(); break;
            case "L3": l3Hits.incrementAndGet(); break;
        }
        responseTime.record(responseTimeMs);
    }
    
    public void recordMiss(long responseTimeMs) {
        misses.incrementAndGet();
        responseTime.record(responseTimeMs);
    }
    
    public void recordWrite() { writes.incrementAndGet(); }
    public void recordEviction() { evictions.incrementAndGet(); }
    public void recordError() { errors.incrementAndGet(); }
    
    public double getOverallHitRate() {
        long totalHits = l1Hits.get() + l2Hits.get() + l3Hits.get();
        long totalRequests = totalHits + misses.get();
        return totalRequests == 0 ? 0.0 : (double) totalHits / totalRequests;
    }
    
    public void printSummary() {
        System.out.println("=== 缓存性能统计 ===");
        System.out.printf("L1命中: %d, L2命中: %d, L3命中: %d, 未命中: %d%n",
            l1Hits.get(), l2Hits.get(), l3Hits.get(), misses.get());
        System.out.printf("总体命中率: %.2f%%%n", getOverallHitRate() * 100);
        System.out.printf("平均响应时间: %.2f ms%n", responseTime.getAverage());
        System.out.printf("写入次数: %d, 淘汰次数: %d, 错误次数: %d%n",
            writes.get(), evictions.get(), errors.get());
    }
}

/**
 * 简单的直方图指标
 */
class HistogramMetric {
    private final AtomicLong sum = new AtomicLong(0);
    private final AtomicLong count = new AtomicLong(0);
    
    public void record(long value) {
        sum.addAndGet(value);
        count.incrementAndGet();
    }
    
    public double getAverage() {
        long totalCount = count.get();
        return totalCount == 0 ? 0.0 : (double) sum.get() / totalCount;
    }
}

/**
 * Redis缓存实现（模拟）
 */
class RedisCache<K, V> {
    // 实际实现中会使用Jedis或Lettuce等Redis客户端
    private final Map<K, V> redisSimulation = new ConcurrentHashMap<>();
    private final AtomicLong hitCount = new AtomicLong(0);
    private final AtomicLong missCount = new AtomicLong(0);
    
    public V get(K key) {
        V value = redisSimulation.get(key);
        if (value != null) {
            hitCount.incrementAndGet();
        } else {
            missCount.incrementAndGet();
        }
        return value;
    }
    
    public void put(K key, V value) {
        redisSimulation.put(key, value);
    }
    
    public void remove(K key) {
        redisSimulation.remove(key);
    }
    
    public double getHitRate() {
        long hits = hitCount.get();
        long total = hits + missCount.get();
        return total == 0 ? 0.0 : (double) hits / total;
    }
}

/**
 * 数据库缓存实现（模拟）
 */
class DatabaseCache<K, V> {
    // 实际实现中会使用JDBC或ORM框架
    private final Map<K, V> databaseSimulation = new ConcurrentHashMap<>();
    private final AtomicLong hitCount = new AtomicLong(0);
    private final AtomicLong missCount = new AtomicLong(0);
    
    public V get(K key) {
        // 模拟数据库查询延迟
        try {
            Thread.sleep(10);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        
        V value = databaseSimulation.get(key);
        if (value != null) {
            hitCount.incrementAndGet();
        } else {
            missCount.incrementAndGet();
        }
        return value;
    }
    
    public void put(K key, V value) {
        databaseSimulation.put(key, value);
    }
    
    public void remove(K key) {
        databaseSimulation.remove(key);
    }
    
    public double getHitRate() {
        long hits = hitCount.get();
        long total = hits + missCount.get();
        return total == 0 ? 0.0 : (double) hits / total;
    }
}

/**
 * 缓存异常类
 */
class CacheException extends RuntimeException {
    public CacheException(String message) {
        super(message);
    }
    
    public CacheException(String message, Throwable cause) {
        super(message, cause);
    }
}

/**
 * 使用示例和测试
 */
public class CacheSystemDemo {
    
    public static void main(String[] args) throws InterruptedException {
        // 创建多级缓存系统
        RedisCache<String, String> redisCache = new RedisCache<>();
        DatabaseCache<String, String> dbCache = new DatabaseCache<>();
        MultiLevelCacheManager<String, String> cacheManager = 
            new MultiLevelCacheManager<>(100, redisCache, dbCache);
        
        // 预填充数据库
        for (int i = 0; i < 1000; i++) {
            dbCache.put("key" + i, "value" + i);
        }
        
        // 缓存预热
        List<String> warmupKeys = IntStream.range(0, 50)
            .mapToObj(i -> "key" + i)
            .collect(Collectors.toList());
        cacheManager.warmUp(warmupKeys);
        
        // 模拟并发访问
        ExecutorService executor = Executors.newFixedThreadPool(10);
        CountDownLatch latch = new CountDownLatch(1000);
        
        for (int i = 0; i < 1000; i++) {
            final int index = i;
            executor.submit(() -> {
                try {
                    String key = "key" + (index % 200); // 模拟热点数据
                    String value = cacheManager.get(key);
                    
                    if (value == null && index % 100 == 0) {
                        // 模拟写入新数据
                        cacheManager.put(key, "newValue" + index);
                    }
                } finally {
                    latch.countDown();
                }
            });
        }
        
        latch.await();
        
        // 输出统计信息
        cacheManager.getMetrics().printSummary();
        
        // 清理资源
        executor.shutdown();
        cacheManager.shutdown();
    }
} 