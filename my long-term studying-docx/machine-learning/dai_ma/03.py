import pandas as pd
from sec_ond import house
from sklearn.preprocessing import MinMaxScaler

# 告诉 Pandas：东亚文字（中文/日文/韩文）按宽字符计算
pd.set_option('display.unicode.east_asian_width', True)
# 告诉 Pandas：模糊宽度字符也按宽字符计算
pd.set_option('display.unicode.ambiguous_as_wide', True)
#\:是续行符
df=pd.DataFrame({"是否第二学位":["Y","N","N","N","Y","N"],\
                 "性别":["男","女","女","女","男","男"],\
                 "籍贯":["北京","山东","北京","安徽","安徽","北京"]})
print(df)

df["是否第二学位"]=df["是否第二学位"].map({"N":0,"Y":1})
df["性别"]=df["性别"].map({"女":0,"男":1})
# 代码片段	含义
# pd.get_dummies()	Pandas 内置函数，专门做 独热编码（One-Hot）
# data=df	要处理的原始表格是 df
# columns="籍贯"	只对「籍贯」这一列做编码，其他列不动
# prefix="籍贯"	给新生成的列加前缀，方便识别
# df1=	把编码后的新表格，存到新变量 df1 里
df1=pd.get_dummies(data=df,columns=["籍贯"],prefix="籍贯",dtype=int)
print(df1)

m_m=MinMaxScaler()#初始化模型，赋值给m_m
#让机器学习模型 m_m，学习房屋数据 house 中 3 列特征的规律
# 作用：只学习数据的规律，不修改数据、不输出结果
# 比如：算平均值、方差、找数据特征、训练模型参数
# fit() 方法不返回数据！
# 模型.fit() 的作用：让模型学习数据规律
# 它的返回值：就是模型自己（m_m）
abc=m_m.fit(house[["MedInc","HouseAge","AveRooms"]])
print("min=",m_m.data_min_,"max=",m_m.data_max_)
#结果存在m里，注意：transform默认返回numpy 数组（没有列名的纯数值）。
m = m_m.transform(house[["MedInc","HouseAge","AveRooms"]])
# 把transform返回的 numpy 数组m，转成带列名的 pandas DataFrame，
# 列名还是RM和LSTAT，方便后续和其他列合并。
house2m = pd.DataFrame(m, columns=["MedInc","HouseAge","AveRooms"])
house2m[['AveBedrms', 'MEDV']] = house[['AveBedrms', 'MEDV']]
print(house2m[:5])

#1、导入工具 & 初始化标准化器
from sklearn.preprocessing import StandardScaler
zScaler = StandardScaler()
#2.fit() 学习数据的均值和方差
zScaler.fit(house[["MedInc","HouseAge","AveRooms"]])
#3.打印学习到的统计量
print("mean=", zScaler.mean_, "variance=", zScaler.var_)
#4.transform() 用学到的规律转换数据
z = zScaler.transform(house[["MedInc","HouseAge","AveRooms"]])
#6.把数组转回 DataFrame
house2z = pd.DataFrame(z, columns=["MedInc","HouseAge","AveRooms"])
#7.合并未标准化的列
house2z[['AveBedrms', 'MEDV']] = house[['AveBedrms', 'MEDV']]
print(house2z[:5])

#提取特征集和目标集
x=house2z[["MedInc","HouseAge","AveRooms",'AveBedrms']]
y=house2z[['MEDV']]
print(x[:5],y[:5])

# - 数据预处理：波士顿房价数据集
#   - 既没有**缺失值**，也没有**重复值**
#   - 所包含的3个特征项（房间数RM、低层人口比例LSTAT和河景房CHAS）是经过**相关性分析**筛选出来的，再加上预测目标（房价MEDV），共4列数据
#   - 非数值型特征采用0-1形式的**独热编码**，数值型数据经过Min-Max或z-score**标准化处理**
