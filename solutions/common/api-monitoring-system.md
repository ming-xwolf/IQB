# 通用面试 - API监控系统完整实现

[← 返回API设计面试题](../../questions/backend/api-design.md)

## 🎯 解决方案概述

API监控系统是现代微服务架构中的关键组件，负责实时监控API的健康状态、性能指标和业务数据。本方案设计了一个完整的API监控系统，包含指标收集、实时监控、告警通知、性能分析和可视化展示等功能。

## 💡 核心问题分析

### API监控系统的技术挑战

**业务背景**：随着微服务架构的普及，单个系统可能包含数百个API接口，需要对所有接口进行全方位监控

**技术难点**：
- 海量API调用数据的实时收集和处理
- 多维度监控指标的设计和计算
- 异常检测和智能告警机制
- 高可用监控系统的架构设计
- 监控数据的存储和查询优化

## 📝 题目解决方案

### 解决方案思路分析

#### 1. 监控系统架构设计

**为什么选择分层监控架构？**
- **数据收集层**：通过中间件、探针等方式收集监控数据
- **数据处理层**：实时计算监控指标和异常检测
- **存储层**：时序数据库存储海量监控数据
- **展示层**：实时仪表板和告警通知系统

#### 2. 监控指标体系设计

**完整监控维度**：
- **基础指标**：响应时间、QPS、错误率、可用性
- **业务指标**：业务成功率、用户活跃度、转化率
- **系统指标**：CPU、内存、网络、磁盘使用率
- **依赖指标**：数据库、缓存、第三方服务状态

#### 3. 告警策略设计

**智能告警机制**：
- **阈值告警**：静态阈值和动态阈值结合
- **趋势告警**：基于历史数据的趋势分析
- **异常检测**：机器学习异常检测算法
- **告警聚合**：避免告警风暴的聚合策略

### 代码实现要点

#### API监控系统核心实现

```javascript
/**
 * API监控系统完整实现
 * 
 * 设计原理：
 * 1. 采用插件化架构，支持多种数据源和告警渠道
 * 2. 实时流处理架构，支持海量数据处理
 * 3. 多级缓存设计，保证监控系统高可用
 * 4. 智能告警算法，减少误报和漏报
 */

const EventEmitter = require('events');
const redis = require('redis');
const { InfluxDB } = require('@influxdata/influxdb-client');

// ==================== 核心监控引擎 ====================

/**
 * API监控核心引擎
 */
class APIMonitoringEngine extends EventEmitter {
    constructor(config) {
        super();
        this.config = config;
        this.collectors = new Map();
        this.processors = new Map();
        this.alertRules = new Map();
        this.storage = null;
        this.isRunning = false;
        
        this.initializeStorage();
        this.initializeDefaultProcessors();
    }

    /**
     * 初始化存储系统
     */
    async initializeStorage() {
        // InfluxDB用于时序数据存储
        this.influxDB = new InfluxDB({
            url: this.config.influxdb.url,
            token: this.config.influxdb.token
        });
        
        this.writeAPI = this.influxDB.getWriteApi(
            this.config.influxdb.org, 
            this.config.influxdb.bucket
        );
        
        // Redis用于实时数据缓存
        this.redis = redis.createClient(this.config.redis);
        await this.redis.connect();
        
        console.log('监控存储系统初始化完成');
    }

    /**
     * 初始化默认数据处理器
     */
    initializeDefaultProcessors() {
        // 响应时间处理器
        this.addProcessor('response_time', new ResponseTimeProcessor());
        
        // 错误率处理器
        this.addProcessor('error_rate', new ErrorRateProcessor());
        
        // QPS处理器
        this.addProcessor('qps', new QPSProcessor());
        
        // 可用性处理器
        this.addProcessor('availability', new AvailabilityProcessor());
    }

    /**
     * 添加数据收集器
     */
    addCollector(name, collector) {
        this.collectors.set(name, collector);
        collector.on('data', (data) => this.processData(data));
        console.log(`添加数据收集器: ${name}`);
    }

    /**
     * 添加数据处理器
     */
    addProcessor(name, processor) {
        this.processors.set(name, processor);
        console.log(`添加数据处理器: ${name}`);
    }

    /**
     * 添加告警规则
     */
    addAlertRule(name, rule) {
        this.alertRules.set(name, rule);
        console.log(`添加告警规则: ${name}`);
    }

    /**
     * 启动监控引擎
     */
    async start() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        
        // 启动所有数据收集器
        for (const [name, collector] of this.collectors) {
            await collector.start();
            console.log(`启动收集器: ${name}`);
        }
        
        // 启动告警检查
        this.startAlertChecking();
        
        console.log('API监控引擎已启动');
        this.emit('started');
    }

    /**
     * 停止监控引擎
     */
    async stop() {
        if (!this.isRunning) return;
        
        this.isRunning = false;
        
        // 停止所有数据收集器
        for (const [name, collector] of this.collectors) {
            await collector.stop();
            console.log(`停止收集器: ${name}`);
        }
        
        // 关闭存储连接
        await this.writeAPI.close();
        await this.redis.disconnect();
        
        console.log('API监控引擎已停止');
        this.emit('stopped');
    }

    /**
     * 处理监控数据
     */
    async processData(rawData) {
        try {
            const timestamp = Date.now();
            const processedData = {
                ...rawData,
                timestamp,
                processed_at: new Date().toISOString()
            };

            // 通过所有处理器处理数据
            for (const [name, processor] of this.processors) {
                try {
                    const result = await processor.process(processedData);
                    if (result) {
                        await this.storeMetric(name, result);
                        await this.checkAlerts(name, result);
                    }
                } catch (error) {
                    console.error(`处理器 ${name} 处理失败:`, error);
                }
            }

            // 存储原始数据
            await this.storeRawData(processedData);
            
            this.emit('data_processed', processedData);
        } catch (error) {
            console.error('数据处理失败:', error);
            this.emit('error', error);
        }
    }

    /**
     * 存储指标数据
     */
    async storeMetric(metricName, data) {
        // 写入InfluxDB
        const point = {
            measurement: metricName,
            tags: data.tags || {},
            fields: data.fields || {},
            timestamp: data.timestamp
        };
        
        this.writeAPI.writePoint(point);
        
        // 写入Redis缓存（用于实时查询）
        const cacheKey = `metric:${metricName}:${JSON.stringify(data.tags)}`;
        await this.redis.setEx(cacheKey, 300, JSON.stringify(data)); // 5分钟缓存
    }

    /**
     * 存储原始数据
     */
    async storeRawData(data) {
        const point = {
            measurement: 'api_requests',
            tags: {
                api: data.api,
                method: data.method,
                status: data.status,
                service: data.service
            },
            fields: {
                response_time: data.response_time,
                request_size: data.request_size || 0,
                response_size: data.response_size || 0
            },
            timestamp: data.timestamp
        };
        
        this.writeAPI.writePoint(point);
    }

    /**
     * 检查告警
     */
    async checkAlerts(metricName, data) {
        for (const [ruleName, rule] of this.alertRules) {
            if (rule.metric === metricName) {
                const shouldAlert = await rule.evaluate(data);
                if (shouldAlert) {
                    this.triggerAlert(ruleName, rule, data);
                }
            }
        }
    }

    /**
     * 触发告警
     */
    async triggerAlert(ruleName, rule, data) {
        const alert = {
            rule: ruleName,
            level: rule.level,
            message: rule.generateMessage(data),
            data: data,
            timestamp: Date.now()
        };

        console.warn(`🚨 告警触发: ${alert.message}`);
        
        // 发送告警通知
        await this.sendAlert(alert);
        
        this.emit('alert', alert);
    }

    /**
     * 发送告警通知
     */
    async sendAlert(alert) {
        // 这里可以集成多种告警渠道：邮件、短信、钉钉、Slack等
        
        // 示例：发送到告警队列
        await this.redis.lpush('alerts', JSON.stringify(alert));
        
        // 示例：Webhook通知
        if (this.config.webhook) {
            try {
                await fetch(this.config.webhook.url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(alert)
                });
            } catch (error) {
                console.error('Webhook告警发送失败:', error);
            }
        }
    }

    /**
     * 启动告警检查
     */
    startAlertChecking() {
        // 定期检查告警规则
        setInterval(async () => {
            if (!this.isRunning) return;
            
            try {
                await this.performScheduledChecks();
            } catch (error) {
                console.error('定期告警检查失败:', error);
            }
        }, this.config.alertCheckInterval || 60000); // 默认1分钟检查一次
    }

    /**
     * 执行定期检查
     */
    async performScheduledChecks() {
        for (const [ruleName, rule] of this.alertRules) {
            if (rule.type === 'scheduled') {
                try {
                    const shouldAlert = await rule.evaluate();
                    if (shouldAlert) {
                        await this.triggerAlert(ruleName, rule, {});
                    }
                } catch (error) {
                    console.error(`定期检查规则 ${ruleName} 失败:`, error);
                }
            }
        }
    }

    /**
     * 获取实时指标
     */
    async getRealtimeMetrics(metricName, tags = {}) {
        const cacheKey = `metric:${metricName}:${JSON.stringify(tags)}`;
        const cached = await this.redis.get(cacheKey);
        
        if (cached) {
            return JSON.parse(cached);
        }
        
        // 从InfluxDB查询最新数据
        const query = `
            from(bucket: "${this.config.influxdb.bucket}")
            |> range(start: -5m)
            |> filter(fn: (r) => r._measurement == "${metricName}")
            |> last()
        `;
        
        const queryAPI = this.influxDB.getQueryApi(this.config.influxdb.org);
        const result = await queryAPI.collectRows(query);
        
        return result[0] || null;
    }
}

// ==================== 数据收集器 ====================

/**
 * Express中间件数据收集器
 */
class ExpressCollector extends EventEmitter {
    constructor(options = {}) {
        super();
        this.options = options;
        this.isActive = false;
    }

    /**
     * 创建Express中间件
     */
    createMiddleware() {
        return (req, res, next) => {
            if (!this.isActive) return next();
            
            const startTime = Date.now();
            const originalSend = res.send;
            
            // 重写response.send方法来捕获响应数据
            res.send = function(data) {
                const endTime = Date.now();
                const responseTime = endTime - startTime;
                
                // 收集监控数据
                const monitoringData = {
                    api: req.route ? req.route.path : req.path,
                    method: req.method,
                    status: res.statusCode,
                    response_time: responseTime,
                    request_size: req.get('content-length') || 0,
                    response_size: Buffer.byteLength(data || ''),
                    user_agent: req.get('user-agent'),
                    ip: req.ip || req.connection.remoteAddress,
                    service: this.options.serviceName || 'unknown',
                    timestamp: startTime
                };
                
                // 发送监控数据
                this.emit('data', monitoringData);
                
                // 调用原始的send方法
                return originalSend.call(this, data);
            }.bind(this);
            
            next();
        };
    }

    async start() {
        this.isActive = true;
        console.log('Express收集器已启动');
    }

    async stop() {
        this.isActive = false;
        console.log('Express收集器已停止');
    }
}

/**
 * HTTP客户端请求收集器
 */
class HTTPClientCollector extends EventEmitter {
    constructor(options = {}) {
        super();
        this.options = options;
        this.originalRequest = null;
    }

    async start() {
        const http = require('http');
        const https = require('https');
        
        // 劫持HTTP请求
        this.originalRequest = http.request;
        http.request = this.wrapRequest(http.request);
        https.request = this.wrapRequest(https.request);
        
        console.log('HTTP客户端收集器已启动');
    }

    async stop() {
        if (this.originalRequest) {
            const http = require('http');
            http.request = this.originalRequest;
        }
        console.log('HTTP客户端收集器已停止');
    }

    wrapRequest(originalRequest) {
        return (...args) => {
            const startTime = Date.now();
            const req = originalRequest.apply(this, args);
            
            req.on('response', (res) => {
                const endTime = Date.now();
                const responseTime = endTime - startTime;
                
                const monitoringData = {
                    api: req.path,
                    method: req.method,
                    status: res.statusCode,
                    response_time: responseTime,
                    host: req.getHeader('host'),
                    service: this.options.serviceName || 'http-client',
                    timestamp: startTime,
                    type: 'outbound'
                };
                
                this.emit('data', monitoringData);
            });
            
            return req;
        };
    }
}

// ==================== 数据处理器 ====================

/**
 * 响应时间处理器
 */
class ResponseTimeProcessor {
    constructor() {
        this.buckets = [10, 50, 100, 200, 500, 1000, 2000, 5000]; // 响应时间分桶
        this.cache = new Map();
    }

    async process(data) {
        const key = `${data.service}:${data.api}:${data.method}`;
        const responseTime = data.response_time;
        
        // 更新缓存统计
        if (!this.cache.has(key)) {
            this.cache.set(key, {
                count: 0,
                sum: 0,
                min: Infinity,
                max: 0,
                buckets: new Array(this.buckets.length).fill(0)
            });
        }
        
        const stats = this.cache.get(key);
        stats.count++;
        stats.sum += responseTime;
        stats.min = Math.min(stats.min, responseTime);
        stats.max = Math.max(stats.max, responseTime);
        
        // 更新直方图桶
        for (let i = 0; i < this.buckets.length; i++) {
            if (responseTime <= this.buckets[i]) {
                stats.buckets[i]++;
                break;
            }
        }
        
        return {
            tags: {
                service: data.service,
                api: data.api,
                method: data.method
            },
            fields: {
                response_time: responseTime,
                avg_response_time: stats.sum / stats.count,
                min_response_time: stats.min,
                max_response_time: stats.max,
                p95_response_time: this.calculatePercentile(stats, 0.95),
                p99_response_time: this.calculatePercentile(stats, 0.99)
            },
            timestamp: data.timestamp
        };
    }

    calculatePercentile(stats, percentile) {
        const totalCount = stats.count;
        const targetCount = Math.ceil(totalCount * percentile);
        
        let cumulativeCount = 0;
        for (let i = 0; i < this.buckets.length; i++) {
            cumulativeCount += stats.buckets[i];
            if (cumulativeCount >= targetCount) {
                return this.buckets[i];
            }
        }
        
        return this.buckets[this.buckets.length - 1];
    }
}

/**
 * 错误率处理器
 */
class ErrorRateProcessor {
    constructor() {
        this.cache = new Map();
        this.windowSize = 60000; // 1分钟窗口
    }

    async process(data) {
        const key = `${data.service}:${data.api}:${data.method}`;
        const now = data.timestamp;
        const windowStart = now - this.windowSize;
        
        if (!this.cache.has(key)) {
            this.cache.set(key, []);
        }
        
        const requests = this.cache.get(key);
        
        // 添加当前请求
        requests.push({
            timestamp: now,
            status: data.status,
            isError: data.status >= 400
        });
        
        // 清理过期数据
        while (requests.length > 0 && requests[0].timestamp < windowStart) {
            requests.shift();
        }
        
        // 计算错误率
        const totalRequests = requests.length;
        const errorRequests = requests.filter(r => r.isError).length;
        const errorRate = totalRequests > 0 ? errorRequests / totalRequests : 0;
        
        return {
            tags: {
                service: data.service,
                api: data.api,
                method: data.method
            },
            fields: {
                total_requests: totalRequests,
                error_requests: errorRequests,
                error_rate: errorRate,
                success_rate: 1 - errorRate
            },
            timestamp: data.timestamp
        };
    }
}

/**
 * QPS处理器
 */
class QPSProcessor {
    constructor() {
        this.cache = new Map();
        this.windowSize = 60000; // 1分钟窗口
    }

    async process(data) {
        const key = `${data.service}:${data.api}:${data.method}`;
        const now = data.timestamp;
        const windowStart = now - this.windowSize;
        
        if (!this.cache.has(key)) {
            this.cache.set(key, []);
        }
        
        const requests = this.cache.get(key);
        
        // 添加当前请求
        requests.push(now);
        
        // 清理过期数据
        while (requests.length > 0 && requests[0] < windowStart) {
            requests.shift();
        }
        
        const qps = requests.length / (this.windowSize / 1000); // 每秒请求数
        
        return {
            tags: {
                service: data.service,
                api: data.api,
                method: data.method
            },
            fields: {
                qps: qps,
                request_count: requests.length
            },
            timestamp: data.timestamp
        };
    }
}

/**
 * 可用性处理器
 */
class AvailabilityProcessor {
    constructor() {
        this.cache = new Map();
        this.windowSize = 300000; // 5分钟窗口
    }

    async process(data) {
        const key = `${data.service}:${data.api}`;
        const now = data.timestamp;
        const windowStart = now - this.windowSize;
        
        if (!this.cache.has(key)) {
            this.cache.set(key, []);
        }
        
        const requests = this.cache.get(key);
        
        // 添加当前请求
        requests.push({
            timestamp: now,
            isSuccess: data.status < 400
        });
        
        // 清理过期数据
        while (requests.length > 0 && requests[0].timestamp < windowStart) {
            requests.shift();
        }
        
        // 计算可用性
        const totalRequests = requests.length;
        const successRequests = requests.filter(r => r.isSuccess).length;
        const availability = totalRequests > 0 ? successRequests / totalRequests : 0;
        
        return {
            tags: {
                service: data.service,
                api: data.api
            },
            fields: {
                availability: availability,
                uptime_percentage: availability * 100
            },
            timestamp: data.timestamp
        };
    }
}

// ==================== 告警规则 ====================

/**
 * 基础告警规则
 */
class AlertRule {
    constructor(config) {
        this.metric = config.metric;
        this.condition = config.condition;
        this.threshold = config.threshold;
        this.level = config.level || 'warning';
        this.message = config.message;
        this.type = config.type || 'realtime';
    }

    async evaluate(data) {
        const value = this.extractValue(data);
        return this.checkCondition(value);
    }

    extractValue(data) {
        if (data.fields && data.fields[this.condition.field]) {
            return data.fields[this.condition.field];
        }
        return 0;
    }

    checkCondition(value) {
        switch (this.condition.operator) {
            case '>':
                return value > this.threshold;
            case '<':
                return value < this.threshold;
            case '>=':
                return value >= this.threshold;
            case '<=':
                return value <= this.threshold;
            case '==':
                return value === this.threshold;
            default:
                return false;
        }
    }

    generateMessage(data) {
        const value = this.extractValue(data);
        return this.message.replace('{{value}}', value).replace('{{threshold}}', this.threshold);
    }
}

/**
 * 复合告警规则
 */
class CompositeAlertRule extends AlertRule {
    constructor(config) {
        super(config);
        this.rules = config.rules || [];
        this.logic = config.logic || 'and'; // 'and' or 'or'
    }

    async evaluate(data) {
        const results = await Promise.all(
            this.rules.map(rule => rule.evaluate(data))
        );

        if (this.logic === 'and') {
            return results.every(result => result);
        } else {
            return results.some(result => result);
        }
    }
}

// ==================== 使用示例 ====================

/**
 * 监控系统使用示例
 */
class MonitoringSystemExample {
    constructor() {
        this.monitor = null;
    }

    async initialize() {
        // 配置监控系统
        const config = {
            influxdb: {
                url: process.env.INFLUXDB_URL || 'http://localhost:8086',
                token: process.env.INFLUXDB_TOKEN,
                org: 'my-org',
                bucket: 'monitoring'
            },
            redis: {
                host: process.env.REDIS_HOST || 'localhost',
                port: process.env.REDIS_PORT || 6379
            },
            webhook: {
                url: process.env.WEBHOOK_URL
            },
            alertCheckInterval: 30000 // 30秒检查一次
        };

        // 创建监控引擎
        this.monitor = new APIMonitoringEngine(config);

        // 添加数据收集器
        const expressCollector = new ExpressCollector({ serviceName: 'api-service' });
        this.monitor.addCollector('express', expressCollector);

        const httpClientCollector = new HTTPClientCollector({ serviceName: 'api-service' });
        this.monitor.addCollector('http-client', httpClientCollector);

        // 添加告警规则
        this.setupAlertRules();

        // 启动监控
        await this.monitor.start();

        console.log('监控系统初始化完成');
    }

    setupAlertRules() {
        // 响应时间告警
        const responseTimeAlert = new AlertRule({
            metric: 'response_time',
            condition: {
                field: 'avg_response_time',
                operator: '>'
            },
            threshold: 1000, // 1秒
            level: 'warning',
            message: 'API响应时间过高: {{value}}ms > {{threshold}}ms'
        });

        // 错误率告警
        const errorRateAlert = new AlertRule({
            metric: 'error_rate',
            condition: {
                field: 'error_rate',
                operator: '>'
            },
            threshold: 0.05, // 5%
            level: 'critical',
            message: 'API错误率过高: {{value}}% > {{threshold}}%'
        });

        // 可用性告警
        const availabilityAlert = new AlertRule({
            metric: 'availability',
            condition: {
                field: 'availability',
                operator: '<'
            },
            threshold: 0.99, // 99%
            level: 'critical',
            message: 'API可用性过低: {{value}}% < {{threshold}}%'
        });

        this.monitor.addAlertRule('response_time_high', responseTimeAlert);
        this.monitor.addAlertRule('error_rate_high', errorRateAlert);
        this.monitor.addAlertRule('availability_low', availabilityAlert);
    }

    // Express应用示例
    createExpressApp() {
        const express = require('express');
        const app = express();

        // 获取Express收集器中间件
        const expressCollector = this.monitor.collectors.get('express');
        app.use(expressCollector.createMiddleware());

        // 示例API路由
        app.get('/api/users', (req, res) => {
            // 模拟随机响应时间
            const delay = Math.random() * 200 + 50;
            setTimeout(() => {
                if (Math.random() > 0.95) {
                    // 5%概率返回错误
                    res.status(500).json({ error: 'Internal Server Error' });
                } else {
                    res.json({ users: ['user1', 'user2', 'user3'] });
                }
            }, delay);
        });

        app.get('/api/health', (req, res) => {
            res.json({ status: 'healthy', timestamp: new Date().toISOString() });
        });

        return app;
    }

    async shutdown() {
        if (this.monitor) {
            await this.monitor.stop();
        }
        console.log('监控系统已关闭');
    }
}

// 导出核心类
module.exports = {
    APIMonitoringEngine,
    ExpressCollector,
    HTTPClientCollector,
    ResponseTimeProcessor,
    ErrorRateProcessor,
    QPSProcessor,
    AvailabilityProcessor,
    AlertRule,
    CompositeAlertRule,
    MonitoringSystemExample
};

// 如果直接运行此文件，启动示例
if (require.main === module) {
    const example = new MonitoringSystemExample();
    
    example.initialize().then(() => {
        const app = example.createExpressApp();
        const server = app.listen(3000, () => {
            console.log('示例API服务启动在端口3000');
        });

        // 优雅关闭
        process.on('SIGINT', async () => {
            console.log('收到关闭信号，正在关闭...');
            server.close();
            await example.shutdown();
            process.exit(0);
        });
    }).catch(console.error);
} 