# 1. 导入必需的库
import pandas as pd
from sklearn.linear_model import LinearRegression  # 最小二乘法线性回归
from sklearn.metrics import mean_squared_error    # 可选：计算误差

# ===================== 【用户必须修改的部分】 =====================
# 2. 读取你的训练数据（支持CSV/Excel，替换为你的文件路径）
# 读取CSV文件
X_train = pd.read_csv("C:/Users/MECHREVO/Desktop/machine-learning/datasets/X_train.csv")
X_test  = pd.read_csv("C:/Users/MECHREVO/Desktop/machine-learning/datasets/X_test.csv")
y_train = pd.read_csv("C:/Users/MECHREVO/Desktop/machine-learning/datasets/y_train.csv").values.ravel()
y_test  = pd.read_csv("C:/Users/MECHREVO/Desktop/machine-learning/datasets/y_test.csv").values.ravel()
# 若为Excel文件，替换为：df = pd.read_excel("你的训练数据.xlsx")

# =================================================================

# 4. 初始化最小二乘法线性模型（无正则化，纯OLS）
model = LinearRegression()

# 5. 拟合模型 → 自动用最小二乘法求解最优参数
model.fit(X_train, y_train)

# 6. 提取最优参数（核心结果）
intercept = model.intercept_          # 截距项 b
coefficients = model.coef_            # 3个自变量的系数 w1, w2, w3

# 7. 输出结果
print("="*50)
print("最小二乘法求解的线性模型最优参数")
print("="*50)
print(f"截距 (intercept)：{intercept:.2f}")
print(f"自变量1 系数：{coefficients[0]:.2f}")
print(f"自变量2 系数：{coefficients[1]:.2f}")
print(f"自变量3 系数：{coefficients[2]:.2f}")

# 输出完整的线性模型公式
print("\n线性模型公式：")
print(f"y = {intercept:.2f} + {coefficients[0]:.2f}x₁ + {coefficients[1]:.2f}x₂ + {coefficients[2]:.2f}x₃")

# 8. （可选）计算训练集误差，验证模型效果
y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
print(f"\n测试集均方误差 (最小二乘损失值)：{mse:.2f}")