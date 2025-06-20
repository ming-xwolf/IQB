# 通用面试 - APM监控系统完整实现

[← 返回监控调试面试题](../../questions/backend/monitoring-debugging.md)

## 🎯 解决方案概述

APM（Application Performance Monitoring）是现代分布式系统的核心监控解决方案。本方案设计了一套完整的APM监控系统，涵盖性能指标采集、分布式链路追踪、异常监控、智能告警和可视化展示，为生产环境提供全方位的性能监控和问题诊断能力。

## 💡 核心问题分析

### APM监控系统的技术挑战

**业务背景**：微服务架构下的应用系统复杂度高，需要端到端的性能监控和问题快速定位能力

**技术难点**：
- 分布式系统中链路追踪和性能数据关联
- 海量监控数据的实时处理和存储优化
- 智能异常检测和告警降噪机制
- 多维度性能指标的聚合分析
- 监控系统自身的高可用和低侵入性

## 📝 题目解决方案

### 解决方案思路分析

#### 1. 监控数据采集架构

**为什么选择多层次采集？**
- **应用层采集**：业务性能指标、异常信息、用户行为数据
- **中间件采集**：数据库性能、消息队列、缓存系统
- **系统层采集**：CPU、内存、网络、磁盘等基础资源
- **网络层采集**：服务间调用、负载均衡、CDN性能

#### 2. 分布式链路追踪

**完整追踪策略**：
- **Trace生成**：全链路唯一标识和跨服务传播
- **Span管理**：操作级别的时间跨度和依赖关系
- **采样策略**：自适应采样和重要业务100%采样
- **数据关联**：日志、指标、链路数据的统一关联

#### 3. 智能异常检测

**多维度异常识别**：
- **阈值检测**：静态阈值和动态基线检测
- **趋势分析**：时间序列异常和周期性模式识别
- **关联分析**：多指标异常关联和根因分析
- **机器学习**：异常模式学习和预测性告警

### 代码实现要点

#### APM监控系统完整实现

```javascript
/**
 * APM监控系统完整实现
 * 
 * 设计原理：
 * 1. 分布式链路追踪和性能数据采集
 * 2. 多维度监控指标聚合和分析
 * 3. 智能异常检测和告警机制
 * 4. 可视化监控大盘和问题诊断
 */

const EventEmitter = require('events');
const crypto = require('crypto');

// ==================== 链路追踪核心 ====================

/**
 * 分布式链路追踪器
 */
class DistributedTracer {
    constructor(config = {}) {
        this.config = config;
        this.serviceName = config.serviceName || 'unknown-service';
        this.activeSpans = new Map(); // 活跃Span
        this.completedTraces = new Map(); // 完成的Trace
        this.samplingRate = config.samplingRate || 0.1; // 默认10%采样
        
        this.spanExporter = config.spanExporter || this.createDefaultExporter();
    }

    /**
     * 创建新的Trace
     */
    createTrace(operation, parentContext = null) {
        const traceId = this.generateTraceId();
        const spanId = this.generateSpanId();
        
        const span = {
            traceId,
            spanId,
            parentSpanId: parentContext?.spanId || null,
            operation,
            serviceName: this.serviceName,
            startTime: Date.now(),
            endTime: null,
            duration: null,
            status: 'active',
            tags: new Map(),
            logs: [],
            baggage: new Map()
        };

        // 采样决策
        if (this.shouldSample(traceId)) {
            this.activeSpans.set(spanId, span);
        }

        return {
            traceId,
            spanId,
            span
        };
    }

    /**
     * 完成Span
     */
    finishSpan(spanId, status = 'ok') {
        const span = this.activeSpans.get(spanId);
        if (!span) {
            return null;
        }

        span.endTime = Date.now();
        span.duration = span.endTime - span.startTime;
        span.status = status;

        // 移动到完成列表
        this.activeSpans.delete(spanId);
        
        if (!this.completedTraces.has(span.traceId)) {
            this.completedTraces.set(span.traceId, []);
        }
        this.completedTraces.get(span.traceId).push(span);

        // 导出Span数据
        this.spanExporter.export(span);

        return span;
    }

    /**
     * 添加Span标签
     */
    addSpanTag(spanId, key, value) {
        const span = this.activeSpans.get(spanId);
        if (span) {
            span.tags.set(key, value);
        }
    }

    /**
     * 添加Span日志
     */
    addSpanLog(spanId, message, level = 'info') {
        const span = this.activeSpans.get(spanId);
        if (span) {
            span.logs.push({
                timestamp: Date.now(),
                level,
                message
            });
        }
    }

    /**
     * 生成TraceID
     */
    generateTraceId() {
        return crypto.randomBytes(16).toString('hex');
    }

    /**
     * 生成SpanID
     */
    generateSpanId() {
        return crypto.randomBytes(8).toString('hex');
    }

    /**
     * 采样决策
     */
    shouldSample(traceId) {
        // 基于TraceID哈希的确定性采样
        const hash = parseInt(traceId.slice(-8), 16);
        return (hash % 10000) < (this.samplingRate * 10000);
    }

    /**
     * 创建默认导出器
     */
    createDefaultExporter() {
        return {
            export: (span) => {
                console.log(`[TRACE] ${span.traceId}:${span.spanId} ${span.operation} ${span.duration}ms`);
            }
        };
    }

    /**
     * 获取Trace统计信息
     */
    getTraceStats() {
        const activeCount = this.activeSpans.size;
        const completedCount = Array.from(this.completedTraces.values())
            .reduce((sum, spans) => sum + spans.length, 0);

        return {
            activeSpans: activeCount,
            completedSpans: completedCount,
            totalTraces: this.completedTraces.size
        };
    }
}

// ==================== 性能指标收集器 ====================

/**
 * 性能指标收集器
 */
class MetricsCollector extends EventEmitter {
    constructor(config = {}) {
        super();
        this.config = config;
        this.metrics = new Map(); // 指标数据
        this.timeSeries = new Map(); // 时间序列数据
        this.collectors = new Map(); // 指标收集器
        
        this.collectionInterval = config.interval || 5000; // 5秒间隔
        this.retentionPeriod = config.retention || 24 * 60 * 60 * 1000; // 24小时
        
        this.initializeBuiltinCollectors();
        this.startCollection();
    }

    /**
     * 初始化内置收集器
     */
    initializeBuiltinCollectors() {
        // 系统资源收集器
        this.addCollector('system', {
            collect: () => {
                const usage = process.cpuUsage();
                const memUsage = process.memoryUsage();
                
                return {
                    cpu: {
                        user: usage.user / 1000, // 转换为毫秒
                        system: usage.system / 1000
                    },
                    memory: {
                        rss: memUsage.rss,
                        heapTotal: memUsage.heapTotal,
                        heapUsed: memUsage.heapUsed,
                        external: memUsage.external
                    },
                    uptime: process.uptime()
                };
            },
            interval: 5000
        });

        // HTTP请求收集器
        this.addCollector('http', {
            collect: () => {
                return this.getHTTPMetrics();
            },
            interval: 1000
        });

        // 数据库性能收集器
        this.addCollector('database', {
            collect: () => {
                return this.getDatabaseMetrics();
            },
            interval: 5000
        });
    }

    /**
     * 添加指标收集器
     */
    addCollector(name, collector) {
        this.collectors.set(name, {
            ...collector,
            lastCollection: 0
        });
    }

    /**
     * 开始指标收集
     */
    startCollection() {
        this.collectionTimer = setInterval(() => {
            this.collectAllMetrics();
        }, 1000); // 每秒检查一次

        console.log('指标收集已启动');
    }

    /**
     * 收集所有指标
     */
    async collectAllMetrics() {
        const now = Date.now();

        for (const [name, collector] of this.collectors) {
            const interval = collector.interval || this.collectionInterval;
            
            if (now - collector.lastCollection >= interval) {
                try {
                    const metrics = await collector.collect();
                    this.recordMetrics(name, metrics, now);
                    collector.lastCollection = now;
                } catch (error) {
                    console.error(`收集指标失败 ${name}:`, error);
                }
            }
        }

        // 清理过期数据
        this.cleanupExpiredData(now);
    }

    /**
     * 记录指标数据
     */
    recordMetrics(category, metrics, timestamp = Date.now()) {
        if (!this.timeSeries.has(category)) {
            this.timeSeries.set(category, []);
        }

        const seriesData = this.timeSeries.get(category);
        seriesData.push({
            timestamp,
            data: metrics
        });

        // 更新当前指标
        this.metrics.set(category, metrics);

        // 发出指标更新事件
        this.emit('metrics', {
            category,
            metrics,
            timestamp
        });
    }

    /**
     * 获取HTTP指标
     */
    getHTTPMetrics() {
        // 模拟HTTP指标（实际应用中从HTTP框架获取）
        return {
            requestCount: Math.floor(Math.random() * 100),
            responseTime: {
                avg: Math.random() * 100 + 50,
                p95: Math.random() * 200 + 100,
                p99: Math.random() * 500 + 200
            },
            errorRate: Math.random() * 0.05, // 5%以下错误率
            statusCodes: {
                '2xx': Math.floor(Math.random() * 80 + 10),
                '4xx': Math.floor(Math.random() * 10),
                '5xx': Math.floor(Math.random() * 5)
            }
        };
    }

    /**
     * 获取数据库指标
     */
    getDatabaseMetrics() {
        return {
            connectionPool: {
                active: Math.floor(Math.random() * 10),
                idle: Math.floor(Math.random() * 5),
                total: 20
            },
            queryPerformance: {
                avgTime: Math.random() * 50 + 10,
                slowQueries: Math.floor(Math.random() * 3)
            },
            operations: {
                select: Math.floor(Math.random() * 100),
                insert: Math.floor(Math.random() * 20),
                update: Math.floor(Math.random() * 15),
                delete: Math.floor(Math.random() * 5)
            }
        };
    }

    /**
     * 清理过期数据
     */
    cleanupExpiredData(currentTime) {
        const cutoffTime = currentTime - this.retentionPeriod;

        for (const [category, series] of this.timeSeries) {
            const filteredSeries = series.filter(point => point.timestamp > cutoffTime);
            this.timeSeries.set(category, filteredSeries);
        }
    }

    /**
     * 获取指标统计
     */
    getMetricsStats(category, timeRange = 300000) { // 默认5分钟
        const series = this.timeSeries.get(category);
        if (!series) {
            return null;
        }

        const cutoffTime = Date.now() - timeRange;
        const recentData = series.filter(point => point.timestamp > cutoffTime);

        if (recentData.length === 0) {
            return null;
        }

        return {
            count: recentData.length,
            latest: recentData[recentData.length - 1],
            timeRange: timeRange,
            data: recentData
        };
    }

    /**
     * 停止收集
     */
    stopCollection() {
        if (this.collectionTimer) {
            clearInterval(this.collectionTimer);
            this.collectionTimer = null;
        }
        console.log('指标收集已停止');
    }
}

// ==================== 异常检测器 ====================

/**
 * 智能异常检测器
 */
class AnomalyDetector extends EventEmitter {
    constructor(config = {}) {
        super();
        this.config = config;
        this.baselines = new Map(); // 基线数据
        this.thresholds = new Map(); // 阈值配置
        this.anomalies = new Map(); // 检测到的异常
        
        this.detectionRules = new Map();
        this.initializeDetectionRules();
    }

    /**
     * 初始化检测规则
     */
    initializeDetectionRules() {
        // CPU使用率异常检测
        this.addDetectionRule('cpu_high', {
            metric: 'system.cpu.user',
            threshold: 80,
            operator: '>',
            duration: 60000, // 持续1分钟
            severity: 'warning'
        });

        // 内存使用异常检测
        this.addDetectionRule('memory_high', {
            metric: 'system.memory.heapUsed',
            threshold: 0.8, // 80%
            operator: '>',
            relative: true,
            baseline: 'system.memory.heapTotal',
            duration: 30000,
            severity: 'critical'
        });

        // 响应时间异常检测
        this.addDetectionRule('response_time_high', {
            metric: 'http.responseTime.avg',
            threshold: 200,
            operator: '>',
            duration: 30000,
            severity: 'warning'
        });

        // 错误率异常检测
        this.addDetectionRule('error_rate_high', {
            metric: 'http.errorRate',
            threshold: 0.05, // 5%
            operator: '>',
            duration: 60000,
            severity: 'critical'
        });
    }

    /**
     * 添加检测规则
     */
    addDetectionRule(name, rule) {
        this.detectionRules.set(name, {
            ...rule,
            violationStart: null,
            isViolating: false
        });
    }

    /**
     * 检测指标异常
     */
    detectAnomalies(metrics, timestamp = Date.now()) {
        const detectedAnomalies = [];

        for (const [ruleName, rule] of this.detectionRules) {
            const anomaly = this.checkRule(rule, metrics, timestamp);
            if (anomaly) {
                detectedAnomalies.push({
                    rule: ruleName,
                    ...anomaly
                });
            }
        }

        // 处理检测到的异常
        detectedAnomalies.forEach(anomaly => {
            this.handleAnomaly(anomaly);
        });

        return detectedAnomalies;
    }

    /**
     * 检查单个规则
     */
    checkRule(rule, metrics, timestamp) {
        const value = this.extractMetricValue(metrics, rule.metric);
        if (value === null || value === undefined) {
            return null;
        }

        let threshold = rule.threshold;
        
        // 相对阈值计算
        if (rule.relative && rule.baseline) {
            const baselineValue = this.extractMetricValue(metrics, rule.baseline);
            if (baselineValue) {
                threshold = baselineValue * rule.threshold;
            }
        }

        // 评估条件
        const isViolating = this.evaluateCondition(value, rule.operator, threshold);

        if (isViolating) {
            if (!rule.isViolating) {
                rule.violationStart = timestamp;
                rule.isViolating = true;
            }

            // 检查持续时间
            const violationDuration = timestamp - rule.violationStart;
            if (violationDuration >= rule.duration) {
                return {
                    timestamp,
                    value,
                    threshold,
                    violationDuration,
                    severity: rule.severity,
                    metric: rule.metric
                };
            }
        } else {
            rule.isViolating = false;
            rule.violationStart = null;
        }

        return null;
    }

    /**
     * 提取指标值
     */
    extractMetricValue(metrics, metricPath) {
        const parts = metricPath.split('.');
        let value = metrics;

        for (const part of parts) {
            if (value && typeof value === 'object' && part in value) {
                value = value[part];
            } else {
                return null;
            }
        }

        return value;
    }

    /**
     * 评估条件
     */
    evaluateCondition(value, operator, threshold) {
        switch (operator) {
            case '>':
                return value > threshold;
            case '<':
                return value < threshold;
            case '>=':
                return value >= threshold;
            case '<=':
                return value <= threshold;
            case '==':
                return value === threshold;
            case '!=':
                return value !== threshold;
            default:
                return false;
        }
    }

    /**
     * 处理异常
     */
    handleAnomaly(anomaly) {
        const anomalyId = `${anomaly.rule}_${anomaly.timestamp}`;
        
        // 存储异常记录
        this.anomalies.set(anomalyId, anomaly);

        // 发出异常事件
        this.emit('anomaly', anomaly);

        console.log(`[ANOMALY] ${anomaly.rule}: ${anomaly.metric}=${anomaly.value} (threshold: ${anomaly.threshold})`);
    }

    /**
     * 获取异常统计
     */
    getAnomalyStats(timeRange = 3600000) { // 默认1小时
        const cutoffTime = Date.now() - timeRange;
        const recentAnomalies = Array.from(this.anomalies.values())
            .filter(anomaly => anomaly.timestamp > cutoffTime);

        const severityCount = recentAnomalies.reduce((acc, anomaly) => {
            acc[anomaly.severity] = (acc[anomaly.severity] || 0) + 1;
            return acc;
        }, {});

        return {
            total: recentAnomalies.length,
            bySeverity: severityCount,
            recent: recentAnomalies.slice(-10) // 最近10个异常
        };
    }
}

// ==================== 告警管理器 ====================

/**
 * 告警管理器
 */
class AlertManager extends EventEmitter {
    constructor(config = {}) {
        super();
        this.config = config;
        this.alerts = new Map(); // 活跃告警
        this.alertHistory = new Map(); // 告警历史
        this.notificationChannels = new Map(); // 通知渠道
        this.suppressionRules = new Map(); // 抑制规则
        
        this.initializeNotificationChannels();
    }

    /**
     * 初始化通知渠道
     */
    initializeNotificationChannels() {
        // 邮件通知
        this.addNotificationChannel('email', {
            send: async (alert, recipients) => {
                console.log(`[EMAIL] 发送告警邮件: ${alert.title} -> ${recipients.join(', ')}`);
                // 实际应用中集成邮件服务
            }
        });

        // 短信通知
        this.addNotificationChannel('sms', {
            send: async (alert, recipients) => {
                console.log(`[SMS] 发送告警短信: ${alert.title} -> ${recipients.join(', ')}`);
                // 实际应用中集成短信服务
            }
        });

        // Webhook通知
        this.addNotificationChannel('webhook', {
            send: async (alert, webhooks) => {
                console.log(`[WEBHOOK] 发送告警Webhook: ${alert.title}`);
                // 实际应用中发送HTTP请求
            }
        });
    }

    /**
     * 添加通知渠道
     */
    addNotificationChannel(name, channel) {
        this.notificationChannels.set(name, channel);
    }

    /**
     * 创建告警
     */
    createAlert(anomaly, alertRule = {}) {
        const alertId = `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
        const alert = {
            id: alertId,
            title: alertRule.title || `${anomaly.rule} 异常`,
            description: this.generateAlertDescription(anomaly),
            severity: anomaly.severity || 'warning',
            timestamp: anomaly.timestamp,
            source: anomaly.rule,
            metric: anomaly.metric,
            value: anomaly.value,
            threshold: anomaly.threshold,
            status: 'active',
            acknowledgedBy: null,
            acknowledgedAt: null,
            resolvedAt: null,
            notificationsSent: [],
            tags: anomaly.tags || {}
        };

        // 检查告警抑制
        if (this.shouldSuppressAlert(alert)) {
            console.log(`告警被抑制: ${alert.title}`);
            return null;
        }

        this.alerts.set(alertId, alert);
        
        // 发送通知
        this.sendNotifications(alert, alertRule);

        // 发出告警事件
        this.emit('alert', alert);

        return alert;
    }

    /**
     * 生成告警描述
     */
    generateAlertDescription(anomaly) {
        return `指标 ${anomaly.metric} 的值 ${anomaly.value} 超过阈值 ${anomaly.threshold}，持续时间 ${Math.round(anomaly.violationDuration / 1000)} 秒`;
    }

    /**
     * 检查告警抑制
     */
    shouldSuppressAlert(alert) {
        // 检查重复告警抑制
        const similarAlerts = Array.from(this.alerts.values())
            .filter(existingAlert => 
                existingAlert.source === alert.source &&
                existingAlert.status === 'active' &&
                Date.now() - existingAlert.timestamp < 300000 // 5分钟内
            );

        return similarAlerts.length > 0;
    }

    /**
     * 发送通知
     */
    async sendNotifications(alert, alertRule) {
        const notifications = alertRule.notifications || this.getDefaultNotifications(alert.severity);

        for (const notification of notifications) {
            try {
                const channel = this.notificationChannels.get(notification.channel);
                if (channel) {
                    await channel.send(alert, notification.recipients);
                    alert.notificationsSent.push({
                        channel: notification.channel,
                        timestamp: Date.now(),
                        recipients: notification.recipients
                    });
                }
            } catch (error) {
                console.error(`发送通知失败 ${notification.channel}:`, error);
            }
        }
    }

    /**
     * 获取默认通知配置
     */
    getDefaultNotifications(severity) {
        const defaultNotifications = {
            critical: [
                { channel: 'email', recipients: ['ops@company.com'] },
                { channel: 'sms', recipients: ['13800138000'] }
            ],
            warning: [
                { channel: 'email', recipients: ['ops@company.com'] }
            ],
            info: []
        };

        return defaultNotifications[severity] || [];
    }

    /**
     * 确认告警
     */
    acknowledgeAlert(alertId, acknowledgedBy) {
        const alert = this.alerts.get(alertId);
        if (alert && alert.status === 'active') {
            alert.status = 'acknowledged';
            alert.acknowledgedBy = acknowledgedBy;
            alert.acknowledgedAt = Date.now();
            
            this.emit('alertAcknowledged', alert);
            return alert;
        }
        return null;
    }

    /**
     * 解决告警
     */
    resolveAlert(alertId, resolvedBy) {
        const alert = this.alerts.get(alertId);
        if (alert && alert.status !== 'resolved') {
            alert.status = 'resolved';
            alert.resolvedAt = Date.now();
            
            // 移动到历史记录
            this.alertHistory.set(alertId, alert);
            this.alerts.delete(alertId);
            
            this.emit('alertResolved', alert);
            return alert;
        }
        return null;
    }

    /**
     * 获取告警统计
     */
    getAlertStats() {
        const activeAlerts = Array.from(this.alerts.values());
        const severityCount = activeAlerts.reduce((acc, alert) => {
            acc[alert.severity] = (acc[alert.severity] || 0) + 1;
            return acc;
        }, {});

        return {
            active: activeAlerts.length,
            bySeverity: severityCount,
            recentAlerts: activeAlerts.slice(-5) // 最近5个告警
        };
    }
}

// ==================== 完整APM监控系统 ====================

/**
 * APM监控系统
 */
class APMMonitoringSystem extends EventEmitter {
    constructor(config = {}) {
        super();
        this.config = config;
        
        // 初始化各个组件
        this.tracer = new DistributedTracer(config.tracing || {});
        this.metricsCollector = new MetricsCollector(config.metrics || {});
        this.anomalyDetector = new AnomalyDetector(config.anomaly || {});
        this.alertManager = new AlertManager(config.alerts || {});
        
        this.setupEventHandlers();
        this.startMonitoring();
    }

    /**
     * 设置事件处理器
     */
    setupEventHandlers() {
        // 指标收集事件处理
        this.metricsCollector.on('metrics', (metricsEvent) => {
            // 执行异常检测
            const anomalies = this.anomalyDetector.detectAnomalies(
                metricsEvent.metrics,
                metricsEvent.timestamp
            );

            // 为每个异常创建告警
            anomalies.forEach(anomaly => {
                this.alertManager.createAlert(anomaly);
            });

            // 发出系统级指标事件
            this.emit('metrics', metricsEvent);
        });

        // 异常检测事件处理
        this.anomalyDetector.on('anomaly', (anomaly) => {
            this.emit('anomaly', anomaly);
        });

        // 告警事件处理
        this.alertManager.on('alert', (alert) => {
            this.emit('alert', alert);
        });
    }

    /**
     * 开始监控
     */
    startMonitoring() {
        console.log('APM监控系统已启动');
        
        // 启动性能统计输出
        this.statsTimer = setInterval(() => {
            this.outputSystemStats();
        }, 30000); // 每30秒输出一次统计
    }

    /**
     * 输出系统统计信息
     */
    outputSystemStats() {
        const traceStats = this.tracer.getTraceStats();
        const alertStats = this.alertManager.getAlertStats();
        const anomalyStats = this.anomalyDetector.getAnomalyStats();

        console.log('\n=== APM系统状态 ===');
        console.log(`链路追踪: ${traceStats.activeSpans} 活跃, ${traceStats.completedSpans} 完成`);
        console.log(`告警: ${alertStats.active} 活跃 (${JSON.stringify(alertStats.bySeverity)})`);
        console.log(`异常: ${anomalyStats.total} 个 (最近1小时)`);
        console.log('===================\n');
    }

    /**
     * 创建链路追踪
     */
    trace(operation, parentContext = null) {
        return this.tracer.createTrace(operation, parentContext);
    }

    /**
     * 完成链路追踪
     */
    finishTrace(spanId, status = 'ok') {
        return this.tracer.finishSpan(spanId, status);
    }

    /**
     * 记录自定义指标
     */
    recordMetric(category, metrics) {
        this.metricsCollector.recordMetrics(category, metrics);
    }

    /**
     * 获取监控大盘数据
     */
    getDashboardData() {
        return {
            timestamp: Date.now(),
            traces: this.tracer.getTraceStats(),
            alerts: this.alertManager.getAlertStats(),
            anomalies: this.anomalyDetector.getAnomalyStats(),
            metrics: {
                system: this.metricsCollector.getMetricsStats('system'),
                http: this.metricsCollector.getMetricsStats('http'),
                database: this.metricsCollector.getMetricsStats('database')
            }
        };
    }

    /**
     * 停止监控
     */
    stopMonitoring() {
        if (this.statsTimer) {
            clearInterval(this.statsTimer);
        }
        
        this.metricsCollector.stopCollection();
        console.log('APM监控系统已停止');
    }
}

// 导出核心类
module.exports = {
    DistributedTracer,
    MetricsCollector,
    AnomalyDetector,
    AlertManager,
    APMMonitoringSystem
};

// 如果直接运行此文件，启动示例
if (require.main === module) {
    const config = {
        tracing: {
            serviceName: 'demo-service',
            samplingRate: 1.0 // 100%采样用于演示
        },
        metrics: {
            interval: 3000 // 3秒收集间隔
        }
    };

    const apmSystem = new APMMonitoringSystem(config);

    // 模拟业务操作产生链路追踪
    setInterval(() => {
        const trace = apmSystem.trace('user-request');
        
        // 模拟业务处理时间
        setTimeout(() => {
            apmSystem.finishTrace(trace.spanId, Math.random() > 0.9 ? 'error' : 'ok');
        }, Math.random() * 200 + 50);
    }, 2000);

    // 模拟自定义业务指标
    setInterval(() => {
        apmSystem.recordMetric('business', {
            orders: Math.floor(Math.random() * 10),
            revenue: Math.random() * 1000,
            userSessions: Math.floor(Math.random() * 50)
        });
    }, 5000);

    console.log('APM监控系统演示已启动...');
    console.log('- 自动生成模拟链路追踪数据');
    console.log('- 自动收集系统性能指标');
    console.log('- 自动检测异常并发送告警');

    // 优雅关闭
    process.on('SIGINT', () => {
        console.log('收到关闭信号，正在关闭APM系统...');
        apmSystem.stopMonitoring();
        process.exit(0);
    });
}
```

## 🎯 面试要点总结

### 技术深度体现
- **分布式链路追踪**：TraceID/SpanID生成、跨服务传播、采样策略
- **多维度指标采集**：应用层、中间件、系统层、网络层监控
- **智能异常检测**：阈值检测、趋势分析、关联分析、机器学习
- **告警管理体系**：告警生命周期、通知渠道、抑制规则、escalation

### 生产实践经验
- **低侵入性设计**：自动插桩、异步处理、性能开销控制
- **海量数据处理**：采样策略、数据压缩、存储优化、查询加速
- **高可用架构**：监控系统容错、故障转移、数据备份恢复
- **运维自动化**：自动发现、自动恢复、自动扩容、智能运维

### 面试回答要点
- **APM架构设计**：数据采集、传输、存储、分析、展示的完整链路
- **性能监控策略**：关键指标选择、监控粒度、数据保留策略
- **异常检测算法**：统计学方法、机器学习、时间序列分析
- **故障排查能力**：链路追踪分析、性能瓶颈定位、根因分析方法

---

*本解决方案展示了企业级APM监控系统的完整实现，体现了对分布式系统监控、性能分析和故障诊断的深度理解*