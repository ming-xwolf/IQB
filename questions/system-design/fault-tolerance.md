# 容错与恢复

## 🎯 核心知识点

- 容错设计原则
- 故障检测机制
- 自动恢复策略
- 容灾备份方案
- 混沌工程实践

## 📊 容错架构设计

```mermaid
graph TB
    A[容错系统] --> B[检测层]
    A --> C[隔离层]
    A --> D[恢复层]
    A --> E[预防层]
    
    B --> B1[健康检查]
    B --> B2[故障检测]
    B --> B3[性能监控]
    
    C --> C1[服务隔离]
    C --> C2[资源隔离]
    C --> C3[故障隔离]
    
    D --> D1[自动重试]
    D --> D2[故障转移]
    D --> D3[降级处理]
    
    E --> E1[冗余设计]
    E --> E2[负载均衡]
    E --> E3[容量规划]
```

## 💡 面试题目

### **初级** 服务容错机制设计
**题目：** 设计一个电商系统的服务容错机制，确保在依赖服务出现故障时系统仍能正常工作。

**答案要点：**

```mermaid
graph TD
    A[用户请求] --> B[API网关]
    B --> C{服务健康检查}
    
    C -->|正常| D[调用服务]
    C -->|异常| E[容错处理]
    
    D --> F{调用成功?}
    F -->|成功| G[返回结果]
    F -->|失败| H[重试机制]
    
    H --> I{重试次数达到上限?}
    I -->|否| D
    I -->|是| J[熔断器]
    
    E --> K[降级服务]
    J --> K
    K --> L[返回默认结果]
```

**容错模式对比：**

| 模式 | 适用场景 | 实现复杂度 | 恢复能力 | 性能影响 |
|------|----------|------------|----------|----------|
| 重试 | 临时故障 | 低 | 高 | 低 |
| 熔断器 | 持续故障 | 中等 | 中等 | 中等 |
| 降级 | 服务不可用 | 中等 | 中等 | 低 |
| 超时 | 响应慢 | 低 | 低 | 低 |
| 隔离 | 资源竞争 | 高 | 高 | 中等 |

### **中级** 分布式系统故障检测
**题目：** 设计一个分布式系统的故障检测机制，能够快速发现节点故障并触发恢复流程。

**答案要点：**

```mermaid
sequenceDiagram
    participant Node1
    participant Node2
    participant Node3
    participant FailureDetector
    participant RecoveryManager
    
    Node1->>Node2: Heartbeat
    Node1->>Node3: Heartbeat
    
    Note over Node2: Node2故障
    
    Node1->>Node2: Heartbeat (超时)
    Node1->>FailureDetector: 报告Node2疑似故障
    
    FailureDetector->>Node3: 确认Node2状态
    Node3->>FailureDetector: 确认Node2不可达
    
    FailureDetector->>RecoveryManager: 触发故障恢复
    RecoveryManager->>Node1: 重新分配Node2任务
    RecoveryManager->>Node3: 重新分配Node2任务
```

**故障检测算法：**

```mermaid
graph TD
    A[故障检测算法] --> B[基于心跳]
    A --> C[基于超时]
    A --> D[基于响应时间]
    A --> E[基于Gossip协议]
    
    B --> B1[定期心跳]
    B --> B2[失败计数器]
    B --> B3[可疑节点标记]
    
    C --> C1[请求超时]
    C --> C2[连接超时]
    C --> C3[读写超时]
    
    D --> D1[响应时间阈值]
    D --> D2[延迟抖动检测]
    D --> D3[性能降级检测]
    
    E --> E1[节点状态传播]
    E --> E2[故障信息汇聚]
    E --> E3[一致性确认]
```

### **高级** 多数据中心容灾设计
**题目：** 设计一个支持多数据中心的容灾系统，要求RPO<1分钟，RTO<5分钟。

```mermaid
graph TB
    subgraph "主数据中心"
        A1[应用服务器]
        A2[数据库主库]
        A3[Redis主节点]
        A4[文件存储]
    end
    
    subgraph "备数据中心"
        B1[应用服务器]
        B2[数据库从库]
        B3[Redis从节点]
        B4[文件存储备份]
    end
    
    subgraph "监控中心"
        C1[故障检测]
        C2[自动切换]
        C3[流量调度]
    end
    
    A1 --> B1
    A2 --> B2
    A3 --> B3
    A4 --> B4
    
    C1 --> C2
    C2 --> C3
    C3 --> A1
    C3 --> B1
```

## 🛡️ 容错设计模式

### 熔断器模式

```mermaid
stateDiagram-v2
    [*] --> 关闭
    关闭 --> 打开: 故障率超过阈值
    打开 --> 半开: 超时时间到达
    半开 --> 关闭: 测试调用成功
    半开 --> 打开: 测试调用失败
    
    关闭: 正常处理请求<br/>记录成功/失败次数
    打开: 快速失败<br/>直接返回错误
    半开: 允许少量请求<br/>测试服务恢复状态
```

**熔断器参数配置：**

| 参数 | 说明 | 典型值 | 调优建议 |
|------|------|--------|----------|
| 失败阈值 | 触发熔断的失败率 | 50% | 根据业务容忍度调整 |
| 时间窗口 | 统计时间窗口 | 10秒 | 考虑请求频率 |
| 最小请求数 | 最小统计样本 | 20 | 避免小样本误判 |
| 等待时间 | 熔断器打开时长 | 60秒 | 给服务恢复时间 |
| 半开试探数 | 半开状态测试请求数 | 3 | 快速验证恢复状态 |

### 舱壁模式

```mermaid
graph TD
    A[请求流量] --> B[路由分发]
    
    subgraph "核心服务舱"
        B --> C1[核心功能1]
        B --> C2[核心功能2]
    end
    
    subgraph "次要服务舱"
        B --> D1[次要功能1]
        B --> D2[次要功能2]
    end
    
    subgraph "实验服务舱"
        B --> E1[实验功能1]
        B --> E2[实验功能2]
    end
    
    C1 --> F1[独立线程池]
    C2 --> F2[独立线程池]
    D1 --> F3[独立线程池]
    D2 --> F4[独立线程池]
    E1 --> F5[独立线程池]
    E2 --> F6[独立线程池]
```

### 重试模式

```mermaid
flowchart TD
    A[发起请求] --> B{请求成功?}
    B -->|成功| C[返回结果]
    B -->|失败| D{是否可重试?}
    
    D -->|否| E[抛出异常]
    D -->|是| F{重试次数<上限?}
    
    F -->|否| E
    F -->|是| G[等待退避时间]
    G --> H[重试计数+1]
    H --> A
```

**重试策略对比：**

| 策略 | 描述 | 适用场景 | 优缺点 |
|------|------|----------|--------|
| 立即重试 | 失败后立即重试 | 网络抖动 | 简单，但可能加重系统负担 |
| 固定延迟 | 固定时间间隔重试 | 临时资源不足 | 避免系统压力，但恢复慢 |
| 指数退避 | 延迟时间指数增长 | 系统过载 | 自适应，但复杂度高 |
| 随机抖动 | 添加随机延迟 | 高并发场景 | 避免雷群效应 |

## 🔧 故障恢复策略

### 自动故障转移

```mermaid
sequenceDiagram
    participant Client
    participant LoadBalancer
    participant PrimaryServer
    participant BackupServer
    participant HealthCheck
    
    Client->>LoadBalancer: 请求
    LoadBalancer->>PrimaryServer: 转发请求
    
    Note over PrimaryServer: 服务故障
    
    HealthCheck->>PrimaryServer: 健康检查失败
    HealthCheck->>LoadBalancer: 标记主服务不可用
    
    Client->>LoadBalancer: 新请求
    LoadBalancer->>BackupServer: 转发到备用服务
    BackupServer->>Client: 响应
    
    Note over PrimaryServer: 服务恢复
    
    HealthCheck->>PrimaryServer: 健康检查成功
    HealthCheck->>LoadBalancer: 恢复主服务状态
```

### 数据恢复机制

```mermaid
graph TD
    A[数据恢复] --> B[备份恢复]
    A --> C[复制恢复]
    A --> D[快照恢复]
    A --> E[增量恢复]
    
    B --> B1[全量备份]
    B --> B2[增量备份]
    B --> B3[差异备份]
    
    C --> C1[同步复制]
    C --> C2[异步复制]
    C --> C3[半同步复制]
    
    D --> D1[定时快照]
    D --> D2[触发快照]
    D --> D3[快照链]
    
    E --> E1[WAL日志]
    E --> E2[Binlog]
    E --> E3[事务日志]
```

### 服务降级策略

```mermaid
graph TD
    A[服务降级] --> B[功能降级]
    A --> C[性能降级]
    A --> D[容量降级]
    
    B --> B1[关闭非核心功能]
    B --> B2[简化业务流程]
    B --> B3[返回默认结果]
    
    C --> C1[减少计算复杂度]
    C --> C2[降低数据精度]
    C --> C3[使用缓存数据]
    
    D --> D1[限制并发数]
    D --> D2[拒绝部分请求]
    D --> D3[启用排队机制]
```

## 📊 容灾指标定义

### RTO与RPO

```mermaid
timeline
    title 故障恢复时间线
    
    section 正常运行
        : 系统正常服务
    
    section 故障发生
        : 故障发生点
        : 最后有效数据备份
    
    section 恢复过程
        : 故障检测
        : 启动恢复流程
        : 数据恢复完成
        : 服务恢复完成
    
    section 指标定义
        : RPO (恢复点目标)
        : RTO (恢复时间目标)
```

**容灾等级划分：**

| 等级 | RTO | RPO | 可用性 | 成本 | 适用场景 |
|------|-----|-----|--------|------|----------|
| Tier 0 | >24小时 | >4小时 | 95% | 低 | 非关键系统 |
| Tier 1 | 4-24小时 | 1-4小时 | 99% | 中低 | 一般业务系统 |
| Tier 2 | 1-4小时 | 15分钟-1小时 | 99.9% | 中等 | 重要业务系统 |
| Tier 3 | 15分钟-1小时 | 1-15分钟 | 99.95% | 中高 | 核心业务系统 |
| Tier 4 | <15分钟 | <1分钟 | 99.99% | 高 | 关键业务系统 |

### 容错能力评估

```mermaid
radar
    title 系统容错能力评估
    "故障检测" : 8
    "自动恢复" : 7
    "数据一致性" : 9
    "服务可用性" : 8
    "性能影响" : 6
    "运维复杂度" : 5
```

## 🏗️ 技术实现

### 健康检查实现

```mermaid
graph TD
    A[健康检查] --> B[浅层检查]
    A --> C[深层检查]
    A --> D[依赖检查]
    
    B --> B1[进程存活]
    B --> B2[端口监听]
    B --> B3[HTTP响应]
    
    C --> C1[数据库连接]
    C --> C2[缓存可用性]
    C --> C3[磁盘空间]
    
    D --> D1[下游服务]
    D --> D2[第三方接口]
    D --> D3[消息队列]
```

### 分布式锁与选主

```mermaid
sequenceDiagram
    participant Node1
    participant Node2
    participant Node3
    participant Coordinator
    
    Note over Node1,Node3: 选主过程
    
    Node1->>Coordinator: 请求锁 (term=1)
    Node2->>Coordinator: 请求锁 (term=1)
    Node3->>Coordinator: 请求锁 (term=1)
    
    Coordinator->>Node1: 获得锁 (leader)
    Coordinator->>Node2: 锁被占用
    Coordinator->>Node3: 锁被占用
    
    Note over Node1: Node1成为Leader
    
    Node1->>Coordinator: 心跳续约
    
    Note over Node1: Node1故障
    
    Node2->>Coordinator: 请求锁 (term=2)
    Node3->>Coordinator: 请求锁 (term=2)
    
    Coordinator->>Node2: 获得锁 (leader)
    
    Note over Node2: Node2成为新Leader
```

## 🧪 混沌工程

### 故障注入实验

```mermaid
graph TD
    A[混沌实验] --> B[网络故障]
    A --> C[服务故障]
    A --> D[资源故障]
    A --> E[数据故障]
    
    B --> B1[网络延迟]
    B --> B2[网络丢包]
    B --> B3[网络分区]
    
    C --> C1[服务崩溃]
    C --> C2[服务假死]
    C --> C3[响应异常]
    
    D --> D1[CPU占满]
    D --> D2[内存耗尽]
    D --> D3[磁盘满载]
    
    E --> E1[数据损坏]
    E --> E2[数据丢失]
    E --> E3[数据不一致]
```

### 混沌实验执行流程

```mermaid
stateDiagram-v2
    [*] --> 假设制定
    假设制定 --> 实验设计: 定义故障场景
    实验设计 --> 基线建立: 确定正常行为
    基线建立 --> 故障注入: 执行混沌实验
    故障注入 --> 观察分析: 监控系统行为
    观察分析 --> 结果验证: 验证假设
    结果验证 --> 改进优化: 发现问题
    改进优化 --> [*]: 实验结束
    
    结果验证 --> 假设制定: 继续其他场景
```

## 💡 面试要点总结

### 容错设计原则
1. **预防优于治疗**：设计阶段考虑容错
2. **快速失败**：尽早发现并处理故障
3. **优雅降级**：保证核心功能可用
4. **隔离故障**：避免故障传播扩散

### 常见容错模式
- **重试模式**：处理临时性故障
- **熔断器模式**：防止故障扩散
- **舱壁模式**：隔离不同功能模块
- **超时模式**：避免资源长时间占用

### 恢复策略选择
- **主动恢复**：系统自动检测和恢复
- **被动恢复**：依赖外部干预恢复
- **预防性维护**：定期检查和更新
- **应急预案**：制定详细的故障处理流程

### 监控指标体系
- **业务指标**：订单成功率、用户活跃度
- **技术指标**：响应时间、错误率、吞吐量
- **基础指标**：CPU、内存、网络、存储
- **自定义指标**：业务特有的关键指标

### 常见误区
❌ **过度设计**：为不常见故障设计复杂方案
❌ **忽视人为因素**：只考虑技术故障，忽略操作失误
❌ **缺乏演练**：容灾方案缺乏实际验证
❌ **单点依赖**：在容错系统中引入新的单点故障

## 🔗 相关链接

- [← 返回系统设计主页](./README.md)
- [分布式系统](./distributed-systems.md)
- [负载均衡](./load-balancing.md)
- [监控与可观测性](./monitoring-observability.md)

---

*容错是分布式系统的基本要求，需要在设计、开发、测试各个阶段都要考虑* ⚡ 