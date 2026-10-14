"""
createAPI.py — API FastAPI  sur adventureworks.db (SQLite)
Objectif : exposer les données pour que d'autres personnes
puissent les consulter via HTTP,sans donner un accès direct au fichier .db.

Usage :
    pip install fastapi uvicorn
    python creat_api.py

    Doc interactive une fois lancé : http://127.0.0.1:4000/docs

Config :
    Par défaut, le script cherche la base à "database/adventureworks.db"
    (chemin relatif à l'endroit d'où on lance la commande, comme les
    autres scripts du projet). On peut le surcharger avec la variable
    d'environnement DB_PATH si besoin :
        DB_PATH=/chemin/vers/adventureworks.db python creat_api.py
"""

import os
from pathlib import Path
from typing import Optional
from agent import ask
from fastapi import Body, FastAPI, HTTPException, Query
import sqlite3
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

# ========== Config ==========

DB_PATH = Path(os.environ.get("DB_PATH", "database/adventureworks.db"))
app = FastAPI(
    title="AdventureWorks API",
    description="API CRUD et KPI sur la base AdventureWorks (SQLite) — Projet Final Wild Code School",
    version="1.0.0",
    openapi_tags=[
        {"name": "Système", "description": "État de l'API et de la base"},
        {"name": "Fournisseurs (CRUD)", "description": "Les 4 opérations CRUD sur la table Vendor"},
        {"name": "KPI", "description": "Indicateurs vente, achat et produit"},
        {"name": "Agent IA", "description": "Questions en langage naturel sur la base"},
    ],
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


def insert_row(table: str, data: dict) -> dict:
    """INSERT générique : data = {colonne: valeur}."""
    if not data:
        raise HTTPException(status_code=400, detail="Corps de requête vide")
    conn = get_conn()
    try:
        cur = conn.cursor()
        cols = list(data.keys())
        col_str = ", ".join(f'"{c}"' for c in cols)
        placeholders = ", ".join("?" for _ in cols)
        sql = f'INSERT INTO "{table}" ({col_str}) VALUES ({placeholders})'
        cur.execute(sql, list(data.values()))
        conn.commit()
        return {"inserted_rowid": cur.lastrowid, **data}
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Contrainte violée : {e}")
    finally:
        conn.close()


def update_row(table: str, pk: dict, data: dict) -> dict:
    """UPDATE générique par clé primaire (simple ou composite)."""
    if not data:
        raise HTTPException(status_code=400, detail="Corps de requête vide")
    conn = get_conn()
    try:
        cur = conn.cursor()
        set_clause = ", ".join(f'"{c}" = ?' for c in data)
        where_clause = " AND ".join(f'"{k}" = ?' for k in pk)
        sql = f'UPDATE "{table}" SET {set_clause} WHERE {where_clause}'
        cur.execute(sql, list(data.values()) + list(pk.values()))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"{table} introuvable pour {pk}")
        conn.commit()
        return {"updated_rows": cur.rowcount, **pk, **data}
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Contrainte violée : {e}")
    finally:
        conn.close()


def delete_row(table: str, pk: dict) -> dict:
    """DELETE générique par clé primaire (simple ou composite)."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        where_clause = " AND ".join(f'"{k}" = ?' for k in pk)
        sql = f'DELETE FROM "{table}" WHERE {where_clause}'
        cur.execute(sql, list(pk.values()))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"{table} introuvable pour {pk}")
        conn.commit()
        return {"deleted_rows": cur.rowcount, **pk}
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Suppression impossible (référencée ailleurs) : {e}")
    finally:
        conn.close()


# ========== Routes de base ==========
@app.get("/",tags=["Système"])
def root():
    return {
        "message": "AdventureWorks API — voir http://127.0.0.1:4000/docs pour la liste complète des endpoints",
        "db_path": str(DB_PATH),
    }


@app.get("/health",tags=["Système"])
def health():
    exists = DB_PATH.exists()
    return {"status": "ok" if exists else "db_missing", "db_path": str(DB_PATH)}


# ========== CRUD Vendor (démonstration des 4 opérations) ==========

@app.get("/vendors", tags=["Fournisseurs (CRUD)"])
def list_vendors(skip: int = 0, limit: int = Query(100, le=500)):
    return fetch_all("Vendor", skip=skip, limit=limit)


@app.get("/vendors/{businessentityid}", tags=["Fournisseurs (CRUD)"])
def get_vendor(businessentityid: int):
    return fetch_one("Vendor", {"businessentityid": businessentityid})


@app.post("/vendors", status_code=201, tags=["Fournisseurs (CRUD)"])
def create_vendor(payload: dict = Body(..., examples=[{
    "businessentityid": 9999,
    "accountnumber": "TESTV01",
    "name": "Fournisseur Test",
    "creditrating": 3,
    "preferredvendorstatus": 1,
    "activeflag": 1,
}])):
    return insert_row("Vendor", payload)


@app.put("/vendors/{businessentityid}", tags=["Fournisseurs (CRUD)"])
def update_vendor(businessentityid: int, payload: dict = Body(..., example=[{"creditrating": 2}])):
    return update_row("Vendor", {"businessentityid": businessentityid}, payload)


@app.delete("/vendors/{businessentityid}", tags=["Fournisseurs (CRUD)"])
def delete_vendor(businessentityid: int):
    return delete_row("Vendor", {"businessentityid": businessentityid})



# ========== Endpoint métier : KPI fournisseur ==========
# Reflète la question centrale du capstone (impact de la performance
# fournisseur sur la rotation des stocks / le profit). À affiner/étendre
# selon les métriques exactes utilisées dans l'analyse.

@app.get("/kpi/vente", tags=["KPI"])
def get_kpi_vente(annee: Optional[int] = None):
    """
    KPI ventes : chiffre d'affaires, nombre de commandes client, nombre de
    clients actifs (ayant passé au moins une commande sur la période).
    Filtrable par année (sur SalesOrderHeader.orderdate).
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        sql = """
            SELECT
                SUM(sod.orderqty * sod.unitprice * (1 - sod.unitpricediscount)) AS chiffre_affaires,
                COUNT(DISTINCT sod.salesorderid) AS nb_commande_client
            FROM "SalesOrderDetail" sod
            JOIN "SalesOrderHeader" soh ON sod.salesorderid = soh.salesorderid
        """
        params = []
        if annee is not None:
            sql += " WHERE strftime('%Y', soh.orderdate) = ?"
            params.append(str(annee))

        cur.execute(sql, params)
        row = dict(cur.fetchone())
        row["chiffre_affaires"] = round(row["chiffre_affaires"], 2) if row["chiffre_affaires"] else 0.0

        # Clients actifs = clients distincts ayant passé une commande sur la période
        # (Customer n'a pas de champ activeflag ; "actif" = a une commande ici)
        sql_clients = 'SELECT COUNT(DISTINCT customerid) AS nb FROM "SalesOrderHeader"'
        params_clients = []
        if annee is not None:
            sql_clients += " WHERE strftime('%Y', orderdate) = ?"
            params_clients.append(str(annee))
        cur.execute(sql_clients, params_clients)
        row["nb_client_active"] = cur.fetchone()["nb"]

        # Top 5 marchés géographiques par chiffre d'affaires
        sql_territoire = (
            'SELECT st.territoryid, st.name, '
            'SUM(sod.orderqty * sod.unitprice * (1 - sod.unitpricediscount)) AS chiffre_affaires '
            'FROM "SalesOrderDetail" sod '
            'JOIN "SalesOrderHeader" soh ON sod.salesorderid = soh.salesorderid '
            'JOIN "SalesTerritory" st ON soh.territoryid = st.territoryid'
        )
        params_territoire = []
        if annee is not None:
            sql_territoire += " WHERE strftime('%Y', soh.orderdate) = ?"
            params_territoire.append(str(annee))
        sql_territoire += " GROUP BY st.territoryid, st.name ORDER BY chiffre_affaires DESC LIMIT 5"
        cur.execute(sql_territoire, params_territoire)
        row["top5_marches_geographiques"] = [
            {"territoryid": r["territoryid"], "name": r["name"], "chiffre_affaires": round(r["chiffre_affaires"], 2)}
            for r in cur.fetchall()
        ]

        # Top 5 clients par chiffre d'affaires (Customer n'a pas de nom propre
        # exploitable simplement — retourne customerid, à croiser avec
        # Person/Store si besoin d'un nom)
        sql_client = (
            'SELECT soh.customerid, '
            'SUM(sod.orderqty * sod.unitprice * (1 - sod.unitpricediscount)) AS chiffre_affaires '
            'FROM "SalesOrderDetail" sod '
            'JOIN "SalesOrderHeader" soh ON sod.salesorderid = soh.salesorderid'
        )
        params_client = []
        if annee is not None:
            sql_client += " WHERE strftime('%Y', soh.orderdate) = ?"
            params_client.append(str(annee))
        sql_client += " GROUP BY soh.customerid ORDER BY chiffre_affaires DESC LIMIT 5"
        cur.execute(sql_client, params_client)
        row["top5_clients"] = [
            {"customerid": r["customerid"], "chiffre_affaires": round(r["chiffre_affaires"], 2)}
            for r in cur.fetchall()
        ]

        row["annee"] = annee
        return row
    finally:
        conn.close()


@app.get("/kpi/achat", tags=["KPI"])
def get_kpi_achat(annee: Optional[int] = None):
    """
    KPI achats : montant brut/net, quantités brutes/nettes, nombre de
    fournisseurs actifs. Filtrable par année (sur PurchaseOrderHeader.orderdate).
    Net = après déduction des quantités rejetées (rejectedqty).
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        sql = """
            SELECT
                SUM(pod.orderqty * pod.unitprice) AS montant_achat_brut,
                SUM((pod.orderqty - pod.rejectedqty) * pod.unitprice) AS montant_achat_net,
                COUNT(DISTINCT pod.purchaseorderid) AS nb_commandes_achat,
                SUM(pod.orderqty) AS nb_achat_fournisseur_total_brut,
                SUM(pod.orderqty - pod.rejectedqty) AS nb_achat_fournisseur_total_net
            FROM "PurchaseOrderDetail" pod
            JOIN "PurchaseOrderHeader" poh ON pod.purchaseorderid = poh.purchaseorderid
        """
        params = []
        if annee is not None:
            sql += " WHERE strftime('%Y', poh.orderdate) = ?"
            params.append(str(annee))

        cur.execute(sql, params)
        row = dict(cur.fetchone())
        row["montant_achat_brut"] = round(row["montant_achat_brut"], 2) if row["montant_achat_brut"] else 0.0
        row["montant_achat_net"] = round(row["montant_achat_net"], 2) if row["montant_achat_net"] else 0.0
        row["nb_commandes_achat"] = row["nb_commandes_achat"] or 0
        row["nb_achat_fournisseur_total_brut"] = row["nb_achat_fournisseur_total_brut"] or 0
        row["nb_achat_fournisseur_total_net"] = row["nb_achat_fournisseur_total_net"] or 0

        # Fournisseurs actifs (indépendant du filtre année, statut global du Vendor)
        cur.execute('SELECT COUNT(*) AS nb FROM "Vendor" WHERE activeflag = 1')
        row["nb_fournisseur_active"] = cur.fetchone()["nb"]

        row["annee"] = annee
        return row
    finally:
        conn.close()


@app.get("/kpi/produit", tags=["KPI"])
def get_kpi_produit(annee: Optional[int] = None):
    """
    KPI produits : quantité achetée, quantité vendue (filtrables par année),
    stock actuel, et top 10 des produits les plus vendus.
    Stock = ProductInventory filtré sur locationid=7 ("Finished Goods
    Storage"), seul entrepôt réel selon l'EDA (les autres locations sont
    des postes d'usine, pas des stocks) ; le stock est un état courant,
    non filtrable par année.
    """
    conn = get_conn()
    try:
        cur = conn.cursor()

        # Quantité achetée (PurchaseOrderDetail)
        sql_achat = (
            'SELECT SUM(pod.orderqty) AS qte FROM "PurchaseOrderDetail" pod '
            'JOIN "PurchaseOrderHeader" poh ON pod.purchaseorderid = poh.purchaseorderid'
        )
        params_achat = []
        if annee is not None:
            sql_achat += " WHERE strftime('%Y', poh.orderdate) = ?"
            params_achat.append(str(annee))
        cur.execute(sql_achat, params_achat)
        quantite_achetee = cur.fetchone()["qte"] or 0

        # Quantité vendue (SalesOrderDetail)
        sql_vente = (
            'SELECT SUM(sod.orderqty) AS qte FROM "SalesOrderDetail" sod '
            'JOIN "SalesOrderHeader" soh ON sod.salesorderid = soh.salesorderid'
        )
        params_vente = []
        if annee is not None:
            sql_vente += " WHERE strftime('%Y', soh.orderdate) = ?"
            params_vente.append(str(annee))
        cur.execute(sql_vente, params_vente)
        quantite_vendue = cur.fetchone()["qte"] or 0

        # Stock actuel (état courant, entrepôt produits finis uniquement)
        cur.execute('SELECT SUM(quantity) AS qte FROM "ProductInventory" WHERE locationid = 7')
        stock_actuel = cur.fetchone()["qte"] or 0

        # Top 10 produits les plus vendus (par quantité)
        sql_top = (
            'SELECT p.productid, p.name, SUM(sod.orderqty) AS quantite_vendue '
            'FROM "SalesOrderDetail" sod '
            'JOIN "SalesOrderHeader" soh ON sod.salesorderid = soh.salesorderid '
            'JOIN "Product" p ON p.productid = sod.productid'
        )
        params_top = []
        if annee is not None:
            sql_top += " WHERE strftime('%Y', soh.orderdate) = ?"
            params_top.append(str(annee))
        sql_top += " GROUP BY p.productid, p.name ORDER BY quantite_vendue DESC LIMIT 10"
        cur.execute(sql_top, params_top)
        top10 = [dict(r) for r in cur.fetchall()]

        return {
            "annee": annee,
            "quantite_achetee": quantite_achetee,
            "quantite_vendue": quantite_vendue,
            "stock_actuel": stock_actuel,
            "top10_produits_vendus": top10,
        }
    finally:
        conn.close()

@app.get("/ask", tags=["Agent IA"])
def ask_agent(question: str):
    """Pose une question en langage naturel sur la base AdventureWorks."""
    return {"question": question, "answer": ask(question)}

if __name__ == "__main__":
    uvicorn.run("creat_api:app", host="127.0.0.1", port=4000, reload=True)