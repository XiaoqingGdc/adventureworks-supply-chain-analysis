1.手动下载 保存到文件夹raw_data里 (原始CSV) 链接:https://github.com/microsoft/sql-server-samples/tree/master/samples/databases/adventure-works/oltp-install-script
    ↓
2. addHeaders.py       加表头 + 分号分隔

3. supprimer_valeurnull.py (对原来的nettyage.py进行优化)  
 ↓
    去掉缺失值到clean_data 文佳夹里，类型CSV
    ↓
4. createbdd.py        建表 + PK/FK 约束
    ↓
5. importCsv.py        导入clean_data 文佳夹里15个csv文件，含表头，空值为 null，然后建立了一个数据库(Sqlite)
    ↓
adventureworks.db     ★ 数据仓库完成 ★
    ↓      
    
6. 建立一个fastAPI把数据库给别人看   需要生成一个creatAPI.py
        ↓
7.从数据库用 export_clean_parquet.py 导出 15 个干净 类型为.parquet 为powerbi 做准备，存到parquet_for_powerbi文件夹里
    ↓
parquet_for_powerbi/*.parquet
    ↓
8. Power BI → 获取数据 → 从parquet_for_powerbi文件夹里的15个parquet类型导入
    ↓
✅ 数字列正常, 空值为 null, 无 ABC