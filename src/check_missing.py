"""
check_missing.py
----------------
Contrôle des valeurs manquantes dans les données telles que Power BI les charge.

Le script reproduit les étapes de Power Query qui touchent aux valeurs manquantes :
    1. lecture des fichiers Parquet chargés par chaque requête Power Query ;
    2. suppression des colonnes retirées (Table.RemoveColumns) ;
    3. remplacement des valeurs nulles (Table.ReplaceValue(..., null, ...)).
Il signale ensuite les valeurs manquantes qui arrivent encore dans le modèle.

Source des étapes Power Query :
    - par défaut, le code M est lu directement dans AdventureWorks.pbix
      (bibliothèque pbixray : pip install pbixray) ;
    - si le .pbix ou pbixray est indisponible, le script utilise la copie
      ETAPES_POWER_QUERY ci-dessous (à mettre à jour si Power Query change).

À exécuter depuis la racine du projet, après export_clean_parquet.py.
"""

import re
from pathlib import Path

import pandas as pd

DOSSIER_PARQUET = Path("parquet_for_powerbi")
CHEMIN_PBIX = Path("AdventureWorks.pbix")

# Copie de secours des étapes Power Query (relevée dans AdventureWorks.pbix)
# Format : requête -> {"fichier", "supprimees", "remplacements" (colonne -> valeur)}
ETAPES_POWER_QUERY = {
    "Customer": {"fichier": "Customer.parquet",
                 "supprimees": ["personid", "storeid"], "remplacements": {}},
    "Location": {"fichier": "Location.parquet",
                 "supprimees": ["costrate", "availability"], "remplacements": {}},
    "Product": {"fichier": "Product.parquet",
                "supprimees": ["weight", "color", "productnumber", "size", "sizeunitmeasurecode",
                               "weightunitmeasurecode", "sellstartdate", "sellenddate",
                               "daystomanufacture", "productline", "class", "style", "productmodelid"],
                "remplacements": {"productsubcategoryid": 999}},
    "ProductCategory": {"fichier": "ProductCategory.parquet",
                        "supprimees": [], "remplacements": {}},
    "ProductInventory": {"fichier": "ProductInventory.parquet",
                         "supprimees": ["shelf", "bin"], "remplacements": {}},
    "ProductSubcategory": {"fichier": "ProductSubcategory.parquet",
                           "supprimees": [], "remplacements": {}},
    "ProductVendor": {"fichier": "ProductVendor.parquet",
                      "supprimees": ["onorderqty", "maxorderqty", "minorderqty",
                                     "lastreceiptdate", "lastreceiptcost"], "remplacements": {}},
    "PurchaseOrderDetail": {"fichier": "PurchaseOrderDetail.parquet",
                            "supprimees": ["purchaseorderdetailid"], "remplacements": {}},
    "PurchaseOrderHeader": {"fichier": "PurchaseOrderHeader.parquet",
                            "supprimees": ["employeeid", "shipmethodid", "revisionnumber", "status"],
                            "remplacements": {}},
    "SalesOrderDetail": {"fichier": "SalesOrderDetail.parquet",
                         "supprimees": ["salesorderdetailid", "carriertrackingnumber", "specialofferid"],
                         "remplacements": {}},
    "SalesOrderHeader": {"fichier": "SalesOrderHeader.parquet",
                         "supprimees": ["creditcardapprovalcode", "currencyrateid", "revisionnumber",
                                        "status", "purchaseordernumber", "accountnumber",
                                        "salespersonid", "billtoaddressid", "shiptoaddressid",
                                        "shipmethodid", "creditcardid"],
                         "remplacements": {}},
    "SalesTerritory": {"fichier": "SalesTerritory.parquet",
                       "supprimees": ["costytd", "costlastyear", "salesytd", "saleslastyear"],
                       "remplacements": {}},
    "Vendor": {"fichier": "Vendor.parquet",
               "supprimees": ["accountnumber"], "remplacements": {}},
    "vendor_segments": {"fichier": "vendor_segments.parquet",
                        "supprimees": [], "remplacements": {}},
}


# ============================================================
# 1. Lecture des étapes Power Query
# ============================================================
def liste_colonnes(texte):
    """Transforme '"a", "b"' (liste M entre accolades) en ['a', 'b']."""
    return re.findall(r'"([^"]+)"', texte)


def convertir_valeur_m(texte):
    """Convertit une valeur M en type Python : 999 -> int, 1.5 -> float, "N/A" -> str."""
    texte = texte.strip()
    if texte.startswith('"'):
        return texte.strip('"')
    for type_num in (int, float):
        try:
            return type_num(texte)
        except ValueError:
            pass
    return texte


def analyser_code_m(code):
    """Extrait d'une requête M : le fichier Parquet lu, les colonnes supprimées
    et les remplacements de null. Les autres étapes (renommage, traduction,
    ajout de lignes) n'ont pas d'effet sur les valeurs manquantes."""
    fichier = re.search(r'parquet_for_powerbi\\([^"\\]+\.parquet)', code)

    supprimees = []
    for bloc in re.findall(r"Table\.RemoveColumns\([^{]*\{([^}]*)\}", code):
        supprimees += liste_colonnes(bloc)

    remplacements = {}
    motif_null = r"Table\.ReplaceValue\([^,]+,\s*null\s*,\s*([^,]+),[^{]*\{([^}]*)\}"
    for valeur, bloc in re.findall(motif_null, code):
        for col in liste_colonnes(bloc):
            remplacements[col] = convertir_valeur_m(valeur)

    return {
        "fichier": fichier.group(1) if fichier else None,
        "supprimees": supprimees,
        "remplacements": remplacements,
    }


def charger_etapes_power_query():
    """Lit le code M dans le .pbix ; à défaut, renvoie la copie de secours."""
    try:
        from pbixray import PBIXRay
    except ImportError:
        print("ℹ️  pbixray non installé : utilisation de la copie ETAPES_POWER_QUERY\n")
        return ETAPES_POWER_QUERY

    if not CHEMIN_PBIX.exists():
        print(f"ℹ️  {CHEMIN_PBIX} introuvable : utilisation de la copie ETAPES_POWER_QUERY\n")
        return ETAPES_POWER_QUERY

    requetes = PBIXRay(str(CHEMIN_PBIX)).power_query
    etapes = {}
    for nom, code in zip(requetes.iloc[:, 0], requetes.iloc[:, 1]):
        infos = analyser_code_m(code)
        if infos["fichier"]:  # on ne garde que les requêtes qui lisent un Parquet
            etapes[nom] = infos
    print(f"✅ Étapes Power Query lues dans {CHEMIN_PBIX} ({len(etapes)} requêtes)\n")
    return etapes


# ============================================================
# 2. Application des étapes et contrôle des valeurs manquantes
# ============================================================
def appliquer_power_query(df, etapes):
    """Reproduit l'effet de Power Query : suppression puis remplacement des null."""
    absentes = [c for c in etapes["supprimees"] if c not in df.columns]
    df = df.drop(columns=[c for c in etapes["supprimees"] if c in df.columns])
    for col, valeur in etapes["remplacements"].items():
        if col in df.columns:
            df[col] = df[col].fillna(valeur)
    return df, absentes


def controler_table(nom, etapes):
    chemin = DOSSIER_PARQUET / etapes["fichier"]
    if not chemin.exists():
        print(f"❌ {nom} : fichier {chemin} introuvable")
        return None

    brut = pd.read_parquet(chemin)
    modele, absentes = appliquer_power_query(brut, etapes)

    nulls_brut = brut.isna().sum()
    nulls_modele = modele.isna().sum()
    nulls_modele = nulls_modele[nulls_modele > 0]

    # Colonnes avec des NULL dans le Parquet, traitées par Power Query
    traitees = [c for c in nulls_brut[nulls_brut > 0].index if c not in nulls_modele.index]

    if nulls_modele.empty:
        print(f"✅ {nom} : aucune valeur manquante dans le modèle "
              f"({len(modele)} lignes, {modele.shape[1]} colonnes)")
    else:
        print(f"⚠️ {nom} : valeurs manquantes encore présentes dans le modèle")
        for col, nb in nulls_modele.items():
            print(f"      - {col} : {nb} ({nb / len(modele):.1%})")

    for col in traitees:
        action = (f"null → {etapes['remplacements'][col]}" if col in etapes["remplacements"]
                  else "colonne supprimée")
        print(f"      · {col} : {int(nulls_brut[col])} NULL dans le Parquet, traitée ({action})")

    # Une colonne supprimée dans Power Query mais absente du Parquet signale
    # un décalage entre le script d'export et le modèle Power BI
    if absentes:
        print(f"      ⚠️ supprimées dans Power Query mais absentes du Parquet : {absentes}")

    return {"table": nom, "colonnes_avec_null": len(nulls_modele)}


def main():
    if not DOSSIER_PARQUET.exists():
        print(f"⚠️  Dossier {DOSSIER_PARQUET.resolve()} introuvable : lancer export_clean_parquet.py")
        return

    etapes_pq = charger_etapes_power_query()

    resultats = [r for nom, etapes in sorted(etapes_pq.items())
                 if (r := controler_table(nom, etapes)) is not None]

    # Fichiers Parquet présents mais non chargés par Power BI
    charges = {e["fichier"] for e in etapes_pq.values()}
    non_charges = sorted(f.name for f in DOSSIER_PARQUET.glob("*.parquet") if f.name not in charges)
    if non_charges:
        print(f"\nℹ️  Fichiers Parquet non chargés dans Power BI : {non_charges}")

    # Synthèse
    a_traiter = [r["table"] for r in resultats if r["colonnes_avec_null"] > 0]
    print("\n" + "=" * 60)
    if a_traiter:
        print(f"⚠️ Tables avec des valeurs manquantes dans le modèle : {a_traiter}")
    else:
        print(f"✅ {len(resultats)} tables contrôlées : aucune valeur manquante dans le modèle Power BI")


if __name__ == "__main__":
    main()
