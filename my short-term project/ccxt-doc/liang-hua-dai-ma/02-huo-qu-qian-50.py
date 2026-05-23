import ccxt
import requests
import pandas as pd
from datetime import datetime

def get_top_50_cryptos_by_market_cap():
    """
    获取按市值从大到小排序的前50个加密货币
    使用CoinGecko API获取准确的市值数据
    """
    # CoinGecko API端点 - 获取市场数据
    url = "https://api.coingecko.com/api/v3/coins/markets"
    
    # 请求参数
    params = {
        'vs_currency': 'usd',          # 计价货币
        'order': 'market_cap_desc',    # 按市值降序排列
        'per_page': 50,                # 每页50个
        'page': 1,                     # 第一页
        'sparkline': 'false',          # 不返回K线数据
        'price_change_percentage': '24h'  # 返回24小时价格变化
    }
    
    try:
        # 发送请求
        response = requests.get(url, params=params)
        response.raise_for_status()  # 检查请求是否成功
        coins_data = response.json()
        
        # 处理数据
        top_coins = []
        for coin in coins_data:
            last_updated = datetime.fromisoformat(coin['last_updated'].replace('Z', '+00:00'))
            top_coins.append({
                'rank': coin['market_cap_rank'],
                'name': coin['name'],
                'symbol': coin['symbol'].upper(),
                'current_price': coin['current_price'],
                'market_cap': coin['market_cap'],
                'market_cap_formatted': f"${coin['market_cap']:,.0f}",
                'price_change_24h': coin['price_change_percentage_24h'],
                'total_volume': coin['total_volume'],
                'last_updated': last_updated.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return top_coins
    
    except requests.exceptions.RequestException as e:
        print(f"请求CoinGecko API时出错: {e}")
        return None
    
top_50_coins = get_top_50_cryptos_by_market_cap()
df = pd.DataFrame(top_50_coins)

print("=" * 120)
print(f"{'排名':<4} {'名称':<20} {'代码':<6} {'当前价格(USD)':<15} {'市值(USD)':<20} {'24h涨跌幅(%)':<12} {'24h成交量(USD)':<15}")
print("=" * 120)

# 遍历DataFrame的每一行数据
for _, row in df.iterrows():
    # 格式化价格：保留4位小数，带$符号，空值显示N/A
    price_str = f"${row['current_price']:,.4f}" if row['current_price'] is not None else "N/A"
    # 格式化涨跌幅：保留2位小数，带%符号，空值显示N/A
    change_str = f"{row['price_change_24h']:,.2f}%" if row['price_change_24h'] is not None else "N/A"
    # 格式化成交量：整数格式，带$符号，空值显示N/A
    volume_str = f"${row['total_volume']:,.0f}" if row['total_volume'] is not None else "N/A"
    
    # 按固定宽度左对齐，打印整齐的表格
    print(f"{row['rank']:<4} {row['name']:<20} {row['symbol']:<6} {price_str:<15} {row['market_cap_formatted']:<20} {change_str:<12} {volume_str:<15}")


df.to_csv('C:/Users/MECHREVO/Desktop/machine-learning/ccxt-doc/datasets/top_50_size.csv', index=False, encoding='utf-8-sig')
print("\n数据已保存到 top_50_size.csv")

