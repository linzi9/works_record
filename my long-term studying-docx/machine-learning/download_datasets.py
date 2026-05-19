import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.datasets import fetch_california_housing #专门用来加载加利福尼亚房价数据集的函数

house = fetch_california_housing() #把房价数据全部装进house这个 “数据盒子” 里。
print(house.data.shape) #house.data:数据盒子里的核心特征数据（比如房屋的犯罪率、房间数、税率等）
                         #.shape:查看数据的形状（几行几列），格式是 (样本数, 特征数)

df=pd.DataFrame(house.data,columns=house.feature_names) #pd.DataFrame( ):创建表格；
                                                         #columns=：给表格添加列名表头
df["MEDV"]=house["target"] #给表格 df 新增一列，列名叫 MEDV;
                           #house["target"]：数据集里的目标值，也就是每栋房子的真实房价
                            #house这个数据集里有两块，一块是特征数据，一块是房价数据
df.to_csv("C:/Users/MECHREVO/Desktop/machine-learning/datasets/c_l.csv",index=None) #index=none,就是不自动生成行索引号

file=open("C:/Users/MECHREVO/Desktop/machine-learning/datasets/c_l.txt","w") #w意味着是写入模式；
#①如果这个 c_l.txt 不存在 → 自动新建一个空的文本文档②如果这个文件已经存在 → 清空里面所有原有内容（覆盖式写入）
file.write(house.DESCR)
file.close()




