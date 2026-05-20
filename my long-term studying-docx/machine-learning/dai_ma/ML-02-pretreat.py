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

#先使用pandas计算各个特征值之间的相关系数
house_0=house.corr(method="pearson") #corr:计算列与列之间的相关系数
print(house_0)




fig=plot.figure(figsize=(8,8),dpi=100) #新建一个空白画布，建一个8×8分辨率是100的画布。
plot.rcParams["font.sans-serif"]=["SimHei"]#rcParams：全局配置参数字典，
                                          #专门用来一次性设置所有图表的默认样式（字体、颜色、尺寸、刻度等），
                                          #改一次，后续所有图都生效。
                                          #font.sans-self:无衬线字体
                                          #SimHei：黑体
                                          #无衬线改为黑体
plot.rcParams['axes.unicode_minus'] = False # 解决坐标轴负号显示异常



plot.subplots_adjust(hspace=0.35)#调整子图之间的垂直间距(hspace = height space)
                                 #0.35是间距占画布高度的比例，避免上下子图的标题、坐标轴标签挤在一起重叠。
plot.subplot(2, 2, 1)#创建一个「2 行 ×2 列」的子图网格，当前要操作的是第 1 个位置（从上到下、从左到右数，第一行第一列）。
plot.scatter(house['MedInc'], house['MEDV'], s=1, marker='o', label='MedInc-MEDV')
# 参数	含义
# house['RM']	X 轴数据：数据集里的「平均房间数」（Room Number）
# house['MEDV']	Y 轴数据：数据集里的「房屋中位数价格」（房价）
# s=1	散点的大小（size），设为 1 是为了避免 500 多个点重叠成一团
# marker='o'	散点形状：圆形（circle）
# label='RM-MEDV'	图例标签（截图被截断了，完整应该是标注这组数据的名称）
plot.xlabel(r"中位收入 - $MedInc$")
plot.ylabel(r"房价 - $MEDV$")
# r"..."：Python 的「原始字符串」，避免特殊字符被转义；
# $RM$：Matplotlib 的LaTeX 语法，会把RM渲染成斜体的数学符号，让图表更专业。
plot.title(r"$\rho=688075$")#设置子图标题
plot.legend()


plot.subplot(2, 2, 2)
plot.scatter(house['HouseAge'], house['MEDV'], s=1, marker='o', label='HouseAge-MEDV')
plot.xlabel(r"房屋年龄 - $HouseAge$")
plot.title(r"$\rho=0.105623$")
plot.legend()

plot.show()

house_11=house[["MedInc","HouseAge","AveRooms","AveBedrms"]]
print(house_11[:5])
