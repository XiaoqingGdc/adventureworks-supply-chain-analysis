"""
Import automatique des 15 CSV nettoyés dans adventureworks.db,
dans l'ordre des dépendances de clés étrangères (même ordre que
create_database.sql / create_database_fr.sql).

Prérequis : les 15 tables vides (avec contraintes PK/FK) doivent
déjà exister dans adventureworks.db (via le script SQL).

Usage : placer ce fichier dans src/, puis lancer :
    python importCsv.py
"""

import sqlite3
import pandas as pd
import os

DOSSIER_CLEAN = "clean_data"
CHEMIN_DB = "database/adventureworks.db"  # à adapter si besoin

# Ordre d'import = ordre des dépendances (groupe 1 -> groupe 5)
# Chaque tuple : (nom_table, nom_fichier_csv)
ORDRE_IMPORT = [
    # Groupe 1 : sans dépendance
    ("ShipMethod", "ShipMethod.csv"),
    ("SalesTerritory", "SalesTerritory.csv"),
    ("Vendor", "Vendor.csv"),
    ("Location", "Location.csv"),
    ("ProductCategory", "ProductCategory.csv"),
    ("Person", "Person.csv"),
    # Groupe 2 : dépend du groupe 1
    ("ProductSubcategory", "ProductSubcategory.csv"),
    ("Customer", "Customer.csv"),
    # Groupe 3 : dépend du groupe 2
    ("Product", "Product.csv"),
    # Groupe 4 : dépend du groupe 3
    ("ProductInventory", "ProductInventory.csv"),
    ("ProductVendor", "ProductVendor.csv"),
    ("PurchaseOrderHeader", "PurchaseOrderHeader.csv"),
    ("SalesOrderHeader", "SalesOrderHeader.csv"),
    # Groupe 5 : dépend du groupe 4
    ("PurchaseOrderDetail", "PurchaseOrderDetail.csv"),
    ("SalesOrderDetail", "SalesOrderDetail.csv"),
]


def importer_toutes_les_tables():
    conn = sqlite3.connect(CHEMIN_DB)
    conn.execute("PRAGMA foreign_keys = ON;")  # active la vérification des FK
    cursor = conn.cursor()

    resultats = []

    for nom_table, nom_fichier in ORDRE_IMPORT:
        chemin_csv = os.path.join(DOSSIER_CLEAN, nom_fichier)

        if not os.path.exists(chemin_csv):
            print(f"❌ {nom_fichier} introuvable dans {DOSSIER_CLEAN}, table {nom_table} ignorée")
            resultats.append((nom_table, "FICHIER MANQUANT", 0))
            continue

        try:
            # keep_default_na=False : empêche pandas de reconvertir la chaîne
            # "N/A" (utilisée volontairement pour remplacer les valeurs
            # manquantes, ex: ProductInventory.shelf) en NaN. Sans ce
            # paramètre, "N/A" redevient NULL à la lecture et provoque
            # une violation de la contrainte NOT NULL à l'insertion.
            df = pd.read_csv(chemin_csv, sep=";", keep_default_na=False, na_values=[""])

            # Ne garder que les colonnes qui existent réellement dans la table
            # (certains CSV contiennent des colonnes calculées comme linetotal,
            # salesordernumber, accountnumber, qui n'ont pas été créées dans le
            # schéma -> on les ignore silencieusement au lieu de planter)
            cursor.execute(f"PRAGMA table_info({nom_table})")
            colonnes_table = [row[1] for row in cursor.fetchall()]
            colonnes_csv = list(df.columns)
            colonnes_communes = [c for c in colonnes_csv if c in colonnes_table]
            colonnes_ignorees = [c for c in colonnes_csv if c not in colonnes_table]

            if colonnes_ignorees:
                print(f"ℹ️  {nom_table} : colonnes ignorées (absentes du schéma) : {colonnes_ignorees}")

            df = df[colonnes_communes]
            # Convertit les vraies valeurs manquantes (NaN) en None Python,
            # pour qu'elles deviennent un vrai NULL SQL à l'insertion
            df = df.where(pd.notnull(df), None)

            # Guillemets doubles autour de chaque nom de colonne : nécessaire
            # pour les colonnes qui sont des mots réservés SQL (ex: "group"
            # dans SalesTerritory)
            colonnes = ",".join(f'"{c}"' for c in colonnes_communes)
            placeholders = ",".join(["?"] * len(colonnes_communes))
            sql_insert = f"INSERT INTO {nom_table} ({colonnes}) VALUES ({placeholders})"

            lignes_ok = 0
            lignes_erreur = 0
            premiere_erreur = None

            for _, row in df.iterrows():
                try:
                    cursor.execute(sql_insert, tuple(row))
                    lignes_ok += 1
                except sqlite3.IntegrityError as e:
                    lignes_erreur += 1
                    if premiere_erreur is None:
                        premiere_erreur = str(e)

            conn.commit()

            if lignes_erreur == 0:
                print(f"✅ {nom_table} : {lignes_ok} lignes importées")
                resultats.append((nom_table, "OK", lignes_ok))
            else:
                print(f"⚠️  {nom_table} : {lignes_ok} lignes OK, {lignes_erreur} lignes REJETÉES")
                print(f"   -> première erreur : {premiere_erreur}")
                resultats.append((nom_table, f"{lignes_erreur} REJETÉES", lignes_ok))

        except Exception as e:
            print(f"❌ Erreur sur {nom_table} : {e}")
            resultats.append((nom_table, f"ERREUR : {e}", 0))

    conn.close()

    # Résumé final
    print("\n" + "=" * 60)
    print("RÉSUMÉ DE L'IMPORT")
    print("=" * 60)
    for nom_table, statut, nb_lignes in resultats:
        print(f"{nom_table:25s} {statut:20s} {nb_lignes} lignes")


if __name__ == "__main__":
    importer_toutes_les_tables()