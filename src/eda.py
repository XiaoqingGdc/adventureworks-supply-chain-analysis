import pandas as pd

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 150)


# =====================================================================
# 1. Diagnostic basique — à exécuter sur chaque table
# =====================================================================
def diagnostic_basique(nom_fichier, df):
    print(f"\n{'='*60}")
    print(f"📋 {nom_fichier}")
    print(f"{'='*60}")
    print(f"Dimensions : {df.shape[0]} lignes, {df.shape[1]} colonnes")

    # Valeurs manquantes
    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]
    if len(nulls) > 0:
        pct = (nulls / len(df) * 100).round(1)
        print(f"\n⚠️ Valeurs manquantes :")
        for col in nulls.index:
            print(f"   {col} : {nulls[col]} ({pct[col]}%)")
    else:
        print("\n✅ Aucune valeur manquante")

    # Lignes dupliquées
    doublons = df.duplicated().sum()
    if doublons > 0:
        print(f"\n⚠️ Lignes dupliquées : {doublons}")
    else:
        print("✅ Aucun doublon")

    # Types de données
    print(f"\nTypes de données :")
    print(df.dtypes.to_string())


# =====================================================================
# 2. Vérification d'intégrité référentielle (clés étrangères)
# =====================================================================
def verifier_cle_etrangere(df_enfant, col_enfant, df_parent, col_parent, nom_relation):
    ids_enfant = set(df_enfant[col_enfant].dropna())
    ids_parent = set(df_parent[col_parent].dropna())
    orphelins = ids_enfant - ids_parent
    if orphelins:
        print(f"⚠️ {nom_relation} : {len(orphelins)} valeurs orphelines "
              f"(présentes dans l'enfant, absentes du parent)")
        print(f"   Exemples : {list(orphelins)[:5]}")
    else:
        print(f"✅ {nom_relation} : intégrité référentielle OK")


# =====================================================================
# 3. Vérifications de cohérence logique
# =====================================================================
def verifier_dates_coherentes(df, col_debut, col_fin, nom_table):
    d1 = pd.to_datetime(df[col_debut], errors="coerce")
    d2 = pd.to_datetime(df[col_fin], errors="coerce")
    incoherentes = df[d2 < d1]
    if len(incoherentes) > 0:
        print(f"⚠️ {nom_table} : {len(incoherentes)} lignes où {col_fin} < {col_debut}")
    else:
        print(f"✅ {nom_table} : dates cohérentes ({col_debut} <= {col_fin})")


def verifier_valeurs_negatives(df, colonne, nom_table):
    valeurs = pd.to_numeric(df[colonne], errors="coerce")
    negatives = df[valeurs < 0]
    if len(negatives) > 0:
        print(f"⚠️ {nom_table}.{colonne} : {len(negatives)} valeurs négatives")
    else:
        print(f"✅ {nom_table}.{colonne} : aucune valeur négative")


def verifier_linetotal(df, col_qty, col_price, col_total, nom_table, tolerance=0.01):
    calcule = df[col_qty] * df[col_price]
    ecart = (calcule - df[col_total]).abs()
    incoherentes = df[ecart > tolerance]
    if len(incoherentes) > 0:
        print(f"⚠️ {nom_table} : {len(incoherentes)} lignes où {col_qty} x {col_price} != {col_total}")
    else:
        print(f"✅ {nom_table} : {col_total} cohérent avec {col_qty} x {col_price}")


# =====================================================================
# 4. Diagnostics spécifiques aux 3 axes du projet
# =====================================================================
def diagnostic_fournisseurs(dfs):
    print(f"\n{'#'*60}")
    print("# Diagnostic — Performance fournisseurs")
    print(f"{'#'*60}")

    header = dfs["PurchaseOrderHeader"]
    detail = dfs["PurchaseOrderDetail"]

    # Délai de livraison
    orderdate = pd.to_datetime(header["orderdate"], errors="coerce")
    shipdate = pd.to_datetime(header["shipdate"], errors="coerce")
    delai = (shipdate - orderdate).dt.days
    print("\nDélai de livraison (jours) — statistiques :")
    print(delai.describe().to_string())
    print(f"\n⚠️ Commandes avec délai négatif : {(delai < 0).sum()}")
    print(f"⚠️ Commandes sans date d'expédition (shipdate manquant) : {header['shipdate'].isnull().sum()}")

    # Taux de rejet global
    taux_rejet = detail["rejectedqty"].sum() / detail["orderqty"].sum()
    print(f"\nTaux de rejet global : {taux_rejet:.2%}")

    # Cohérence linetotal
    verifier_linetotal(detail, "orderqty", "unitprice", "linetotal", "PurchaseOrderDetail")


def diagnostic_stocks(dfs):
    print(f"\n{'#'*60}")
    print("# Diagnostic — Rotation des stocks")
    print(f"{'#'*60}")

    product = dfs["Product"]
    inventory = dfs["ProductInventory"]

    print("\nDistribution des quantités en stock :")
    print(inventory["quantity"].describe().to_string())

    produits_sans_stock = set(product["productid"]) - set(inventory["productid"])
    print(f"\n⚠️ Produits sans enregistrement d'inventaire : {len(produits_sans_stock)}")

    merged = product.merge(inventory, on="productid", how="inner")
    sous_seuil = merged[merged["quantity"] < merged["safetystocklevel"]]
    print(f"⚠️ Produits sous le seuil de sécurité (safetystocklevel) : {len(sous_seuil)}")

    verifier_valeurs_negatives(inventory, "quantity", "ProductInventory")


def diagnostic_marge(dfs):
    print(f"\n{'#'*60}")
    print("# Diagnostic — Marge commerciale")
    print(f"{'#'*60}")

    sales = dfs["SalesOrderDetail"]
    product = dfs["Product"]

    merged = sales.merge(product, on="productid", how="inner")
    merged["marge"] = merged["unitprice"] - merged["standardcost"]
    merged["taux_marge"] = merged["marge"] / merged["unitprice"]

    print("\nDistribution du taux de marge :")
    print(merged["taux_marge"].describe().to_string())

    marge_negative = merged[merged["marge"] < 0]
    print(f"\n⚠️ Lignes avec marge négative (vente à perte) : {len(marge_negative)}")

    verifier_linetotal(sales, "orderqty", "unitprice", "linetotal", "SalesOrderDetail")


# =====================================================================
# Programme principal
# =====================================================================
if __name__ == "__main__":
    dossier = "clean_data"
    fichiers = [
        "Vendor", "ProductVendor", "PurchaseOrderHeader", "PurchaseOrderDetail",
        "ShipMethod", "Location", "Product", "ProductInventory",
        "ProductCategory", "ProductSubcategory", "Customer", "Person",
        "SalesOrderHeader", "SalesOrderDetail", "SalesTerritory"
    ]

    dfs = {}
    for f in fichiers:
        try:
            dfs[f] = pd.read_csv(f"{dossier}/{f}.csv", sep=";")
            diagnostic_basique(f, dfs[f])
        except FileNotFoundError:
            print(f"❌ Fichier introuvable : {dossier}/{f}.csv")

    print(f"\n\n{'#'*60}")
    print("# Vérifications d'intégrité référentielle")
    print(f"{'#'*60}\n")

    verifier_cle_etrangere(dfs["PurchaseOrderDetail"], "productid", dfs["Product"], "productid",
                            "PurchaseOrderDetail.productid → Product.productid")
    verifier_cle_etrangere(dfs["SalesOrderDetail"], "productid", dfs["Product"], "productid",
                            "SalesOrderDetail.productid → Product.productid")
    verifier_cle_etrangere(dfs["PurchaseOrderHeader"], "vendorid", dfs["Vendor"], "businessentityid",
                            "PurchaseOrderHeader.vendorid → Vendor.businessentityid")
    verifier_cle_etrangere(dfs["ProductVendor"], "businessentityid", dfs["Vendor"], "businessentityid",
                            "ProductVendor.businessentityid → Vendor.businessentityid")
    verifier_cle_etrangere(dfs["ProductVendor"], "productid", dfs["Product"], "productid",
                            "ProductVendor.productid → Product.productid")
    verifier_cle_etrangere(dfs["Product"], "productsubcategoryid", dfs["ProductSubcategory"], "productsubcategoryid",
                            "Product.productsubcategoryid → ProductSubcategory.productsubcategoryid")
    verifier_cle_etrangere(dfs["ProductSubcategory"], "productcategoryid", dfs["ProductCategory"], "productcategoryid",
                            "ProductSubcategory.productcategoryid → ProductCategory.productcategoryid")
    verifier_cle_etrangere(dfs["Customer"], "personid", dfs["Person"], "businessentityid",
                            "Customer.personid → Person.businessentityid")
    verifier_cle_etrangere(dfs["SalesOrderHeader"], "customerid", dfs["Customer"], "customerid",
                            "SalesOrderHeader.customerid → Customer.customerid")
    verifier_cle_etrangere(dfs["SalesOrderDetail"], "salesorderid", dfs["SalesOrderHeader"], "salesorderid",
                            "SalesOrderDetail.salesorderid → SalesOrderHeader.salesorderid")
    verifier_cle_etrangere(dfs["ProductInventory"], "locationid", dfs["Location"], "locationid",
                            "ProductInventory.locationid → Location.locationid")

    print(f"\n\n{'#'*60}")
    print("# Vérifications de cohérence logique")
    print(f"{'#'*60}\n")

    verifier_dates_coherentes(dfs["PurchaseOrderHeader"], "orderdate", "shipdate", "PurchaseOrderHeader")
    verifier_dates_coherentes(dfs["SalesOrderHeader"], "orderdate", "shipdate", "SalesOrderHeader")
    verifier_dates_coherentes(dfs["SalesOrderHeader"], "orderdate", "duedate", "SalesOrderHeader")

    verifier_valeurs_negatives(dfs["PurchaseOrderDetail"], "linetotal", "PurchaseOrderDetail")
    verifier_valeurs_negatives(dfs["SalesOrderDetail"], "linetotal", "SalesOrderDetail")
    verifier_valeurs_negatives(dfs["Product"], "standardcost", "Product")
    verifier_valeurs_negatives(dfs["Product"], "listprice", "Product")

    # Diagnostics spécifiques aux 3 axes du projet
    diagnostic_fournisseurs(dfs)
    diagnostic_stocks(dfs)
    diagnostic_marge(dfs)

    print(f"\n\n{'#'*60}")
    print("# Diagnostic terminé")
    print(f"{'#'*60}")
