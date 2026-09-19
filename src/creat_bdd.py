"""
Création de la base de données AdventureWorks (SQLite).

Note : les tables sont créées dans l'ordre des dépendances
       (une table référencée par une clé étrangère doit être
       créée avant la table qui la référence).

Usage : placer ce fichier dans src/, puis lancer :
    python createbdd.py
"""

import sqlite3
import os

CHEMIN_DB = "database/adventureworks.db"  

# Ordre de suppression = inverse de l'ordre de création
# (pour permettre de relancer ce script sans erreur de contrainte)
TABLES_DANS_ORDRE_INVERSE = [
    "SalesOrderDetail", "SalesOrderHeader", "Customer",
    "PurchaseOrderDetail", "PurchaseOrderHeader", "ProductVendor",
    "ProductInventory", "Product", "ProductSubcategory", "Person",
    "ProductCategory", "Location", "Vendor", "SalesTerritory", "ShipMethod",
]

# Chaque script SQL de création, dans l'ordre des dépendances
SCRIPTS_CREATION = {

    # ========================================================
    # Groupe 1 : tables sans dépendance (aucune clé étrangère)
    # ========================================================

    "ShipMethod": """
        CREATE TABLE ShipMethod
        (
            shipmethodid  INTEGER PRIMARY KEY NOT NULL,
            name          VARCHAR(50) NOT NULL,
            shipbase      REAL NOT NULL DEFAULT 0,
            shiprate      REAL NOT NULL DEFAULT 0,
            rowguid       TEXT NOT NULL,
            modifieddate  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """,

    "SalesTerritory": """
        CREATE TABLE SalesTerritory
        (
            territoryid        INTEGER PRIMARY KEY NOT NULL,
            name               VARCHAR(50) NOT NULL,
            countryregioncode  VARCHAR(3) NOT NULL,
            "group"            VARCHAR(50) NOT NULL,
            salesytd           REAL NOT NULL DEFAULT 0,
            saleslastyear      REAL NOT NULL DEFAULT 0,
            costytd            REAL NOT NULL DEFAULT 0,
            costlastyear       REAL NOT NULL DEFAULT 0,
            rowguid            TEXT NOT NULL,
            modifieddate       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """,

    # Remarque : les contraintes de la table Vendor sont déduites du diagramme
    # DBeaver (pas de capture d'écran du schéma officiel avec les "not_null"
    # comme pour les autres tables) -> à revérifier avec l'en-tête réel du CSV
    "Vendor": """
        CREATE TABLE Vendor
        (
            businessentityid         INTEGER PRIMARY KEY NOT NULL,
            accountnumber            VARCHAR(15) NOT NULL,
            name                     VARCHAR(50) NOT NULL,
            creditrating             INTEGER NOT NULL,
            preferredvendorstatus    INTEGER NOT NULL DEFAULT 1,
            activeflag               INTEGER NOT NULL DEFAULT 1,
            purchasingwebserviceurl  TEXT,
            modifieddate             DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """,

    "Location": """
        CREATE TABLE Location
        (
            locationid    INTEGER PRIMARY KEY NOT NULL,
            name          VARCHAR(50) NOT NULL,
            costrate      REAL NOT NULL DEFAULT 0,
            availability  REAL NOT NULL DEFAULT 0,
            modifieddate  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """,

    "ProductCategory": """
        CREATE TABLE ProductCategory
        (
            productcategoryid  INTEGER PRIMARY KEY NOT NULL,
            name                VARCHAR(50) NOT NULL,
            rowguid             TEXT NOT NULL,
            modifieddate        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """,

    "Person": """
        CREATE TABLE Person
        (
            businessentityid       INTEGER PRIMARY KEY NOT NULL,
            persontype             CHAR(2) NOT NULL,
            namestyle              INTEGER NOT NULL DEFAULT 0,
            title                  VARCHAR(8),
            firstname              VARCHAR(50) NOT NULL,
            middlename             VARCHAR(50),
            lastname               VARCHAR(50) NOT NULL,
            suffix                 VARCHAR(10),
            emailpromotion         INTEGER NOT NULL DEFAULT 0,
            additionalcontactinfo  TEXT,
            demographics           TEXT,
            rowguid                TEXT NOT NULL,
            modifieddate           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """,

    # ========================================================
    # Groupe 2 : tables dépendant du groupe 1
    # ========================================================

    "ProductSubcategory": """
        CREATE TABLE ProductSubcategory
        (
            productsubcategoryid  INTEGER PRIMARY KEY NOT NULL,
            productcategoryid     INTEGER NOT NULL,
            name                  VARCHAR(50) NOT NULL,
            rowguid               TEXT NOT NULL,
            modifieddate          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (productcategoryid) REFERENCES ProductCategory(productcategoryid)
        );
    """,

    "Customer": """
        CREATE TABLE Customer
        (
            customerid    INTEGER PRIMARY KEY NOT NULL,
            personid      INTEGER,
            storeid       INTEGER,
            territoryid   INTEGER,
            rowguid       TEXT NOT NULL,
            modifieddate  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (personid) REFERENCES Person(businessentityid),
            FOREIGN KEY (territoryid) REFERENCES SalesTerritory(territoryid)
        );
    """,

    # ========================================================
    # Groupe 3 : tables dépendant du groupe 2
    # ========================================================

    "Product": """
        CREATE TABLE Product
        (
            productid              INTEGER PRIMARY KEY NOT NULL,
            name                   VARCHAR(50) NOT NULL,
            productnumber          VARCHAR(25) NOT NULL,
            makeflag               INTEGER NOT NULL DEFAULT 1,
            finishedgoodsflag      INTEGER NOT NULL DEFAULT 1,
            color                  VARCHAR(15),
            safetystocklevel       INTEGER NOT NULL,
            reorderpoint           INTEGER NOT NULL,
            standardcost           REAL NOT NULL,
            listprice              REAL NOT NULL,
            size                   VARCHAR(5),
            sizeunitmeasurecode    CHAR(3),
            weightunitmeasurecode  CHAR(3),
            weight                 REAL,
            daystomanufacture      INTEGER NOT NULL,
            productline            CHAR(2),
            class                  CHAR(2),
            style                  CHAR(2),
            productsubcategoryid   INTEGER,
            productmodelid         INTEGER,
            sellstartdate          DATETIME NOT NULL,
            sellenddate            DATETIME,
            discontinueddate       DATETIME,
            rowguid                TEXT NOT NULL,
            modifieddate           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (productsubcategoryid) REFERENCES ProductSubcategory(productsubcategoryid)
        );
    """,

    # ========================================================
    # Groupe 4 : tables dépendant du groupe 3 (via Product)
    # ========================================================

    "ProductInventory": """
        CREATE TABLE ProductInventory
        (
            productid     INTEGER NOT NULL,
            locationid    INTEGER NOT NULL,
            shelf         VARCHAR(10) NOT NULL,
            bin           INTEGER NOT NULL,
            quantity      INTEGER NOT NULL DEFAULT 0,
            rowguid       TEXT NOT NULL,
            modifieddate  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (productid, locationid),
            FOREIGN KEY (productid) REFERENCES Product(productid),
            FOREIGN KEY (locationid) REFERENCES Location(locationid)
        );
    """,

    "ProductVendor": """
        CREATE TABLE ProductVendor
        (
            productid         INTEGER NOT NULL,
            businessentityid  INTEGER NOT NULL,
            averageleadtime   INTEGER NOT NULL,
            standardprice     REAL NOT NULL,
            lastreceiptcost   REAL,
            lastreceiptdate   DATETIME,
            minorderqty       INTEGER NOT NULL,
            maxorderqty       INTEGER NOT NULL,
            onorderqty        INTEGER,
            unitmeasurecode   CHAR(3) NOT NULL,
            modifieddate      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (productid, businessentityid),
            FOREIGN KEY (productid) REFERENCES Product(productid),
            FOREIGN KEY (businessentityid) REFERENCES Vendor(businessentityid)
        );
    """,

    "PurchaseOrderHeader": """
        CREATE TABLE PurchaseOrderHeader
        (
            purchaseorderid  INTEGER PRIMARY KEY NOT NULL,
            revisionnumber   INTEGER NOT NULL DEFAULT 0,
            status           INTEGER NOT NULL DEFAULT 1,
            employeeid       INTEGER NOT NULL,
            vendorid         INTEGER NOT NULL,
            shipmethodid     INTEGER NOT NULL,
            orderdate        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            shipdate         DATETIME,
            subtotal         REAL NOT NULL DEFAULT 0,
            taxamt           REAL NOT NULL DEFAULT 0,
            freight          REAL NOT NULL DEFAULT 0,
            totaldue         REAL,
            modifieddate     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendorid) REFERENCES Vendor(businessentityid),
            FOREIGN KEY (shipmethodid) REFERENCES ShipMethod(shipmethodid)
            -- employeeid référence la table Employee, non créée dans ce projet
            -- -> contrainte non ajoutée
        );
    """,

    "SalesOrderHeader": """
        CREATE TABLE SalesOrderHeader
        (
            salesorderid            INTEGER PRIMARY KEY NOT NULL,
            revisionnumber          INTEGER NOT NULL DEFAULT 0,
            orderdate               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            duedate                 DATETIME NOT NULL,
            shipdate                DATETIME,
            status                  INTEGER NOT NULL DEFAULT 1,
            onlineorderflag         INTEGER NOT NULL DEFAULT 1,
            purchaseordernumber     VARCHAR(25),
            accountnumber           VARCHAR(15),
            customerid              INTEGER NOT NULL,
            salespersonid           INTEGER,
            territoryid             INTEGER,
            billtoaddressid         INTEGER NOT NULL,
            shiptoaddressid         INTEGER NOT NULL,
            shipmethodid            INTEGER NOT NULL,
            creditcardid            INTEGER,
            creditcardapprovalcode  VARCHAR(15),
            currencyrateid          INTEGER,
            subtotal                REAL NOT NULL DEFAULT 0,
            taxamt                  REAL NOT NULL DEFAULT 0,
            freight                 REAL NOT NULL DEFAULT 0,
            totaldue                REAL,
            comment                 VARCHAR(128),
            rowguid                 TEXT NOT NULL,
            modifieddate            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customerid) REFERENCES Customer(customerid),
            FOREIGN KEY (territoryid) REFERENCES SalesTerritory(territoryid),
            FOREIGN KEY (shipmethodid) REFERENCES ShipMethod(shipmethodid)
            -- billtoaddressid/shiptoaddressid -> Address, salespersonid -> SalesPerson,
            -- creditcardid -> CreditCard, currencyrateid -> CurrencyRate
            -- ces tables ne sont pas créées dans ce projet -> contraintes non ajoutées
        );
    """,

    # ========================================================
    # Groupe 5 : tables de détail dépendant du groupe 4
    # ========================================================

    "PurchaseOrderDetail": """
        CREATE TABLE PurchaseOrderDetail
        (
            purchaseorderid        INTEGER NOT NULL,
            purchaseorderdetailid  INTEGER NOT NULL,
            duedate                DATETIME NOT NULL,
            orderqty               INTEGER NOT NULL,
            productid              INTEGER NOT NULL,
            unitprice              REAL NOT NULL,
            receivedqty            REAL NOT NULL,
            rejectedqty            REAL NOT NULL,
            stockedqty             REAL NOT NULL,
            modifieddate           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (purchaseorderid, purchaseorderdetailid),
            FOREIGN KEY (purchaseorderid) REFERENCES PurchaseOrderHeader(purchaseorderid),
            FOREIGN KEY (productid) REFERENCES Product(productid)
        );
    """,

    "SalesOrderDetail": """
        CREATE TABLE SalesOrderDetail
        (
            salesorderid           INTEGER NOT NULL,
            salesorderdetailid     INTEGER NOT NULL,
            carriertrackingnumber  VARCHAR(25),
            orderqty               INTEGER NOT NULL,
            productid              INTEGER NOT NULL,
            specialofferid         INTEGER NOT NULL,
            unitprice              REAL NOT NULL,
            unitpricediscount      REAL NOT NULL DEFAULT 0,
            rowguid                TEXT NOT NULL,
            modifieddate           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (salesorderid, salesorderdetailid),
            FOREIGN KEY (salesorderid) REFERENCES SalesOrderHeader(salesorderid),
            FOREIGN KEY (productid) REFERENCES Product(productid)
            -- specialofferid référence la table SpecialOffer, non créée dans ce projet
            -- -> contrainte non ajoutée
        );
    """,
}

# Ordre de création = ordre des dépendances (groupe 1 -> groupe 5)
ORDRE_CREATION = [
    "ShipMethod", "SalesTerritory", "Vendor", "Location", "ProductCategory", "Person",
    "ProductSubcategory", "Customer",
    "Product",
    "ProductInventory", "ProductVendor", "PurchaseOrderHeader", "SalesOrderHeader",
    "PurchaseOrderDetail", "SalesOrderDetail",
]


def creer_base():
    os.makedirs(os.path.dirname(CHEMIN_DB), exist_ok=True)
    conn = sqlite3.connect(CHEMIN_DB)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # Suppression préalable (ordre inverse), pour pouvoir relancer le script
    for nom_table in TABLES_DANS_ORDRE_INVERSE:
        cursor.execute(f"DROP TABLE IF EXISTS {nom_table};")

    # Création dans l'ordre des dépendances
    for nom_table in ORDRE_CREATION:
        cursor.execute(SCRIPTS_CREATION[nom_table])
        print(f"✅ Table {nom_table} créée")

    conn.commit()
    conn.close()
    print(f"\nBase de données créée avec succès : {CHEMIN_DB}")


if __name__ == "__main__":
    creer_base()