# ===================== 1. 导入依赖库 =====================
import pandas as pd
import matplotlib.pyplot as plt

# 设置中文字体，解决图表中文乱码
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# ===================== 2. 数据预处理主函数 =====================
def data_cleaning(
    df,
    # 缺失值处理参数：drop(删除) / mean(均值) / median(中位数) / mode(众数)
    missing_strategy: str = "drop",
    # 重复值处理参数：first(保留第一条) / last(保留最后一条)
    duplicate_keep: str = "first"
):
    """
    数据清洗：自动检查+处理缺失值、重复值
    :param df: 原始数据框 (pandas.DataFrame)
    :param missing_strategy: 缺失值处理策略
    :param duplicate_keep: 重复值处理策略
    :return: 清洗后的数据框
    """
    # 复制数据，避免修改原始数据
    data = df.copy()
    print("=" * 50)
    print(f"原始数据维度：{data.shape} | 总行数：{data.shape[0]} | 总列数：{data.shape[1]}")
    print("=" * 50)

    # -------------------- 一、缺失值处理 --------------------
    print("\n📌 第一步：缺失值检查与处理")
    # 1. 统计缺失值
    #.isnull():给你的表格逐单元格检查：是不是空值 / 缺失值（比如空白、NaN、None）
    #是缺失值 → 标记为 True
    #不是缺失值 → 标记为 False
    #.sum():计算机里 True=1，False=0
    #对每一列把这些数字加起来 → 得到这一列总共有多少个缺失值
    #是一个列表 / 序列，记录每一列单独的缺失数量
    missing_count = data.isnull().sum()  # 每列缺失数量
    #len(表格)统计的是总行数
    #missing_rate 也是一个序列，每列对应一个独立的缺失率
    missing_rate = missing_count / len(data) * 100  # 缺失占比(%)
    #.round(2):百分比表示保留两位小数
    #ascending=False：关闭升序 = 降序（从大到小：3→2→1）
    #按照缺失数量排序
    missing_info = pd.DataFrame({
        "缺失数量": missing_count,
        "缺失占比(%)": missing_rate.round(2)
    }).sort_values(by="缺失数量", ascending=False)

    # 打印缺失值信息
    print("\n【缺失值统计】")
    print(missing_info[missing_info["缺失数量"] > 0])  # 只显示有缺失的列

    # 2. 可视化缺失值（柱状图）
    if missing_count.sum() > 0:
        plt.figure(figsize=(10, 5))
        missing_count[missing_count > 0].plot(kind="bar", color="#ff6b6b")
        plt.title("各列缺失值数量统计", fontsize=14)
        plt.ylabel("缺失数量", fontsize=12)
        plt.tight_layout()
        plt.show()

    # 3. 处理缺失值
    if missing_strategy == "drop":
        data = data.dropna()
        print(f"\n✅ 缺失值处理：删除所有包含缺失值的行")
    elif missing_strategy == "mean":
        data = data.fillna(data.mean(numeric_only=True))
        print(f"\n✅ 缺失值处理：数值列用均值填充")
    elif missing_strategy == "median":
        data = data.fillna(data.median(numeric_only=True))
        print(f"\n✅ 缺失值处理：数值列用中位数填充")
    elif missing_strategy == "mode":
        data = data.fillna(data.mode().iloc[0])  # 众数填充（支持所有列）
        print(f"\n✅ 缺失值处理：全列用众数填充")
    else:
        raise ValueError("缺失值策略仅支持：drop/mean/median/mode")

    # -------------------- 二、重复值处理 --------------------
    print("\n📌 第二步：重复值检查与处理")
    # 1. 统计重复值
    dup_count = data.duplicated().sum()
    print(f"\n【重复值统计】：共发现 {dup_count} 行重复数据")

    # 2. 查看重复行（如果有）
    if dup_count > 0:
        print("\n【重复行详情】")
        print(data[data.duplicated(keep=False)])

    # 3. 处理重复值
    data = data.drop_duplicates(keep=duplicate_keep, ignore_index=True)
    print(f"\n✅ 重复值处理：删除重复行，保留{duplicate_keep}条")

    # -------------------- 三、清洗完成报告 --------------------
    print("\n" + "=" * 50)
    print(f"清洗完成！数据维度：{data.shape} | 剩余行数：{data.shape[0]}")
    print("=" * 50)

    return data

# ===================== 3. 使用示例 =====================
if __name__ == "__main__":
    # 方式1：加载本地数据（CSV/Excel）
    # df = pd.read_csv("你的数据文件.csv")  # CSV文件
    # df = pd.read_excel("你的数据文件.xlsx")  # Excel文件

    # 方式2：生成模拟测试数据（自带缺失+重复，直接运行测试）
    df = pd.read_csv("C:/Users/MECHREVO/Desktop/machine-learning/datasets/c_l.csv")

    # 调用清洗函数（自定义参数）
    # 策略：缺失值用众数填充 | 重复值保留第一条
    cleaned_df = data_cleaning(
        df=df,
        missing_strategy="mean",
        duplicate_keep="first"
    )

    # 保存清洗后的数据
    cleaned_df.to_csv("C:/Users/MECHREVO/Desktop/machine-learning/datasets/清洗后数据.csv", index=False, encoding="utf-8-sig")
    print("\n💾 清洗后数据已保存为：清洗后数据.csv")