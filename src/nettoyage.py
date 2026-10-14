"""
nettoyage.py
------------
Nettoyage des valeurs manquantes dans la base SQLite `adventureworks.db`,
directement en SQL (approche ELT : Transform in-place dans la base).

Principe :
- Colonnes clés étrangères (FK) avec NULL significatif -> ON NE TOUCHE PAS
  (le NULL est un état métier valide, ex: personid NULL = client "Store").
- Colonnes 100% vides ou sans valeur analytique -> SUPPRESSION.
- Colonnes numériques avec règle métier claire -> remplissage par une valeur fixe (0).
- Colonnes catégorielles descriptives -> remplissage par 'Unknown' (placeholder,
  pas une estimation statistique, donc aucun risque de fuite de données pour le ML).
- Colonnes numériques susceptibles d'être utilisées en Machine Learning (ex: weight)
  -> NON TRAITÉES ICI. L'imputation statistique (moyenne/médiane) doit être faite
  plus tard, dans le pipeline ML, après le split train/test, pour éviter le data leakage.

Exécuter après import_csv.py, avant export_clean_parquet.py.
"""

import sqlite3

DB_PATH = "database/adventureworks.db"


def get_columns(cur, table):
    cur.execute(f"PRAGMA table_info({table});")
    return [row[1] for row in cur.fetchall()]


def drop_column_if_exists(cur, table, column):
    cols = get_columns(cur, table)
    if column in cols:
        cur.execute(f"ALTER TABLE {table} DROP COLUMN {column};")
        print(f"  [DROP]   {table}.{column}")
    else:
        print(f"  [SKIP]   {table}.{column} (déjà absente)")


# ============================================================
# 1. Suppression des colonnes sans valeur analytique
#    (100% vides, ou taux de remplissage quasi nul, non-FK)
# ============================================================
def supprimer_colonnes_inutiles(cur):
    print("\n--- 1. Suppression des colonnes inutiles ---")
    drop_column_if_exists(cur, "SalesOrderHeader", "comment")            # 100% NULL
    drop_column_if_exists(cur, "Product", "discontinueddate")            # 100% NULL
    drop_column_if_exists(cur, "Person", "title")                        # 94.9% NULL
    drop_column_if_exists(cur, "Person", "suffix")                       # 99.7% NULL
    drop_column_if_exists(cur, "Person", "additionalcontactinfo")        # 99.9% NULL
    drop_column_if_exists(cur, "Vendor", "purchasingwebserviceurl")      # 94.2% NULL

    # rowguid : identifiant de réplication SQL Server, aucune valeur analytique,
    # présent dans toutes les tables qui en ont une -> suppression systématique
    tables_toutes = [
        "Customer", "Person", "Product", "ProductVendor", "SalesOrderDetail",
        "SalesOrderHeader", "Vendor", "ProductSubcategory", "ProductCategory",
        "PurchaseOrderHeader", "PurchaseOrderDetail", "ProductInventory",
        "Location", "SalesTerritory", "ShipMethod",
    ]
    for table in tables_toutes:
        drop_column_if_exists(cur, table, "rowguid")

    # modifieddate : date technique de dernière modification (réplication),
    # sans lien avec les dates métier (orderdate, shipdate...) -> suppression
    # systématique, cohérente avec le traitement de rowguid ci-dessus
    for table in tables_toutes:
        drop_column_if_exists(cur, table, "modifieddate")


# ============================================================
# 2. Règles métier : NULL numérique = état métier connu (0)
# ============================================================
def remplir_valeurs_metier(cur):
    print("\n--- 2. Remplissage règles métier ---")
    # onorderqty NULL = pas de commande en cours -> 0
    cur.execute("UPDATE ProductVendor SET onorderqty = 0 WHERE onorderqty IS NULL;")
    print(f"  [FILL 0] ProductVendor.onorderqty ({cur.rowcount} lignes)")


# ============================================================
# 3. Colonnes catégorielles descriptives -> placeholder 'Unknown'
#    (pas une estimation statistique -> aucun risque de data leakage)
# ============================================================
def remplir_categorielles(cur):
    print("\n--- 3. Remplissage catégoriel (placeholder 'Unknown') ---")

    product_cols = [
        "color", "size", "sizeunitmeasurecode",
        "weightunitmeasurecode", "productline", "class", "style",
    ]
    for col in product_cols:
        cur.execute(f"UPDATE Product SET {col} = 'Unknown' WHERE {col} IS NULL;")
        print(f"  [FILL Unknown] Product.{col} ({cur.rowcount} lignes)")

    cur.execute(
        "UPDATE SalesOrderDetail SET carriertrackingnumber = 'Unknown' "
        "WHERE carriertrackingnumber IS NULL;"
    )
    print(f"  [FILL Unknown] SalesOrderDetail.carriertrackingnumber ({cur.rowcount} lignes)")


# ============================================================
# 4. Colonnes volontairement NON traitées ici (documentation)
# ============================================================
def colonnes_non_traitees():
    print("\n--- 4. Colonnes volontairement non modifiées ---")
    non_traitees = {
        "Customer.personid / storeid": "FK, NULL = type de client (Individual vs Store)",
        "Person.middlename": "NULL = pas de deuxième prénom, valeur métier normale",
        "Product.productsubcategoryid / productmodelid": "FK vers ProductSubcategory/ProductModel",
        "Product.sellenddate": "NULL = produit toujours en vente actuellement",
        "Product.weight": "Numérique -> imputation statistique réservée à l'étape ML "
                           "(après split train/test, pour éviter le data leakage)",
        "SalesOrderHeader.purchaseordernumber / salespersonid": "NULL = commande en ligne "
                           "(voir onlineorderflag, déjà présent nativement)",
        "SalesOrderHeader.creditcardid / creditcardapprovalcode": "NULL = paiement hors carte bancaire",
        "SalesOrderHeader.currencyrateid": "NULL = pas de conversion de devise nécessaire",
    }
    for col, reason in non_traitees.items():
        print(f"  [KEEP]   {col} -> {reason}")


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    supprimer_colonnes_inutiles(cur)
    remplir_valeurs_metier(cur)
    remplir_categorielles(cur)
    colonnes_non_traitees()
    conn.commit()
    conn.close()
    print("\nNettoyage terminé. Base mise à jour :", DB_PATH)


if __name__ == "__main__":
    main()
