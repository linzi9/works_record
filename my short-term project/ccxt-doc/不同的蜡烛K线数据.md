这三种 K 线都是**加密货币衍生品（永续合约/期货）市场**特有的价格数据，和普通现货的成交价格 K 线不同。它们分别对应三种不同的"价格"：标记价格、指数价格、溢价指数。

---

## 1. 普通 K 线（默认 `fetchOHLCV`）
基于合约市场的**实际成交价格**（Last Price）。记录的是这个合约本身真实的买卖成交价。

---

## 2. Mark Price K 线（标记价格）

**是什么**：交易所用来计算你的**未实现盈亏**和**判断是否爆仓**的"公平价格"。

**为什么不用成交价格**：因为成交价格容易被瞬间大单"插针"操纵。如果直接用成交价格算爆仓，恶意砸盘或拉盘就能让别人被不公平地清算。

**怎么算的**：
> **标记价格 = 指数价格 + 资金费率基差调整**

它比实际成交价格更平滑、更稳定。即使某个瞬间合约价格暴跌，只要标记价格没跌到你的强平价，你就不会被爆仓。

**用途**：
- 计算持仓盈亏（PnL）
- 触发强制平仓
- 作为策略中"真实公允价值"的参考

---

## 3. Index Price K 线（指数价格）

**是什么**：这个币种在**整个现货市场**上的"公允价值"。

**怎么算的**：取多家主流交易所（如 Binance、Coinbase、Kraken、OKX 等）的**现货价格**，按成交量或固定权重做加权平均。

**作用**：
- 作为合约价格的"锚"，防止单一交易所偏离过大
- 是计算标记价格的基础
- 你看到的"BTC/USDT 指数"就是这个

---

## 4. Premium Index K 线（溢价指数）

**是什么**：衡量**合约价格偏离现货指数价格的程度**。

**计算公式**（大致）：
> **溢价指数 = (合约市场价格 - 指数价格) / 指数价格**

**作用**：
- 直接决定**资金费率**（Funding Rate）。当合约价格显著高于现货（正溢价），多头要向空头支付资金费；反之则相反。
- 用于**期现套利**策略：当溢价过高时，做空合约+买入现货；溢价回归时平仓套利。

---

## 在 CCXT 中如何获取

```python
import ccxt

exchange = ccxt.binance({'options': {'defaultType': 'future'}})

# 标记价格 K 线
mark_ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', params={'price': 'mark'})

# 指数价格 K 线
index_ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', params={'price': 'index'})

# 溢价指数 K 线
premium_ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', params={'price': 'premiumIndex'})

# 或者用便捷方法
mark_ohlcv = exchange.fetch_mark_ohlcv('BTC/USDT', '1h')
index_ohlcv = exchange.fetch_index_ohlcv('BTC/USDT', '1h')
premium_ohlcv = exchange.fetch_premium_index_ohlcv('BTC/USDT', '1h')
```


---

## 对你的量化策略有什么意义？

| 数据类型 | 策略用途 |
|---------|---------|
| **普通 K 线** | 常规趋势跟踪、技术指标计算（MA、RSI 等） |
| **Mark Price K 线** | 如果你做合约，计算策略信号时用它比用成交价格更抗噪音；也可用于估算对手盘的爆仓点位 |
| **Index Price K 线** | 作为"真实价值"基准，判断合约是否被高估/低估 |
| **Premium Index K 线** | **期现套利**的核心数据；也可作为情绪指标——极高溢价往往意味着市场过热（顶部信号） |

**一句话总结**：普通 K 线是"实际成交价格"，Mark 是"交易所认定的公平价格（用于清算）"，Index 是"全市场现货公允价格"，Premium 是"合约相对现货的偏离度"。如果你只做现货量化，这三者基本用不上；但如果你涉及**合约交易或期现套利**，Mark 和 Premium 是非常关键的因子来源。