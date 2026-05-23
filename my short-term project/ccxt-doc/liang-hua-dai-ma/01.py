import ccxt
from itertools import islice

# print(ccxt.exchanges[:10])

# 来自变量 id
exchange_id = 'okx'  # 可以换成任意交易所ID：'okx', 'kucoin', 'bybit'等
exchange_class = getattr(ccxt, exchange_id)  # 获取对应的交易所类
exchange = exchange_class({
    'apiKey': 'e97ebc82-da76-4dfe-8a5c-d2623679e12a',
    'secret': 'D7D007640B2D2BE28987E5CBE7E2E5B8',
    # 强烈建议加上这两个参数
    'enableRateLimit': True,  # 自动处理交易所的速率限制，防止被封IP
    'timeout': 30000,         # 请求超时时间（毫秒）
    'password':'201573Canada.'
})
exchange.set_sandbox_mode(True)

#print(exchange.id)
#print(exchange.has)

#先加载市场
exchange.load_markets()

# islice 是 Python 内置模块 itertools 里的一个函数，全称是 "iterator slice"（迭代器切片）。
# 它让你可以像切片 list[:3] 那样去切迭代器，但不会一次性把所有数据加载到内存。
#print(exchange.has.get('fetchCurrencies'))  
# 如果输出 False 或 None，说明该交易所**不提供**这个接口
d=exchange.fetchMarkets()

currencies =[]
usdt_pairs=[]
for market in d:
    if market['quote'] == 'USDT':
        usdt_pairs.append(market)
for c in usdt_pairs:
    currencies.append(c["symbol"])
print(currencies[:100])


