import pandas as pd
import os

def ajouter_entetes(fichier_entree, fichier_sortie, colonnes, sep_entree="\t", sep_sortie=";"):
    """
    Ajoute les noms de colonnes à un CSV brut et l'exporte en CSV propre.
    """
    raw = pd.read_csv(fichier_entree, sep=sep_entree, header=None, encoding="utf-8")
    
    if raw.shape[1] != len(colonnes):
        raise ValueError(
            f"⚠️ {os.path.basename(fichier_entree)} : "
            f"{raw.shape[1]} colonnes trouvées, {len(colonnes)} attendues dans la config"
        )
    
    raw.columns = colonnes
    raw.to_csv(fichier_sortie, index=False, sep=sep_sortie)
    print(f"✅ {os.path.basename(fichier_sortie)} : {raw.shape[0]} lignes, {raw.shape[1]} colonnes")

def lire_person(fichier_entree, fichier_sortie, colonnes, sep_sortie=";"):
    """
    Cas spécial : Person.csv utilise un délimiteur custom '+|' entre les champs
    et '&|' comme terminateur de ligne (à cause des champs XML additionalcontactinfo
    et demographics, qui peuvent contenir des séparateurs classiques).
    """
    lignes_parsees = []

    with open(fichier_entree, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            champs = line.split("+|")
            champs[-1] = champs[-1].rstrip("&|")
            lignes_parsees.append(champs)

    raw = pd.DataFrame(lignes_parsees)

    if raw.shape[1] != len(colonnes):
        raise ValueError(
            f"⚠️ {os.path.basename(fichier_entree)} : "
            f"{raw.shape[1]} colonnes trouvées, {len(colonnes)} attendues dans la config"
        )

    raw.columns = colonnes
    raw.to_csv(fichier_sortie, index=False, sep=sep_sortie)
    print(f"✅ {os.path.basename(fichier_sortie)} : {raw.shape[0]} lignes, {raw.shape[1]} colonnes")

def lire_product_inventory(fichier_entree, fichier_sortie, colonnes, sep_entree="\t", sep_sortie=";"):
    """
    Cas spécial : ProductInventory.csv a environ 27% de valeurs manquantes
    dans la colonne 'shelf' (confirmé lors de l'EDA), malgré une contrainte
    NOT NULL officielle. On les remplace par "N/A" pour pouvoir les importer
    dans la base sans violer cette contrainte.
    """
    raw = pd.read_csv(fichier_entree, sep=sep_entree, header=None, encoding="utf-8")

    if raw.shape[1] != len(colonnes):
        raise ValueError(
            f"⚠️ {os.path.basename(fichier_entree)} : "
            f"{raw.shape[1]} colonnes trouvées, {len(colonnes)} attendues dans la config"
        )

    raw.columns = colonnes
    nb_vides = raw["shelf"].isna().sum()
    raw["shelf"] = raw["shelf"].fillna("N/A")
    raw.to_csv(fichier_sortie, index=False, sep=sep_sortie)
    print(f"✅ {os.path.basename(fichier_sortie)} : {raw.shape[0]} lignes, {raw.shape[1]} colonnes "
          f"({nb_vides} valeurs 'shelf' vides remplacées par 'N/A')")

# --- Configuration : fichier -> colonnes ---
CONFIG_FICHIERS = {
    "ProductVendor.csv": [
        "productid", "businessentityid", "averageleadtime", "standardprice",
        "lastreceiptcost", "lastreceiptdate", "minorderqty", "maxorderqty",
        "onorderqty", "unitmeasurecode", "modifieddate"
    ],
    "PurchaseOrderDetail.csv": [
        "purchaseorderid", "purchaseorderdetailid", "duedate",
        "orderqty", "productid", "unitprice", "linetotal",
        "receivedqty", "rejectedqty", "stockedqty", "modifieddate"
    ],
    "PurchaseOrderHeader.csv": [
        "purchaseorderid", "revisionnumber", "status", "employeeid",
        "vendorid", "shipmethodid", "orderdate", "shipdate",
        "subtotal", "taxamt", "freight", "totaldue", "modifieddate"
    ],
    "ShipMethod.csv": [
        "shipmethodid", "name", "shipbase", "shiprate",
        "rowguid", "modifieddate"
    ],
    "Vendor.csv": [
        "businessentityid", "accountnumber", "name", "creditrating",
        "preferredvendorstatus", "activeflag", "purchasingwebserviceurl",
        "modifieddate"
    ],
    "Location.csv": [
        "locationid", "name", "costrate", "availability", "modifieddate"
    ],
    "Product.csv": [
        "productid", "name", "productnumber", "makeflag", "finishedgoodsflag",
        "color", "safetystocklevel", "reorderpoint", "standardcost", "listprice",
        "size", "sizeunitmeasurecode", "weightunitmeasurecode", "weight",
        "daystomanufacture", "productline", "class", "style",
        "productsubcategoryid", "productmodelid", "sellstartdate",
        "sellenddate", "discontinueddate", "rowguid", "modifieddate"
    ],
    "ProductInventory.csv": [
        "productid", "locationid", "shelf", "bin", "quantity",
        "rowguid", "modifieddate"
    ],
    "ProductCategory.csv": [
        "productcategoryid", "name", "rowguid", "modifieddate"
    ],
    "ProductSubcategory.csv": [
        "productsubcategoryid", "productcategoryid", "name", "rowguid", "modifieddate"
    ],
    "Customer.csv": [
        "customerid", "personid", "storeid", "territoryid",
        "accountnumber", "rowguid", "modifieddate"
    ],
    "SalesOrderHeader.csv": [
        "salesorderid", "revisionnumber", "orderdate", "duedate", "shipdate", "status",
        "onlineorderflag", "salesordernumber", "purchaseordernumber", "accountnumber",
        "customerid", "salespersonid", "territoryid", "billtoaddressid", "shiptoaddressid",
        "shipmethodid", "creditcardid", "creditcardapprovalcode", "currencyrateid",
        "subtotal", "taxamt", "freight", "totaldue", "comment", "rowguid", "modifieddate"
     ],
    "SalesOrderDetail.csv": [
        "salesorderid", "salesorderdetailid", "carriertrackingnumber",
        "orderqty", "productid", "specialofferid", "unitprice",
        "unitpricediscount", "linetotal", "rowguid", "modifieddate"
    ],
    "SalesTerritory.csv": [
        "territoryid", "name", "countryregioncode", "group",
        "salesytd", "saleslastyear", "costytd", "costlastyear",
        "rowguid", "modifieddate"
    ],
    "Person.csv": [
        "businessentityid", "persontype", "namestyle", "title",
        "firstname", "middlename", "lastname", "suffix", "emailpromotion",
        "additionalcontactinfo", "demographics", "rowguid", "modifieddate"
    ],
}

if __name__ == "__main__":
    dossier_raw = "raw_data"
    dossier_sortie = "clean_data"

    for nom_fichier, colonnes in CONFIG_FICHIERS.items():
        chemin_entree = os.path.join(dossier_raw, nom_fichier)
        chemin_sortie = os.path.join(dossier_sortie, nom_fichier)
        try:
            if nom_fichier == "Person.csv":
                lire_person(chemin_entree, chemin_sortie, colonnes)
            elif nom_fichier == "ProductInventory.csv":
                lire_product_inventory(chemin_entree, chemin_sortie, colonnes)
            else:
                ajouter_entetes(chemin_entree, chemin_sortie, colonnes)
        except ValueError as e:
            print(e)
        except FileNotFoundError:
            print(f"❌ Fichier introuvable : {chemin_entree}")
