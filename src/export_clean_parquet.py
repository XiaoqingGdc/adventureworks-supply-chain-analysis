"""
export_clean_parquet.py — 从 adventureworks.db 导出15个表给PowerBI用，Parquet版本

跟 export_clean_csv.py 对比说明：
    Parquet是列式存储格式，自带schema（每一列的类型、是否可空都写在文件里），
    所以这一版脚本比CSV版本简单很多——不需要处理：
        - 小数点符号（逗号 vs 句点）  → Parquet不存在这个问题，数字就是数字
        - 空值导出成什么样的字符串    → Parquet有原生的null，不需要 na_rep 这种技巧
        - 假小数点整数列(934.0 vs 934) → 同样用 Int64 可空整数类型处理一次，
          写进Parquet后，PowerBI读到的就是"整数、有缺失"，不会变成文本

    也就是说，fix_fake_float_columns 这个函数原样保留（这个问题跟文件格式无关，
    是pandas从SQLite读取INTEGER+NULL列时的固有行为），但去掉了CSV版本里所有跟
    "文本格式怎么写才能让PowerBI猜对类型"相关的处理（分隔符、小数点、locale）。

    另外新增了 fix_all_null_columns：某一列如果整列都是NULL（比如Product表的
    discontinueddate、SalesOrderHeader表的comment——这两列在这份AdventureWorks
    样本数据里刚好一行都没填），pandas/pyarrow没法从"全空"的内容里推断出具体
    类型，写进Parquet时会被标记成Arrow的null类型。PowerBI的Parquet读取器不认识
    这种类型，会报"L'argument 'dataType' ne peut pas être null"然后直接连接失败。
    解决办法是强制把这类列转成字符串类型，内容依然是空，但至少有明确类型可读。

用法：
    python export_clean_parquet.py
    默认从 adventureworks.db 读出所有表，导出到 parquet_for_powerbi/ 目录
    （跟 csv_for_powerbi/ 是并列的兄弟目录，方便两边导入PowerBI后对比效果）。

依赖：
    pip install pandas pyarrow
"""

import sqlite3
import pandas as pd
from pathlib import Path

# ========== 配置（与CSV版本保持同一套路径习惯，只是output目录名不同）==========
DB_PATH = Path("database/adventureworks.db")
OUTPUT_DIR = Path("parquet_for_powerbi")


def get_table_names(conn: sqlite3.Connection) -> list[str]:
    """读取数据库里所有的表名（排除sqlite自己的内部表）。"""
    query = """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name;
    """
    return [row[0] for row in conn.execute(query).fetchall()]


def fix_fake_float_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    把"本来是整数、只因为有空值被pandas转成float64"的列，
    转换成可空整数类型(Int64)，避免出现 934.0 这种假小数点。

    这一步跟CSV版本完全一样——问题出在pandas从SQLite读数据这一环，
    跟后面导出成什么格式无关，所以两个脚本都需要它。
    """
    for col in df.columns:
        if df[col].dtype == "float64":
            non_null = df[col].dropna()
            # 全部是空值的列，直接跳过（没有信息可判断，保持原样）
            if non_null.empty:
                continue
            # 所有非空值是否都等于自己取整后的结果 → 说明本来就是整数
            is_all_integer = (non_null % 1 == 0).all()
            if is_all_integer:
                df[col] = df[col].astype("Int64")  # 可空整数类型
    return df


def fix_all_null_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    整列全是空值的列（比如discontinueddate、comment这种"预留但没人填"的字段），
    pyarrow写Parquet时会把它推断成null类型，PowerBI读不懂这个类型会直接报错。

    这里强制把这类列转成pandas的string类型——内容还是空(<NA>)，
    但schema里有明确的"这是字符串列"声明，PowerBI就能正常读取（显示为空白）。
    """
    for col in df.columns:
        if df[col].isna().all():
            df[col] = df[col].astype("string")
    return df


def export_table(conn: sqlite3.Connection, table_name: str) -> None:
    """把一张表导出成Parquet，类型和空值都由文件schema自己保证，不需要额外格式处理。"""

    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    df = fix_fake_float_columns(df)
    df = fix_all_null_columns(df)

    out_path = OUTPUT_DIR / f"{table_name}.parquet"
    df.to_parquet(
        out_path,
        index=False,
        engine="pyarrow",
    )

    null_counts = df.isna().sum()
    null_counts = null_counts[null_counts > 0]
    n_nulls = int(null_counts.sum())
    print(f"  [{table_name}] {len(df)} 行, {len(df.columns)} 列, 共 {n_nulls} 个空值 → {out_path.name}")


def main():
    if not DB_PATH.exists():
        print(f"⚠️ 找不到数据库文件：{DB_PATH.resolve()}")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        table_names = get_table_names(conn)

        if not table_names:
            print("⚠️ 数据库里没有找到任何表。")
            return

        print(f"共找到 {len(table_names)} 张表，开始导出到 {OUTPUT_DIR}/ ...\n")

        for table_name in table_names:
            export_table(conn, table_name)

        print(f"\n✅ 导出完成，共 {len(table_names)} 个Parquet文件。")
        print("   类型和空值都由Parquet的schema自带，PowerBI导入时不需要选区域设置，")
        print("   也不需要担心逗号/句点小数点或假小数点整数列的问题。")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
