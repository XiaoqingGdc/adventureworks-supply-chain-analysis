"""
Projet AdventureWorks — Script de CHARGEMENT des donnees (etape 2/2)
CSV nettoye (avec en-tete) -> Chargement dans SQLite

Ce script suppose que nettoyage.py a deja ete execute et que les CSV
nettoyes existent dans INPUT_DIR (dates deja au format ISO grace au to_csv
de pandas, donc pas besoin de reconvertir ici).

A modifier avant utilisation :
1. PROJECT_DIR : chemin local racine du projet

Structure attendue :
    PROJECT_DIR/
    ├── clean_data/*.csv        (entree, sortie de nettoyage.py)
    └── database/
        └── adventureworks.db   (sortie, base SQLite generee)
"""

import pandas as pd
import sqlite3
import os

# ========== Configuration ==========
PROJECT_DIR = r"C:\Projets_Data\ProjetFinal"
INPUT_DIR = os.path.join(PROJECT_DIR, "clean_data")
DB_PATH = os.path.join(PROJECT_DIR, "database", "adventureworks.db")

# Liste des tables a charger, dans un ordre qui respecte les dependances
# de cles etrangeres (tables parentes avant tables enfants)
TABLES = [
    "Vendor", "ShipMethod", "Location", "SalesTerritory",
    "Person", "Customer",
    "Product", "ProductInventory", "ProductVendor",
    "PurchaseOrderHeader", "PurchaseOrderDetail",
    "SalesOrderHeader", "SalesOrderDetail",
]

# Colonnes de type date pour chaque table (reconversion en datetime avant insertion)
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


def load_cleaned_csv(table_name: str) -> pd.DataFrame:
    """Lit un CSV deja nettoye (avec en-tete)."""
    filepath = os.path.join(INPUT_DIR, f"{table_name}.csv")
    df = pd.read_csv(filepath)

    for col in DATE_COLUMNS.get(table_name, []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df


def write_to_sqlite(df: pd.DataFrame, table_name: str, conn: sqlite3.Connection):
    df.to_sql(table_name.lower(), conn, if_exists="replace", index=False)
    print(f"  OK {table_name.lower()} : {len(df)} lignes chargees")


def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")  # Desactive par defaut dans SQLite

    for table_name in TABLES:
        csv_path = os.path.join(INPUT_DIR, f"{table_name}.csv")
        if not os.path.exists(csv_path):
            print(f"  SKIP {table_name} : fichier introuvable dans {INPUT_DIR}")
            continue

        df = load_cleaned_csv(table_name)
        write_to_sqlite(df, table_name, conn)

    conn.close()
    print(f"\nChargement termine. Base de donnees : {DB_PATH}")


if __name__ == "__main__":
    main()
