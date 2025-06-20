# 通用面试 - API性能优化完整实现

[← 返回性能优化面试题](../../questions/backend/performance-optimization.md)

## 🎯 解决方案概述

API性能优化是后端开发中的核心技能，涉及缓存策略、数据库优化、网络优化、架构设计等多个维度。本方案提供了一套完整的API性能优化解决方案，从单个接口优化到整体架构优化，包含具体的实现策略和监控方案。

## 💡 核心问题分析

### API性能优化的技术挑战

**业务背景**：现代应用对API性能要求越来越高，需要在高并发场景下保持低延迟和高吞吐量

**技术难点**：
- 数据库查询性能瓶颈和N+1查询问题
- 缓存设计和缓存一致性保证
- 网络延迟和带宽优化
- 代码层面的性能优化和资源管理
- 架构层面的扩展性和负载均衡

## 📝 题目解决方案

### 解决方案思路分析

#### 1. 缓存优化策略

**为什么选择多级缓存架构？**
- **应用缓存**：内存缓存减少计算开销
- **分布式缓存**：Redis集群提供高可用缓存
- **CDN缓存**：静态资源和API响应的边缘缓存
- **数据库缓存**：查询结果缓存和连接池优化

#### 2. 数据库优化策略

**完整优化方案**：
- **索引优化**：复合索引、覆盖索引、部分索引
- **查询优化**：避免N+1、批量查询、分页优化
- **连接池管理**：连接数控制、超时设置、监控
- **读写分离**：主从复制、读写分离中间件

#### 3. 网络和协议优化

**网络层优化**：
- **HTTP/2**：多路复用、服务器推送、头部压缩
- **压缩算法**：Gzip、Brotli响应压缩
- **Keep-Alive**：连接复用和超时控制
- **批量请求**：GraphQL、批量API设计

### 代码实现要点

#### API性能优化完整实现

```javascript
/**
 * API性能优化完整实现
 * 
 * 设计原理：
 * 1. 多级缓存架构，从内存到分布式缓存
 * 2. 数据库连接池和查询优化
 * 3. 响应压缩和网络优化
 * 4. 异步处理和资源管理
 */

const express = require('express');
const compression = require('compression');
const redis = require('redis');
const { Pool } = require('pg');
const LRU = require('lru-cache');

// ==================== 多级缓存管理器 ====================

/**
 * 多级缓存管理器
 */
class MultiLevelCacheManager {
    constructor(config) {
        this.config = config;
        
        // L1缓存：进程内存缓存
        this.l1Cache = new LRU({
            max: config.l1.maxSize || 1000,
            ttl: config.l1.ttl || 300000 // 5分钟
        });
        
        // L2缓存：Redis分布式缓存
        this.l2Cache = redis.createClient(config.redis);
        this.l2Cache.connect();
        
        // 缓存统计
        this.stats = {
            l1Hits: 0,
            l2Hits: 0,
            misses: 0,
            sets: 0
        };
    }

    /**
     * 获取缓存数据
     */
    async get(key) {
        try {
            // 尝试L1缓存
            const l1Value = this.l1Cache.get(key);
            if (l1Value !== undefined) {
                this.stats.l1Hits++;
                return JSON.parse(l1Value);
            }

            // 尝试L2缓存
            const l2Value = await this.l2Cache.get(key);
            if (l2Value !== null) {
                this.stats.l2Hits++;
                
                // 回填L1缓存
                this.l1Cache.set(key, l2Value);
                return JSON.parse(l2Value);
            }

            this.stats.misses++;
            return null;
        } catch (error) {
            console.error('缓存获取失败:', error);
            return null;
        }
    }

    /**
     * 设置缓存数据
     */
    async set(key, value, ttl = null) {
        try {
            const serializedValue = JSON.stringify(value);
            
            // 设置L1缓存
            this.l1Cache.set(key, serializedValue);
            
            // 设置L2缓存
            if (ttl) {
                await this.l2Cache.setEx(key, ttl, serializedValue);
            } else {
                await this.l2Cache.set(key, serializedValue);
            }
            
            this.stats.sets++;
        } catch (error) {
            console.error('缓存设置失败:', error);
        }
    }

    /**
     * 删除缓存
     */
    async delete(key) {
        try {
            this.l1Cache.delete(key);
            await this.l2Cache.del(key);
        } catch (error) {
            console.error('缓存删除失败:', error);
        }
    }

    /**
     * 清空缓存
     */
    async clear() {
        try {
            this.l1Cache.clear();
            await this.l2Cache.flushAll();
        } catch (error) {
            console.error('缓存清空失败:', error);
        }
    }

    /**
     * 获取缓存统计
     */
    getStats() {
        const total = this.stats.l1Hits + this.stats.l2Hits + this.stats.misses;
        return {
            ...this.stats,
            l1HitRate: total > 0 ? this.stats.l1Hits / total : 0,
            l2HitRate: total > 0 ? this.stats.l2Hits / total : 0,
            missRate: total > 0 ? this.stats.misses / total : 0,
            totalRequests: total
        };
    }
}

// ==================== 数据库优化管理器 ====================

/**
 * 数据库连接池和查询优化器
 */
class DatabaseOptimizer {
    constructor(config) {
        this.config = config;
        
        // 创建连接池
        this.pool = new Pool({
            host: config.host,
            port: config.port,
            database: config.database,
            user: config.user,
            password: config.password,
            max: config.maxConnections || 20,
            min: config.minConnections || 5,
            acquireTimeoutMillis: config.acquireTimeout || 5000,
            createTimeoutMillis: config.createTimeout || 5000,
            idleTimeoutMillis: config.idleTimeout || 30000,
            createRetryIntervalMillis: config.retryInterval || 200,
            connectionTimeoutMillis: config.connectionTimeout || 5000
        });

        // 查询缓存
        this.queryCache = new Map();
        this.preparedStatements = new Map();
        
        // 监控指标
        this.metrics = {
            totalQueries: 0,
            slowQueries: 0,
            cacheHits: 0,
            connectionErrors: 0
        };
    }

    /**
     * 执行优化查询
     */
    async executeQuery(sql, params = [], options = {}) {
        const startTime = Date.now();
        const client = await this.pool.connect();
        
        try {
            this.metrics.totalQueries++;
            
            // 查询缓存检查
            const cacheKey = this.generateCacheKey(sql, params);
            if (options.cache && this.queryCache.has(cacheKey)) {
                this.metrics.cacheHits++;
                return this.queryCache.get(cacheKey);
            }

            // 执行查询
            const result = await client.query(sql, params);
            const executionTime = Date.now() - startTime;
            
            // 慢查询检测
            if (executionTime > (options.slowQueryThreshold || 1000)) {
                this.metrics.slowQueries++;
                console.warn(`慢查询检测: ${sql} 耗时 ${executionTime}ms`);
            }

            // 缓存结果
            if (options.cache && options.cacheTTL) {
                this.queryCache.set(cacheKey, result);
                setTimeout(() => {
                    this.queryCache.delete(cacheKey);
                }, options.cacheTTL);
            }

            return result;
        } catch (error) {
            this.metrics.connectionErrors++;
            console.error('数据库查询失败:', error);
            throw error;
        } finally {
            client.release();
        }
    }

    /**
     * 批量查询优化
     */
    async executeBatchQuery(queries) {
        const client = await this.pool.connect();
        
        try {
            await client.query('BEGIN');
            
            const results = [];
            for (const { sql, params } of queries) {
                const result = await client.query(sql, params);
                results.push(result);
            }
            
            await client.query('COMMIT');
            return results;
        } catch (error) {
            await client.query('ROLLBACK');
            throw error;
        } finally {
            client.release();
        }
    }

    /**
     * 预编译语句管理
     */
    async prepareStatement(name, sql) {
        if (!this.preparedStatements.has(name)) {
            const client = await this.pool.connect();
            try {
                await client.query(`PREPARE ${name} AS ${sql}`);
                this.preparedStatements.set(name, sql);
            } finally {
                client.release();
            }
        }
    }

    /**
     * 执行预编译语句
     */
    async executePrepared(name, params = []) {
        const client = await this.pool.connect();
        try {
            return await client.query(`EXECUTE ${name}(${params.map((_, i) => `$${i + 1}`).join(',')})`, params);
        } finally {
            client.release();
        }
    }

    /**
     * 生成缓存键
     */
    generateCacheKey(sql, params) {
        return `query:${Buffer.from(sql + JSON.stringify(params)).toString('base64')}`;
    }

    /**
     * 获取数据库指标
     */
    getMetrics() {
        return {
            ...this.metrics,
            activeConnections: this.pool.totalCount,
            idleConnections: this.pool.idleCount,
            waitingClients: this.pool.waitingCount
        };
    }

    /**
     * 关闭连接池
     */
    async close() {
        await this.pool.end();
    }
}

// ==================== 响应优化中间件 ====================

/**
 * 响应优化中间件
 */
class ResponseOptimizer {
    constructor(options = {}) {
        this.options = {
            enableCompression: options.enableCompression !== false,
            enableETag: options.enableETag !== false,
            enableCaching: options.enableCaching !== false,
            compressionLevel: options.compressionLevel || 6,
            cacheMaxAge: options.cacheMaxAge || 3600,
            ...options
        };
    }

    /**
     * 创建压缩中间件
     */
    createCompressionMiddleware() {
        return compression({
            level: this.options.compressionLevel,
            threshold: 1024, // 大于1KB才压缩
            filter: (req, res) => {
                // 跳过已压缩的响应
                if (res.getHeader('content-encoding')) {
                    return false;
                }
                
                // 检查Accept-Encoding头
                return compression.filter(req, res);
            }
        });
    }

    /**
     * 创建ETag中间件
     */
    createETagMiddleware() {
        return (req, res, next) => {
            if (!this.options.enableETag) {
                return next();
            }

            const originalSend = res.send;
            res.send = function(data) {
                if (data && typeof data === 'string' || Buffer.isBuffer(data)) {
                    const etag = this.generateETag(data);
                    res.setHeader('ETag', etag);
                    
                    // 检查If-None-Match头
                    const ifNoneMatch = req.get('If-None-Match');
                    if (ifNoneMatch === etag) {
                        res.status(304);
                        return res.end();
                    }
                }
                
                return originalSend.call(this, data);
            }.bind(this);

            next();
        };
    }

    /**
     * 生成ETag
     */
    generateETag(data) {
        const crypto = require('crypto');
        return `"${crypto.createHash('md5').update(data).digest('hex')}"`;
    }

    /**
     * 创建缓存控制中间件
     */
    createCacheControlMiddleware() {
        return (req, res, next) => {
            if (!this.options.enableCaching) {
                return next();
            }

            // 为GET请求设置缓存头
            if (req.method === 'GET') {
                res.setHeader('Cache-Control', `public, max-age=${this.options.cacheMaxAge}`);
            } else {
                res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
            }

            next();
        };
    }

    /**
     * 创建响应时间中间件
     */
    createResponseTimeMiddleware() {
        return (req, res, next) => {
            const startTime = Date.now();
            
            res.on('finish', () => {
                const responseTime = Date.now() - startTime;
                res.setHeader('X-Response-Time', `${responseTime}ms`);
            });

            next();
        };
    }
}

// ==================== API性能监控器 ====================

/**
 * API性能监控器
 */
class APIPerformanceMonitor {
    constructor() {
        this.metrics = new Map();
        this.alertThresholds = {
            responseTime: 1000, // 1秒
            errorRate: 0.05,    // 5%
            throughput: 100     // 100 req/min
        };
    }

    /**
     * 记录API调用指标
     */
    recordMetric(apiPath, method, responseTime, statusCode, requestSize, responseSize) {
        const key = `${method}:${apiPath}`;
        
        if (!this.metrics.has(key)) {
            this.metrics.set(key, {
                totalRequests: 0,
                totalResponseTime: 0,
                errorCount: 0,
                requestSizes: [],
                responseSizes: [],
                lastMinuteRequests: [],
                timestamps: []
            });
        }

        const metric = this.metrics.get(key);
        const now = Date.now();
        
        // 更新基础指标
        metric.totalRequests++;
        metric.totalResponseTime += responseTime;
        metric.timestamps.push(now);
        
        if (statusCode >= 400) {
            metric.errorCount++;
        }
        
        if (requestSize) {
            metric.requestSizes.push(requestSize);
        }
        
        if (responseSize) {
            metric.responseSizes.push(responseSize);
        }

        // 维护最近一分钟的请求记录
        const oneMinuteAgo = now - 60000;
        metric.lastMinuteRequests = metric.lastMinuteRequests.filter(time => time > oneMinuteAgo);
        metric.lastMinuteRequests.push(now);

        // 清理过期的时间戳（保留最近24小时）
        const oneDayAgo = now - 86400000;
        metric.timestamps = metric.timestamps.filter(time => time > oneDayAgo);

        // 检查告警条件
        this.checkAlerts(key, metric, responseTime, statusCode);
    }

    /**
     * 检查告警条件
     */
    checkAlerts(apiKey, metric, responseTime, statusCode) {
        // 响应时间告警
        if (responseTime > this.alertThresholds.responseTime) {
            console.warn(`⚠️ API响应时间告警: ${apiKey} 响应时间 ${responseTime}ms`);
        }

        // 错误率告警
        const errorRate = metric.errorCount / metric.totalRequests;
        if (errorRate > this.alertThresholds.errorRate && metric.totalRequests > 10) {
            console.warn(`⚠️ API错误率告警: ${apiKey} 错误率 ${(errorRate * 100).toFixed(2)}%`);
        }

        // 吞吐量告警（每分钟请求数过低）
        const currentThroughput = metric.lastMinuteRequests.length;
        if (currentThroughput > 0 && currentThroughput < this.alertThresholds.throughput) {
            console.warn(`⚠️ API吞吐量告警: ${apiKey} 当前吞吐量 ${currentThroughput} req/min`);
        }
    }

    /**
     * 获取API性能报告
     */
    getPerformanceReport(apiPath = null, method = null) {
        const reports = [];
        
        for (const [key, metric] of this.metrics) {
            const [metricMethod, metricPath] = key.split(':', 2);
            
            // 过滤条件
            if (apiPath && metricPath !== apiPath) continue;
            if (method && metricMethod !== method) continue;
            
            const avgResponseTime = metric.totalRequests > 0 ? 
                metric.totalResponseTime / metric.totalRequests : 0;
            const errorRate = metric.totalRequests > 0 ? 
                metric.errorCount / metric.totalRequests : 0;
            const currentThroughput = metric.lastMinuteRequests.length;
            
            reports.push({
                api: metricPath,
                method: metricMethod,
                totalRequests: metric.totalRequests,
                avgResponseTime: Math.round(avgResponseTime),
                errorRate: Math.round(errorRate * 10000) / 100, // 百分比，保留2位小数
                currentThroughput,
                avgRequestSize: this.calculateAverage(metric.requestSizes),
                avgResponseSize: this.calculateAverage(metric.responseSizes)
            });
        }
        
        return reports.sort((a, b) => b.totalRequests - a.totalRequests);
    }

    /**
     * 计算平均值
     */
    calculateAverage(values) {
        if (values.length === 0) return 0;
        const sum = values.reduce((acc, val) => acc + val, 0);
        return Math.round(sum / values.length);
    }

    /**
     * 重置统计数据
     */
    reset() {
        this.metrics.clear();
    }
}

// ==================== 完整性能优化解决方案 ====================

/**
 * API性能优化解决方案
 */
class APIPerformanceOptimizer {
    constructor(config) {
        this.config = config;
        
        // 初始化各个组件
        this.cacheManager = new MultiLevelCacheManager(config.cache);
        this.dbOptimizer = new DatabaseOptimizer(config.database);
        this.responseOptimizer = new ResponseOptimizer(config.response);
        this.performanceMonitor = new APIPerformanceMonitor();
        
        this.app = express();
        this.setupMiddlewares();
    }

    /**
     * 设置中间件
     */
    setupMiddlewares() {
        // 性能监控中间件
        this.app.use((req, res, next) => {
            const startTime = Date.now();
            const originalSend = res.send;
            
            res.send = function(data) {
                const responseTime = Date.now() - startTime;
                const requestSize = req.get('content-length') || 0;
                const responseSize = Buffer.byteLength(data || '');
                
                // 记录性能指标
                this.performanceMonitor.recordMetric(
                    req.route ? req.route.path : req.path,
                    req.method,
                    responseTime,
                    res.statusCode,
                    parseInt(requestSize),
                    responseSize
                );
                
                return originalSend.call(this, data);
            }.bind(this);
            
            next();
        });

        // 响应优化中间件
        if (this.responseOptimizer.options.enableCompression) {
            this.app.use(this.responseOptimizer.createCompressionMiddleware());
        }
        
        this.app.use(this.responseOptimizer.createETagMiddleware());
        this.app.use(this.responseOptimizer.createCacheControlMiddleware());
        this.app.use(this.responseOptimizer.createResponseTimeMiddleware());

        // JSON解析中间件
        this.app.use(express.json({ limit: '10mb' }));
        this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));
    }

    /**
     * 创建缓存装饰器
     */
    createCacheDecorator(key, ttl = 300) {
        return (target, propertyName, descriptor) => {
            const originalMethod = descriptor.value;
            
            descriptor.value = async function(...args) {
                const cacheKey = typeof key === 'function' ? key(...args) : key;
                
                // 尝试从缓存获取
                const cached = await this.cacheManager.get(cacheKey);
                if (cached !== null) {
                    return cached;
                }
                
                // 执行原始方法
                const result = await originalMethod.apply(this, args);
                
                // 存储到缓存
                await this.cacheManager.set(cacheKey, result, ttl);
                
                return result;
            }.bind(this);
            
            return descriptor;
        };
    }

    /**
     * 创建数据库查询优化方法
     */
    async queryWithOptimization(sql, params = [], options = {}) {
        return await this.dbOptimizer.executeQuery(sql, params, {
            cache: true,
            cacheTTL: 300000, // 5分钟
            slowQueryThreshold: 1000,
            ...options
        });
    }

    /**
     * 批量数据处理
     */
    async processBatchData(items, processor, batchSize = 100) {
        const results = [];
        
        for (let i = 0; i < items.length; i += batchSize) {
            const batch = items.slice(i, i + batchSize);
            const batchResults = await Promise.all(
                batch.map(item => processor(item))
            );
            results.push(...batchResults);
            
            // 让出事件循环控制权
            await new Promise(resolve => setImmediate(resolve));
        }
        
        return results;
    }

    /**
     * 启动性能优化的Express应用
     */
    listen(port, callback) {
        return this.app.listen(port, callback);
    }

    /**
     * 获取性能报告
     */
    getPerformanceReport() {
        return {
            api: this.performanceMonitor.getPerformanceReport(),
            cache: this.cacheManager.getStats(),
            database: this.dbOptimizer.getMetrics()
        };
    }

    /**
     * 关闭优化器
     */
    async close() {
        await this.dbOptimizer.close();
        await this.cacheManager.l2Cache.disconnect();
    }
}

// ==================== 使用示例 ====================

/**
 * 性能优化使用示例
 */
async function createOptimizedAPIExample() {
    const config = {
        cache: {
            l1: { maxSize: 1000, ttl: 300000 },
            redis: { host: 'localhost', port: 6379 }
        },
        database: {
            host: 'localhost',
            port: 5432,
            database: 'testdb',
            user: 'user',
            password: 'password',
            maxConnections: 20
        },
        response: {
            enableCompression: true,
            enableETag: true,
            enableCaching: true,
            compressionLevel: 6,
            cacheMaxAge: 3600
        }
    };

    const optimizer = new APIPerformanceOptimizer(config);

    // 示例API：用户列表（带缓存）
    optimizer.app.get('/api/users', async (req, res) => {
        try {
            const cacheKey = `users:page:${req.query.page || 1}`;
            const cached = await optimizer.cacheManager.get(cacheKey);
            
            if (cached) {
                return res.json(cached);
            }

            const page = parseInt(req.query.page) || 1;
            const limit = parseInt(req.query.limit) || 10;
            const offset = (page - 1) * limit;

            const result = await optimizer.queryWithOptimization(
                'SELECT * FROM users ORDER BY created_at DESC LIMIT $1 OFFSET $2',
                [limit, offset],
                { cache: true, cacheTTL: 300000 }
            );

            const response = {
                users: result.rows,
                pagination: {
                    page,
                    limit,
                    total: result.rowCount
                }
            };

            await optimizer.cacheManager.set(cacheKey, response, 300);
            res.json(response);
        } catch (error) {
            console.error('用户列表查询失败:', error);
            res.status(500).json({ error: 'Internal Server Error' });
        }
    });

    // 示例API：批量用户创建
    optimizer.app.post('/api/users/batch', async (req, res) => {
        try {
            const users = req.body.users;
            
            if (!Array.isArray(users) || users.length === 0) {
                return res.status(400).json({ error: 'Invalid users data' });
            }

            // 批量处理用户创建
            const results = await optimizer.processBatchData(
                users,
                async (user) => {
                    return await optimizer.queryWithOptimization(
                        'INSERT INTO users (name, email) VALUES ($1, $2) RETURNING *',
                        [user.name, user.email]
                    );
                },
                50 // 每批处理50个
            );

            // 清除相关缓存
            await optimizer.cacheManager.delete('users:page:1');

            res.json({
                success: true,
                created: results.length,
                users: results.map(r => r.rows[0])
            });
        } catch (error) {
            console.error('批量用户创建失败:', error);
            res.status(500).json({ error: 'Internal Server Error' });
        }
    });

    // 性能报告API
    optimizer.app.get('/api/performance', (req, res) => {
        const report = optimizer.getPerformanceReport();
        res.json(report);
    });

    return optimizer;
}

// 导出核心类和函数
module.exports = {
    MultiLevelCacheManager,
    DatabaseOptimizer,
    ResponseOptimizer,
    APIPerformanceMonitor,
    APIPerformanceOptimizer,
    createOptimizedAPIExample
};

// 如果直接运行此文件，启动示例
if (require.main === module) {
    createOptimizedAPIExample().then(optimizer => {
        const server = optimizer.listen(3000, () => {
            console.log('优化的API服务启动在端口3000');
            console.log('性能报告: http://localhost:3000/api/performance');
        });

        // 优雅关闭
        process.on('SIGINT', async () => {
            console.log('收到关闭信号，正在关闭...');
            server.close();
            await optimizer.close();
            process.exit(0);
        });
    }).catch(console.error);
} 