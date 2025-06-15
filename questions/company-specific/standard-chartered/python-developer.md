# 渣打银行 Python 开发岗位面试题

## 难度级别
- 初级 / 中级 / 高级

## 标签
- Python, FastAPI, 微服务, 数据分析, 机器学习, 金融科技

## 基础编程题

### 1. 数据结构与算法
**题目**：实现一个交易监控系统，检测在指定时间窗口内的异常交易模式。

**要求**：
- 处理实时交易流数据
- 识别短时间内的大额交易
- 检测异常交易频率
- 时间复杂度 O(n)

**解决方案**：
```python
from collections import deque, defaultdict
from datetime import datetime, timedelta
import heapq

class TransactionMonitor:
    def __init__(self, time_window_minutes=5, max_amount_threshold=10000, max_frequency=10):
        self.time_window = timedelta(minutes=time_window_minutes)
        self.max_amount = max_amount_threshold
        self.max_frequency = max_frequency
        
        # 使用双端队列存储时间窗口内的交易
        self.transactions = deque()
        # 按账户分组的交易计数
        self.account_transactions = defaultdict(lambda: deque())
        
    def add_transaction(self, account_id, amount, timestamp):
        """添加新交易并检测异常"""
        transaction = {
            'account_id': account_id,
            'amount': amount,
            'timestamp': timestamp
        }
        
        # 清理过期交易
        self._clean_expired_transactions(timestamp)
        
        # 添加新交易
        self.transactions.append(transaction)
        self.account_transactions[account_id].append(transaction)
        
        # 检测异常
        anomalies = []
        
        # 检测大额交易
        if amount > self.max_amount:
            anomalies.append(f"Large amount transaction: {amount}")
        
        # 检测高频交易
        if len(self.account_transactions[account_id]) > self.max_frequency:
            anomalies.append(f"High frequency trading: {len(self.account_transactions[account_id])} transactions")
        
        # 检测短时间内多笔大额交易
        recent_large_transactions = [
            t for t in self.account_transactions[account_id]
            if t['amount'] > self.max_amount * 0.5
        ]
        if len(recent_large_transactions) >= 3:
            anomalies.append("Multiple large transactions in short period")
        
        return anomalies
    
    def _clean_expired_transactions(self, current_time):
        """清理过期的交易记录"""
        cutoff_time = current_time - self.time_window
        
        # 清理主交易队列
        while self.transactions and self.transactions[0]['timestamp'] < cutoff_time:
            self.transactions.popleft()
        
        # 清理按账户分组的交易
        for account_id in list(self.account_transactions.keys()):
            account_queue = self.account_transactions[account_id]
            while account_queue and account_queue[0]['timestamp'] < cutoff_time:
                account_queue.popleft()
            
            # 如果队列为空，删除该账户
            if not account_queue:
                del self.account_transactions[account_id]

# 使用示例
monitor = TransactionMonitor()
now = datetime.now()

# 模拟交易流
transactions = [
    ("ACC001", 5000, now),
    ("ACC001", 8000, now + timedelta(minutes=1)),
    ("ACC001", 12000, now + timedelta(minutes=2)),  # 大额交易
    ("ACC002", 3000, now + timedelta(minutes=1)),
]

for account, amount, timestamp in transactions:
    anomalies = monitor.add_transaction(account, amount, timestamp)
    if anomalies:
        print(f"账户 {account} 异常: {anomalies}")
```

### 2. 异步编程和API设计
**题目**：设计一个异步的汇率查询服务，支持多个数据源并提供缓存机制。

**要求**：
- 使用 asyncio 和 aiohttp
- 实现多数据源的并发查询
- 添加缓存和错误处理
- 提供 REST API 接口

**实现方案**：
```python
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis.asyncio as redis

app = FastAPI(title="Exchange Rate Service")

class ExchangeRateResponse(BaseModel):
    base_currency: str
    target_currency: str
    rate: float
    timestamp: datetime
    source: str

class ExchangeRateService:
    def __init__(self):
        self.redis_client = None
        self.data_sources = {
            "fixer": "https://api.fixer.io/latest",
            "exchangerate": "https://api.exchangerate-api.com/v4/latest",
            "currencylayer": "https://api.currencylayer.com/live"
        }
        
    async def init_redis(self):
        """初始化Redis连接"""
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    async def get_exchange_rate(self, base: str, target: str) -> ExchangeRateResponse:
        """获取汇率，优先从缓存获取"""
        cache_key = f"rate:{base}:{target}"
        
        # 尝试从缓存获取
        cached_rate = await self.redis_client.get(cache_key)
        if cached_rate:
            data = json.loads(cached_rate)
            return ExchangeRateResponse(**data)
        
        # 从多个数据源并发获取
        rate_data = await self._fetch_from_multiple_sources(base, target)
        
        if not rate_data:
            raise HTTPException(status_code=404, detail="Exchange rate not found")
        
        # 缓存结果（5分钟过期）
        await self.redis_client.setex(
            cache_key, 
            300, 
            json.dumps(rate_data.dict(), default=str)
        )
        
        return rate_data
    
    async def _fetch_from_multiple_sources(self, base: str, target: str) -> Optional[ExchangeRateResponse]:
        """从多个数据源并发获取汇率"""
        tasks = []
        
        async with aiohttp.ClientSession() as session:
            for source_name, base_url in self.data_sources.items():
                task = self._fetch_from_source(session, source_name, base_url, base, target)
                tasks.append(task)
            
            # 等待第一个成功的响应
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 返回第一个成功的结果
                for result in results:
                    if isinstance(result, ExchangeRateResponse):
                        return result
                
                # 如果所有数据源都失败，返回None
                return None
                
            except Exception as e:
                print(f"Error fetching exchange rates: {e}")
                return None
    
    async def _fetch_from_source(self, session: aiohttp.ClientSession, source: str, 
                                url: str, base: str, target: str) -> Optional[ExchangeRateResponse]:
        """从单个数据源获取汇率"""
        try:
            params = {"base": base, "symbols": target}
            
            async with session.get(url, params=params, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # 解析不同数据源的响应格式
                    rate = self._parse_rate_response(data, source, target)
                    
                    if rate:
                        return ExchangeRateResponse(
                            base_currency=base,
                            target_currency=target,
                            rate=rate,
                            timestamp=datetime.now(),
                            source=source
                        )
                        
        except asyncio.TimeoutError:
            print(f"Timeout fetching from {source}")
        except Exception as e:
            print(f"Error fetching from {source}: {e}")
        
        return None
    
    def _parse_rate_response(self, data: dict, source: str, target: str) -> Optional[float]:
        """解析不同数据源的响应格式"""
        try:
            if source == "fixer":
                return data.get("rates", {}).get(target)
            elif source == "exchangerate":
                return data.get("rates", {}).get(target)
            elif source == "currencylayer":
                return data.get("quotes", {}).get(f"USD{target}")
        except (KeyError, TypeError):
            pass
        
        return None

# 全局服务实例
exchange_service = ExchangeRateService()

@app.on_event("startup")
async def startup_event():
    await exchange_service.init_redis()

@app.get("/exchange-rate/{base}/{target}", response_model=ExchangeRateResponse)
async def get_exchange_rate(base: str, target: str):
    """获取汇率API端点"""
    return await exchange_service.get_exchange_rate(base.upper(), target.upper())

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}
```

### 3. 数据分析与金融建模
**题目**：实现一个简单的投资组合风险评估系统。

**要求**：
- 计算投资组合的VaR（Value at Risk）
- 支持不同的风险模型
- 提供可视化输出
- 处理缺失数据

**解决方案**：
```python
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class Asset:
    symbol: str
    weight: float
    price_history: List[float]

@dataclass
class RiskMetrics:
    var_95: float
    var_99: float
    expected_return: float
    volatility: float
    sharpe_ratio: float

class PortfolioRiskAnalyzer:
    def __init__(self, assets: List[Asset], confidence_levels: List[float] = [0.95, 0.99]):
        self.assets = assets
        self.confidence_levels = confidence_levels
        self.returns_df = None
        self.portfolio_returns = None
        
    def calculate_returns(self) -> pd.DataFrame:
        """计算各资产的收益率"""
        returns_data = {}
        
        for asset in self.assets:
            prices = pd.Series(asset.price_history)
            # 计算日收益率
            returns = prices.pct_change().dropna()
            returns_data[asset.symbol] = returns
        
        self.returns_df = pd.DataFrame(returns_data)
        
        # 处理缺失值
        self.returns_df = self.returns_df.fillna(method='ffill').fillna(0)
        
        return self.returns_df
    
    def calculate_portfolio_returns(self) -> pd.Series:
        """计算投资组合收益率"""
        if self.returns_df is None:
            self.calculate_returns()
        
        # 获取权重
        weights = np.array([asset.weight for asset in self.assets])
        
        # 计算加权投资组合收益率
        self.portfolio_returns = (self.returns_df * weights).sum(axis=1)
        
        return self.portfolio_returns
    
    def calculate_var(self, method: str = 'historical') -> Dict[float, float]:
        """计算VaR值"""
        if self.portfolio_returns is None:
            self.calculate_portfolio_returns()
        
        var_results = {}
        
        if method == 'historical':
            # 历史模拟法
            for confidence in self.confidence_levels:
                var_results[confidence] = np.percentile(
                    self.portfolio_returns, 
                    (1 - confidence) * 100
                )
        
        elif method == 'parametric':
            # 参数法（假设正态分布）
            mean_return = self.portfolio_returns.mean()
            std_return = self.portfolio_returns.std()
            
            for confidence in self.confidence_levels:
                z_score = stats.norm.ppf(1 - confidence)
                var_results[confidence] = mean_return + z_score * std_return
        
        elif method == 'monte_carlo':
            # 蒙特卡罗模拟
            var_results = self._monte_carlo_var()
        
        return var_results
    
    def _monte_carlo_var(self, num_simulations: int = 10000) -> Dict[float, float]:
        """蒙特卡罗VaR计算"""
        if self.returns_df is None:
            self.calculate_returns()
        
        # 计算协方差矩阵
        cov_matrix = self.returns_df.cov()
        mean_returns = self.returns_df.mean()
        
        # 权重向量
        weights = np.array([asset.weight for asset in self.assets])
        
        # 模拟投资组合收益率
        simulated_returns = []
        
        for _ in range(num_simulations):
            # 生成随机收益率
            random_returns = np.random.multivariate_normal(
                mean_returns, 
                cov_matrix
            )
            
            # 计算投资组合收益率
            portfolio_return = np.dot(weights, random_returns)
            simulated_returns.append(portfolio_return)
        
        # 计算VaR
        var_results = {}
        for confidence in self.confidence_levels:
            var_results[confidence] = np.percentile(
                simulated_returns, 
                (1 - confidence) * 100
            )
        
        return var_results
    
    def calculate_risk_metrics(self) -> RiskMetrics:
        """计算综合风险指标"""
        if self.portfolio_returns is None:
            self.calculate_portfolio_returns()
        
        # 基本统计量
        expected_return = self.portfolio_returns.mean() * 252  # 年化收益率
        volatility = self.portfolio_returns.std() * np.sqrt(252)  # 年化波动率
        
        # 夏普比率（假设无风险利率为2%）
        risk_free_rate = 0.02
        sharpe_ratio = (expected_return - risk_free_rate) / volatility
        
        # VaR计算
        var_results = self.calculate_var()
        
        return RiskMetrics(
            var_95=var_results.get(0.95, 0),
            var_99=var_results.get(0.99, 0),
            expected_return=expected_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio
        )
    
    def generate_risk_report(self) -> str:
        """生成风险报告"""
        metrics = self.calculate_risk_metrics()
        
        report = f"""
        投资组合风险评估报告
        =====================
        
        基本指标:
        - 预期年化收益率: {metrics.expected_return:.2%}
        - 年化波动率: {metrics.volatility:.2%}
        - 夏普比率: {metrics.sharpe_ratio:.2f}
        
        风险价值(VaR):
        - 95%置信度: {metrics.var_95:.2%}
        - 99%置信度: {metrics.var_99:.2%}
        
        资产配置:
        """
        
        for asset in self.assets:
            report += f"- {asset.symbol}: {asset.weight:.1%}\n"
        
        return report
    
    def plot_risk_analysis(self):
        """绘制风险分析图表"""
        if self.portfolio_returns is None:
            self.calculate_portfolio_returns()
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. 投资组合收益率分布
        ax1.hist(self.portfolio_returns, bins=50, alpha=0.7, color='blue')
        ax1.set_title('投资组合收益率分布')
        ax1.set_xlabel('收益率')
        ax1.set_ylabel('频数')
        
        # 添加VaR线
        var_95 = np.percentile(self.portfolio_returns, 5)
        ax1.axvline(var_95, color='red', linestyle='--', label=f'VaR 95%: {var_95:.2%}')
        ax1.legend()
        
        # 2. 累计收益率
        cumulative_returns = (1 + self.portfolio_returns).cumprod()
        ax2.plot(cumulative_returns)
        ax2.set_title('累计收益率')
        ax2.set_ylabel('累计收益率')
        
        # 3. 滚动波动率
        rolling_vol = self.portfolio_returns.rolling(window=30).std() * np.sqrt(252)
        ax3.plot(rolling_vol)
        ax3.set_title('30日滚动波动率')
        ax3.set_ylabel('年化波动率')
        
        # 4. 资产配置饼图
        labels = [asset.symbol for asset in self.assets]
        weights = [asset.weight for asset in self.assets]
        ax4.pie(weights, labels=labels, autopct='%1.1f%%')
        ax4.set_title('资产配置')
        
        plt.tight_layout()
        plt.show()

# 使用示例
if __name__ == "__main__":
    # 模拟数据
    np.random.seed(42)
    
    # 创建资产
    assets = [
        Asset("AAPL", 0.4, np.random.normal(0.001, 0.02, 252).tolist()),
        Asset("GOOGL", 0.3, np.random.normal(0.0008, 0.025, 252).tolist()),
        Asset("MSFT", 0.3, np.random.normal(0.0012, 0.018, 252).tolist()),
    ]
    
    # 创建分析器
    analyzer = PortfolioRiskAnalyzer(assets)
    
    # 生成报告
    print(analyzer.generate_risk_report())
    
    # 绘制图表
    analyzer.plot_risk_analysis()
```

## 面试评估要点

### 技术深度
1. **代码质量**：结构清晰、错误处理完善
2. **性能考虑**：算法复杂度、内存使用优化
3. **异步编程**：正确使用asyncio和并发处理
4. **数据处理**：pandas、numpy的高效使用

### 金融业务理解
1. **风险管理**：理解金融风险的概念和计算方法
2. **监管合规**：考虑数据安全和审计要求
3. **实时处理**：处理高频交易数据的能力
4. **国际化**：多币种、多时区的处理

### 系统设计能力
1. **可扩展性**：代码结构支持功能扩展
2. **可维护性**：清晰的模块划分和接口设计
3. **容错性**：异常处理和优雅降级
4. **监控性**：日志记录和性能监控

## 常见追问问题

1. **如何处理大规模数据？**
   - 数据分片和并行处理
   - 使用数据库索引优化查询
   - 流处理架构（Apache Kafka + Spark）

2. **如何确保计算准确性？**
   - 使用Decimal类型处理金融数据
   - 实现数据验证和校验机制
   - 单元测试覆盖关键计算逻辑

3. **如何处理系统故障？**
   - 实现断路器模式
   - 数据备份和恢复机制
   - 服务降级策略

4. **性能优化策略？**
   - 缓存热点数据
   - 异步处理非关键任务
   - 数据库连接池管理

---
[← 返回渣打面试题目录](./README.md) 