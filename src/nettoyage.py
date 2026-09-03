"""
Projet AdventureWorks — Script de NETTOYAGE des donnees (etape 1/2)
CSV brut (separateur Tab, sans en-tete) -> Nettoyage -> CSV nettoye avec en-tete

Ce script ne fait QUE le nettoyage. Le chargement en base est gere
separement par chargement.py.

A modifier avant utilisation :
1. PROJECT_DIR : chemin local racine du projet (contient raw_data, clean_data, src...)

Structure attendue :
    PROJECT_DIR/
    ├── raw_data/{achat,produit,vente}/*.csv   (entree, sans en-tete)
    └── clean_data/*.csv                        (sortie, avec en-tete)
"""

import pandas as pd
import os

# ========== Configuration ==========
PROJECT_DIR = r"C:\Projets_Data\ProjetFinal"
BASE_DIR = os.path.join(PROJECT_DIR, "raw_data")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "clean_data")

FOLDERS = {
    "achat": "purchasing",
    "produit": "production",
    "vente": "sales",
}

# ========== Definition des colonnes pour chaque table (ordre officiel instawdb.sql) ==========
COLUMNS = {
    # --- Purchasing ---
    "Vendor": ["businessentityid", "accountnumber", "name", "creditrating",
               "preferredvendorstatus", "activeflag", "purchasingwebserviceurl", "modifieddate"],
    "ShipMethod": ["shipmethodid", "name", "shipbase", "shiprate", "rowguid", "modifieddate"],
    "ProductVendor": ["productid", "businessentityid", "averageleadtime", "standardprice",
                       "lastreceiptcost", "lastreceiptdate", "minorderqty", "maxorderqty",
                       "onorderqty", "unitmeasurecode", "modifieddate"],
    "PurchaseOrderHeader": ["purchaseorderid", "revisionnumber", "status", "employeeid",
                             "vendorid", "shipmethodid", "orderdate", "shipdate", "subtotal",
                             "taxamt", "freight", "totaldue", "modifieddate"],
    "PurchaseOrderDetail": ["purchaseorderid", "purchaseorderdetailid", "duedate", "orderqty",
                             "productid", "unitprice", "linetotal", "receivedqty", "rejectedqty",
                             "stockedqty", "modifieddate"],

    # --- Production ---
    "Product": ["productid", "name", "productnumber", "makeflag", "finishedgoodsflag",
                "color", "safetystocklevel", "reorderpoint", "standardcost", "listprice",
                "size", "sizeunitmeasurecode", "weightunitmeasurecode", "weight",
                "daystomanufacture", "productline", "class", "style", "productsubcategoryid",
                "productmodelid", "sellstartdate", "sellenddate", "discontinueddate",
                "rowguid", "modifieddate"],
    "ProductInventory": ["productid", "locationid", "shelf", "bin", "quantity",
                          "rowguid", "modifieddate"],
    "Location": ["locationid", "name", "costrate", "availability", "modifieddate"],

    # --- Sales ---
    "Customer": ["customerid", "personid", "storeid", "territoryid", "accountnumber",
                 "rowguid", "modifieddate"],
    "Person": ["businessentityid", "persontype", "namestyle", "title", "firstname",
               "middlename", "lastname", "suffix", "emailpromotion",
               "additionalcontactinfo", "demographics", "rowguid", "modifieddate"],
    "SalesOrderDetail": ["salesorderid", "salesorderdetailid", "carriertrackingnumber",
                          "orderqty", "productid", "specialofferid", "unitprice",
                          "unitpricediscount", "linetotal", "rowguid", "modifieddate"],
    "SalesOrderHeader": ["salesorderid", "revisionnumber", "orderdate", "duedate", "shipdate",
                          "status", "onlineorderflag", "purchaseordernumber", "accountnumber",
                          "customerid", "salespersonid", "territoryid", "billtoaddressid",
                          "shiptoaddressid", "shipmethodid", "creditcardid",
                          "creditcardapprovalcode", "currencyrateid", "subtotal", "taxamt",
                          "freight", "totaldue", "comment", "rowguid", "modifieddate"],
    "SalesTerritory": ["territoryid", "name", "countryregioncode", "group", "salesytd",
                        "saleslastyear", "costytd", "costlastyear", "rowguid", "modifieddate"],
}

# Colonnes de type date pour chaque table (conversion en datetime lors du nettoyage)
DATE_COLUMNS = {
    "Vendor": ["modifieddate"],
    "ShipMethod": ["modifieddate"],
    "ProductVendor": ["lastreceiptdate", "modifieddate"],
    "PurchaseOrderHeader": ["orderdate", "shipdate", "modifieddate"],
    "PurchaseOrderDetail": ["duedate", "modifieddate"],
    "Product": ["sellstartdate", "sellenddate", "discontinueddate", "modifieddate"],
    "ProductInventory": ["modifieddate"],
    "Location": ["modifieddate"],
    "Customer": ["modifieddate"],
    "Person": ["modifieddate"],
    "SalesOrderDetail": ["modifieddate"],
    "SalesOrderHeader": ["orderdate", "duedate", "shipdate", "modifieddate"],
    "SalesTerritory": ["modifieddate"],
}

# Tables necessitant un separateur different du Tab standard
SPECIAL_SEPARATORS = {
    "Person": r"\+\|",
}


# ========== Lecture d'une table brute ==========
def load_table(folder_path: str, table_name: str) -> pd.DataFrame:
    """Lit un fichier CSV brut selon les noms de colonnes officiels."""
    filepath = os.path.join(folder_path, f"{table_name}.csv")
    cols = COLUMNS[table_name]

    if table_name in SPECIAL_SEPARATORS:
        df = pd.read_csv(filepath, sep=SPECIAL_SEPARATORS[table_name],
                          header=None, names=cols, engine="python")
    else:
        df = pd.read_csv(filepath, sep="\t", header=None, names=cols)

    for col in DATE_COLUMNS.get(table_name, []):
        df[col] = pd.to_datetime(df[col], errors="coerce")

    return df


# ========== Fonctions de nettoyage specifiques par table ==========
def clean_vendor(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop(columns=["purchasingwebserviceurl"], errors="ignore")
    return df


def clean_purchase_order_detail(df: pd.DataFrame) -> pd.DataFrame:
    df["linetotal"] = df["linetotal"].fillna(df["orderqty"] * df["unitprice"])
    df["stockedqty"] = df["stockedqty"].fillna(df["receivedqty"] - df["rejectedqty"])
    return df


def clean_sales_order_detail(df: pd.DataFrame) -> pd.DataFrame:
    df["linetotal"] = df["linetotal"].fillna(
        df["unitprice"] * (1 - df["unitpricediscount"]) * df["orderqty"]
    )
    return df


def clean_product_vendor(df: pd.DataFrame) -> pd.DataFrame:
    df["onorderqty"] = df["onorderqty"].fillna(0)
    df["lastreceiptcost"] = df["lastreceiptcost"].fillna(0)
    return df


def clean_purchase_order_header(df: pd.DataFrame) -> pd.DataFrame:
    # Filtre optionnel : ne garder que les commandes terminees (Status = 4)
    # df = df[df["status"] == 4]
    return df


def clean_person(df: pd.DataFrame) -> pd.DataFrame:
    df["modifieddate"] = df["modifieddate"].astype(str).str.replace(r"&\|", "", regex=True)
    df["modifieddate"] = pd.to_datetime(df["modifieddate"], errors="coerce")
    df = df.drop(columns=["additionalcontactinfo", "demographics"], errors="ignore")
    return df


def clean_product_inventory(df: pd.DataFrame) -> pd.DataFrame:
    # ~27% de valeurs manquantes sur "shelf" (NOT NULL dans le schema officiel) ;
    # comble avec un placeholder plutot que de supprimer les lignes, pour ne pas
    # perdre les quantites en stock (colonne "quantity", bien renseignee).
    df["shelf"] = df["shelf"].fillna("N/A")
    return df


CLEAN_FUNCTIONS = {
    "Vendor": clean_vendor,
    "PurchaseOrderDetail": clean_purchase_order_detail,
    "SalesOrderDetail": clean_sales_order_detail,
    "ProductVendor": clean_product_vendor,
    "PurchaseOrderHeader": clean_purchase_order_header,
    "ProductInventory": clean_product_inventory,
    "Person": clean_person,
}


def clean_table(table_name: str, df: pd.DataFrame) -> pd.DataFrame:
    func = CLEAN_FUNCTIONS.get(table_name)
    if func:
        df = func(df)
    return df


# ========== Ecriture du CSV nettoye (avec en-tete) ==========
def write_cleaned_csv(df: pd.DataFrame, table_name: str):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"{table_name}.csv")
    df.to_csv(out_path, index=False)
    print(f"  OK {table_name} nettoye -> {out_path} ({len(df)} lignes)")


# ========== Processus principal ==========
def main():
    for folder_fr, schema_en in FOLDERS.items():
        folder_path = os.path.join(BASE_DIR, folder_fr)
        print(f"\nDossier : {folder_fr} ({schema_en})")

        for table_name in COLUMNS:
            csv_path = os.path.join(folder_path, f"{table_name}.csv")
            if not os.path.exists(csv_path):
                continue  # Cette table n'appartient pas a ce dossier

            df = load_table(folder_path, table_name)
            df = clean_table(table_name, df)
            write_cleaned_csv(df, table_name)

    print(f"\nNettoyage termine. CSV nettoyes dans : {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
