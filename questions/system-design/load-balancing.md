# 负载均衡

## 🎯 核心知识点

- 负载均衡算法
- 硬件负载均衡 vs 软件负载均衡
- 四层负载均衡 vs 七层负载均衡
- 健康检查机制
- 会话保持策略

## 📊 负载均衡架构层次

```mermaid
graph TD
    A[负载均衡层次] --> B[DNS负载均衡]
    A --> C[硬件负载均衡]
    A --> D[软件负载均衡]
    A --> E[应用层负载均衡]
    
    B --> B1[地理位置路由]
    B --> B2[权重分配]
    B --> B3[故障转移]
    
    C --> C1[F5 BIG-IP]
    C --> C2[Citrix NetScaler]
    C --> C3[硬件专用芯片]
    
    D --> D1[Nginx]
    D --> D2[HAProxy]
    D --> D3[LVS]
    
    E --> E1[微服务网关]
    E --> E2[API网关]
    E --> E3[服务发现]
```

## 💡 面试题目

### **初级** 负载均衡算法对比
**题目：** 介绍常见的负载均衡算法，并分析各自的优缺点和适用场景。

**答案要点：**

```mermaid
graph LR
    A[负载均衡算法] --> B[轮询Round Robin]
    A --> C[加权轮询]
    A --> D[最少连接]
    A --> E[IP哈希]
    A --> F[最短响应时间]
    
    B --> B1[优点: 简单公平]
    B --> B2[缺点: 不考虑服务器性能]
    
    C --> C1[优点: 考虑服务器配置差异]
    C --> C2[缺点: 静态权重调整]
    
    D --> D1[优点: 动态负载均衡]
    D --> D2[缺点: 需要维护连接状态]
    
    E --> E1[优点: 会话保持]
    E --> E2[缺点: 可能负载不均]
    
    F --> F1[优点: 性能导向]
    F --> F2[缺点: 实现复杂]
```

**适用场景分析：**
- **轮询**：无状态服务、服务器配置相同
- **加权轮询**：服务器配置不同、需要差异化分配
- **最少连接**：长连接场景、连接持续时间不确定
- **IP哈希**：需要会话保持、状态化应用
- **最短响应时间**：对延迟敏感的应用

### **中级** 四层 vs 七层负载均衡
**题目：** 设计一个电商系统的负载均衡架构，说明何时使用四层负载均衡，何时使用七层负载均衡？

**答案要点：**

```mermaid
graph TB
    subgraph "七层负载均衡(应用层)"
        A[用户请求] --> B[Nginx/HAProxy]
        B --> C{URL路由}
        C --> D[静态资源服务器]
        C --> E[商品服务API]
        C --> F[用户服务API]
        C --> G[订单服务API]
    end
    
    subgraph "四层负载均衡(传输层)"
        H[数据库连接池] --> I[LVS/F5]
        I --> J[主数据库]
        I --> K[从数据库1]
        I --> L[从数据库2]
    end
    
    E --> H
    F --> H
    G --> H
```

**使用场景对比：**

| 维度 | 四层负载均衡 | 七层负载均衡 |
|------|-------------|-------------|
| 工作层次 | 传输层(TCP/UDP) | 应用层(HTTP/HTTPS) |
| 路由依据 | IP + 端口 | URL、Header、Cookie |
| 性能 | 高性能，低延迟 | 相对较慢，功能丰富 |
| 会话保持 | IP哈希 | Cookie、Session |
| SSL卸载 | 不支持 | 支持 |
| 内容缓存 | 不支持 | 支持 |

### **高级** 全局负载均衡设计
**题目：** 设计一个支持多地域部署的全球化应用的负载均衡方案，考虑延迟、容灾和成本优化。

**答案要点：**

```mermaid
graph TB
    A[全球用户] --> B[智能DNS]
    B --> C[北美CDN]
    B --> D[欧洲CDN]
    B --> E[亚洲CDN]
    
    C --> F[美西数据中心]
    C --> G[美东数据中心]
    
    D --> H[伦敦数据中心]
    D --> I[法兰克福数据中心]
    
    E --> J[东京数据中心]
    E --> K[新加坡数据中心]
    
    subgraph "数据中心内部"
        L[入口负载均衡] --> M[应用服务集群]
        M --> N[数据库集群]
        M --> O[缓存集群]
    end
```

**设计要点：**
1. **DNS智能解析**：基于地理位置和网络状况路由
2. **CDN分发**：静态资源就近缓存
3. **数据中心选择**：延迟、成本、合规性考虑
4. **故障转移**：自动检测和流量切换
5. **数据同步**：跨地域数据一致性保证

## 🔧 负载均衡器配置示例

### Nginx配置示例
```nginx
upstream backend {
    # 加权轮询
    server 192.168.1.10:8080 weight=3;
    server 192.168.1.11:8080 weight=2;
    server 192.168.1.12:8080 weight=1;
    
    # 健康检查
    server 192.168.1.13:8080 backup;
    
    # 会话保持
    ip_hash;
}

server {
    listen 80;
    location / {
        proxy_pass http://backend;
        
        # 健康检查配置
        proxy_connect_timeout 3s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
        
        # 重试机制
        proxy_next_upstream error timeout;
        proxy_next_upstream_tries 3;
    }
}
```

### HAProxy配置示例
```haproxy
backend webservers
    balance roundrobin
    option httpchk GET /health
    
    server web1 192.168.1.10:8080 check weight 3
    server web2 192.168.1.11:8080 check weight 2
    server web3 192.168.1.12:8080 check weight 1 backup
    
    # 会话保持
    cookie SERVERID insert indirect nocache
```

## ⚡ 性能优化策略

### 连接优化

```mermaid
graph TD
    A[连接优化] --> B[连接池]
    A --> C[长连接]
    A --> D[连接复用]
    
    B --> B1[预建立连接]
    B --> B2[连接数限制]
    B --> B3[空闲连接回收]
    
    C --> C1[Keep-Alive]
    C --> C2[HTTP/2多路复用]
    C --> C3[WebSocket持久连接]
    
    D --> D1[同一连接多请求]
    D --> D2[减少握手开销]
    D --> D3[提高吞吐量]
```

### 缓存策略

| 缓存类型 | 位置 | 缓存内容 | 优势 |
|---------|------|----------|------|
| 浏览器缓存 | 客户端 | 静态资源 | 减少网络传输 |
| CDN缓存 | 边缘节点 | 静态内容 | 就近访问 |
| 负载均衡器缓存 | LB层 | 热点数据 | 减少后端压力 |
| 应用缓存 | 应用服务器 | 计算结果 | 提高响应速度 |

## 🛡️ 高可用保障

### 健康检查机制

```mermaid
sequenceDiagram
    participant LB as 负载均衡器
    participant S1 as 服务器1
    participant S2 as 服务器2
    participant S3 as 服务器3
    
    LB->>S1: 健康检查请求
    S1->>LB: 响应正常
    
    LB->>S2: 健康检查请求
    S2-->>LB: 超时/异常
    Note over LB: 标记S2为不可用
    
    LB->>S3: 健康检查请求
    S3->>LB: 响应正常
    
    Note over LB: 只向S1和S3转发请求
    
    loop 定期检查
        LB->>S2: 健康检查请求
        S2->>LB: 恢复正常
        Note over LB: 恢复S2服务
    end
```

### 故障转移策略
```mermaid
stateDiagram-v2
    [*] --> Normal: 所有服务器正常
    Normal --> Degraded: 部分服务器故障
    Degraded --> Critical: 大量服务器故障
    Critical --> Emergency: 紧急降级模式
    
    Degraded --> Normal: 服务器恢复
    Critical --> Degraded: 部分服务器恢复
    Emergency --> Critical: 服务逐步恢复
```

## 📈 监控指标

### 关键性能指标
```mermaid
graph TD
    A[负载均衡监控] --> B[请求指标]
    A --> C[响应指标]
    A --> D[健康状态]
    A --> E[资源使用]
    
    B --> B1[QPS/TPS]
    B --> B2[并发连接数]
    B --> B3[请求分布]
    
    C --> C1[响应时间]
    C --> C2[错误率]
    C --> C3[成功率]
    
    D --> D1[服务器状态]
    D --> D2[健康检查结果]
    D --> D3[故障转移次数]
    
    E --> E1[CPU使用率]
    E --> E2[内存使用率]
    E --> E3[网络带宽]
```

## 🔍 故障排查

### 常见问题诊断
```mermaid
flowchart TD
    A[负载均衡问题] --> B{请求分布不均}
    A --> C{响应时间过长}
    A --> D{服务不可用}
    
    B --> B1[检查算法配置]
    B --> B2[检查权重设置]
    B --> B3[检查会话保持]
    
    C --> C1[检查健康检查配置]
    C --> C2[检查网络延迟]
    C --> C3[检查后端服务性能]
    
    D --> D1[检查服务器状态]
    D --> D2[检查防火墙规则]
    D --> D3[检查DNS解析]
```

## 💡 面试要点总结

### 设计考虑因素
1. **业务需求**：流量模式、会话要求、地域分布
2. **技术约束**：现有架构、性能要求、成本预算
3. **可用性要求**：SLA目标、故障恢复时间
4. **扩展性规划**：未来流量增长、功能扩展

### 权衡取舍
- **性能 vs 功能**：四层负载均衡 vs 七层负载均衡
- **成本 vs 可靠性**：硬件设备 vs 软件方案
- **简单性 vs 灵活性**：静态配置 vs 动态调整
- **一致性 vs 可用性**：会话保持 vs 负载分布

## 🔗 相关链接

- [← 返回系统设计主页](./README.md)
- [系统设计基础](./system-design-fundamentals.md)
- [高可用架构](./high-availability.md)
- [性能优化](./performance-optimization.md)

---

*负载均衡是系统扩展性和可用性的基础保障* ⚖️ 