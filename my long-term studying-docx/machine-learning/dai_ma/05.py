import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.preprocessing import StandardScaler
import warnings

# 忽略警告
warnings.filterwarnings('ignore')

# 设置中文字体（根据你的系统调整）
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class FeatureAnalyzer:
    """特征分析器：检测特征冗余性并分析与目标变量的相关性"""
    
    #它是整个特征分析类的初始化核心，作用就是给分析工具准备好数据、分好类
    def __init__(self, data, target_col=None):
        """
        初始化分析器
        :param data: pandas DataFrame，包含特征和目标变量的数据集
        :param target_col: 字符串，目标变量列名，如果为None则只分析特征间冗余性
        """
        self.data = data.copy()
        self.target_col = target_col
        #.tolist(),把 pandas 的列名格式，转换成标准 Python 列表
        #.columns,上一步筛选出了「数值列的数据」，这一步只拿这些列的名字（表头）
        #.select_dtypes(include=[np.number]);这是pandas 专用筛选函数，作用：按数据类型筛选列
        self.numeric_cols = self.data.select_dtypes(include=[np.number]).columns.tolist()
        
        if target_col and target_col in self.numeric_cols:
            self.features = [col for col in self.numeric_cols if col != target_col]
            self.target = self.data[target_col]
        else:
            self.features = self.numeric_cols
            self.target = None
            
        print(f"数据集形状: {self.data.shape}")
        print(f"数值型特征数量: {len(self.features)}")
        if self.target is not None:
            print(f"目标变量: {target_col}")
    
    # 这个函数叫 detect_highly_correlated_features
    # 作用：计算所有特征两两之间的相关系数，筛选出超过你设定阈值的特征对
    # 默认阈值 0.95：相关系数≥0.95，说明两个特征极度相似、信息冗余，建模时需要删一个！
    def detect_highly_correlated_features(self, threshold=0.90):
        """检测高度相关的特征（线性冗余）"""
        print("\n" + "="*50)
        print(f"2. 高度相关特征检测 (阈值: {threshold})")
        print("="*50)
        
        # self.data[self.features]：取出数据里所有用于分析的特征列
        # .corr()：pandas 内置函数，计算皮尔逊相关系数矩阵
        # 输出一个方形表格：行 = 特征，列 = 特征，格子里是两个特征的相关系数
        # .abs()：取绝对值
        corr_matrix = self.data[self.features].corr().abs()
        # 相关系数矩阵有两个问题：
        # 对角线全是 1（特征自己和自己的相关系数，毫无意义）
        # 矩阵是对称的（A 和 B 的系数 = B 和 A 的系数，会重复统计）
        # corr_matrix.shape,作用：获取相关矩阵的大小(形状)
        # np.ones(corr_matrix.shape),生成一个和相关矩阵一模一样大的全 1 矩阵
        # np.triu( ... , k=1)
        # triu = 上三角函数（triangle upper）
        # k=1 = 跳过主对角线，只保留对角线上方的数字
        # .astype(bool)把数字转成布尔值（True/False）,最后得到一个布尔值蒙版
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        
        high_corr_pairs = []
        for col in upper.columns:
            for row in upper.index:
                if upper.loc[row, col] > threshold:
                    high_corr_pairs.append((row, col, upper.loc[row, col]))
        
        if high_corr_pairs:
            print(f"发现 {len(high_corr_pairs)} 对高度相关的特征:")
            for pair in high_corr_pairs:
                print(f"  - {pair[0]} 和 {pair[1]}: 相关系数 = {pair[2]:.4f}")
            return high_corr_pairs
        else:
            print(f"未发现相关系数超过 {threshold} 的特征对")
            return []
    # 计算每个特征的「方差膨胀因子 (VIF)」，判断它是否能被其他所有特征线性组合出来，
    # 从而检测出隐藏的多重共线性。
    def calculate_vif(self, threshold=10.0):
        """计算方差膨胀因子(VIF)检测多重共线性"""
        print("\n" + "="*50)
        print(f"3. 多重共线性分析 (VIF阈值: {threshold})")
        print("="*50)

        # scaler = StandardScaler()：创建标准化器
        # scaled_data = scaler.fit_transform(...)：对所有特征列进行标准化
        # scaled_df = pd.DataFrame(...)：把标准化后的数组转回 DataFrame，保留列名
        # StandardScaler() 把所有特征变成均值 = 0，方差 = 1的标准正态分布
        # 标准化数据（VIF对尺度敏感）
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(self.data[self.features])
        scaled_df = pd.DataFrame(scaled_data, columns=self.features)
        
        # variance_inflation_factor(X, i)：statsmodels 库的内置函数
        # 输入 1：X = 标准化后的特征矩阵
        # 输入 2：i = 第 i 个特征的索引
        # 输出：第 i 个特征的 VIF 值
        # 列表推导式：遍历所有特征，逐个计算 VIF 值
        # 把结果存入 DataFrame，方便查看和排序
        vif_data = pd.DataFrame()
        vif_data["特征"] = self.features
        vif_data["VIF值"] = [variance_inflation_factor(scaled_df.values, i) 
                           for i in range(scaled_df.shape[1])]
        # sort_values("VIF值", ascending=False)：按 VIF 值从高到低排序
        # → 最严重的共线性特征排在最前面，优先处理
        # reset_index(drop=True)：重置索引，让表格更整洁
        vif_data = vif_data.sort_values("VIF值", ascending=False).reset_index(drop=True)
        
        high_vif_features = vif_data[vif_data["VIF值"] > threshold]
        
        print("所有特征的VIF值:")
        print(vif_data.to_string(index=False))
        
        if not high_vif_features.empty:
            print(f"\n发现 {len(high_vif_features)} 个存在严重多重共线性的特征 (VIF > {threshold}):")
            print(high_vif_features.to_string(index=False))
        else:
            print(f"\n所有特征的VIF值均低于 {threshold}，多重共线性不明显")
        
        return vif_data
    

    # 同时计算每个特征与目标变量的「线性相关性」和「单调相关性」，
    # 并通过统计学检验判断相关性是否真实存在（不是偶然）。
    def analyze_feature_target_correlation(self):
        """分析特征与目标变量的相关性"""
        if self.target is None:
            print("\n未指定目标变量，跳过特征-目标相关性分析")
            return None
        
        print("\n" + "="*50)
        print("4. 特征与目标变量的相关性分析")
        print("="*50)
        
        # 计算三种相关系数
        corr_results = pd.DataFrame()
        corr_results["特征"] = self.features
        
        # 皮尔逊相关系数（线性相关）
        pearson_corr = []
        pearson_p = []
        for col in self.features:
            corr, p = stats.pearsonr(self.data[col], self.target)
            pearson_corr.append(corr)
            pearson_p.append(p)
        
        corr_results["皮尔逊相关系数"] = pearson_corr
        corr_results["皮尔逊p值"] = pearson_p
        
        # 斯皮尔曼相关系数（单调相关，对异常值不敏感）
        spearman_corr = []
        spearman_p = []
        for col in self.features:
            corr, p = stats.spearmanr(self.data[col], self.target)
            spearman_corr.append(corr)
            spearman_p.append(p)
        
        corr_results["斯皮尔曼相关系数"] = spearman_corr
        corr_results["斯皮尔曼p值"] = spearman_p
        
        # 按皮尔逊相关系数绝对值排序
        corr_results["相关系数绝对值"] = corr_results["皮尔逊相关系数"].abs()
        corr_results = corr_results.sort_values("相关系数绝对值", ascending=False).reset_index(drop=True)
        
        # 标记显著相关的特征（p < 0.05）
        significant_features = corr_results[corr_results["皮尔逊p值"] < 0.05]
        
        print("特征与目标变量的相关性结果（按皮尔逊相关系数绝对值排序）:")
        print(corr_results[["特征", "皮尔逊相关系数", "皮尔逊p值", "斯皮尔曼相关系数"]].to_string(index=False))
        
        if not significant_features.empty:
            print(f"\n发现 {len(significant_features)} 个与目标变量显著相关的特征 (p < 0.05):")
            print(significant_features[["特征", "皮尔逊相关系数", "皮尔逊p值"]].to_string(index=False))
        else:
            print("\n未发现与目标变量显著相关的特征 (p < 0.05)")
        
        return corr_results
    
    def plot_correlation_heatmap(self, figsize=(12, 10)):
        """绘制特征间相关性热力图"""
        print("\n" + "="*50)
        print("5. 特征间相关性热力图")
        print("="*50)
        
        plt.figure(figsize=figsize)
        corr_matrix = self.data[self.features].corr()
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        
        sns.heatmap(corr_matrix, mask=mask, annot=True, fmt=".2f", cmap="coolwarm", 
                   center=0, square=True, linewidths=.5, cbar_kws={"shrink": .8})
        plt.title("特征间皮尔逊相关性热力图", fontsize=15)
        plt.tight_layout()
        
        
    
    def plot_feature_target_correlation(self, top_n=10, figsize=(12, 8)):
        """绘制特征与目标变量的相关性条形图"""
        if self.target is None:
            return
        
        print("\n" + "="*50)
        print(f"6. 特征与目标变量相关性Top {top_n} 条形图")
        print("="*50)
        
        corr_results = self.analyze_feature_target_correlation()
        if corr_results is None:
            return
        
        top_features = corr_results.head(top_n)
        
        plt.figure(figsize=figsize)
        colors = ['red' if x < 0 else 'green' for x in top_features["皮尔逊相关系数"]]
        sns.barplot(x="皮尔逊相关系数", y="特征", data=top_features, palette=colors)
        plt.title(f"与目标变量 '{self.target_col}' 相关性Top {top_n} 的特征", fontsize=15)
        plt.xlabel("皮尔逊相关系数", fontsize=12)
        plt.ylabel("特征", fontsize=12)
        plt.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
        plt.tight_layout()
        
    
    def run_full_analysis(self, corr_threshold=0.95, vif_threshold=10.0, top_n=10):
        """运行完整的特征分析流程"""
        print("开始特征数据冗余性与相关性分析...")
        
   
        
        # 2. 高度相关特征检测
        self.detect_highly_correlated_features(threshold=corr_threshold)
        
        # 3. 多重共线性分析(VIF)
        self.calculate_vif(threshold=vif_threshold)
        
        # 4. 特征与目标变量相关性分析
        if self.target is not None:
            self.analyze_feature_target_correlation()
        
        # 5. 可视化
        self.plot_correlation_heatmap()
        
        if self.target is not None:
            self.plot_feature_target_correlation(top_n=top_n)
        
        print("\n" + "="*50)
        print("分析完成！")
        print("="*50)
        
        # 给出建议
        print("\n建议:")
        print(f"2. 对于相关系数超过 {corr_threshold} 的特征对，考虑删除其中一个或进行特征融合")
        print(f"3. 对于VIF值超过 {vif_threshold} 的特征，存在严重多重共线性，建议逐步删除VIF最高的特征")
        print("4. 优先保留与目标变量相关性高且p值小的特征")
        print("5. 注意区分线性相关和非线性相关，斯皮尔曼系数可用于检测单调关系")

        plt.show()

# ------------------- 使用示例 -------------------
if __name__ == "__main__":
    # 示例1：使用内置的波士顿房价数据集（注意：sklearn 1.2+已移除，可使用fetch_california_housing）
    from sklearn.datasets import fetch_california_housing
    
    # 加载数据
    
    df = pd.read_csv("C:/Users/MECHREVO/Desktop/machine-learning/datasets/清洗后数据.csv")
    
    # 创建分析器
    analyzer = FeatureAnalyzer(df, target_col='MEDV')
    
    # 运行完整分析
    analyzer.run_full_analysis(
        corr_threshold=0.8,   # 高度相关阈值
        vif_threshold=8,   # VIF阈值
        top_n=3               # 显示相关性Top N的特征
    )
    
    # 示例2：使用你自己的CSV文件
    # df = pd.read_csv("your_data.csv")
    # analyzer = FeatureAnalyzer(df, target_col="your_target_column")
    # analyzer.run_full_analysis()

# 五、建模建议
# 1. 模型选择：不要用简单的线性回归！因为存在大量非线性关系，推荐使用随机森林、XGBoost、LightGBM等树模型
# 2. 特征处理：
# ◦ 保留 MedInc 作为核心特征
# ◦ 对 AveRooms 和 AveOccup 进行非线性变换（如取对数、平方）
# ◦ 可以将 AveBedrms 和 AveRooms 结合，计算 "卧室数占总房间数的比例" 这个新特征
# 3. 特征筛选：
# ◦ 不要删除任何特征，所有特征都显著相关
# ◦ 虽然 Population 相关性很低，但可以先保留，让模型自己判断是否有用
# 4. 多重共线性处理：
# ◦ 之前的 VIF 分析应该会显示 AveRooms 和 AveBedrms 有一定的共线性
# ◦ 可以考虑删除其中一个，或者用主成分分析降维    