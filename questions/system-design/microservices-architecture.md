# 微服务架构

## 🎯 核心知识点

- 微服务架构原理
- 服务拆分策略
- API网关设计
- 服务间通信
- 数据管理模式
- 服务治理体系

## 📊 微服务架构演进

```mermaid
graph TD
    A[架构演进] --> B[单体架构]
    A --> C[SOA架构]
    A --> D[微服务架构]
    
    B --> B1[单一部署单元]
    B --> B2[共享数据库]
    B --> B3[紧耦合组件]
    
    C --> C1[服务化拆分]
    C --> C2[ESB企业服务总线]
    C --> C3[标准化接口]
    
    D --> D1[独立部署]
    D --> D2[去中心化]
    D --> D3[数据隔离]
    
    subgraph "微服务特征"
        E[业务能力导向]
        F[去中心化治理]
        G[故障隔离]
        H[技术多样性]
    end
```

## 💡 面试题目

### **初级** 微服务 vs 单体架构对比
**题目：** 比较微服务架构和单体架构的优缺点，什么情况下应该选择微服务架构？

**答案要点：**

```mermaid
graph LR
    A[架构对比] --> B[开发复杂度]
    A --> C[部署复杂度]
    A --> D[运维复杂度]
    A --> E[性能影响]
    
    B --> B1[单体: 简单统一]
    B --> B2[微服务: 分布式复杂]
    
    C --> C1[单体: 整体部署]
    C --> C2[微服务: 独立部署]
    
    D --> D1[单体: 监控简单]
    D --> D2[微服务: 分布式监控]
    
    E --> E1[单体: 进程内调用]
    E --> E2[微服务: 网络调用]
```

**选择标准矩阵：**

| 因素 | 单体架构 | 微服务架构 |
|------|----------|------------|
| 团队规模 | 小团队(≤10人) | 大团队(>10人) |
| 业务复杂度 | 简单明确 | 复杂多变 |
| 技术栈 | 统一技术栈 | 多元化需求 |
| 部署频率 | 低频部署 | 高频部署 |
| 扩展需求 | 整体扩展 | 差异化扩展 |
| 团队经验 | 传统开发经验 | 分布式经验丰富 |

**微服务适用场景：**
- 大型复杂业务系统
- 高频发布需求
- 团队规模较大且分布式
- 不同服务性能要求差异大
- 需要技术栈多样性

### **中级** 服务拆分策略设计
**题目：** 针对一个电商系统，如何进行微服务拆分？请设计具体的拆分方案和边界定义。

**答案要点：**

```mermaid
graph TB
    subgraph "电商微服务架构"
        A[API网关] --> B[用户服务]
        A --> C[商品服务]
        A --> D[订单服务]
        A --> E[支付服务]
        A --> F[库存服务]
        A --> G[推荐服务]
        A --> H[通知服务]
        
        B --> B1[(用户数据库)]
        C --> C1[(商品数据库)]
        D --> D1[(订单数据库)]
        E --> E1[(支付数据库)]
        F --> F1[(库存数据库)]
        G --> G1[(推荐数据库)]
        
        subgraph "服务间通信"
            I[同步调用]
            J[异步消息]
            K[事件驱动]
        end
        
        D --> E
        D --> F
        F --> C
        G --> C
        H --> MQ[消息队列]
    end
```

**拆分原则和方法：**

```mermaid
flowchart TD
    A[服务拆分策略] --> B[按业务能力]
    A --> C[按数据模型]
    A --> D[按组织结构]
    A --> E[按技术边界]
    
    B --> B1[用户管理]
    B --> B2[商品管理]
    B --> B3[订单处理]
    B --> B4[支付结算]
    
    C --> C1[用户域数据]
    C --> C2[商品域数据]
    C --> C3[交易域数据]
    
    D --> D1[前端团队]
    D --> D2[后台团队]
    D --> D3[运营团队]
    
    E --> E1[高并发服务]
    E --> E2[计算密集服务]
    E --> E3[IO密集服务]
```

### **高级** 微服务架构治理体系
**题目：** 设计一个完整的微服务治理体系，包括服务发现、配置管理、监控告警、熔断降级等。

**答案要点：**

```mermaid
graph TB
    subgraph "服务治理平台"
        A[服务注册中心] --> A1[Eureka/Consul]
        B[配置中心] --> B1[Apollo/Nacos]
        C[API网关] --> C1[Zuul/Gateway]
        D[服务网格] --> D1[Istio/Linkerd]
    end
    
    subgraph "监控体系"
        E[链路追踪] --> E1[Jaeger/Zipkin]
        F[指标监控] --> F1[Prometheus/Grafana]
        G[日志聚合] --> G1[ELK/EFK]
        H[告警系统] --> H1[AlertManager]
    end
    
    subgraph "容错机制"
        I[熔断器] --> I1[Hystrix/Sentinel]
        J[限流器] --> J1[Guava RateLimiter]
        K[重试机制] --> K1[Spring Retry]
        L[降级策略] --> L1[Fallback]
    end
    
    subgraph "部署运维"
        M[容器化] --> M1[Docker/K8s]
        N[CI/CD] --> N1[Jenkins/GitLab]
        O[灰度发布] --> O1[蓝绿/金丝雀]
    end
```

## 🔧 核心组件设计

### API网关架构

```mermaid
graph TD
    A[客户端请求] --> B[API网关]
    
    B --> C[认证授权]
    B --> D[限流控制]
    B --> E[请求路由]
    B --> F[协议转换]
    B --> G[响应聚合]
    
    C --> C1[JWT验证]
    C --> C2[OAuth2.0]
    C --> C3[权限检查]
    
    D --> D1[令牌桶]
    D --> D2[漏桶算法]
    D --> D3[滑动窗口]
    
    E --> E1[路径匹配]
    E --> E2[负载均衡]
    E --> E3[版本控制]
    
    F --> F1[HTTP → gRPC]
    F --> F2[RESTful → GraphQL]
    
    G --> G1[数据聚合]
    G --> G2[字段过滤]
    G --> G3[格式转换]
    
    E --> H[微服务集群]
```

### 服务间通信模式

```mermaid
sequenceDiagram
    participant Client
    participant APIGateway
    participant OrderService
    participant PaymentService
    participant InventoryService
    participant MessageQueue
    
    Note over Client,MessageQueue: 同步调用模式
    Client->>APIGateway: 创建订单请求
    APIGateway->>OrderService: 验证订单信息
    OrderService->>InventoryService: 检查库存
    InventoryService->>OrderService: 库存确认
    OrderService->>PaymentService: 发起支付
    PaymentService->>OrderService: 支付结果
    OrderService->>APIGateway: 订单创建结果
    APIGateway->>Client: 返回订单信息
    
    Note over OrderService,MessageQueue: 异步消息模式
    OrderService->>MessageQueue: 发布订单创建事件
    MessageQueue->>InventoryService: 消费库存扣减事件
    MessageQueue->>PaymentService: 消费支付处理事件
```

## ⚡ 数据管理策略

### 数据一致性模式

```mermaid
graph TD
    A[数据一致性] --> B[强一致性]
    A --> C[最终一致性]
    A --> D[事务一致性]
    
    B --> B1[同步调用]
    B --> B2[分布式锁]
    B --> B3[两阶段提交]
    
    C --> C1[事件驱动]
    C --> C2[消息队列]
    C --> C3[异步补偿]
    
    D --> D1[Saga模式]
    D --> D2[TCC模式]
    D --> D3[事件溯源]
```

### Saga分布式事务

```mermaid
sequenceDiagram
    participant Orchestrator
    participant OrderService
    participant PaymentService
    participant InventoryService
    
    Note over Orchestrator: 编排式Saga
    Orchestrator->>OrderService: 1. 创建订单
    OrderService->>Orchestrator: 订单创建成功
    
    Orchestrator->>PaymentService: 2. 扣款
    PaymentService->>Orchestrator: 扣款成功
    
    Orchestrator->>InventoryService: 3. 扣减库存
    InventoryService-->>Orchestrator: 库存不足，失败
    
    Note over Orchestrator: 执行补偿事务
    Orchestrator->>PaymentService: 补偿：退款
    Orchestrator->>OrderService: 补偿：取消订单
```

## 🛡️ 容错与监控

### 熔断器模式

```mermaid
stateDiagram-v2
    [*] --> Closed: 正常状态
    Closed --> Open: 失败率超过阈值
    Open --> HalfOpen: 超时时间到达
    HalfOpen --> Closed: 测试调用成功
    HalfOpen --> Open: 测试调用失败
    
    note right of Closed
        允许请求通过
        记录成功/失败次数
    end note
    
    note right of Open
        拒绝所有请求
        直接返回失败
    end note
    
    note right of HalfOpen
        允许少量测试请求
        根据结果决定状态
    end note
```

### 服务监控体系

```mermaid
graph TD
    A[微服务监控] --> B[基础设施监控]
    A --> C[应用性能监控]
    A --> D[业务指标监控]
    A --> E[用户体验监控]
    
    B --> B1[CPU/内存/磁盘]
    B --> B2[网络连通性]
    B --> B3[容器资源]
    
    C --> C1[请求响应时间]
    C --> C2[错误率统计]
    C --> C3[吞吐量指标]
    
    D --> D1[订单转化率]
    D --> D2[用户活跃度]
    D --> D3[收入指标]
    
    E --> E1[页面加载时间]
    E --> E2[用户操作流畅度]
    E --> E3[错误页面监控]
```

## 📈 部署与扩展

### 容器化部署

```mermaid
graph TB
    subgraph "开发环境"
        A[源码仓库] --> B[CI/CD流水线]
    end
    
    subgraph "镜像仓库"
        B --> C[Docker镜像]
    end
    
    subgraph "Kubernetes集群"
        C --> D[Pod部署]
        D --> E[Service暴露]
        E --> F[Ingress路由]
        
        G[ConfigMap] --> D
        H[Secret] --> D
        I[PersistentVolume] --> D
    end
    
    subgraph "监控告警"
        J[Prometheus] --> K[Grafana]
        J --> L[AlertManager]
    end
    
    D --> J
```

### 弹性扩缩容策略

```mermaid
flowchart TD
    A[扩缩容策略] --> B[水平扩缩容]
    A --> C[垂直扩缩容]
    A --> D[自动扩缩容]
    
    B --> B1[增减Pod数量]
    B --> B2[基于CPU/内存指标]
    B --> B3[基于自定义指标]
    
    C --> C1[调整资源限制]
    C --> C2[升级节点规格]
    
    D --> D1[HPA水平扩缩容]
    D --> D2[VPA垂直扩缩容]
    D --> D3[集群自动扩缩容]
```

## 💡 面试要点总结

### 设计考虑要素
1. **业务边界**：根据业务能力和数据模型拆分服务
2. **团队结构**：康威定律 - 组织架构决定系统架构
3. **技术成熟度**：团队对分布式系统的掌握程度
4. **运维能力**：监控、部署、故障处理能力

### 架构权衡
- **复杂性 vs 灵活性**：分布式复杂度 vs 独立演进能力
- **性能 vs 隔离性**：网络调用开销 vs 故障隔离
- **一致性 vs 可用性**：强一致性 vs 系统可用性
- **标准化 vs 自主性**：统一标准 vs 技术自主选择

### 成功要素
1. **渐进式演进**：从单体逐步拆分，避免大爆炸式重构
2. **文化转变**：DevOps文化、自动化运维能力
3. **工具链完善**：监控、部署、测试工具支持
4. **组织调整**：小团队、全栈职责、快速响应

### 常见陷阱
❌ **过度拆分**：拆分过细导致管理复杂度爆炸
❌ **数据耦合**：服务间直接共享数据库
❌ **分布式单体**：服务间强依赖，失去微服务优势
❌ **忽视运维**：只关注开发，忽视部署和监控

## 🔗 相关链接

- [← 返回系统设计主页](./README.md)
- [分布式系统](./distributed-systems.md)
- [API设计](./api-design.md)
- [容错与恢复](./fault-tolerance.md)

---

*微服务架构是现代大型系统的主流选择，但需要在复杂性和收益之间找到平衡* 🏗️ 