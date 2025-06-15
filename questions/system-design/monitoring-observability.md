# 监控与可观测性

## 🎯 核心知识点

- 监控指标体系
- 日志管理与分析
- 链路追踪与调用链
- 告警系统设计
- 可观测性三大支柱

## 📊 可观测性架构设计

```mermaid
graph TB
    A[应用服务] --> B[数据收集层]
    C[基础设施] --> B
    D[业务流程] --> B
    
    subgraph "数据收集层"
        B --> E[Metrics指标]
        B --> F[Logs日志]
        B --> G[Traces链路]
    end
    
    subgraph "数据处理层"
        E --> H[时序数据库]
        F --> I[日志存储]
        G --> J[链路存储]
    end
    
    subgraph "分析展示层"
        H --> K[监控仪表板]
        I --> L[日志分析]
        J --> M[链路分析]
    end
    
    subgraph "告警系统"
        K --> N[告警规则]
        L --> N
        M --> N
        N --> O[通知渠道]
    end
```

## 💡 面试题目

### **初级** 监控指标体系设计
**题目：** 设计一个Web服务的监控指标体系，包括系统指标、应用指标和业务指标。

**答案要点：**

```mermaid
graph TD
    A[监控指标体系] --> B[基础设施指标]
    A --> C[应用指标]
    A --> D[业务指标]
    
    B --> B1[CPU使用率]
    B --> B2[内存使用率]
    B --> B3[磁盘I/O]
    B --> B4[网络带宽]
    
    C --> C1[响应时间]
    C --> C2[吞吐量QPS]
    C --> C3[错误率]
    C --> C4[可用性]
    
    D --> D1[用户活跃度]
    D --> D2[转化率]
    D --> D3[收入指标]
    D --> D4[功能使用率]
```

**四个黄金指标（Golden Signals）：**

| 指标 | 描述 | 计算方式 | 告警阈值 |
|------|------|----------|----------|
| 延迟 | 请求处理时间 | P95、P99响应时间 | P95 > 100ms |
| 流量 | 请求数量 | QPS、每秒事务数 | 超过容量80% |
| 错误 | 错误请求比例 | 错误率 = 错误数/总请求数 | 错误率 > 1% |
| 饱和度 | 资源利用率 | CPU、内存、磁盘使用率 | 使用率 > 80% |

### **中级** 分布式链路追踪系统
**题目：** 设计一个微服务架构的分布式链路追踪系统，能够追踪请求在多个服务间的调用路径。

**答案要点：**

```mermaid
sequenceDiagram
    participant Client
    participant APIGateway
    participant UserService
    participant OrderService
    participant PaymentService
    participant Database
    
    Client->>APIGateway: Request (TraceID: 123)
    APIGateway->>UserService: Forward (TraceID: 123, SpanID: 1)
    UserService->>OrderService: Get Orders (TraceID: 123, SpanID: 2)
    OrderService->>PaymentService: Check Payment (TraceID: 123, SpanID: 3)
    PaymentService->>Database: Query (TraceID: 123, SpanID: 4)
    Database-->>PaymentService: Result
    PaymentService-->>OrderService: Payment Status
    OrderService-->>UserService: Order List
    UserService-->>APIGateway: User Data
    APIGateway-->>Client: Response
```

**链路追踪核心概念：**

```mermaid
graph TD
    A[Trace链路] --> B[Span调用]
    B --> C[SpanContext上下文]
    
    A --> A1[TraceID全局唯一]
    A --> A2[完整调用链]
    
    B --> B1[操作名称]
    B --> B2[开始时间]
    B --> B3[结束时间]
    B --> B4[标签Tags]
    B --> B5[日志Logs]
    
    C --> C1[SpanID]
    C --> C2[ParentSpanID]
    C --> C3[采样标识]
    C --> C4[Baggage]
```

### **高级** 智能告警系统设计
**题目：** 设计一个智能告警系统，能够减少告警疲劳，提供根因分析和自动化处理能力。

```mermaid
graph TB
    A[数据源] --> B[告警引擎]
    
    subgraph "告警处理"
        B --> C[规则匹配]
        C --> D[异常检测]
        D --> E[告警聚合]
        E --> F[告警抑制]
        F --> G[告警路由]
    end
    
    subgraph "智能分析"
        G --> H[根因分析]
        H --> I[影响评估]
        I --> J[预测分析]
    end
    
    subgraph "自动化响应"
        J --> K[自动修复]
        K --> L[扩容缩容]
        L --> M[故障转移]
    end
    
    G --> N[通知渠道]
    M --> N
```

## 📈 监控指标设计

### RED方法 vs USE方法

```mermaid
graph LR
    A[监控方法] --> B[RED方法]
    A --> C[USE方法]
    
    B --> B1[Rate请求速率]
    B --> B2[Errors错误率]
    B --> B3[Duration持续时间]
    
    C --> C1[Utilization利用率]
    C --> C2[Saturation饱和度]
    C --> C3[Errors错误]
    
    B --> B4[面向服务]
    C --> C4[面向资源]
```

### 监控指标分层架构

```mermaid
graph TD
    A[监控分层] --> B[基础设施层]
    A --> C[平台层]
    A --> D[应用层]
    A --> E[业务层]
    
    B --> B1[CPU/内存/磁盘/网络]
    B --> B2[主机存活/连通性]
    
    C --> C1[容器/K8s/数据库]
    C --> C2[中间件/缓存/队列]
    
    D --> D1[接口响应时间/错误率]
    D --> D2[JVM/GC/线程池]
    
    E --> E1[用户行为/业务流程]
    E --> E2[核心业务指标]
```

## 🔍 日志管理系统

### 日志架构设计

```mermaid
graph TD
    A[应用日志] --> B[日志收集]
    C[系统日志] --> B
    D[访问日志] --> B
    
    subgraph "收集层"
        B --> E[Filebeat]
        B --> F[Fluentd]
        B --> G[Logstash]
    end
    
    subgraph "传输层"
        E --> H[Kafka]
        F --> H
        G --> H
    end
    
    subgraph "存储层"
        H --> I[Elasticsearch]
        H --> J[ClickHouse]
    end
    
    subgraph "分析层"
        I --> K[Kibana]
        J --> L[Grafana]
    end
```

### 结构化日志格式

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "user-service",
  "traceId": "abc123",
  "spanId": "def456",
  "userId": "user123",
  "action": "login",
  "duration": 150,
  "status": "success",
  "message": "User login successful",
  "metadata": {
    "ip": "192.168.1.100",
    "userAgent": "Mozilla/5.0...",
    "version": "1.2.3"
  }
}
```

### 日志级别与用途

| 级别 | 用途 | 示例场景 | 生产环境 |
|------|------|----------|----------|
| TRACE | 详细执行流程 | 函数调用轨迹 | 否 |
| DEBUG | 调试信息 | 变量值、条件判断 | 否 |
| INFO | 关键业务信息 | 用户操作、系统状态 | 是 |
| WARN | 潜在问题 | 配置缺失、性能问题 | 是 |
| ERROR | 错误信息 | 异常、失败操作 | 是 |
| FATAL | 致命错误 | 系统崩溃 | 是 |

## 🔗 链路追踪实现

### OpenTelemetry标准

```mermaid
graph TD
    A[OpenTelemetry] --> B[API]
    A --> C[SDK]
    A --> D[Collector]
    A --> E[Instrumentation]
    
    B --> B1[Tracer]
    B --> B2[Meter]
    B --> B3[Logger]
    
    C --> C1[采样策略]
    C --> C2[资源检测]
    C --> C3[导出器]
    
    D --> D1[接收器]
    D --> D2[处理器]
    D --> D3[导出器]
    
    E --> E1[自动埋点]
    E --> E2[手动埋点]
```

### 采样策略

```mermaid
flowchart TD
    A[请求到达] --> B{是否需要采样}
    B -->|是| C[确定采样策略]
    B -->|否| D[不采样]
    
    C --> E[固定比例采样]
    C --> F[自适应采样]
    C --> G[基于延迟采样]
    
    E --> H[创建Trace]
    F --> H
    G --> H
    
    H --> I[生成SpanContext]
    I --> J[传播到下游]
```

## 🚨 告警系统设计

### 告警规则引擎

```mermaid
graph TD
    A[监控数据] --> B[规则引擎]
    
    subgraph "规则类型"
        B --> C[阈值规则]
        B --> D[趋势规则]
        B --> E[异常检测]
        B --> F[复合规则]
    end
    
    subgraph "告警处理"
        C --> G[告警生成]
        D --> G
        E --> G
        F --> G
        
        G --> H[告警聚合]
        H --> I[告警抑制]
        I --> J[告警路由]
    end
    
    J --> K[通知发送]
```

### 告警降噪策略

```mermaid
stateDiagram-v2
    [*] --> 监控
    监控 --> 触发: 阈值超标
    触发 --> 等待: 启动抑制期
    等待 --> 触发: 持续异常
    等待 --> 监控: 恢复正常
    触发 --> 告警: 确认异常
    告警 --> 恢复: 问题解决
    恢复 --> 监控: 自动恢复
```

### 告警级别与响应

| 级别 | 描述 | 响应时间 | 通知方式 | 升级策略 |
|------|------|----------|----------|----------|
| P0-致命 | 服务完全不可用 | 5分钟 | 电话+短信+邮件 | 立即升级 |
| P1-严重 | 核心功能受影响 | 15分钟 | 短信+邮件 | 30分钟升级 |
| P2-重要 | 部分功能异常 | 30分钟 | 邮件+IM | 2小时升级 |
| P3-一般 | 性能问题 | 1小时 | 邮件 | 24小时升级 |
| P4-轻微 | 潜在风险 | 24小时 | 邮件 | 无升级 |

## 🛠️ 技术栈选型

### 监控技术栈对比

```mermaid
graph TD
    A[监控技术栈] --> B[Prometheus生态]
    A --> C[ELK Stack]
    A --> D[云原生方案]
    A --> E[商业解决方案]
    
    B --> B1[Prometheus]
    B --> B2[Grafana]
    B --> B3[AlertManager]
    B --> B4[Jaeger]
    
    C --> C1[Elasticsearch]
    C --> C2[Logstash]
    C --> C3[Kibana]
    C --> C4[Beats]
    
    D --> D1[Kubernetes]
    D --> D2[OpenTelemetry]
    D --> D3[Istio]
    
    E --> E1[Datadog]
    E --> E2[New Relic]
    E --> E3[Dynatrace]
```

### 存储方案选择

| 数据类型 | 存储方案 | 特点 | 适用场景 |
|----------|----------|------|----------|
| 时序指标 | Prometheus/InfluxDB | 高写入性能 | 监控指标 |
| 日志数据 | Elasticsearch/ClickHouse | 全文搜索 | 日志分析 |
| 链路数据 | Jaeger/Zipkin | 图数据库 | 链路追踪 |
| 事件数据 | Kafka/RabbitMQ | 消息队列 | 事件流处理 |

## 📋 实施最佳实践

### 监控即代码

```yaml
# 监控规则示例
groups:
  - name: api_monitoring
    rules:
      - alert: HighErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.01
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"
      
      - alert: HighLatency
        expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High latency detected"
```

### 仪表板设计原则

```mermaid
graph TD
    A[仪表板设计] --> B[分层展示]
    A --> C[关键指标突出]
    A --> D[交互式探索]
    A --> E[自动刷新]
    
    B --> B1[概览视图]
    B --> B2[详细视图]
    B --> B3[钻取分析]
    
    C --> C1[RED指标]
    C --> C2[SLA指标]
    C --> C3[业务指标]
    
    D --> D1[时间范围选择]
    D --> D2[维度过滤]
    D --> D3[关联分析]
```

## 💡 面试要点总结

### 可观测性三大支柱
1. **Metrics指标**：定量数据，反映系统状态
2. **Logs日志**：离散事件，提供详细上下文
3. **Traces链路**：请求流转，展示调用关系

### 监控设计原则
- **业务优先**：从业务角度设计监控指标
- **分层监控**：基础设施→应用→业务多层监控
- **主动监控**：预测性监控，提前发现问题
- **自动化运维**：监控驱动的自动化处理

### 告警系统要点
- **有效性**：准确识别真正的问题
- **及时性**：在问题影响用户前发现
- **可操作性**：提供明确的处理指导
- **可扩展性**：支持规则动态配置

### 性能优化策略
- **采样策略**：平衡监控精度和性能开销
- **数据压缩**：减少存储和传输成本
- **批量处理**：提高数据处理效率
- **缓存机制**：加速查询响应

### 常见问题与解决方案

| 问题 | 影响 | 解决方案 |
|------|------|----------|
| 告警风暴 | 影响响应效率 | 告警聚合、抑制规则 |
| 数据孤岛 | 缺乏全局视角 | 统一监控平台 |
| 存储成本高 | 运维成本上升 | 数据分层、自动清理 |
| 查询性能差 | 影响故障排查 | 索引优化、预聚合 |

## 🔗 相关链接

- [← 返回系统设计主页](./README.md)
- [分布式系统](./distributed-systems.md)
- [微服务架构](./microservices-architecture.md)
- [安全架构设计](./security-architecture.md)

---

*可观测性是现代分布式系统的基础设施，为系统稳定性提供重要保障* 📊 