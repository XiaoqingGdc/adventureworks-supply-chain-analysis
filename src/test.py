import pandas as pd
df = pd.read_csv(r"C:\Projets_Data\ProjetFinal\csv_avec_entetes\ProductInventory.csv")
print("总行数：", len(df))
print("shelf 非空数量：", df['shelf'].notna().sum())
print("shelf 空值数量：", df['shelf'].isna().sum())
print("shelf 空字符串数量：", (df['shelf'] == '').sum())