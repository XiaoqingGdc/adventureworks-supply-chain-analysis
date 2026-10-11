"""
Export des tables SQLite (adventureworks.db) vers des fichiers Parquet pour Power BI.

Seules les tables utilisées par le modèle Power BI sont exportées (TABLES_POWERBI).
Tables exclues :
    - Person     : données personnelles non nécessaires à l'analyse (RGPD, minimisation, art. 5.1.c)
    - ShipMethod : modes de livraison non utilisés dans le dashboard
Le fichier vendor_segments.parquet est produit par le notebook ml/clustering_fournisseur.ipynb,
pas par ce script.

Corrections appliquées à chaque table :
    - colonnes float contenant uniquement des entiers  -> Int64
    - colonnes entièrement vides                       -> string
    - colonnes de dates stockées en texte              -> datetime

dependencies: pandas, pyarrow
    pip install pandas pyarrow
"""

import sqlite3
import pandas as pd
from pathlib import Path


DB_PATH = Path("database/adventureworks.db")
OUTPUT_DIR = Path("parquet_for_powerbi")

# Tables chargées dans Power BI (le choix des colonnes est fait dans Power Query)
TABLES_POWERBI = [
    "Customer",
    "Location",
    "Product",
    "ProductCategory",
    "ProductInventory",
    "ProductSubcategory",
    "ProductVendor",
    "PurchaseOrderDetail",
    "PurchaseOrderHeader",
    "SalesOrderDetail",
    "SalesOrderHeader",
    "SalesTerritory",
    "Vendor",
]


def get_table_names(conn: sqlite3.Connection) -> list[str]:

    query = """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name;
    """
    return [row[0] for row in conn.execute(query).fetchall()]


def fix_fake_float_columns(df: pd.DataFrame) -> pd.DataFrame:

    for col in df.columns:
        if df[col].dtype == "float64":
            non_null = df[col].dropna()

            if non_null.empty:
                continue
            is_all_integer = (non_null % 1 == 0).all()
            if is_all_integer:
                df[col] = df[col].astype("Int64")
    return df


def fix_all_null_columns(df: pd.DataFrame) -> pd.DataFrame:

    for col in df.columns:
        if df[col].isna().all():
            df[col] = df[col].astype("string")
    return df


def fix_date_columns(df: pd.DataFrame, table_name: str) -> pd.DataFrame:

    for col in df.columns:
        if "date" in col.lower() and df[col].dtype == "object":
            avant = df[col].notna().sum()
            df[col] = pd.to_datetime(df[col], errors="coerce")
            apres = df[col].notna().sum()

            if avant != apres:
                print(f"    ⚠️ [{table_name}] {col} : {avant - apres} valeurs non converties")
    return df


def export_table(conn: sqlite3.Connection, table_name: str) -> None:

    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    df = fix_fake_float_columns(df)
    df = fix_all_null_columns(df)
    df = fix_date_columns(df, table_name)

    out_path = OUTPUT_DIR / f"{table_name}.parquet"
    df.to_parquet(
        out_path,
        index=False,
        engine="pyarrow",
    )

    null_counts = df.isna().sum()
    n_nulls = int(null_counts[null_counts > 0].sum())
    date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

    print(
        f"  [{table_name}] {len(df)} lignes, {len(df.columns)} colonnes, "
        f"{n_nulls} valeurs manquantes, dates : {date_cols} → {out_path.name}"
    )


def main():
    if not DB_PATH.exists():
        print(f"⚠️ Fichier introuvable : {DB_PATH.resolve()}")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        tables_db = get_table_names(conn)

        if not tables_db:
            print("⚠️ Aucune table trouvée.")
            return

        manquantes = [t for t in TABLES_POWERBI if t not in tables_db]
        if manquantes:
            print(f"⚠️ Tables absentes de la base : {manquantes}")

        table_names = [t for t in TABLES_POWERBI if t in tables_db]
        exclues = [t for t in tables_db if t not in TABLES_POWERBI]

        print(f"{len(table_names)} tables à exporter vers {OUTPUT_DIR}/")
        print(f"Tables exclues : {exclues}\n")

        for table_name in table_names:
            export_table(conn, table_name)

        print(f"\n✅ Terminé : {len(table_names)} fichiers Parquet exportés.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
