# 1. 导入必需的库
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 2. 读取数据
X_train = pd.read_csv("C:/Users/MECHREVO/Desktop/machine-learning/datasets/X_train.csv")
X_test  = pd.read_csv("C:/Users/MECHREVO/Desktop/machine-learning/datasets/X_test.csv")
y_train = pd.read_csv("C:/Users/MECHREVO/Desktop/machine-learning/datasets/y_train.csv").values.ravel()
y_test  = pd.read_csv("C:/Users/MECHREVO/Desktop/machine-learning/datasets/y_test.csv").values.ravel()

# 3. 训练模型
model = LinearRegression()
model.fit(X_train, y_train)

# 4. 预测
y_train_pred = model.predict(X_train)
y_test_pred = model.predict(X_test)

# ========================================
# 5. 计算评估指标
# ========================================

# 训练集指标
train_r2 = r2_score(y_train, y_train_pred)
train_mse = mean_squared_error(y_train, y_train_pred)
train_rmse = np.sqrt(train_mse)
train_mae = mean_absolute_error(y_train, y_train_pred)

# 测试集指标
test_r2 = r2_score(y_test, y_test_pred)
test_mse = mean_squared_error(y_test, y_test_pred)
test_rmse = np.sqrt(test_mse)
test_mae = mean_absolute_error(y_test, y_test_pred)

# ========================================
# 6. 打印评估结果
# ========================================

print("="*70)
print("📊 线性回归模型评估报告")
print("="*70)

print("\n【训练集评估指标】")
print(f"  决定系数 R²:      {train_r2:.4f}  ({train_r2*100:.2f}%)")
print(f"  均方误差 MSE:     {train_mse:.4f}")
print(f"  均方根误差 RMSE:  {train_rmse:.4f}")
print(f"  平均绝对误差 MAE: {train_mae:.4f}")

print("\n【测试集评估指标】")
print(f"  决定系数 R²:      {test_r2:.4f}  ({test_r2*100:.2f}%)")
print(f"  均方误差 MSE:     {test_mse:.4f}")
print(f"  均方根误差 RMSE:  {test_rmse:.4f}")
print(f"  平均绝对误差 MAE: {test_mae:.4f}")

# ========================================
# 7. 过拟合检查
# ========================================

print("\n【过拟合分析】")
r2_gap = train_r2 - test_r2
mse_gap = test_mse - train_mse

print(f"  R²差距 (训练集 - 测试集): {r2_gap:.4f}")
print(f"  MSE差距 (测试集 - 训练集): {mse_gap:.4f}")

if abs(r2_gap) < 0.05:
    print("  ✅ 模型泛化能力良好（R²差距 < 0.05）")
elif r2_gap > 0.1:
    print("  ⚠️  可能存在过拟合（训练集R²显著高于测试集）")
else:
    print("  ⚠️  存在轻微过拟合")

# ========================================
# 8. 特征重要性分析
# ========================================

print("\n【特征重要性分析】")
feature_importance = pd.DataFrame({
    '特征': X_train.columns,
    '系数': model.coef_,
    '绝对系数': np.abs(model.coef_)
})
feature_importance = feature_importance.sort_values('绝对系数', ascending=False)
print(feature_importance.to_string(index=False))

# ========================================
# 9. 可视化评估
# ========================================

# 创建评估图表
fig, axes = plt.subplots(2, 2, figsize=(15, 12))

# 1. 训练集预测效果
axes[0, 0].scatter(y_train, y_train_pred, alpha=0.6, s=30)
axes[0, 0].plot([y_train.min(), y_train.max()], 
                [y_train.min(), y_train.max()], 'r--', lw=2)
axes[0, 0].set_xlabel('真实值', fontsize=12)
axes[0, 0].set_ylabel('预测值', fontsize=12)
axes[0, 0].set_title(f'训练集预测效果 (R² = {train_r2:.4f})', fontsize=14, fontweight='bold')
axes[0, 0].grid(True, alpha=0.3)

# 2. 测试集预测效果
axes[0, 1].scatter(y_test, y_test_pred, alpha=0.6, s=30, color='orange')
axes[0, 1].plot([y_test.min(), y_test.max()], 
                [y_test.min(), y_test.max()], 'r--', lw=2)
axes[0, 1].set_xlabel('真实值', fontsize=12)
axes[0, 1].set_ylabel('预测值', fontsize=12)
axes[0, 1].set_title(f'测试集预测效果 (R² = {test_r2:.4f})', fontsize=14, fontweight='bold')
axes[0, 1].grid(True, alpha=0.3)

# 3. 残差分析
train_residuals = y_train - y_train_pred
test_residuals = y_test - y_test_pred

axes[1, 0].scatter(y_train_pred, train_residuals, alpha=0.6, label='训练集', s=30)
axes[1, 0].scatter(y_test_pred, test_residuals, alpha=0.6, label='测试集', s=30, color='orange')
axes[1, 0].axhline(y=0, color='r', linestyle='--', lw=2)
axes[1, 0].set_xlabel('预测值', fontsize=12)
axes[1, 0].set_ylabel('残差', fontsize=12)
axes[1, 0].set_title('残差分析图', fontsize=14, fontweight='bold')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# 4. 评估指标对比柱状图
metrics = ['R²', 'MSE', 'RMSE', 'MAE']
train_values = [train_r2, train_mse, train_rmse, train_mae]
test_values = [test_r2, test_mse, test_rmse, test_mae]

x = np.arange(len(metrics))
width = 0.35

bars1 = axes[1, 1].bar(x - width/2, train_values, width, label='训练集', alpha=0.8)
bars2 = axes[1, 1].bar(x + width/2, test_values, width, label='测试集', alpha=0.8, color='orange')

axes[1, 1].set_xlabel('评估指标', fontsize=12)
axes[1, 1].set_ylabel('数值', fontsize=12)