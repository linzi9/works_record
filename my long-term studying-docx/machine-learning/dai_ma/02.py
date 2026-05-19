import numpy as np
import pandas as pd
import matplotlib.pyplot as plot

house = pd.read_csv("C:/Users/MECHREVO/Desktop/machine-learning/datasets/c_l.csv")
print("shape=",house.shape)
print(house[:5])

#生成带有缺失值和重复值的数据
np.random.seed(2020) #random是随机数的生成函数；括号里的.seed(2020)是固定随机数，保证结果的可复现性
df=pd.DataFrame(np.random.randn(6,3),columns=list("ABC")) #random.randn()：生成标准正态分布的随机数（均值为 0，方差为 1）
                                                          #list("ABC")：快速把字符串转成列表 ['A', 'B', 'C']
df.loc[1:2,"A"]=np.nan;df.loc[4,"B"]=np.nan
df.loc[5,"C"]=50
print(df)

df1=df.isna()
print(df1)

df2=df.dropna(axis=0)#把带有缺失值的每一行给去掉
print(df2)

df3=df.fillna(df.mean())#计算 DataFrame 中每一列的平均值
df4=df.ffill()#向前填充，向上填充
df5=df.interpolate(method="linear")#线性插值

print(df3)
print(df4)
print(df5)

df_0=pd.DataFrame({"A":[1,1,4],"B":[2,2,5],"C":[3,3,6]})
print(df_0)

df_0_1=df_0.drop_duplicates()#去掉重复值
print(df_0_1)

#特征应尽量与预测目标线性相关，否则属于无意义特征
#各特征之间也应该尽量相互不相干，否则属于冗余特征

#使用皮尔逊相关系数