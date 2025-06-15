# 数据库设计

## 🎯 核心知识点

- SQL vs NoSQL 选择
- 数据建模与范式设计
- 数据库分片策略
- 主从复制与读写分离
- 数据一致性保证
- 索引设计与优化

## 📊 数据库类型选择框架

```mermaid
graph TD
    A[数据库选择] --> B[关系型数据库]
    A --> C[文档数据库]
    A --> D[键值数据库]
    A --> E[图数据库]
    A --> F[列式数据库]
    
    B --> B1[MySQL, PostgreSQL]
    B --> B2[ACID事务]
    B --> B3[复杂查询]
    
    C --> C1[MongoDB, CouchDB]
    C --> C2[灵活模式]
    C --> C3[嵌套数据]
    
    D --> D1[Redis, DynamoDB]
    D --> D2[高性能访问]
    D --> D3[简单数据结构]
    
    E --> E1[Neo4j, ArangoDB]
    E --> E2[关系图谱]
    E --> E3[复杂关联查询]
    
    F --> F1[Cassandra, HBase]
    F --> F2[大数据分析]
    F --> F3[时序数据]
```

## 💡 面试题目

### **初级** SQL vs NoSQL 选择标准
**题目：** 针对不同的应用场景，如何选择合适的数据库类型？请给出选择标准和理由。

**答案要点：**

```mermaid
graph LR
    A[选择标准] --> B[数据结构]
    A --> C[一致性需求]
    A --> D[扩展性要求]
    A --> E[查询复杂度]
    
    B --> B1[结构化 → SQL]
    B --> B2[半结构化 → Document]
    B --> B3[简单KV → NoSQL]
    
    C --> C1[强一致性 → SQL]
    C --> C2[最终一致性 → NoSQL]
    
    D --> D1[垂直扩展 → SQL]
    D --> D2[水平扩展 → NoSQL]
    
    E --> E1[复杂查询 → SQL]
    E --> E2[简单查询 → NoSQL]
```

**典型应用场景：**

| 场景 | 推荐方案 | 理由 |
|------|----------|------|
| 电商订单系统 | MySQL + Redis | 事务保证 + 缓存性能 |
| 内容管理系统 | MongoDB | 灵活的文档结构 |
| 实时推荐系统 | Redis + Elasticsearch | 高性能读取 + 搜索 |
| 社交网络关系 | Neo4j + MySQL | 图查询 + 基础数据 |
| 日志分析系统 | ClickHouse + Kafka | 列式存储 + 流处理 |

### **中级** 数据库分片设计
**题目：** 设计一个支持千万级用户的社交平台数据库分片方案，考虑用户数据、关系数据和内容数据的分片策略。

**答案要点：**

```mermaid
graph TB
    subgraph "应用层"
        A[应用服务] --> B[分片路由层]
    end
    
    subgraph "用户数据分片"
        B --> C[用户分片1<br/>user_id % 4 = 0]
        B --> D[用户分片2<br/>user_id % 4 = 1]
        B --> E[用户分片3<br/>user_id % 4 = 2]
        B --> F[用户分片4<br/>user_id % 4 = 3]
    end
    
    subgraph "内容数据分片"
        B --> G[内容分片1<br/>按时间+用户ID]
        B --> H[内容分片2<br/>按时间+用户ID]
        B --> I[内容分片3<br/>按时间+用户ID]
    end
    
    subgraph "关系数据"
        B --> J[关系图数据库<br/>Neo4j集群]
    end
```

**分片策略选择：**

1. **水平分片（Horizontal）**
   - 按用户ID哈希分片
   - 按时间范围分片
   - 按地理位置分片

2. **垂直分片（Vertical）**
   - 用户基础信息单独存储
   - 用户动态内容单独存储
   - 关系数据单独存储

3. **跨分片查询解决方案**
   ```mermaid
   sequenceDiagram
       participant App as 应用层
       participant Router as 路由层
       participant Shard1 as 分片1
       participant Shard2 as 分片2
       participant Aggregator as 聚合层
       
       App->>Router: 跨分片查询请求
       Router->>Shard1: 子查询1
       Router->>Shard2: 子查询2
       Shard1->>Aggregator: 返回结果1
       Shard2->>Aggregator: 返回结果2
       Aggregator->>App: 合并返回结果
   ```

### **高级** 数据一致性架构设计
**题目：** 在分布式环境下，如何设计一个既保证数据一致性又支持高可用性的数据库架构？

**答案要点：**

```mermaid
graph TB
    subgraph "强一致性层"
        A[主数据库] --> B[同步复制]
        B --> C[从数据库1]
        B --> D[从数据库2]
    end
    
    subgraph "最终一致性层"
        E[事件总线] --> F[异步复制]
        F --> G[缓存层]
        F --> H[搜索引擎]
        F --> I[数据仓库]
    end
    
    A --> E
    
    subgraph "一致性保证机制"
        J[两阶段提交]
        K[Saga模式]
        L[事件溯源]
    end
```

**一致性级别选择：**

```mermaid
graph LR
    A[一致性需求] --> B[强一致性]
    A --> C[最终一致性]
    A --> D[会话一致性]
    
    B --> B1[金融交易]
    B --> B2[库存管理]
    
    C --> C1[用户资料]
    C --> C2[内容推荐]
    
    D --> D1[用户会话]
    D --> D2[购物车状态]
```

## 🔧 数据建模最佳实践

### 关系型数据库设计

```mermaid
erDiagram
    USER {
        bigint user_id PK
        varchar username UK
        varchar email UK
        varchar password_hash
        timestamp created_at
        timestamp updated_at
        enum status
    }
    
    POST {
        bigint post_id PK
        bigint user_id FK
        text content
        varchar media_urls
        int like_count
        int comment_count
        timestamp created_at
        boolean is_deleted
    }
    
    FOLLOW {
        bigint follower_id FK
        bigint following_id FK
        timestamp created_at
        enum status
    }
    
    COMMENT {
        bigint comment_id PK
        bigint post_id FK
        bigint user_id FK
        bigint parent_comment_id FK
        text content
        timestamp created_at
    }
    
    USER ||--o{ POST : "creates"
    USER ||--o{ FOLLOW : "follows"
    USER ||--o{ COMMENT : "writes"
    POST ||--o{ COMMENT : "has"
```

### NoSQL文档设计

```json
// 用户文档 (MongoDB)
{
  "_id": ObjectId("..."),
  "username": "john_doe",
  "email": "john@example.com",
  "profile": {
    "avatar": "https://...",
    "bio": "Software Developer",
    "location": "San Francisco"
  },
  "stats": {
    "followers": 1250,
    "following": 300,
    "posts": 45
  },
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}

// 嵌入式评论设计
{
  "_id": ObjectId("..."),
  "content": "Post content...",
  "user_id": ObjectId("..."),
  "comments": [
    {
      "comment_id": ObjectId("..."),
      "user_id": ObjectId("..."),
      "content": "Comment content...",
      "created_at": ISODate("..."),
      "replies": [
        {
          "reply_id": ObjectId("..."),
          "user_id": ObjectId("..."),
          "content": "Reply content...",
          "created_at": ISODate("...")
        }
      ]
    }
  ]
}
```

## ⚡ 性能优化策略

### 索引设计原则

```mermaid
graph TD
    A[索引设计] --> B[查询模式分析]
    A --> C[复合索引]
    A --> D[覆盖索引]
    A --> E[部分索引]
    
    B --> B1[WHERE条件]
    B --> B2[ORDER BY字段]
    B --> B3[JOIN关联字段]
    
    C --> C1[最左前缀原则]
    C --> C2[区分度高的字段优先]
    
    D --> D1[减少回表查询]
    D --> D2[包含所需字段]
    
    E --> E1[条件过滤]
    E --> E2[减少索引大小]
```

### 读写分离架构

```mermaid
sequenceDiagram
    participant App as 应用层
    participant Proxy as 读写分离代理
    participant Master as 主数据库
    participant Slave1 as 从数据库1
    participant Slave2 as 从数据库2
    
    App->>Proxy: 写入请求
    Proxy->>Master: 路由到主库
    Master->>Proxy: 写入成功
    Proxy->>App: 返回结果
    
    Master->>Slave1: 异步复制
    Master->>Slave2: 异步复制
    
    App->>Proxy: 读取请求
    Proxy->>Slave1: 路由到从库
    Slave1->>Proxy: 返回数据
    Proxy->>App: 返回结果
```

## 🔒 数据安全与备份

### 数据加密策略

```mermaid
graph TD
    A[数据安全] --> B[传输加密]
    A --> C[存储加密]
    A --> D[应用层加密]
    
    B --> B1[TLS/SSL]
    B --> B2[VPN隧道]
    
    C --> C1[透明数据加密]
    C --> C2[字段级加密]
    
    D --> D1[敏感字段加密]
    D --> D2[密钥管理]
```

### 备份恢复策略

| 备份类型 | 频率 | 恢复时间 | 存储成本 | 适用场景 |
|----------|------|----------|----------|----------|
| 全量备份 | 每周 | 较长 | 高 | 完整数据恢复 |
| 增量备份 | 每日 | 中等 | 中 | 日常数据保护 |
| 差异备份 | 实时 | 较短 | 中 | 快速恢复 |
| 日志备份 | 实时 | 最短 | 低 | 点时间恢复 |

## 📈 监控与优化

### 数据库性能指标

```mermaid
graph TD
    A[性能监控] --> B[查询性能]
    A --> C[系统资源]
    A --> D[复制延迟]
    A --> E[连接状态]
    
    B --> B1[慢查询日志]
    B --> B2[查询执行计划]
    B --> B3[索引使用率]
    
    C --> C1[CPU使用率]
    C --> C2[内存使用率]
    C --> C3[磁盘IO]
    
    D --> D1[主从延迟]
    D --> D2[复制错误]
    
    E --> E1[连接池状态]
    E --> E2[活跃连接数]
```

### 容量规划

```mermaid
flowchart TD
    A[容量规划] --> B[数据增长预测]
    A --> C[性能需求分析]
    A --> D[硬件资源规划]
    
    B --> B1[历史数据分析]
    B --> B2[业务增长预期]
    
    C --> C1[QPS峰值]
    C --> C2[响应时间要求]
    
    D --> D1[存储容量]
    D --> D2[计算资源]
    D --> D3[网络带宽]
```

## 💡 面试要点总结

### 设计决策考虑因素
1. **数据特征**：结构化程度、数据量大小、增长速度
2. **访问模式**：读写比例、查询复杂度、一致性要求
3. **性能要求**：延迟要求、吞吐量需求、可用性目标
4. **技术约束**：团队技能、运维能力、成本预算

### 常见权衡取舍
- **一致性 vs 可用性**：CAP理论的权衡选择
- **性能 vs 灵活性**：专用数据库 vs 通用数据库
- **成本 vs 性能**：存储成本 vs 查询性能
- **复杂性 vs 可维护性**：功能丰富 vs 系统简单

## 🔗 相关链接

- [← 返回系统设计主页](./README.md)
- [缓存系统](./caching-systems.md)
- [分布式系统](./distributed-systems.md)
- [数据处理](./data-processing.md)

---

*数据库设计是系统架构的核心，需要在多个维度间找到最佳平衡点* 🗄️ 