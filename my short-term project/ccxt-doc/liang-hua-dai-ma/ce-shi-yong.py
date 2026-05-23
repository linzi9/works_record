import ccxt
import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import time

df_sta_rt=pd.read_csv("C:/Users/MECHREVO/Desktop/machine-learning/ccxt-doc/datasets/top_50_size.csv")
bi_dui=[]
for value in df_sta_rt['symbol'][:]:
    bi_dui.append(value)

print(bi_dui)
print(len(bi_dui))