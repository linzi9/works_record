#建立目标集和特征集
#还有测试集和训练集
# 1. 导入必需的库
# 拆分数据集的核心函数
from sklearn.model_selection import train_test_split
import pandas as pd  
# 加载示例数据集（替换为你的数据即可）
#from sklearn.datasets import load_iris

df=pd.read_csv("C:/Users/MECHREVO/Desktop/machine-learning/datasets/清洗后数据.csv")  

# 2. 加载数据（区分 特征X 和 标签y）
# 加载数据集
#data = load_iris()  
# 特征矩阵（所有输入特征）
X = df[["MedInc","HouseAge","AveRooms"]]
# 标签向量（预测目标）
Y = df[["MEDV"]]  

# 3. 拆分训练集和测试集（核心代码）
#stratify=y = 按标签比例分层抽样
#保证：训练集 + 测试集的标签分布比例，和原始数据集完全一致，回归任务不用加
X_train, X_test, y_train, y_test = train_test_split(
    X, Y,                
    test_size=0.2,       # 测试集占比 20%，训练集占 80%
    random_state=42,     # 固定随机种子，保证结果可复现
    #stratify=y           # 分层抽样（分类任务必加，保持标签分布一致）
)

# 4. 查看拆分结果（验证数据形状）
print(f"训练集特征形状: {X_train.shape}")
print(f"测试集特征形状: {X_test.shape}")
print(f"训练集标签形状: {y_train.shape}")
print(f"测试集标签形状: {y_test.shape}")

if isinstance(X_train, pd.DataFrame):
    print("这是一个DataFrame")
else:
    print("这不是一个DataFrame")

# X_train.to_csv("C:/Users/MECHREVO/Desktop/machine-learning/datasets/X_train.csv", index=False,encoding="utf-8-sig")
# X_test.to_csv("C:/Users/MECHREVO/Desktop/machine-learning/datasets/X_test.csv", index=False,encoding="utf-8-sig")
# y_train.to_csv("C:/Users/MECHREVO/Desktop/machine-learning/datasets/y_train.csv", index=False,encoding="utf-8-sig")
# y_test.to_csv("C:/Users/MECHREVO/Desktop/machine-learning/datasets/y_test.csv", index=False,encoding="utf-8-sig")