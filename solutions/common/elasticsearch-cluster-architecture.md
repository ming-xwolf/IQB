# Elasticsearch集群架构设计完整实现

## 🎯 解决方案概述

深入分析Elasticsearch集群的架构设计和实现方案，通过完整的配置和代码展示大规模搜索系统的构建方法。

## 💡 核心问题分析

### 大规模搜索系统的技术挑战
**业务背景**：构建支持PB级数据和亿级用户的搜索服务
**技术难点**：
- 集群节点角色的合理分工和配置优化
- 分片和副本数量的科学规划和动态调整
- 数据分布的均衡性和查询路由的效率
- 故障恢复的快速性和数据一致性保障

## 📝 题目1：Elasticsearch集群架构设计

### 解决方案思路分析

#### 1. 集群节点角色设计策略
**为什么需要节点角色分离？**
- 主节点专注集群状态管理，避免数据处理干扰
- 数据节点优化存储和计算资源配置
- 协调节点减轻数据节点的查询协调负担
- 专用节点提高集群的稳定性和可扩展性

#### 2. 分片策略设计原理
**分片规划策略**：
- 基于数据量和查询模式的分片大小计算
- 考虑硬件资源和网络带宽的分片分布
- 支持水平扩展的分片数量预留
- 分片重平衡的自动化和性能优化

#### 3. 高可用保障机制
**可用性设计要点**：
- 多副本的数据冗余和故障切换
- 跨机架/数据中心的节点分布
- 脑裂问题的预防和检测机制
- 滚动升级和零停机维护策略

### 代码实现要点

#### Elasticsearch集群配置实现
通过完整的配置和管理代码展示集群架构

```yaml
# elasticsearch.yml - 主节点配置
cluster.name: production-search-cluster
node.name: master-node-${HOSTNAME}

# 节点角色配置
node.roles: [ master ]

# 网络配置
network.host: 0.0.0.0
http.port: 9200
transport.port: 9300

# 集群发现配置
discovery.seed_hosts: 
  - master-node-1:9300
  - master-node-2:9300
  - master-node-3:9300

cluster.initial_master_nodes:
  - master-node-1
  - master-node-2
  - master-node-3

# 集群设置
cluster.routing.allocation.awareness.attributes: rack_id,zone
cluster.routing.allocation.awareness.force.zone.values: zone-1,zone-2,zone-3

# 防止脑裂
discovery.zen.minimum_master_nodes: 2
gateway.expected_master_nodes: 3
gateway.expected_data_nodes: 6
gateway.recover_after_master_nodes: 2
gateway.recover_after_data_nodes: 4

# JVM配置
bootstrap.memory_lock: true

# 索引配置
action.auto_create_index: false
action.destructive_requires_name: true

---
# elasticsearch.yml - 数据节点配置
cluster.name: production-search-cluster
node.name: data-node-${HOSTNAME}

# 节点角色配置
node.roles: [ data, ingest ]

# 网络配置
network.host: 0.0.0.0
http.port: 9200
transport.port: 9300

# 集群发现配置
discovery.seed_hosts: 
  - master-node-1:9300
  - master-node-2:9300
  - master-node-3:9300

# 节点属性
node.attr.rack_id: ${RACK_ID}
node.attr.zone: ${ZONE}

# 数据路径配置
path.data: 
  - /data1/elasticsearch
  - /data2/elasticsearch
path.logs: /var/log/elasticsearch

# 内存和存储配置
indices.memory.index_buffer_size: 30%
indices.memory.min_index_buffer_size: 96mb

# 线程池配置
thread_pool.write.queue_size: 1000
thread_pool.search.queue_size: 1000

---
# elasticsearch.yml - 协调节点配置
cluster.name: production-search-cluster
node.name: coordinating-node-${HOSTNAME}

# 节点角色配置（仅协调，不存储数据）
node.roles: []

# 网络配置
network.host: 0.0.0.0
http.port: 9200
transport.port: 9300

# 集群发现配置
discovery.seed_hosts: 
  - master-node-1:9300
  - master-node-2:9300
  - master-node-3:9300

# 协调节点优化
search.remote.connect: false
```

```python
# cluster_manager.py - 集群管理工具
import json
import requests
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ElasticsearchClusterManager:
    """Elasticsearch集群管理类"""
    
    def __init__(self, hosts: List[str], auth: Optional[tuple] = None):
        self.hosts = hosts
        self.auth = auth
        self.session = requests.Session()
        if auth:
            self.session.auth = auth
    
    def get_cluster_health(self) -> Dict[str, Any]:
        """获取集群健康状态"""
        try:
            response = self.session.get(f"{self.hosts[0]}/_cluster/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get cluster health: {e}")
            raise
    
    def get_cluster_stats(self) -> Dict[str, Any]:
        """获取集群统计信息"""
        try:
            response = self.session.get(f"{self.hosts[0]}/_cluster/stats")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get cluster stats: {e}")
            raise
    
    def get_nodes_info(self) -> Dict[str, Any]:
        """获取节点信息"""
        try:
            response = self.session.get(f"{self.hosts[0]}/_nodes")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get nodes info: {e}")
            raise
    
    def create_index_template(self, name: str, template: Dict[str, Any]):
        """创建索引模板"""
        try:
            response = self.session.put(
                f"{self.hosts[0]}/_index_template/{name}",
                json=template,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            logger.info(f"Index template '{name}' created successfully")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create index template '{name}': {e}")
            raise
    
    def setup_index_lifecycle_policy(self, policy_name: str, policy: Dict[str, Any]):
        """设置索引生命周期策略"""
        try:
            response = self.session.put(
                f"{self.hosts[0]}/_ilm/policy/{policy_name}",
                json=policy,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            logger.info(f"ILM policy '{policy_name}' created successfully")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create ILM policy '{policy_name}': {e}")
            raise
    
    def configure_cluster_settings(self, settings: Dict[str, Any]):
        """配置集群设置"""
        try:
            response = self.session.put(
                f"{self.hosts[0]}/_cluster/settings",
                json=settings,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            logger.info("Cluster settings updated successfully")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to update cluster settings: {e}")
            raise
    
    def monitor_cluster_status(self, interval: int = 60):
        """监控集群状态"""
        logger.info(f"Starting cluster monitoring (interval: {interval}s)")
        
        while True:
            try:
                health = self.get_cluster_health()
                stats = self.get_cluster_stats()
                
                # 检查关键指标
                status = health.get('status', 'unknown')
                active_shards = health.get('active_shards', 0)
                relocating_shards = health.get('relocating_shards', 0)
                unassigned_shards = health.get('unassigned_shards', 0)
                
                # 记录状态
                logger.info(f"Cluster Status: {status}")
                logger.info(f"Active Shards: {active_shards}")
                logger.info(f"Relocating Shards: {relocating_shards}")
                logger.info(f"Unassigned Shards: {unassigned_shards}")
                
                # 检查警告条件
                if status == 'red':
                    logger.error("ALERT: Cluster status is RED!")
                elif status == 'yellow':
                    logger.warning("WARNING: Cluster status is YELLOW")
                
                if unassigned_shards > 0:
                    logger.warning(f"WARNING: {unassigned_shards} unassigned shards")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(interval)

def setup_production_cluster():
    """生产环境集群初始化配置"""
    
    # 集群管理器
    cluster_manager = ElasticsearchClusterManager(
        hosts=["http://coordinating-node-1:9200", 
               "http://coordinating-node-2:9200"]
    )
    
    # 1. 配置集群设置
    cluster_settings = {
        "persistent": {
            # 分片分配设置
            "cluster.routing.allocation.disk.threshold.enabled": True,
            "cluster.routing.allocation.disk.watermark.low": "85%",
            "cluster.routing.allocation.disk.watermark.high": "90%",
            "cluster.routing.allocation.disk.watermark.flood_stage": "95%",
            
            # 恢复设置
            "cluster.routing.allocation.node_concurrent_recoveries": 2,
            "cluster.routing.allocation.cluster_concurrent_rebalance": 2,
            "indices.recovery.max_bytes_per_sec": "100mb",
            
            # 搜索设置
            "search.max_buckets": 100000,
            "search.allow_expensive_queries": False,
            
            # 索引设置
            "action.auto_create_index": False,
            "action.destructive_requires_name": True
        }
    }
    
    cluster_manager.configure_cluster_settings(cluster_settings)
    
    # 2. 创建索引模板
    log_template = {
        "index_patterns": ["logs-*"],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1,
                "refresh_interval": "30s",
                "index.codec": "best_compression",
                "index.lifecycle.name": "logs-policy",
                "index.lifecycle.rollover_alias": "logs"
            },
            "mappings": {
                "properties": {
                    "@timestamp": {
                        "type": "date",
                        "format": "strict_date_optional_time||epoch_millis"
                    },
                    "level": {
                        "type": "keyword"
                    },
                    "service": {
                        "type": "keyword"
                    },
                    "message": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "host": {
                        "type": "keyword"
                    },
                    "ip": {
                        "type": "ip"
                    },
                    "user_id": {
                        "type": "keyword"
                    },
                    "request_id": {
                        "type": "keyword"
                    },
                    "duration": {
                        "type": "long"
                    },
                    "status_code": {
                        "type": "integer"
                    }
                }
            }
        },
        "priority": 100
    }
    
    cluster_manager.create_index_template("logs-template", log_template)
    
    # 3. 设置索引生命周期策略
    logs_ilm_policy = {
        "policy": {
            "phases": {
                "hot": {
                    "actions": {
                        "rollover": {
                            "max_size": "10GB",
                            "max_age": "1d",
                            "max_docs": 10000000
                        },
                        "set_priority": {
                            "priority": 100
                        }
                    }
                },
                "warm": {
                    "min_age": "1d",
                    "actions": {
                        "allocate": {
                            "number_of_replicas": 0
                        },
                        "forcemerge": {
                            "max_num_segments": 1
                        },
                        "set_priority": {
                            "priority": 50
                        }
                    }
                },
                "cold": {
                    "min_age": "7d",
                    "actions": {
                        "allocate": {
                            "number_of_replicas": 0,
                            "include": {
                                "node_type": "cold"
                            }
                        },
                        "set_priority": {
                            "priority": 10
                        }
                    }
                },
                "delete": {
                    "min_age": "30d",
                    "actions": {
                        "delete": {}
                    }
                }
            }
        }
    }
    
    cluster_manager.setup_index_lifecycle_policy("logs-policy", logs_ilm_policy)
    
    # 4. 创建用户数据索引模板
    user_template = {
        "index_patterns": ["users-*"],
        "template": {
            "settings": {
                "number_of_shards": 3,
                "number_of_replicas": 2,
                "refresh_interval": "1s",
                "index.max_result_window": 50000
            },
            "mappings": {
                "properties": {
                    "user_id": {
                        "type": "keyword"
                    },
                    "username": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "email": {
                        "type": "keyword"
                    },
                    "profile": {
                        "type": "object",
                        "properties": {
                            "age": {"type": "integer"},
                            "gender": {"type": "keyword"},
                            "location": {"type": "geo_point"},
                            "interests": {"type": "keyword"}
                        }
                    },
                    "created_at": {
                        "type": "date"
                    },
                    "updated_at": {
                        "type": "date"
                    },
                    "status": {
                        "type": "keyword"
                    }
                }
            }
        },
        "priority": 200
    }
    
    cluster_manager.create_index_template("users-template", user_template)
    
    print("Production cluster setup completed successfully!")
    
    return cluster_manager

# 集群监控和管理脚本
class ClusterHealthMonitor:
    """集群健康监控类"""
    
    def __init__(self, cluster_manager: ElasticsearchClusterManager):
        self.cluster_manager = cluster_manager
        self.alerts = []
    
    def check_cluster_health(self) -> Dict[str, Any]:
        """检查集群健康状态"""
        health = self.cluster_manager.get_cluster_health()
        stats = self.cluster_manager.get_cluster_stats()
        
        issues = []
        
        # 检查集群状态
        if health.get('status') == 'red':
            issues.append({
                'severity': 'critical',
                'message': 'Cluster status is RED - some primary shards are not allocated'
            })
        elif health.get('status') == 'yellow':
            issues.append({
                'severity': 'warning',
                'message': 'Cluster status is YELLOW - some replica shards are not allocated'
            })
        
        # 检查未分配分片
        unassigned_shards = health.get('unassigned_shards', 0)
        if unassigned_shards > 0:
            issues.append({
                'severity': 'warning',
                'message': f'{unassigned_shards} shards are unassigned'
            })
        
        # 检查磁盘使用率
        nodes = self.cluster_manager.get_nodes_info()
        for node_id, node_info in nodes.get('nodes', {}).items():
            fs_info = node_info.get('fs', {})
            if fs_info:
                total_bytes = fs_info.get('total', {}).get('total_in_bytes', 0)
                available_bytes = fs_info.get('total', {}).get('available_in_bytes', 0)
                
                if total_bytes > 0:
                    usage_percent = (total_bytes - available_bytes) / total_bytes * 100
                    if usage_percent > 90:
                        issues.append({
                            'severity': 'critical',
                            'message': f'Node {node_info.get("name", node_id)} disk usage: {usage_percent:.1f}%'
                        })
                    elif usage_percent > 85:
                        issues.append({
                            'severity': 'warning',
                            'message': f'Node {node_info.get("name", node_id)} disk usage: {usage_percent:.1f}%'
                        })
        
        return {
            'timestamp': datetime.now().isoformat(),
            'cluster_health': health,
            'cluster_stats': stats,
            'issues': issues
        }
    
    def generate_health_report(self) -> str:
        """生成健康报告"""
        health_data = self.check_cluster_health()
        
        report = f"""
Elasticsearch Cluster Health Report
Generated: {health_data['timestamp']}

=== Cluster Overview ===
Status: {health_data['cluster_health'].get('status', 'unknown').upper()}
Nodes: {health_data['cluster_health'].get('number_of_nodes', 0)}
Data Nodes: {health_data['cluster_health'].get('number_of_data_nodes', 0)}
Active Shards: {health_data['cluster_health'].get('active_shards', 0)}
Relocating Shards: {health_data['cluster_health'].get('relocating_shards', 0)}
Unassigned Shards: {health_data['cluster_health'].get('unassigned_shards', 0)}

=== Issues Detected ===
"""
        
        if health_data['issues']:
            for issue in health_data['issues']:
                report += f"[{issue['severity'].upper()}] {issue['message']}\n"
        else:
            report += "No issues detected.\n"
        
        return report

if __name__ == "__main__":
    # 初始化生产环境集群
    cluster_manager = setup_production_cluster()
    
    # 创建健康监控器
    health_monitor = ClusterHealthMonitor(cluster_manager)
    
    # 生成健康报告
    report = health_monitor.generate_health_report()
    print(report)
    
    # 启动监控（可选）
    # cluster_manager.monitor_cluster_status(interval=60)
```

```dockerfile
# Dockerfile for Elasticsearch node
FROM docker.elastic.co/elasticsearch/elasticsearch:8.11.0

# 安装插件
RUN bin/elasticsearch-plugin install analysis-icu
RUN bin/elasticsearch-plugin install analysis-smartcn

# 复制配置文件
COPY elasticsearch.yml /usr/share/elasticsearch/config/
COPY jvm.options /usr/share/elasticsearch/config/

# 设置环境变量
ENV ES_JAVA_OPTS="-Xms4g -Xmx4g"
ENV discovery.type=zen

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:9200/_cluster/health || exit 1

EXPOSE 9200 9300
```

```yaml
# docker-compose.yml for Elasticsearch cluster
version: '3.8'

services:
  # Master nodes
  es-master-1:
    build: .
    container_name: es-master-1
    environment:
      - node.name=es-master-1
      - cluster.name=production-cluster
      - node.roles=master
      - discovery.seed_hosts=es-master-1,es-master-2,es-master-3
      - cluster.initial_master_nodes=es-master-1,es-master-2,es-master-3
      - HOSTNAME=es-master-1
    volumes:
      - master1_data:/usr/share/elasticsearch/data
      - ./config/master.yml:/usr/share/elasticsearch/config/elasticsearch.yml
    networks:
      - elastic

  es-master-2:
    build: .
    container_name: es-master-2
    environment:
      - node.name=es-master-2
      - cluster.name=production-cluster
      - node.roles=master
      - discovery.seed_hosts=es-master-1,es-master-2,es-master-3
      - cluster.initial_master_nodes=es-master-1,es-master-2,es-master-3
      - HOSTNAME=es-master-2
    volumes:
      - master2_data:/usr/share/elasticsearch/data
      - ./config/master.yml:/usr/share/elasticsearch/config/elasticsearch.yml
    networks:
      - elastic

  es-master-3:
    build: .
    container_name: es-master-3
    environment:
      - node.name=es-master-3
      - cluster.name=production-cluster
      - node.roles=master
      - discovery.seed_hosts=es-master-1,es-master-2,es-master-3
      - cluster.initial_master_nodes=es-master-1,es-master-2,es-master-3
      - HOSTNAME=es-master-3
    volumes:
      - master3_data:/usr/share/elasticsearch/data
      - ./config/master.yml:/usr/share/elasticsearch/config/elasticsearch.yml
    networks:
      - elastic

  # Data nodes
  es-data-1:
    build: .
    container_name: es-data-1
    environment:
      - node.name=es-data-1
      - cluster.name=production-cluster
      - node.roles=data,ingest
      - discovery.seed_hosts=es-master-1,es-master-2,es-master-3
      - node.attr.rack_id=rack-1
      - node.attr.zone=zone-1
      - HOSTNAME=es-data-1
      - RACK_ID=rack-1
      - ZONE=zone-1
    volumes:
      - data1_data:/usr/share/elasticsearch/data
      - ./config/data.yml:/usr/share/elasticsearch/config/elasticsearch.yml
    networks:
      - elastic
    depends_on:
      - es-master-1
      - es-master-2
      - es-master-3

  # Coordinating nodes
  es-coord-1:
    build: .
    container_name: es-coord-1
    environment:
      - node.name=es-coord-1
      - cluster.name=production-cluster
      - node.roles=[]
      - discovery.seed_hosts=es-master-1,es-master-2,es-master-3
      - HOSTNAME=es-coord-1
    ports:
      - "9200:9200"
    volumes:
      - ./config/coordinating.yml:/usr/share/elasticsearch/config/elasticsearch.yml
    networks:
      - elastic
    depends_on:
      - es-master-1
      - es-data-1

volumes:
  master1_data:
  master2_data:
  master3_data:
  data1_data:

networks:
  elastic:
    driver: bridge
```

## 🎯 面试要点总结

### 技术深度体现
- **节点角色分离**：主节点、数据节点、协调节点的职责划分和优化配置
- **分片策略**：基于数据量和查询模式的分片大小和数量计算
- **高可用设计**：多副本、跨机架部署、脑裂预防的完整方案
- **性能优化**：JVM配置、线程池调优、索引生命周期管理

### 生产实践经验
- **监控体系**：集群健康、节点状态、性能指标的全方位监控
- **运维自动化**：索引模板、ILM策略、配置管理的自动化
- **故障处理**：常见问题的诊断和解决方案
- **容量规划**：基于业务增长的集群扩容策略

### 面试回答要点
- **架构设计**：从业务需求到技术架构的完整设计思路
- **性能调优**：JVM、操作系统、网络等多层次的优化策略
- **运维经验**：生产环境的部署、监控、故障处理实践
- **扩展性**：支持PB级数据和水平扩展的架构设计

[← 返回搜索引擎面试题](../../questions/backend/search-engines.md) 