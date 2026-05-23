import ccxt
import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import time

# -------------------------- 配置项 --------------------------
EXCHANGE = 'okx'        # 交易所（币安，支持主流币种最全）
QUOTE = 'USDT'             # 计价货币
TIMEFRAME = '1d'           # K线周期：1天（日线）
DAYS = 30                  # 近1个月 = 30天
SAVE_FOLDER = 'C:/Users/MECHREVO/Desktop/machine-learning/ccxt-doc/datasets/la_zhu_xian_data'  # 保存CSV的文件夹名
# -----------------------------------------------------------

# 创建保存文件夹
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

df_sta_rt=pd.read_csv("C:/Users/MECHREVO/Desktop/machine-learning/ccxt-doc/datasets/top_50_size.csv")
bi_dui=[]
for value in df_sta_rt['symbol'][:]:
    bi_dui.append(value)

def get_ohlcv_data(exchange, symbol, timeframe, days):
    """
    获取单个币种的K线数据
    :param exchange: ccxt交易所实例
    :param symbol: 交易对（如 BTC/USDT）
    :param timeframe: K线周期
    :param days: 获取天数
    :return: DataFrame格式K线数据
    """
    try:
        # 计算起始时间戳（毫秒）
        now = datetime.now()
        start_time = now - timedelta(days=days)
        since = exchange.parse8601(start_time.strftime('%Y-%m-%d %H:%M:%S'))

        # 获取K线数据
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=days)
        if not ohlcv:
            return None

        # 转换为DataFrame
        df = pd.DataFrame(ohlcv, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume'
        ])

        # 时间戳转可读时间
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['symbol'] = symbol  # 添加币种列
        # 调整列顺序
        df = df[['datetime', 'symbol', 'open', 'high', 'low', 'close', 'volume']]
        return df

    except Exception as e:
        print(f"获取 {symbol} K线失败：{str(e)}")
        return None

def batch_save_ohlcv(top_symbols):
    """批量获取并保存50个币种的K线到CSV"""
    # 初始化交易所
    exchange = getattr(ccxt, EXCHANGE)({
        'enableRateLimit': True,  # 强制限速，防止被封IP
        'timeout': 30000
    })
    exchange.load_markets()  # 加载所有交易对

    success_count = 0
    total = len(top_symbols)

    print(f"\n开始获取 {total} 个币种近1个月K线数据...\n")

    for symbol in top_symbols:
        # 拼接交易对（如 BTC -> BTC/USDT）
        trade_symbol = f"{symbol}/{QUOTE}"

        # 跳过交易所未上架的币种
        if trade_symbol not in exchange.markets:
            print(f"⚠️  {trade_symbol} 未在{EXCHANGE}上架，跳过")
            continue

        # 获取K线
        df = get_ohlcv_data(exchange, trade_symbol, TIMEFRAME, DAYS)
        if df is not None:
            # 保存为CSV文件
            filename = f"{SAVE_FOLDER}/{symbol}_{QUOTE}_1month.csv"
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"✅  已保存：{trade_symbol} | 数据量：{len(df)} 根K线")
            success_count += 1

        # 防止请求过快
        time.sleep(0.5)

    print(f"\n🎉 任务完成！成功保存 {success_count}/{total} 个币种的月度K线数据")
    print(f"文件保存在：{os.path.abspath(SAVE_FOLDER)}")

# ------------------- 主程序执行 -------------------
if __name__ == '__main__':
    # 1. 获取前50市值币种
    top_50 = bi_dui
    # 2. 批量获取K线并保存CSV
    batch_save_ohlcv(top_50)