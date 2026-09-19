共找到 15 张表，开始导出到 parquet_for_powerbi/ ...

  [Customer] 19820 行, 6 列, 共 19185 个空值 → Customer.parquet
  [Location] 14 行, 5 列, 共 0 个空值 → Location.parquet
  [Person] 19972 行, 13 列, 共 67343 个空值 → Person.parquet
  [Product] 504 行, 25 列, 共 3571 个空值 → Product.parquet
  [ProductCategory] 4 行, 4 列, 共 0 个空值 → ProductCategory.parquet
  [ProductInventory] 1069 行, 7 列, 共 0 个空值 → ProductInventory.parquet
  [ProductSubcategory] 37 行, 5 列, 共 0 个空值 → ProductSubcategory.parquet
  [ProductVendor] 460 行, 11 列, 共 305 个空值 → ProductVendor.parquet
  [PurchaseOrderDetail] 8845 行, 10 列, 共 0 个空值 → PurchaseOrderDetail.parquet
  [PurchaseOrderHeader] 4012 行, 13 列, 共 0 个空值 → PurchaseOrderHeader.parquet
  [SalesOrderDetail] 121317 行, 10 列, 共 60398 个空值 → SalesOrderDetail.parquet
  [SalesOrderHeader] 31465 行, 25 列, 共 106534 个空值 → SalesOrderHeader.parquet
  [SalesTerritory] 10 行, 10 列, 共 0 个空值 → SalesTerritory.parquet
  [ShipMethod] 5 行, 6 列, 共 0 个空值 → ShipMethod.parquet
  [Vendor] 104 行, 8 列, 共 98 个空值 → Vendor.parquet

✅ 导出完成，共 15 个Parquet文件。
   类型和空值都由Parquet的schema自带，PowerBI导入时不需要选区域设置，
   也不需要担心逗号/句点小数点或假小数点整数列的问题。