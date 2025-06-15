# 设计短链接服务

## 🎯 题目描述

设计一个类似 bit.ly 或 TinyURL 的短链接服务，能够将长URL转换为短URL，并支持重定向功能。

## 📋 需求分析

### 功能需求
1. **URL缩短**：将长URL转换为短URL
2. **URL重定向**：通过短URL跳转到原始长URL  
3. **自定义短链**：用户可以自定义短链接后缀
4. **链接过期**：支持设置链接过期时间
5. **访问统计**：统计短链接的访问次数

### 非功能需求
1. **高可用性**：99.9%以上的可用性
2. **低延迟**：URL重定向延迟<100ms
3. **高并发**：支持10万QPS的读取操作
4. **存储容量**：支持1000万条URL映射

## 📊 容量估算

### 流量估算
- **写入QPS**：1000 QPS（URL缩短）
- **读取QPS**：100,000 QPS（URL重定向）
- **读写比例**：100:1

### 存储估算
```mermaid
graph LR
    A[存储需求] --> B[URL映射]
    A --> C[访问统计]
    A --> D[用户数据]
    
    B --> B1[1000万条记录]
    B --> B2[平均500字节/条]
    B --> B3[5GB基础数据]
    
    C --> C1[访问日志]
    C --> C2[统计数据]
    C --> C3[预估10GB/年]
    
    D --> D1[用户信息]
    D --> D2[预估1GB]
```

**总存储需求**：约15GB（基础数据 + 统计数据 + 冗余）

## 🏗️ 高层设计

```mermaid
graph TB
    Client[客户端] --> LB[负载均衡器]
    LB --> App1[应用服务器1]
    LB --> App2[应用服务器2]
    LB --> App3[应用服务器3]
    
    App1 --> Cache[Redis缓存]
    App2 --> Cache
    App3 --> Cache
    
    App1 --> DB[(主数据库)]
    App2 --> DB
    App3 --> DB
    
    DB --> Slave1[(从数据库1)]
    DB --> Slave2[(从数据库2)]
    
    App1 --> Analytics[分析服务]
    App2 --> Analytics
    App3 --> Analytics
    
    Analytics --> TSDB[(时序数据库)]
```

## 🔧 详细设计

### 短链接生成算法

#### 方案1：Base62编码 + 计数器
```mermaid
flowchart TD
    A[接收长URL] --> B[获取全局计数器]
    B --> C[计数器+1]
    C --> D[Base62编码]
    D --> E[生成短链接]
    E --> F[存储映射关系]
    
    G[Base62字符集] --> G1[0-9: 10个]
    G --> G2[a-z: 26个]
    G --> G3[A-Z: 26个]
    G --> G4[总计: 62个字符]
```

**优点**：简单、不重复、可预测长度
**缺点**：需要维护全局计数器、可能暴露系统规模

#### 方案2：哈希算法 + 冲突处理
```mermaid
flowchart TD
    A[接收长URL] --> B[MD5哈希]
    B --> C[取前7位]
    C --> D{检查冲突}
    D -->|无冲突| E[存储映射]
    D -->|有冲突| F[添加盐值重新哈希]
    F --> C
    E --> G[返回短链接]
```

**优点**：无需全局状态、可分布式生成
**缺点**：可能存在哈希冲突、长度不固定

### 数据库设计

```mermaid
erDiagram
    URL_MAPPING {
        string short_url PK
        text long_url
        string user_id FK
        datetime created_at
        datetime expires_at
        boolean is_active
    }
    
    USER {
        string user_id PK
        string username
        string email
        datetime created_at
    }
    
    ACCESS_LOG {
        bigint id PK
        string short_url FK
        string user_agent
        string ip_address
        datetime access_time
    }
    
    URL_MAPPING ||--o{ ACCESS_LOG : "has"
    USER ||--o{ URL_MAPPING : "creates"
```

### 缓存策略

```mermaid
sequenceDiagram
    participant Client
    participant App
    participant Cache
    participant DB
    
    Client->>App: 请求短链接重定向
    App->>Cache: 查询缓存
    
    alt 缓存命中
        Cache->>App: 返回长URL
        App->>Client: 302重定向
    else 缓存未命中
        App->>DB: 查询数据库
        DB->>App: 返回长URL
        App->>Cache: 更新缓存
        App->>Client: 302重定向
    end
```

**缓存策略**：
- **热点数据**：LRU策略，保留最近访问的链接
- **过期策略**：TTL设置为1小时
- **缓存更新**：写回策略，更新时同时更新缓存和数据库

## ⚡ 性能优化

### 数据库优化
1. **读写分离**：写入主库，读取从库
2. **分库分表**：按short_url哈希分片
3. **索引优化**：short_url主键索引，user_id二级索引

### 应用层优化
```mermaid
graph TD
    A[性能优化策略] --> B[应用层]
    A --> C[缓存层]
    A --> D[数据库层]
    
    B --> B1[连接池]
    B --> B2[异步处理]
    B --> B3[批量操作]
    
    C --> C1[多级缓存]
    C --> C2[CDN加速]
    C --> C3[预热策略]
    
    D --> D1[读写分离]
    D --> D2[分库分表]
    D --> D3[索引优化]
```

## 🛡️ 安全考虑

### 防滥用机制
1. **限流**：用户级别和IP级别的请求限制
2. **黑名单**：过滤恶意URL和垃圾内容
3. **URL验证**：检查URL格式和可达性

### 安全措施
```mermaid
graph LR
    A[安全措施] --> B[认证授权]
    A --> C[内容过滤]
    A --> D[访问控制]
    
    B --> B1[用户认证]
    B --> B2[API密钥]
    
    C --> C1[恶意URL检测]
    C --> C2[内容审核]
    
    D --> D1[IP白名单]
    D --> D2[地域限制]
```

## 📈 扩展讨论

### 监控指标
- **业务指标**：URL创建速率、访问成功率、热门链接
- **系统指标**：响应时间、QPS、错误率、缓存命中率
- **基础设施**：CPU使用率、内存使用率、磁盘IO

### 故障处理
```mermaid
graph TD
    A[故障类型] --> B[服务器故障]
    A --> C[数据库故障]
    A --> D[缓存故障]
    
    B --> B1[自动故障转移]
    B --> B2[负载均衡重路由]
    
    C --> C1[主从切换]
    C --> C2[读写分离降级]
    
    D --> D1[缓存预热]
    D --> D2[降级到数据库]
```

### 国际化支持
- **多地域部署**：就近访问降低延迟
- **数据同步**：跨地域数据一致性
- **CDN分发**：静态资源全球加速

## 💡 面试要点

### 关键设计决策
1. **为什么选择Base62编码？**
   - 包含数字和大小写字母，URL友好
   - 相比Base64少了+/字符，避免URL编码问题
   
2. **如何处理热点数据？**
   - 多级缓存：本地缓存 + Redis集群
   - 异步预热：提前加载热门链接到缓存

3. **数据一致性如何保证？**
   - 强一致性：同步写入主数据库
   - 最终一致性：异步同步到从数据库和缓存

### 权衡取舍
- **存储 vs 计算**：预计算 vs 实时计算访问统计
- **一致性 vs 可用性**：CAP理论的权衡选择
- **成本 vs 性能**：缓存大小和命中率的平衡

## 🔗 相关链接

- [← 返回系统设计主页](./README.md)
- [数据库设计](./database-design.md)
- [缓存系统](./caching-systems.md)
- [负载均衡](./load-balancing.md)

---

*短链接服务是学习系统设计的经典案例，涵盖了分布式系统的多个核心概念* 🔗 