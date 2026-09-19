"""
createAPI.py — API FastAPI en lecture seule sur adventureworks.db (SQLite)

Objectif : exposer les 15 tables de la base pour que d'autres personnes
(ou Power BI, un frontend, etc.) puissent consulter les données via HTTP,
sans donner un accès direct au fichier .db.

Usage :
    pip install fastapi uvicorn
    python createAPI.py
    (ou : uvicorn createAPI:app --reload)

    Doc interactive une fois lancé : http://127.0.0.1:8000/docs

Config :
    Par défaut, le script cherche la base à "database/adventureworks.db"
    (chemin relatif à l'endroit d'où on lance la commande, comme les
    autres scripts du projet). On peut le surcharger avec la variable
    d'environnement DB_PATH si besoin :
        DB_PATH=/chemin/vers/adventureworks.db python createAPI.py
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# ========== Config ==========
DB_PATH = Path(os.environ.get("DB_PATH", "database/adventureworks.db"))

app = FastAPI(
    title="AdventureWorks API",
    description="API en lecture seule sur la base adventureworks.db (SQLite) — projet Data Analyst",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== Accès DB ==========
def get_conn() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Base introuvable à {DB_PATH.resolve()}. Vérifiez DB_PATH ou lancez le script depuis la racine du projet.",
        )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_all(table: str, filters: Optional[dict] = None, skip: int = 0, limit: int = 100) -> list:
    """SELECT * générique avec filtres optionnels (égalité) + pagination."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        sql = f'SELECT * FROM "{table}"'
        params: list = []

        clauses = []
        if filters:
            for col, val in filters.items():
                if val is not None:
                    clauses.append(f'"{col}" = ?')
                    params.append(val)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)

        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, skip])

        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def fetch_one(table: str, pk: dict) -> dict:
    """SELECT une ligne par clé primaire (simple ou composite)."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        clauses = " AND ".join(f'"{k}" = ?' for k in pk)
        sql = f'SELECT * FROM "{table}" WHERE {clauses}'
        cur.execute(sql, list(pk.values()))
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail=f"{table} introuvable pour {pk}")
        return dict(row)
    finally:
        conn.close()


# ========== Routes de base ==========
@app.get("/")
def root():
    return {
        "message": "AdventureWorks API — voir /docs pour la liste des endpoints",
        "db_path": str(DB_PATH),
    }


@app.get("/health")
def health():
    exists = DB_PATH.exists()
    return {"status": "ok" if exists else "db_missing", "db_path": str(DB_PATH)}


# ========== Groupe 1 : tables sans dépendance ==========

@app.get("/shipmethods")
def list_shipmethods(skip: int = 0, limit: int = Query(100, le=500)):
    return fetch_all("ShipMethod", skip=skip, limit=limit)


@app.get("/shipmethods/{shipmethodid}")
def get_shipmethod(shipmethodid: int):
    return fetch_one("ShipMethod", {"shipmethodid": shipmethodid})


@app.get("/salesterritories")
def list_salesterritories(skip: int = 0, limit: int = Query(100, le=500)):
    return fetch_all("SalesTerritory", skip=skip, limit=limit)


@app.get("/salesterritories/{territoryid}")
def get_salesterritory(territoryid: int):
    return fetch_one("SalesTerritory", {"territoryid": territoryid})


@app.get("/vendors")
def list_vendors(
    skip: int = 0,
    limit: int = Query(100, le=500),
    activeflag: Optional[int] = None,
    preferredvendorstatus: Optional[int] = None,
):
    return fetch_all(
        "Vendor",
        filters={"activeflag": activeflag, "preferredvendorstatus": preferredvendorstatus},
        skip=skip,
        limit=limit,
    )


@app.get("/vendors/{businessentityid}")
def get_vendor(businessentityid: int):
    return fetch_one("Vendor", {"businessentityid": businessentityid})


@app.get("/locations")
def list_locations(skip: int = 0, limit: int = Query(100, le=500)):
    return fetch_all("Location", skip=skip, limit=limit)


@app.get("/locations/{locationid}")
def get_location(locationid: int):
    return fetch_one("Location", {"locationid": locationid})


@app.get("/productcategories")
def list_productcategories(skip: int = 0, limit: int = Query(100, le=500)):
    return fetch_all("ProductCategory", skip=skip, limit=limit)


@app.get("/productcategories/{productcategoryid}")
def get_productcategory(productcategoryid: int):
    return fetch_one("ProductCategory", {"productcategoryid": productcategoryid})


@app.get("/persons")
def list_persons(skip: int = 0, limit: int = Query(100, le=500), persontype: Optional[str] = None):
    return fetch_all("Person", filters={"persontype": persontype}, skip=skip, limit=limit)


@app.get("/persons/{businessentityid}")
def get_person(businessentityid: int):
    return fetch_one("Person", {"businessentityid": businessentityid})


# ========== Groupe 2 ==========

@app.get("/productsubcategories")
def list_productsubcategories(
    skip: int = 0, limit: int = Query(100, le=500), productcategoryid: Optional[int] = None
):
    return fetch_all(
        "ProductSubcategory", filters={"productcategoryid": productcategoryid}, skip=skip, limit=limit
    )


@app.get("/productsubcategories/{productsubcategoryid}")
def get_productsubcategory(productsubcategoryid: int):
    return fetch_one("ProductSubcategory", {"productsubcategoryid": productsubcategoryid})


@app.get("/customers")
def list_customers(
    skip: int = 0, limit: int = Query(100, le=500), territoryid: Optional[int] = None
):
    return fetch_all("Customer", filters={"territoryid": territoryid}, skip=skip, limit=limit)


@app.get("/customers/{customerid}")
def get_customer(customerid: int):
    return fetch_one("Customer", {"customerid": customerid})


# ========== Groupe 3 ==========

@app.get("/products")
def list_products(
    skip: int = 0,
    limit: int = Query(100, le=500),
    productsubcategoryid: Optional[int] = None,
    color: Optional[str] = None,
):
    return fetch_all(
        "Product",
        filters={"productsubcategoryid": productsubcategoryid, "color": color},
        skip=skip,
        limit=limit,
    )


@app.get("/products/{productid}")
def get_product(productid: int):
    return fetch_one("Product", {"productid": productid})


# ========== Groupe 4 ==========

@app.get("/productinventory")
def list_productinventory(
    skip: int = 0, limit: int = Query(100, le=500), productid: Optional[int] = None, locationid: Optional[int] = None
):
    return fetch_all(
        "ProductInventory", filters={"productid": productid, "locationid": locationid}, skip=skip, limit=limit
    )


@app.get("/productinventory/{productid}/{locationid}")
def get_productinventory(productid: int, locationid: int):
    return fetch_one("ProductInventory", {"productid": productid, "locationid": locationid})


@app.get("/productvendors")
def list_productvendors(
    skip: int = 0, limit: int = Query(100, le=500), productid: Optional[int] = None, businessentityid: Optional[int] = None
):
    return fetch_all(
        "ProductVendor",
        filters={"productid": productid, "businessentityid": businessentityid},
        skip=skip,
        limit=limit,
    )


@app.get("/productvendors/{productid}/{businessentityid}")
def get_productvendor(productid: int, businessentityid: int):
    return fetch_one("ProductVendor", {"productid": productid, "businessentityid": businessentityid})


@app.get("/purchaseorderheaders")
def list_purchaseorderheaders(
    skip: int = 0, limit: int = Query(100, le=500), vendorid: Optional[int] = None, status: Optional[int] = None
):
    return fetch_all(
        "PurchaseOrderHeader", filters={"vendorid": vendorid, "status": status}, skip=skip, limit=limit
    )


@app.get("/purchaseorderheaders/{purchaseorderid}")
def get_purchaseorderheader(purchaseorderid: int):
    return fetch_one("PurchaseOrderHeader", {"purchaseorderid": purchaseorderid})


@app.get("/salesorderheaders")
def list_salesorderheaders(
    skip: int = 0, limit: int = Query(100, le=500), customerid: Optional[int] = None, territoryid: Optional[int] = None
):
    return fetch_all(
        "SalesOrderHeader", filters={"customerid": customerid, "territoryid": territoryid}, skip=skip, limit=limit
    )


@app.get("/salesorderheaders/{salesorderid}")
def get_salesorderheader(salesorderid: int):
    return fetch_one("SalesOrderHeader", {"salesorderid": salesorderid})


# ========== Groupe 5 ==========

@app.get("/purchaseorderdetails")
def list_purchaseorderdetails(
    skip: int = 0, limit: int = Query(100, le=500), purchaseorderid: Optional[int] = None, productid: Optional[int] = None
):
    return fetch_all(
        "PurchaseOrderDetail",
        filters={"purchaseorderid": purchaseorderid, "productid": productid},
        skip=skip,
        limit=limit,
    )


@app.get("/purchaseorderdetails/{purchaseorderid}/{purchaseorderdetailid}")
def get_purchaseorderdetail(purchaseorderid: int, purchaseorderdetailid: int):
    return fetch_one(
        "PurchaseOrderDetail",
        {"purchaseorderid": purchaseorderid, "purchaseorderdetailid": purchaseorderdetailid},
    )


@app.get("/salesorderdetails")
def list_salesorderdetails(
    skip: int = 0, limit: int = Query(100, le=500), salesorderid: Optional[int] = None, productid: Optional[int] = None
):
    return fetch_all(
        "SalesOrderDetail",
        filters={"salesorderid": salesorderid, "productid": productid},
        skip=skip,
        limit=limit,
    )


@app.get("/salesorderdetails/{salesorderid}/{salesorderdetailid}")
def get_salesorderdetail(salesorderid: int, salesorderdetailid: int):
    return fetch_one(
        "SalesOrderDetail", {"salesorderid": salesorderid, "salesorderdetailid": salesorderdetailid}
    )


# ========== Endpoint métier : KPI fournisseur ==========
# Reflète la question centrale du capstone (impact de la performance
# fournisseur sur la rotation des stocks / le profit). À affiner/étendre
# selon les métriques exactes utilisées dans l'analyse.

@app.get("/vendors/{businessentityid}/kpi")
def get_vendor_kpi(businessentityid: int):
    conn = get_conn()
    try:
        cur = conn.cursor()

        cur.execute('SELECT * FROM "Vendor" WHERE businessentityid = ?', (businessentityid,))
        vendor = cur.fetchone()
        if vendor is None:
            raise HTTPException(status_code=404, detail="Vendor introuvable")

        cur.execute(
            """
            SELECT
                COUNT(DISTINCT poh.purchaseorderid) AS nb_commandes,
                AVG(pod.receivedqty - pod.rejectedqty) AS qte_recue_nette_moyenne,
                SUM(pod.rejectedqty) AS total_rejete,
                SUM(pod.orderqty) AS total_commande,
                AVG(pv.averageleadtime) AS lead_time_moyen
            FROM "PurchaseOrderHeader" poh
            JOIN "PurchaseOrderDetail" pod ON pod.purchaseorderid = poh.purchaseorderid
            LEFT JOIN "ProductVendor" pv
                ON pv.productid = pod.productid AND pv.businessentityid = poh.vendorid
            WHERE poh.vendorid = ?
            """,
            (businessentityid,),
        )
        kpi = dict(cur.fetchone())

        total_commande = kpi.get("total_commande") or 0
        total_rejete = kpi.get("total_rejete") or 0
        kpi["taux_rejet"] = round(total_rejete / total_commande, 4) if total_commande else None

        return {"vendor": dict(vendor), "kpi": kpi}
    finally:
        conn.close()


if __name__ == "__main__":
    uvicorn.run("createAPI:app", host="127.0.0.1", port=8000, reload=True)
