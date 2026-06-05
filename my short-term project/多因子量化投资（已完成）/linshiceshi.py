import pandas as pd

df1=pd.read_excel(r"C:\Users\MECHREVO\Desktop\machine-learning\lianghuatouzi\shuju\并表.xlsx", engine="openpyxl")
df2=pd.read_excel(r"C:\Users\MECHREVO\Desktop\machine-learning\lianghuatouzi\shuju\沪深300前100股票_流通市值.xlsx", engine="openpyxl")

df3 = pd.merge(
    df1,    # 第一个表（股票基础信息）
    df2,    # 第二个表（市值/财务数据）
    on=['股票代码','日期'],  # 按哪一列合并（必须两个表都有这列）
    how='inner'    # 合并方式（重点！）
)

df3.to_csv(r"C:\Users\MECHREVO\Desktop\machine-learning\lianghuatouzi\shuju\并表1.csv")

print("已完成")
