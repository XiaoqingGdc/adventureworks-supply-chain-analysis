# Dictionnaire de données du projet AdventureWorks

Source des définitions officielles : dépôt GitHub officiel de Microsoft.
**Colonnes ajoutées dans cette version : le type et la contrainte réellement utilisés dans `createbdd.py` (base SQLite du projet).** Quand le script diffère de la définition officielle (contrainte non reprise, valeur par défaut différente, table non créée...), c'est signalé dans la colonne « Remarque d'implémentation ».

> Règle générale de conversion effectivement appliquée dans le script :
> `int/smallint/tinyint` → `INTEGER` | `money/smallmoney` → `REAL` | `bit` → `INTEGER` (0/1) | `nvarchar/varchar/nchar/char` → `VARCHAR(n)` ou `CHAR(n)` (longueur conservée) | `datetime` → `DATETIME` | `uniqueidentifier` → `TEXT`
> ⚠️ SQLite ne vérifie pas nativement les `CHECK` de plage de valeurs indiqués dans la doc officielle (ex. CreditRating 1~5) : ils ne sont **pas** repris dans `createbdd.py`, à valider soi-même côté application/pandas si besoin.

---

## 1. Schéma Purchasing (Achats)

### 1.1 purchasing.Vendor (Fournisseur)
| Champ officiel | Colonne SQLite | Type SQLite réel | Contrainte réelle | Description |
|---|---|---|---|---|
| BusinessEntityID | businessentityid | INTEGER | **PRIMARY KEY NOT NULL** | ID du fournisseur |
| AccountNumber | accountnumber | VARCHAR(15) | NOT NULL | Numéro de compte |
| Name | name | VARCHAR(50) | NOT NULL | Nom du fournisseur |
| CreditRating | creditrating | INTEGER | NOT NULL | Note de crédit, 1 = meilleure, 5 = pire (plage 1~5 non vérifiée par SQLite) |
| PreferredVendorStatus | preferredvendorstatus | INTEGER | NOT NULL, DEFAULT 1 | Fournisseur préféré ou non (0/1) |
| ActiveFlag | activeflag | INTEGER | NOT NULL, DEFAULT 1 | Actif ou non (0/1) |
| PurchasingWebServiceURL | purchasingwebserviceurl | TEXT | NULL | Très souvent vide, conservé tel quel |
| ModifiedDate | modifieddate | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |



### 1.2 purchasing.ShipMethod (Mode d'expédition)
| Champ officiel | Colonne SQLite | Type SQLite réel | Contrainte réelle | Description |
|---|---|---|---|---|
| ShipMethodID | shipmethodid | INTEGER | **PRIMARY KEY NOT NULL** | ID de Mode d'expédition|
| Name | name | VARCHAR(50) | NOT NULL | Nom du mode d'expédition |
| ShipBase | shipbase | REAL | NOT NULL, DEFAULT 0 | Frais de port de base |
| ShipRate | shiprate | REAL | NOT NULL, DEFAULT 0 | Taux additionnel |
| rowguid | rowguid | TEXT | NOT NULL | Identifiant technique de réplication (à ignorer pour l'analyse) |
| ModifiedDate | modifieddate | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |

### 1.3 purchasing.ProductVendor (Produit-Fournisseur)
| Champ officiel | Colonne SQLite | Type SQLite réel | Contrainte réelle | Description |
|---|---|---|---|---|
| ProductID | productid | INTEGER | NOT NULL, **PK composite** | FK→Product |
| BusinessEntityID | businessentityid | INTEGER | NOT NULL, **PK composite** | FK→Vendor |
| AverageLeadTime | averageleadtime | INTEGER | NOT NULL | **Délai moyen de livraison (jours)** |
| StandardPrice | standardprice | REAL | NOT NULL | Prix standard |
| LastReceiptCost | lastreceiptcost | REAL | NULL | Coût réel de la dernière réception |
| LastReceiptDate | lastreceiptdate | DATETIME | NULL | Date de la dernière réception |
| MinOrderQty | minorderqty | INTEGER | NOT NULL | Quantité minimale de commande |
| MaxOrderQty | maxorderqty | INTEGER | NOT NULL | Quantité maximale de commande |
| OnOrderQty | onorderqty | INTEGER | NULL | Quantité en cours de commande |
| UnitMeasureCode | unitmeasurecode | CHAR(3) | NOT NULL | Unité de mesure (CS/CTN/EA, etc.) |
| ModifiedDate | modifieddate | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |

PRIMARY KEY (productid, businessentityid) ; FOREIGN KEY productid→Product, businessentityid→Vendor.

### 1.4 purchasing.PurchaseOrderHeader (En-tête de commande d'achat)
| Champ officiel | Colonne SQLite | Type SQLite réel | Contrainte réelle | Description |
|---|---|---|---|---|
| PurchaseOrderID | purchaseorderid | INTEGER | **PRIMARY KEY NOT NULL** | ID de la commande d'achat |
| RevisionNumber | revisionnumber | INTEGER | NOT NULL, DEFAULT 0 | Numéro de révision de la commande |
| Status | status | INTEGER | NOT NULL, DEFAULT 1 | **1=En attente, 2=Approuvé, 3=Rejeté, 4=Terminé** |
| EmployeeID | employeeid | INTEGER | NOT NULL | Employé ayant passé la commande — ⚠️ pas de FK : la table Employee n'est pas créée dans ce projet |
| VendorID | vendorid | INTEGER | NOT NULL, FK→Vendor(businessentityid) | Fournisseur concerné par la commande |
| ShipMethodID | shipmethodid | INTEGER | NOT NULL, FK→ShipMethod(shipmethodid) | Mode d'expédition utilisé |
| OrderDate | orderdate | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Date de passation de la commande |
| ShipDate | shipdate | DATETIME | NULL | Date d'expédition effective |
| SubTotal | subtotal | REAL | NOT NULL, DEFAULT 0 | Montant hors taxes et frais de port |
| TaxAmt | taxamt | REAL | NOT NULL, DEFAULT 0 | Montant de la taxe |
| Freight | freight | REAL | NOT NULL, DEFAULT 0 | Frais de port |
| TotalDue | totaldue | REAL | NULL | ⚠️ n'est **pas** une colonne calculée en SQLite : à calculer soi-même (SubTotal+TaxAmt+Freight) lors du remplissage |
| ModifiedDate | modifieddate | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Date de dernière modification de l'enregistrement |

### 1.5 purchasing.PurchaseOrderDetail (Détail de commande d'achat)
| Champ officiel | Colonne SQLite | Type SQLite réel | Contrainte réelle | Description |
|---|---|---|---|---|
| PurchaseOrderID | purchaseorderid | INTEGER | NOT NULL, **PK composite**, FK→PurchaseOrderHeader | Commande d'achat à laquelle appartient la ligne |
| PurchaseOrderDetailID | purchaseorderdetailid | INTEGER | NOT NULL, **PK composite** | Numéro de la ligne au sein de la commande |
| DueDate | duedate | DATETIME | NOT NULL | Date de livraison attendue pour cette ligne |
| OrderQty | orderqty | INTEGER | NOT NULL | Quantité commandée |
| ProductID | productid | INTEGER | NOT NULL, FK→Product | Produit commandé |
| UnitPrice | unitprice | REAL | NOT NULL | Prix d'achat unitaire (coût) |
| LineTotal | — | — | ⚠️ **colonne non créée** dans la table SQLite | À calculer avec pandas = OrderQty × UnitPrice |
| ReceivedQty | receivedqty | REAL | NOT NULL | Quantité réellement reçue |
| RejectedQty | rejectedqty | REAL | NOT NULL | Quantité rejetée |
| StockedQty | stockedqty | REAL | NOT NULL | ⚠️ stockée en dur (pas calculée automatiquement) = ReceivedQty − RejectedQty à renseigner soi-même |
| ModifiedDate | modifieddate | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Date de dernière modification de l'enregistrement |

---

## 2. Schéma Produit

### 2.1 Product (Produit)
| Champ officiel | Colonne SQLite | Type SQLite réel | Contrainte réelle | Description |
|---|---|---|---|---|
| ProductID | productid | INTEGER | **PRIMARY KEY NOT NULL** | ID du produit |
| Name | name | VARCHAR(50) | NOT NULL | Nom du produit |
| ProductNumber | productnumber | VARCHAR(25) | NOT NULL | Référence/code produit |
| MakeFlag | makeflag | INTEGER | NOT NULL, DEFAULT 1 | **1=Fabriqué en interne, 0=Acheté** (filtrer MakeFlag=0 pour l'analyse achats) |
| FinishedGoodsFlag | finishedgoodsflag | INTEGER | NOT NULL, DEFAULT 1 | Produit fini ou non |
| Color | color | VARCHAR(15) | NULL | Couleur du produit |
| SafetyStockLevel | safetystocklevel | INTEGER | NOT NULL | Niveau de stock de sécurité |
| ReorderPoint | reorderpoint | INTEGER | NOT NULL | Point de commande |
| StandardCost | standardcost | REAL | NOT NULL | Coût standard interne |
| ListPrice | listprice | REAL | NOT NULL | Prix catalogue officiel |
| Size | size | VARCHAR(5) | NULL | Taille du produit |
| SizeUnitMeasureCode | sizeunitmeasurecode | CHAR(3) | NULL | Unité de mesure de la taille |
| WeightUnitMeasureCode | weightunitmeasurecode | CHAR(3) | NULL | Unité de mesure du poids |
| Weight | weight | REAL | NULL | Poids du produit |
| DaysToManufacture | daystomanufacture | INTEGER | NOT NULL | Nombre de jours de fabrication nécessaires |
| ProductLine | productline | CHAR(2) | NULL | Gamme de produit |
| Class | class | CHAR(2) | NULL | Classe du produit (L/M/H) |
| Style | style | CHAR(2) | NULL | Style du produit (W/M/U) |
| ProductSubcategoryID | productsubcategoryid | INTEGER | NULL, FK→ProductSubcategory | Sous-catégorie du produit |
| ProductModelID | productmodelid | INTEGER | NULL | ⚠️ pas de FK : la table ProductModel n'est pas créée dans ce projet |
| SellStartDate | sellstartdate | DATETIME | NOT NULL | Date de début de commercialisation |
| SellEndDate | sellenddate | DATETIME | NULL | Date de fin de commercialisation |
| DiscontinuedDate | discontinueddate | DATETIME | NULL | Date d'arrêt de production, à exclure éventuellement lors de l'analyse |
| rowguid | rowguid | TEXT | NOT NULL | Identifiant technique de réplication (à ignorer pour l'analyse) |
| ModifiedDate | modifieddate | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Date de dernière modification de l'enregistrement |

### 2.2 ProductCategory (Catégorie de produit) — *table non présente dans le dictionnaire d'origine, ajoutée ici*
| Colonne SQLite | Type SQLite réel | Contrainte réelle | Description |
|---|---|---|---|
| productcategoryid | INTEGER | **PRIMARY KEY NOT NULL** | ID de la catégorie |
| name | VARCHAR(50) | NOT NULL | Nom de la catégorie |
| rowguid | TEXT | NOT NULL | Identifiant technique de réplication (à ignorer pour l'analyse) |
| modifieddate | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Date de dernière modification de l'enregistrement |

### 2.3 ProductSubcategory (Sous-catégorie de produit) — *table non présente dans le dictionnaire d'origine, ajoutée ici*
| Colonne SQLite | Type SQLite réel | Contrainte réelle | Description |
|---|---|---|---|
| productsubcategoryid | INTEGER | **PRIMARY KEY NOT NULL** | ID de la sous-catégorie |
| productcategoryid | INTEGER | NOT NULL, FK→ProductCategory | Catégorie parente |
| name | VARCHAR(50) | NOT NULL | Nom de la sous-catégorie |
| rowguid | TEXT | NOT NULL | Identifiant technique de réplication (à ignorer pour l'analyse) |
| modifieddate | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Date de dernière modification de l'enregistrement |

### 2.4 ProductInventory (Inventaire produit)
| Champ officiel | Colonne SQLite | Type SQLite réel | Contrainte réelle | Description |
|---|---|---|---|---|
| ProductID | productid | INTEGER | NOT NULL, **PK composite**, FK→Product | Produit stocké |
| LocationID | locationid | INTEGER | NOT NULL, **PK composite**, FK→Location | Emplacement/poste où le produit est stocké |
| Shelf | shelf | VARCHAR(10) | NOT NULL | Étagère |
| Bin | bin | INTEGER | NOT NULL | Casier/bac |
| Quantity | quantity | INTEGER | NOT NULL, DEFAULT 0 | Quantité en stock, à agréger par Location pour un même ProductID |
| rowguid | rowguid | TEXT | NOT NULL | Identifiant technique de réplication (à ignorer pour l'analyse) |
| ModifiedDate | modifieddate | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Date de dernière modification de l'enregistrement |

### 2.5 Location (Site/Atelier)
| Champ officiel | Colonne SQLite | Type SQLite réel | Contrainte réelle | Description |
|---|---|---|---|---|
| LocationID | locationid | INTEGER | **PRIMARY KEY NOT NULL** | ⚠️ correspond à des postes internes à l'usine, pas à des entrepôts géographiques |
| Name | name | VARCHAR(50) | NOT NULL | |
| CostRate | costrate | REAL | NOT NULL, DEFAULT 0 | Coût horaire du poste, 0 pour les postes de stockage |
| Availability | availability | REAL | NOT NULL, DEFAULT 0 | Heures disponibles |
| ModifiedDate | modifieddate | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |

---

## 3. Schéma Sales (Ventes)

### 3.1 sales.Customer (Client)
| Champ officiel | Colonne SQLite | Type SQLite réel | Contrainte réelle | Description |
|---|---|---|---|---|
| CustomerID | customerid | INTEGER | **PRIMARY KEY NOT NULL** | ID du client |
| PersonID | personid | INTEGER | NULL, FK→Person(businessentityid) | Non nul si le client est un particulier |
| StoreID | storeid | INTEGER | NULL | ⚠️ pas de FK : la table Store n'est pas créée dans ce projet |
| TerritoryID | territoryid | INTEGER | NULL, FK→SalesTerritory | Territoire de vente rattaché au client |
| AccountNumber | — | — | ⚠️ colonne non créée | Colonne calculée officielle ('AW' + CustomerID complété de zéros), non reprise dans le schéma SQLite |
| rowguid | rowguid | TEXT | NOT NULL | Identifiant technique de réplication (à ignorer pour l'analyse) |
| ModifiedDate | modifieddate | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Date de dernière modification de l'enregistrement |


### 3.2 sales.SalesOrderHeader (En-tête de commande client)
| Champ officiel | Colonne SQLite | Type SQLite réel | Contrainte réelle | Description |
|---|---|---|---|---|
| SalesOrderID | salesorderid | INTEGER | **PRIMARY KEY NOT NULL** | ID de la commande client |
| RevisionNumber | revisionnumber | INTEGER | NOT NULL, DEFAULT 0 | Numéro de révision de la commande |
| OrderDate | orderdate | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Date de passation de la commande |
| DueDate | duedate | DATETIME | NOT NULL | Date de livraison attendue |
| ShipDate | shipdate | DATETIME | NULL | Date d'expédition effective |
| Status | status | INTEGER | NOT NULL, DEFAULT 1 | Plage 0~8 de la doc officielle non vérifiée par SQLite |
| OnlineOrderFlag | onlineorderflag | INTEGER | NOT NULL, DEFAULT 1 | Commande passée en ligne ou non (0/1) |
| SalesOrderNumber | — | — | ⚠️ colonne non créée | Colonne calculée officielle ('SO'+SalesOrderID), non reprise |
| PurchaseOrderNumber | purchaseordernumber | VARCHAR(25) | NULL | Numéro de bon de commande du client |
| AccountNumber | accountnumber | VARCHAR(15) | NULL | Numéro de compte du client |
| CustomerID | customerid | INTEGER | NOT NULL, FK→Customer | Client ayant passé la commande |
| SalesPersonID | salespersonid | INTEGER | NULL | ⚠️ pas de FK : table SalesPerson non créée |
| TerritoryID | territoryid | INTEGER | NULL, FK→SalesTerritory | Territoire de vente rattaché à la commande |
| BillToAddressID | billtoaddressid | INTEGER | NOT NULL | ⚠️ pas de FK : table Address non créée |
| ShipToAddressID | shiptoaddressid | INTEGER | NOT NULL | ⚠️ pas de FK : table Address non créée |
| ShipMethodID | shipmethodid | INTEGER | NOT NULL, FK→ShipMethod | Mode d'expédition utilisé |
| CreditCardID | creditcardid | INTEGER | NULL | ⚠️ pas de FK : table CreditCard non créée |
| CreditCardApprovalCode | creditcardapprovalcode | VARCHAR(15) | NULL | Code d'approbation de la carte bancaire |
| CurrencyRateID | currencyrateid | INTEGER | NULL | ⚠️ pas de FK : table CurrencyRate non créée |
| SubTotal | subtotal | REAL | NOT NULL, DEFAULT 0 | Montant hors taxes et frais de port |
| TaxAmt | taxamt | REAL | NOT NULL, DEFAULT 0 | Montant de la taxe |
| Freight | freight | REAL | NOT NULL, DEFAULT 0 | Frais de port |
| TotalDue | totaldue | REAL | NULL | ⚠️ n'est pas calculée automatiquement (SubTotal+TaxAmt+Freight à renseigner soi-même) |
| Comment | comment | VARCHAR(128) | NULL | Commentaire libre sur la commande |
| rowguid | rowguid | TEXT | NOT NULL | Identifiant technique de réplication (à ignorer pour l'analyse) |
| ModifiedDate | modifieddate | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Date de dernière modification de l'enregistrement |

### 3.3 sales.SalesOrderDetail (Détail de commande client)
| Champ officiel | Colonne SQLite | Type SQLite réel | Contrainte réelle | Description |
|---|---|---|---|---|
| SalesOrderID | salesorderid | INTEGER | NOT NULL, **PK composite**, FK→SalesOrderHeader | Commande client à laquelle appartient la ligne |
| SalesOrderDetailID | salesorderdetailid | INTEGER | NOT NULL, **PK composite** | Numéro de la ligne au sein de la commande |
| CarrierTrackingNumber | carriertrackingnumber | VARCHAR(25) | NULL | Numéro de suivi transporteur |
| OrderQty | orderqty | INTEGER | NOT NULL | Quantité commandée |
| ProductID | productid | INTEGER | NOT NULL, FK→Product | Produit vendu |
| SpecialOfferID | specialofferid | INTEGER | NOT NULL | ⚠️ pas de FK : table SpecialOffer non créée |
| UnitPrice | unitprice | REAL | NOT NULL | Prix de vente unitaire |
| UnitPriceDiscount | unitpricediscount | REAL | NOT NULL, DEFAULT 0 | Taux de remise |
| LineTotal | — | — | ⚠️ **colonne non créée** | À calculer avec pandas = UnitPrice×(1−UnitPriceDiscount)×OrderQty |
| rowguid | rowguid | TEXT | NOT NULL | Identifiant technique de réplication (à ignorer pour l'analyse) |
| ModifiedDate | modifieddate | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Date de dernière modification de l'enregistrement |

### 3.4 sales.SalesTerritory (Territoire de vente)
| Champ officiel | Colonne SQLite | Type SQLite réel | Contrainte réelle | Description |
|---|---|---|---|---|
| TerritoryID | territoryid | INTEGER | **PRIMARY KEY NOT NULL** | ID du territoire |
| Name | name | VARCHAR(50) | NOT NULL | Nom du territoire |
| CountryRegionCode | countryregioncode | VARCHAR(3) | NOT NULL | Code pays/région |
| Group | "group" | VARCHAR(50) | NOT NULL | ⚠️ mot réservé SQL → entouré de guillemets doubles dans le script (`"group"`) — Regroupement géographique du territoire |
| SalesYTD | salesytd | REAL | NOT NULL, DEFAULT 0 | Chiffre de vente officiel, utilisable pour recouper avec les calculs personnels |
| SalesLastYear | saleslastyear | REAL | NOT NULL, DEFAULT 0 | Chiffre de vente de l'année précédente |
| CostYTD | costytd | REAL | NOT NULL, DEFAULT 0 | Coût cumulé de l'année en cours |
| CostLastYear | costlastyear | REAL | NOT NULL, DEFAULT 0 | Coût cumulé de l'année précédente |
| rowguid | rowguid | TEXT | NOT NULL | Identifiant technique de réplication (à ignorer pour l'analyse) |
| ModifiedDate | modifieddate | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Date de dernière modification de l'enregistrement |

---

## 4. Schéma Person (Personne)

### 4.1 Person
| Champ officiel | Colonne SQLite | Type SQLite réel | Contrainte réelle | Description |
|---|---|---|---|---|
| BusinessEntityID | businessentityid | INTEGER | **PRIMARY KEY NOT NULL** | ID de la personne |
| PersonType | persontype | CHAR(2) | NOT NULL | IN=client particulier, SC=contact magasin, EM=employé, SP=commercial, VC=contact fournisseur, GC=contact général (valeurs autorisées non vérifiées par SQLite) |
| NameStyle | namestyle | INTEGER | NOT NULL, DEFAULT 0 | Format d'affichage du nom (occidental/oriental) |
| Title | title | VARCHAR(8) | NULL | Civilité (M., Mme, etc.) |
| FirstName | firstname | VARCHAR(50) | NOT NULL | Prénom |
| MiddleName | middlename | VARCHAR(50) | NULL | Second prénom |
| LastName | lastname | VARCHAR(50) | NOT NULL | Nom de famille |
| Suffix | suffix | VARCHAR(10) | NULL | Suffixe (Jr., Sr., etc.) |
| EmailPromotion | emailpromotion | INTEGER | NOT NULL, DEFAULT 0 | Plage 0~2 de la doc officielle non vérifiée par SQLite |
| AdditionalContactInfo | additionalcontactinfo | TEXT | NULL | Informations de contact complémentaires (XML à l'origine) |
| Demographics | demographics | TEXT | NULL | Enquête individuelle (XML à l'origine, structure IndividualSurvey) — contient uniquement TotalPurchaseYTD (montant d'achat cumulé sur l'année), quasi toujours à 0 |
| rowguid | rowguid | TEXT | NOT NULL | Identifiant technique de réplication (à ignorer pour l'analyse) |
| ModifiedDate | modifieddate | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Date de dernière modification de l'enregistrement |

---

## 5. Formules clés à consulter directement pour les requêtes SQL

| Indicateur | Formule |
|---|---|
| Délai de livraison achats | `PurchaseOrderHeader.shipdate - orderdate` |
| Taux de respect des délais | part des commandes où `délai réel ≤ ProductVendor.averageleadtime` |
| Taux de complétude de livraison | `PurchaseOrderDetail.receivedqty / orderqty` |
| Taux de rejet qualité | `PurchaseOrderDetail.rejectedqty / orderqty` |
| Quantité réellement mise en stock | `PurchaseOrderDetail.stockedqty` — ⚠️ **pas calculée automatiquement en SQLite**, à renseigner/valider soi-même (= receivedqty − rejectedqty) |
| Montant de vente réel | `LineTotal` — ⚠️ **colonne absente du schéma SQLite**, à calculer avec pandas = unitprice×(1−unitpricediscount)×orderqty |
| Marge brute (par ligne) | `LineTotal (calculé) − (PurchaseOrderDetail.unitprice × orderqty)` (nécessite de relier au dernier prix d'achat par productid) |
| Taux de rotation des stocks | `quantité vendue sur la période / MOYENNE(SOMME(ProductInventory.quantity) OÙ locationid = ID de l'entrepôt de produits finis)` |
| Alerte de rupture de stock | `SOMME(quantity) OÙ locationid=entrepôt de produits finis < Product.reorderpoint` |

⚠️ **Recommandations de filtrage avant analyse** :
- Pour l'analyse achats, ne conserver que les commandes avec `PurchaseOrderHeader.status = 4` (Terminé)
- Pour l'analyse de stock/réapprovisionnement, ne conserver dans `ProductInventory` que les enregistrements dont `locationid` correspond à « Finished Goods Storage »
- Pour l'analyse de la chaîne d'achats, filtrer d'abord les produits avec `Product.makeflag = 0` (achetés en externe)

---

## 6. Écarts entre la documentation officielle et l'implémentation réelle (`createbdd.py`)

- **Tables non créées dans ce projet** : `Store`, `ProductCostHistory`, `ProductListPriceHistory`, ainsi que toutes les tables référencées mais absentes (`Employee`, `Address`, `SalesPerson`, `CreditCard`, `CurrencyRate`, `SpecialOffer`, `ProductModel`) → les clés étrangères correspondantes ne sont pas déclarées dans le script.
- **Tables ajoutées / non documentées dans le dictionnaire d'origine** : `ProductCategory`, `ProductSubcategory` (nécessaires pour relier `Product` à sa catégorie).
- **Colonnes calculées officielles non reprises en SQLite** (SQLite ne gère pas nativement les colonnes calculées) : `PurchaseOrderHeader.TotalDue`, `PurchaseOrderDetail.LineTotal`, `SalesOrderHeader.TotalDue`, `SalesOrderHeader.SalesOrderNumber`, `SalesOrderDetail.LineTotal`, `Customer.AccountNumber` → à calculer manuellement avec pandas lors du nettoyage, avant écriture en base.
- **`PurchaseOrderDetail.StockedQty`** : bien que documentée comme colonne calculée, elle existe comme colonne stockée « en dur » dans le script → à remplir soi-même.
- **Types simplifiés** : tous les types numériques entiers (`int/smallint/tinyint/bit`) deviennent `INTEGER` ; tous les types monétaires (`money/smallmoney`) deviennent `REAL` ; les longueurs de chaînes (`varchar(n)`) sont changés.
- **Mot réservé** : `SalesTerritory.Group` est mappé sur la colonne `"group"` (entre guillemets doubles) car `GROUP` est un mot réservé SQLite.

