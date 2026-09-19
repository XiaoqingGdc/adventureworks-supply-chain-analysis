# Rapport d'analyse exploratoire (EDA) — AdventureWorks Supply Chain

**Projet :** Analyse de l'impact de la performance fournisseurs sur la rotation des stocks et la marge commerciale, du diagnostic à la restitution.

**Date :** Septembre 2026

---

## 1. Contexte et objectif

Ce rapport présente les résultats de l'analyse exploratoire (EDA) menée sur les 15 tables nettoyées du jeu de données AdventureWorks, en préparation de la modélisation Power BI. L'objectif est de diagnostiquer la qualité des données (valeurs manquantes, doublons, intégrité référentielle, cohérence logique) avant toute analyse ou visualisation, conformément à la démarche « du diagnostic à la restitution » du projet.

---

## 2. Périmètre des données

Le jeu de données comprend **15 tables** réparties sur trois domaines fonctionnels :

| Domaine | Tables |
|---|---|
| **Achat** | Vendor, ProductVendor, PurchaseOrderHeader, PurchaseOrderDetail, ShipMethod |
| **Produit** | Location, Product, ProductInventory, ProductCategory, ProductSubcategory |
| **Vente** | Customer, Person, SalesOrderHeader, SalesOrderDetail, SalesTerritory |

Les données ont été extraites de fichiers CSV bruts sans en-tête, avec des délimiteurs non standards (tabulation, ou délimiteur personnalisé `+|`/`&|` pour `Person.csv`), puis structurées via un script de nettoyage (`addHeaders.py`) avant cette phase de diagnostic.

---

## 3. Intégrité référentielle

L'ensemble des relations clé-primaire / clé-étrangère testées entre les tables sont **validées à 100%** : aucune valeur orpheline détectée.

| Relation | Statut |
|---|---|
| PurchaseOrderDetail.productid → Product.productid | ✅ OK |
| SalesOrderDetail.productid → Product.productid | ✅ OK |
| PurchaseOrderHeader.vendorid → Vendor.businessentityid | ✅ OK |
| ProductVendor.businessentityid → Vendor.businessentityid | ✅ OK |
| ProductVendor.productid → Product.productid | ✅ OK |
| Product.productsubcategoryid → ProductSubcategory.productsubcategoryid | ✅ OK |
| ProductSubcategory.productcategoryid → ProductCategory.productcategoryid | ✅ OK |
| Customer.personid → Person.businessentityid | ✅ OK |
| SalesOrderHeader.customerid → Customer.customerid | ✅ OK |
| SalesOrderDetail.salesorderid → SalesOrderHeader.salesorderid | ✅ OK |
| ProductInventory.locationid → Location.locationid | ✅ OK |

## 4. Relation inter tables

Tables de faits (5) — événements métier avec mesures agrégeables

Table	Grain
PurchaseOrderHeader	1 ligne = 1 commande d'achat
PurchaseOrderDetail	1 ligne = 1 ligne de commande d'achat (produit × quantité)
SalesOrderHeader	1 ligne = 1 commande de vente
SalesOrderDetail	1 ligne = 1 ligne de commande de vente
ProductInventory	1 ligne = 1 stock instantané (produit × emplacement)



Tables de dimension (7) — attributs descriptifs, relativement statiques

Table	Décrit
Vendor	le fournisseur
Product	le produit
ShipMethod	le mode de transport
Location	l'emplacement d'entrepôt
Customer	le client
Person	la personne physique
SalesTerritory	le territoire de vente

Extensions de dimension / hiérarchie en flocon (2)

Table	Rôle
ProductCategory	catégorie de niveau supérieur (parent de ProductSubcategory)
ProductSubcategory	sous-catégorie (parent de Product)

Table pont (1)

Table	Rôle
ProductVendor	relie Vendor ↔ Product (relation many-to-many : quel fournisseur fournit quel produit, à quel prix, avec quel délai)

Conclusion

Le modèle relationnel en étoile/flocon (5 tables de faits, 7 tables de dimension, 2 tables d'extension hiérarchique — ProductCategory/ProductSubcategory —, 1 table pont ProductVendor) repose sur des clés cohérentes et peut être construit sans risque de perte de lignes lors des jointures dans Power BI.
---

## 5. Cohérence logique

| Vérification | Résultat |
|---|---|
| PurchaseOrderHeader : orderdate ≤ shipdate | ✅ Cohérent |
| SalesOrderHeader : orderdate ≤ shipdate | ✅ Cohérent |
| SalesOrderHeader : orderdate ≤ duedate | ✅ Cohérent |
| Valeurs négatives (linetotal, standardcost, listprice) | ✅ Aucune détectée |

Aucune anomalie temporelle ou de signe n'a été détectée sur les champs testés.

---

## 5. Analyse des valeurs manquantes

### 5.1 Valeurs manquantes attendues (logique métier)

La majorité des valeurs manquantes identifiées reflètent des règles métier normales et ne nécessitent **aucun traitement correctif** :

| Table.Champ | Taux | Explication |
|---|---|---|
| Vendor.purchasingwebserviceurl | 94.2% | Tous les fournisseurs ne disposent pas d'une API |
| Customer.storeid / personid | 93.3% / 3.5% | Relation mutuellement exclusive : client individuel (personid) vs client via magasin (storeid) |
| Product.discontinueddate | 100% | Aucun produit n'est actuellement arrêté dans ce jeu de données |
| Person.title / suffix / middlename | 94.9% / 99.7% / 42.6% | Champs facultatifs sur l'état civil |
| SalesOrderHeader.comment | 100% | Champ jamais renseigné dans ce jeu de données |
| SalesOrderHeader.purchaseordernumber / salespersonid | 87.9% | Toutes les commandes ne sont pas rattachées à un commercial ou un bon de commande externe |

### 5.2 Investigation approfondie : Product (color, size, productline)

Ces trois champs affichent des taux de valeurs manquantes élevés (41% à 65%). Une analyse croisée avec la hiérarchie de catégories (ProductCategory → ProductSubcategory → Product) permet d'expliquer ce phénomène :

- **Components (composants)** : quasi-totalité sans couleur, taille ni ligne de produit — logique, un roulement ou une manivelle n'a pas de variation d'apparence.
- **Bikes et Clothing** : couleur et taille quasi systématiquement renseignées — logique, ce sont des attributs de choix pour le client final.
- **Accessories** : catégorie hétérogène — 82.8% sans couleur et 96.6% sans taille (articles fonctionnels : pompes, antivols, éclairages, gourdes), mais une minorité (~17%) présente une couleur (casques, sacoches), reflétant une variation d'apparence pertinente pour ces articles précis.
- **Cas particulier** : le champ `size` du produit « Hydration Pack – 70 oz. » encode en réalité une capacité (70 oz.) et non une taille vestimentaire — illustration d'une réutilisation du champ selon le type de produit.

**Conclusion :** les valeurs manquantes sur `color`, `size` et `productline` ne constituent pas une anomalie de qualité des données, mais reflètent fidèlement la diversité du catalogue produit (véhicules complets vs. composants vs. accessoires).

### 5.3 ProductInventory.shelf (27.1% manquant)

Anomalie déjà documentée lors du nettoyage initial : le champ `shelf` présente des valeurs manquantes malgré une contrainte NOT NULL en base source. Traité en amont par remplissage avec la valeur `"N/A"`.

---

## 6. Diagnostic — Performance fournisseurs

| Indicateur | Résultat |
|---|---|
| Délai de livraison moyen | 9.05 jours (médiane : 9 jours) |
| Délai de livraison max | 25 jours |
| Commandes avec délai négatif | 0 |
| Commandes sans date d'expédition | 0 |
| Taux de rejet global | 3.10% |
| Cohérence linetotal (PurchaseOrderDetail) | ✅ Conforme (orderqty × unitprice) |

**Observation :** la distribution du délai de livraison est très concentrée (écart-type de 0.87 jour), à l'exception de quelques commandes atteignant 25 jours — ces cas mériteront une investigation ciblée par fournisseur dans la phase d'analyse.

---

## 7. Diagnostic — Rotation des stocks

| Indicateur | Résultat |
|---|---|
| Stock moyen par produit | 314 unités |
| Stock médian | 299 unités |
| Produits sans enregistrement d'inventaire | 72 |
| Produits sous le seuil de sécurité (safetystocklevel) | **968** |
| Valeurs négatives en stock | 0 |

**⚠️ Point d'attention majeur :** un nombre élevé de lignes (968) présente un stock inférieur au seuil de sécurité défini. Ce chiffre dépasse le nombre total de produits (504), ce qui indique que ce calcul résulte d'une jointure multipliant les lignes (un produit peut apparaître dans plusieurs emplacements de stock). **Ce point nécessite une correction méthodologique** (agrégation du stock par produit avant comparaison au seuil) avant d'être présenté comme indicateur définitif dans le tableau de bord.

Les 72 produits sans enregistrement d'inventaire devront être identifiés individuellement (probablement des produits non stockés physiquement, ex. services ou composants virtuels).

---

## 8. Diagnostic — Marge commerciale

| Indicateur | Résultat |
|---|---|
| Taux de marge moyen | 29.1% |
| Taux de marge médian | 35.2% |
| Taux de marge minimum | **-172.8%** |
| Lignes en marge négative (vente à perte) | **29 154 lignes (24.0%)** |
| Cohérence linetotal (SalesOrderDetail) | **3 282 lignes incohérentes (2.7%)** |

**⚠️ Anomalie critique identifiée :** près d'un quart des lignes de vente affichent une marge négative, et environ 3 000 lignes présentent un écart entre le `linetotal` déclaré et le calcul `orderqty × unitprice`.

**Hypothèse retenue :** ces deux anomalies partagent probablement une cause commune — le champ `unitpricediscount` (remise appliquée à la ligne) n'est pas pris en compte dans les calculs de vérification. La formule correcte devrait être :

```
linetotal attendu = orderqty × unitprice × (1 − unitpricediscount)
```

**Action à mener :** recalculer le taux de marge et la vérification de cohérence en intégrant `unitpricediscount`, puis relancer le diagnostic pour confirmer si l'anomalie disparaît. *Ce point reste à valider — investigation en cours au moment de la rédaction de ce rapport.*

---

## 9. Synthèse et recommandations

| Constat | Statut | Action recommandée |
|---|---|---|
| Intégrité référentielle des 15 tables | ✅ Validée | Aucune |
| Cohérence des dates et des montants (hors marge) | ✅ Validée | Aucune |
| Valeurs manquantes Product (color, size, productline) | ✅ Expliquées | Aucun traitement correctif ; documenter dans le dictionnaire de données |
| Champs à 100% ou quasi-100% manquants (comment, discontinueddate) | ✅ Identifiés | Masquer dans la vue de rapport Power BI |
| ProductInventory.shelf manquant (27%) | ✅ Déjà traité | RAS |
| Produits sous seuil de sécurité (968) | ⚠️ À corriger | Revoir la méthode de calcul (agrégation par produit) |
| Marge négative (24% des lignes) | 🔴 À résoudre | Intégrer `unitpricediscount` dans le calcul, revalider |
| Incohérence linetotal (2.7% des lignes) | 🔴 À résoudre | Idem — probablement même cause racine |

Ce diagnostic constitue la base factuelle sur laquelle s'appuiera la construction du modèle de données Power BI et la définition des mesures DAX (marge, rotation des stocks, performance fournisseurs).