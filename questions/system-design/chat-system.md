# 设计聊天系统

## 🎯 题目描述

设计一个类似WhatsApp、微信或Slack的实时聊天系统，支持一对一聊天、群聊、文件传输和在线状态显示。

## 📋 需求分析

### 功能需求
1. **实时消息**：支持文本、图片、文件等多种消息类型
2. **一对一聊天**：用户间私人对话
3. **群组聊天**：多人群聊功能
4. **在线状态**：显示用户在线/离线状态
5. **消息历史**：持久化存储聊天记录
6. **消息推送**：离线消息推送通知
7. **已读回执**：消息已读状态显示

### 非功能需求
1. **实时性**：消息延迟<200ms
2. **高可用性**：99.9%系统可用性
3. **大规模**：支持1000万日活用户
4. **数据一致性**：消息顺序和完整性保证

## 📊 容量估算

### 用户规模估算
```mermaid
graph TD
    A[用户规模] --> B[总用户: 1亿]
    A --> C[日活用户: 1000万]
    A --> D[同时在线: 500万]
    
    B --> B1[平均好友数: 100]
    C --> C1[日均消息: 50条]
    D --> D1[峰值消息: 10万QPS]
```

### 存储估算
- **日消息量**：1000万用户 × 50条 = 5亿条消息
- **消息大小**：平均100字节/条
- **日存储增长**：5亿 × 100字节 = 50GB
- **年存储需求**：50GB × 365 = 18TB

## 🏗️ 系统架构设计

```mermaid
graph TB
    subgraph "客户端层"
        iOS[iOS App]
        Android[Android App]
        Web[Web App]
    end
    
    subgraph "网关层"
        LB[负载均衡器]
        Gateway[API网关]
    end
    
    subgraph "服务层"
        Auth[认证服务]
        Chat[聊天服务]
        User[用户服务]
        Group[群组服务]
        Notification[通知服务]
    end
    
    subgraph "消息层"
        MessageQueue[消息队列]
        WebSocket[WebSocket服务]
    end
    
    subgraph "存储层"
        UserDB[(用户数据库)]
        MessageDB[(消息数据库)]
        Redis[(Redis缓存)]
    end
    
    iOS --> LB
    Android --> LB
    Web --> LB
    
    LB --> Gateway
    Gateway --> Auth
    Gateway --> Chat
    Gateway --> User
    Gateway --> Group
    
    Chat --> MessageQueue
    Chat --> WebSocket
    Chat --> Redis
    
    MessageQueue --> Notification
    
    Auth --> UserDB
    User --> UserDB
    Chat --> MessageDB
    Group --> UserDB
```

## 🔧 核心组件设计

### 实时通信架构

```mermaid
sequenceDiagram
    participant A as 用户A
    participant WS1 as WebSocket服务1
    participant MQ as 消息队列
    participant WS2 as WebSocket服务2
    participant B as 用户B
    participant DB as 消息数据库
    
    A->>WS1: 发送消息
    WS1->>DB: 存储消息
    WS1->>MQ: 发布消息事件
    
    alt 用户B在线
        MQ->>WS2: 路由消息
        WS2->>B: 实时推送消息
        B->>WS2: 发送已读回执
        WS2->>MQ: 发布已读事件
        MQ->>WS1: 路由已读回执
        WS1->>A: 推送已读状态
    else 用户B离线
        MQ->>Notification: 离线推送
    end
```

### 消息存储设计

```mermaid
erDiagram
    USER {
        string user_id PK
        string username
        string phone
        datetime last_seen
        enum status
    }
    
    CONVERSATION {
        string conversation_id PK
        enum type
        datetime created_at
        datetime updated_at
    }
    
    MESSAGE {
        string message_id PK
        string conversation_id FK
        string sender_id FK
        text content
        enum message_type
        datetime sent_at
        boolean is_deleted
    }
    
    PARTICIPANT {
        string conversation_id FK
        string user_id FK
        datetime joined_at
        datetime last_read_at
    }
    
    USER ||--o{ MESSAGE : "sends"
    CONVERSATION ||--o{ MESSAGE : "contains"
    CONVERSATION ||--o{ PARTICIPANT : "has"
    USER ||--o{ PARTICIPANT : "participates"
```

### 在线状态管理

```mermaid
graph TD
    A[在线状态管理] --> B[心跳机制]
    A --> C[状态缓存]
    A --> D[状态同步]
    
    B --> B1[客户端定时发送心跳]
    B --> B2[服务端检测心跳超时]
    B --> B3[更新最后活跃时间]
    
    C --> C1[Redis存储在线用户]
    C --> C2[用户状态TTL过期]
    C --> C3[实时状态查询]
    
    D --> D1[状态变更事件]
    D --> D2[好友状态推送]
    D --> D3[群组成员状态更新]
```

## ⚡ 性能优化

### 消息分片策略

```mermaid
graph LR
    A[消息分片] --> B[按对话ID分片]
    A --> C[按时间分片]
    A --> D[按用户分片]
    
    B --> B1[保证对话消息在同一分片]
    B --> B2[便于消息顺序查询]
    
    C --> C1[按月/年分表存储]
    C --> C2[历史数据归档]
    
    D --> D1[用户相关数据就近存储]
    D --> D2[减少跨分片查询]
```

### 缓存策略

| 缓存类型 | 存储内容 | TTL | 更新策略 |
|---------|----------|-----|----------|
| 用户在线状态 | user_id -> status | 5分钟 | 心跳更新 |
| 最近消息 | conversation_id -> messages | 1小时 | 写入时更新 |
| 用户会话列表 | user_id -> conversations | 30分钟 | 懒加载更新 |
| 群组成员信息 | group_id -> members | 1天 | 成员变更时更新 |

## 🔒 数据一致性保证

### 消息顺序保证

```mermaid
flowchart TD
    A[消息顺序保证] --> B[单对话顺序]
    A --> C[全局顺序]
    
    B --> B1[使用对话级锁]
    B --> B2[时间戳 + 序列号]
    B --> B3[单线程处理同一对话]
    
    C --> C1[分布式ID生成]
    C --> C2[Lamport时间戳]
    C --> C3[向量时钟]
```

### 消息可靠性传输

```mermaid
stateDiagram-v2
    [*] --> Sending: 发送消息
    Sending --> Sent: 服务端接收
    Sent --> Delivered: 对方设备接收
    Delivered --> Read: 对方已读
    
    Sending --> Failed: 发送失败
    Failed --> Sending: 重试发送
    
    Sent --> Sending: 超时重发
```

## 📱 移动端优化

### 消息同步策略
```mermaid
sequenceDiagram
    participant App
    participant Server
    participant DB
    
    Note over App: 应用启动/恢复前台
    App->>Server: 请求增量同步
    Server->>DB: 查询未同步消息
    DB->>Server: 返回消息列表
    
    alt 消息量较少(<100条)
        Server->>App: 返回完整消息
    else 消息量较多
        Server->>App: 返回消息摘要
        App->>Server: 分页拉取详细消息
    end
    
    App->>Server: 确认同步完成
```

### 离线消息处理
- **消息队列**：为每个用户维护离线消息队列
- **优先级排序**：重要消息优先推送
- **批量推送**：合并多条消息减少推送次数
- **推送策略**：根据用户习惯调整推送时间

## 🌐 多端同步

```mermaid
graph TD
    A[多端同步] --> B[消息状态同步]
    A --> C[设备管理]
    A --> D[冲突解决]
    
    B --> B1[已读状态同步]
    B --> B2[消息删除同步]
    B --> B3[会话状态同步]
    
    C --> C1[设备注册管理]
    C --> C2[活跃设备检测]
    C --> C3[推送路由选择]
    
    D --> D1[时间戳比较]
    D --> D2[操作优先级]
    D --> D3[最终一致性]
```

## 🛡️ 安全考虑

### 消息加密
```mermaid
graph LR
    A[消息安全] --> B[传输加密]
    A --> C[存储加密]
    A --> D[端到端加密]
    
    B --> B1[TLS/SSL]
    B --> B2[WebSocket Secure]
    
    C --> C1[数据库字段加密]
    C --> C2[文件存储加密]
    
    D --> D1[客户端密钥生成]
    D --> D2[密钥交换协议]
    D --> D3[消息加解密]
```

### 防滥用机制
- **频率限制**：每用户每分钟消息数限制
- **内容过滤**：敏感词汇和垃圾信息检测
- **举报机制**：用户举报和管理员审核
- **黑名单**：恶意用户拉黑功能

## 📈 监控告警

### 关键指标
```mermaid
graph TD
    A[监控指标] --> B[业务指标]
    A --> C[技术指标]
    A --> D[用户体验]
    
    B --> B1[消息发送成功率]
    B --> B2[平均消息延迟]
    B --> B3[用户活跃度]
    
    C --> C1[WebSocket连接数]
    C --> C2[消息队列长度]
    C --> C3[数据库QPS]
    
    D --> D1[消息到达率]
    D --> D2[推送成功率]
    D --> D3[应用崩溃率]
```

## 💡 面试关键点

### 设计难点讨论
1. **消息顺序性**：
   - 单对话内的消息顺序如何保证？
   - 跨设备消息同步的一致性问题

2. **实时性保证**：
   - 如何选择WebSocket vs HTTP长轮询？
   - 连接断开后的消息如何处理？

3. **扩展性设计**：
   - 如何支持百万级并发连接？
   - 消息存储的分片策略

### 权衡取舍
- **一致性 vs 可用性**：消息顺序 vs 系统可用性
- **存储成本 vs 查询性能**：消息归档 vs 实时查询
- **功能完整性 vs 系统复杂度**：丰富功能 vs 系统维护成本

## 🔗 相关链接

- [← 返回系统设计主页](./README.md)
- [消息队列](./message-queues.md)
- [实时通信技术](./real-time-communication.md)
- [分布式系统](./distributed-systems.md)

---

*聊天系统设计涵盖了实时通信、数据一致性、性能优化等系统设计的核心要素* 💬 