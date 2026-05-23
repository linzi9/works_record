import pandas as pd
from sklearn.preprocessing import StandardScaler

# 创建示例数据
df = pd.DataFrame({
    '特征1': [10, 20, 30, 40, 50],
    '特征2': [100, 200, 300, 400, 500],
    '特征3': [5, 10, 15, 20, 25]
})

# 初始化标准化器
scaler = StandardScaler()

# 对特征进行标准化（注意：只对特征标准化，不要对目标变量标准化）
df_scaled = pd.DataFrame(
    scaler.fit_transform(df),  # 拟合并转换
    columns=df.columns,
    index=df.index
)

print("标准化后的数据：")
print(df_scaled)

# 验证：标准化后的均值≈0，标准差≈1
print("\n标准化后的统计信息：")
print(f"均值: {df_scaled.mean().values}")
print(f"标准差: {df_scaled.std().values}")