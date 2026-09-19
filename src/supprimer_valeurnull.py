"""
nettoyage.py — 清洗 clean_data 下的15个CSV文件
目标：把所有"看起来是空"的值（空字符串、NULL、N/A、NaN 等）统一转换成
      真正的空值（pandas 的 NaN → 写出时为空字符串），而不是用 "N/A" 这种
      文本去填充。

原因：
    之前的做法是"文本列填N/A，数字列保留空"。但如果某个数字列里混进了
    "N/A" 这种字符串，PowerBI 在推断该列类型时会认为整列是文本(ABC)，
    而不是数字(123)。为了避免这个问题，这里统一策略：
        - 不管是文本列还是数字列，缺失值一律变成 NaN
        - 导出时 NaN 会被写成空字符串（""），在CSV里就是"空"
        - 到PowerBI导入时，数字列会被正确识别为数字类型，空值显示为null

用法：
    python nettoyage.py
    默认会处理 clean_data/ 目录下的所有 .csv 文件（15个表）。
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ========== 配置 ==========
CLEAN_DATA_DIR = Path("clean_data")   # ①addHeaders.py 的输出目录，也是本脚本的输入/输出目录
CSV_SEP = ";"                          # 项目统一用分号分隔（兼容法语版Excel）
ENCODING = "utf-8-sig"                 # 保留BOM，Excel/PowerBI打开时中文/法语字符不乱码

# 会被当作"空值"处理的字符串（不区分大小写），除了pandas默认识别的空值之外
EXTRA_NA_VALUES = [
    "", " ", "NA", "N/A", "n/a", "NULL", "null", "None", "none",
    "NaN", "nan", "#N/A", "-", "--",
]


def clean_one_csv(csv_path: Path) -> None:
    """读取一个CSV，把所有空缺值统一变成真正的NaN，然后原地覆盖写回。"""

    # 读取时全部按字符串读入，避免pandas提前把某些列自动推断成float
    # （这样我们才能完全控制"什么算空值"，不受pandas自动类型推断干扰）
    df = pd.read_csv(
        csv_path,
        sep=CSV_SEP,
        encoding=ENCODING,
        dtype=str,
        keep_default_na=True,   # 保留pandas默认的空值识别（如空字符串）
        na_values=EXTRA_NA_VALUES,
    )

    # 保险起见，再显式做一次：去掉每个字符串两端空格后，如果结果在
    # EXTRA_NA_VALUES里，也统一替换为真正的NaN
    def normalize(val):
        if pd.isna(val):
            return np.nan
        val_stripped = str(val).strip()
        if val_stripped in EXTRA_NA_VALUES:
            return np.nan
        return val_stripped

    df = df.apply(lambda col: col.map(normalize))

    # 统计一下这个文件里每列的空值数量，方便你核对
    null_counts = df.isna().sum()
    null_counts = null_counts[null_counts > 0]
    if not null_counts.empty:
        print(f"  [{csv_path.name}] 空值统计:")
        for col, cnt in null_counts.items():
            print(f"      - {col}: {cnt} 个空值")
    else:
        print(f"  [{csv_path.name}] 无空值")

    # 写回：NaN会被写成空字符串，也就是真正的"空"
    df.to_csv(
        csv_path,
        sep=CSV_SEP,
        encoding=ENCODING,
        index=False,
        na_rep="",   # 关键：空值导出为空字符串，而不是"N/A"或"nan"
    )


def main():
    csv_files = sorted(CLEAN_DATA_DIR.glob("*.csv"))

    if not csv_files:
        print(f"⚠️ 在 {CLEAN_DATA_DIR.resolve()} 下没有找到任何CSV文件，请检查路径。")
        return

    print(f"共找到 {len(csv_files)} 个CSV文件，开始清洗...\n")

    for csv_path in csv_files:
        clean_one_csv(csv_path)

    print(f"\n✅ 清洗完成，共处理 {len(csv_files)} 个文件。")
    print("   所有空缺值已统一为真正的空值（NULL），可以安全导入PowerBI了。")


if __name__ == "__main__":
    main()