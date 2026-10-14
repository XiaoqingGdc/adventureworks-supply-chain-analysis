# Rapport de risques — AdventureWorks Supply Chain Analysis

## Objectif

Ce document recense les risques et limites identifiés au cours de l'analyse (EDA, clustering fournisseurs, indicateur de risque de rupture par couverture en jours), afin de contextualiser les résultats présentés dans le dashboard Power BI et les modèles de machine learning. L'objectif est de documenter de façon transparente les hypothèses prises lorsque les données présentaient des ambiguïtés ou des lacunes, pour que ces limites soient explicites lors de la présentation orale.

---

## 1. Limites liées aux données de délai de livraison fournisseur

**Constat** : le taux de commandes livrées en retard (`shipdate > duedate`) est de **0,08 %** (7 commandes en retard sur 8 845). Ce taux est trop faible pour constituer un indicateur discriminant de la performance fournisseur.

**Hypothèse retenue** : les dates `duedate` de la table `PurchaseOrderDetail` semblent générées selon une règle fixe (probablement un délai standard appliqué systématiquement), plutôt que refléter des contraintes métier réelles variables. Le champ `late_flag` a donc été **écarté des features de clustering**.

**Impact** : la performance fournisseur a été évaluée principalement via le taux de rejet (`reject_rate`) et le taux de réception (`receipt_rate`), plus discriminants dans ce jeu de données simulé.

---

## 2. Filtrage des fournisseurs à faible volume de commandes

**Constat** : les fournisseurs avec peu de lignes d'achat (≤ 15) affichaient systématiquement un `avg_reject_rate` de 0 % — un artefact statistique lié à la petite taille d'échantillon plutôt qu'à une réelle absence de problème qualité. Note : `total_orders` dans la requête SQL est un `COUNT(*)` sur `PurchaseOrderDetail`, c'est-à-dire un nombre de **lignes d'achat**, pas de commandes.

**Hypothèse retenue** : seuil de filtrage `HAVING COUNT(*) >= 30` (30 lignes d'achat) appliqué avant le K-Means, ce qui ramène l'échantillon clusterisé de 86 fournisseurs ayant des achats à 79.

**Traitement des fournisseurs hors K-Means** : aucun fournisseur n'est laissé de côté. Les 25 fournisseurs non clusterisés sont classés par règle métier (section 5 bis du notebook) :
- **Peu d'historique** (7) : au moins une ligne d'achat mais moins de 30 ;
- **Sans commande** (18) : aucune ligne d'achat (fournisseurs du référentiel sans achat).

Le référentiel complet compte ainsi 104 fournisseurs : 79 (K-Means : Gros volumes 44, Petites séries 22, Généralistes 13) + 25 (règles métier).

**Impact** : « Peu d'historique » signifie « données insuffisantes pour évaluer », **pas** « fournisseur sans risque ». Aucun jugement de risque n'est porté sur ces 7 fournisseurs. Recommandation : les réévaluer une fois davantage d'historique disponible.

---

## 3. Données de stock : agrégation par entrepôt et produits sans enregistrement

**Constat** : sur les 295 produits vendables (`finishedgoodsflag=1`), la répartition est la suivante :
- **83 produits achetés en externe** (`makeflag=0`) : tous ont un enregistrement de stock ;
- **140 produits fabriqués en interne** (`makeflag=1`) avec stock ;
- **72 produits sans aucun enregistrement** dans `ProductInventory` (tous entrepôts confondus).

**Erreur corrigée** : une première version de l'analyse ne retenait que l'entrepôt `locationid=7`. Ce filtre était erroné : le stock d'un produit est réparti sur plusieurs entrepôts et doit être calculé par `SUM(quantity)` sur l'ensemble des entrepôts. Il avait fait apparaître à tort 29 produits externes « sans stock », un taux de rupture de 39,8 % et une accuracy de 95 % — des artefacts, abandonnés.

**Hypothèse retenue** : un produit sans enregistrement n'est **pas** considéré comme ayant un stock nul (l'absence de ligne est une donnée manquante, pas une mesure). Ces 72 produits sont signalés mais exclus des calculs de rupture. Dans Power BI, la mesure `Stock` utilisait `COALESCE(...,0)`, ce qui transformait les données manquantes en stock 0 : 77 produits « sous le seuil » = 5 réels + 72 manquants. La mesure a été corrigée (`SUM(quantity)` sans `COALESCE`).

**Impact** : le périmètre d'analyse du risque de rupture est de 83 produits achetés en externe, tous avec stock connu.

---

## 4. Seuil `reorderpoint` peu discriminant — abandon de la classification supervisée

**Constat** : une fois le stock correctement agrégé, **5 produits seulement sur 83 (6 %)** sont sous leur `reorderpoint` ; aucun produit fabriqué en interne ne l'est. Avec 5 cas positifs, un modèle de classification (rupture oui/non) n'est pas viable : trop peu d'exemples, métriques non interprétables.

**Décision** : le modèle a été remplacé par un **indicateur de couverture en jours** : `couverture = stock actuel / ventes moyennes par jour`, comparée au délai d'approvisionnement moyen du fournisseur (`productvendor.averageleadtime`). Un produit est « à risque » si sa couverture est inférieure à son délai. Résultat : **19 produits à risque sur 76** (7 produits sans vente exclus), contre 5 seulement avec le seuil fixe — le `reorderpoint` ne détecte pas les produits à forte rotation.

**Observation complémentaire** : sur les 83 produits externes, `safetystocklevel = reorderpoint × 4/3`, ce qui va à l'encontre de la logique métier (le point de commande devrait être supérieur au stock de sécurité). Ces champs semblent générés par une règle arithmétique ; `safetystocklevel` n'est pas utilisé dans l'indicateur.

**Impact** : la conclusion repose sur un indicateur simple et explicable plutôt que sur un modèle statistique ; le seuil `reorderpoint` ne doit pas être utilisé seul pour piloter les réapprovisionnements.

---

## 4bis. Le fournisseur responsable des pertes réelles n'est pas évalué par le clustering — limite du seuil de filtrage

**Constat** : parmi les produits achetés en externe (`makeflag=0`), la quasi-totalité des pertes commerciales (vente en dessous du coût standard) est concentrée sur un seul fournisseur, **vendorid 1636**, pour un montant de **-195 807 €**, soit **4,3 % de la perte totale de l'entreprise** (-4 546 168 € tous produits confondus, y compris les produits fabriqués en interne).

**Problème méthodologique identifié** : ce fournisseur (vendorid 1636) n'appartient à **aucun des 3 clusters** K-Means (`clustering_fournisseur.ipynb`), car il ne totalise que **10 lignes d'achat**, en dessous du seuil `HAVING COUNT(*) >= 30` appliqué en amont du clustering (cf. section 2). Il est donc classé par règle métier dans le segment **« Peu d'historique »** : ce segment signifie « données insuffisantes pour évaluer », et **aucun jugement de risque** n'est porté sur lui.

**Ce qui rend ce cas notable** : sur ses 10 lignes d'achat, ce fournisseur affiche des indicateurs de performance en apparence excellents — `avg_reject_rate = 0 %`, `avg_receipt_rate = 100 %` — ce qui, s'il avait été inclus, l'aurait probablement classé dans le profil « fournisseur fiable ». Sur ses 10 lignes d'achat, ses indicateurs sont donc les mêmes que ceux d'un fournisseur sans problème. Or c'est précisément ce fournisseur qui est associé aux seules pertes commerciales attribuables à un fournisseur externe dans le jeu de données. Ceci confirme, avec un cas concret, le biais déjà identifié en section 2 : un taux de rejet à 0 % sur un petit échantillon reflète une absence d'opportunité de défaillance observée, pas une garantie de fiabilité.

**Implication méthodologique** : le filtre par volume, nécessaire pour fiabiliser les taux statistiques du clustering, crée un **angle mort** sur les fournisseurs à faible fréquence (segment « Peu d'historique », 7 fournisseurs) — précisément ceux pour lesquels le risque est le plus difficile à évaluer avec les méthodes statistiques classiques. Le classement par règle métier évite de les perdre de vue, mais ne les évalue pas : une évaluation des risques fondée uniquement sur le clustering ne peut pas être considérée comme exhaustive.

**Recommandation** : compléter l'approche statistique par une revue qualitative ciblée des fournisseurs du segment « Peu d'historique », en particulier ceux associés à des lignes de vente à perte, et réévaluation par clustering dès que 30 lignes d'achat sont atteintes.

---

## 5bis. Marge négative — confirmation d'une stratégie de vente à perte (et non d'une anomalie de données)

**Constat initial (EDA)** : 24 % des lignes de `SalesOrderDetail` affichaient une marge négative. L'hypothèse initiale (non prise en compte de `unitpricediscount`) a été testée et **invalidée** : recalculer la marge avec la remise appliquée ne change quasiment rien au nombre de lignes en perte (29 154 → 29 161), car `unitpricediscount` ne fait que réduire davantage un prix déjà remisé — il ne peut pas expliquer un passage sous le coût.

**Investigation approfondie** : la comparaison entre `unitprice` (prix de vente réel), `listprice` (prix catalogue) et `standardcost` (coût standard) révèle que le prix catalogue est presque toujours supérieur au coût (marge normale à ce niveau), mais le **prix de vente réel** tombe fréquemment sous le coût pour certaines références — notamment les produits à forte rotation.

**Exemples représentatifs** (taux de lignes vendues à perte, sur le total des lignes de vente du produit) :

| Produit | Lignes vendues | % vendu à perte |
|---|---|---|
| Road-650 Red, 44 | 2 254 | 88,8 % |
| Road-650 Black, 52 | 2 270 | 86,9 % |
| Road-650 Red, 60 | 2 232 | 79,7 % |
| Long-Sleeve Logo Jersey, L | 6 592 | 72,4 % |
| Short-Sleeve Classic Jersey, XL | 3 864 | 54,8 % |
| AWC Logo Cap | 8 311 | 35,2 % |

**Interprétation retenue** : ce n'est pas une anomalie de qualité des données, mais une **politique de remise commerciale agressive sur les produits à forte rotation** (vélos Road-650, textile logotypé). Deux profils distincts se dégagent :
- **Vente à perte structurelle** (Road-650, Jersey) : la quasi-totalité des ventes se fait sous le coût — probablement une stratégie de volume ou un article d'appel
- **Vente à perte ponctuelle** (AWC Logo Cap) : le produit reste globalement rentable en moyenne, avec des promotions ponctuelles qui passent sous le coût

**Impact sur le projet** : ce constat relie directement les trois axes analytiques du projet — les produits les plus vendus (forte rotation, cf. indicateur de couverture en jours) sont aussi ceux dont la marge est la plus compressée, voire négative. C'est un résultat clé à mettre en avant dans la restitution finale : la performance commerciale (volume) n'est pas alignée avec la performance financière (marge) sur ces références.

---

## 6. Limites de l'indicateur de couverture en jours

**Constat** : l'indicateur repose sur des hypothèses simplificatrices :
- **Cadence de vente** : moyenne sur la période historique observée (`total vendu / nombre de jours`), sans saisonnalité ni tendance ;
- **Stock** : somme de tous les entrepôts, y compris d'éventuels stocks en cours de fabrication ou non disponibles à la vente ;
- **Commandes en cours** : les quantités déjà commandées aux fournisseurs ne sont pas prises en compte, ce qui peut surestimer le risque ;
- **Délai** : `averageleadtime` moyen par produit–fournisseur, sans variabilité ;
- **Exclusions** : 7 produits sans vente (couverture non calculable) et 72 produits sans enregistrement de stock.

**Lien avec les segments fournisseurs** : les 19 produits à risque proviennent de seulement **5 fournisseurs** (1546 : 6 produits ; 1636 : 5 ; 1594 : 5 ; 1676 : 2 ; 1520 : 1), qui totalisent respectivement 9, 10, 9, 15 et 3 lignes d'achat. Tous sont sous le seuil de 30 lignes et sont donc classés « Peu d'historique » : **aucun n'a été évalué par le clustering**. Parmi eux figure le vendorid 1636 (section 4bis), déjà associé aux ventes à perte (AWC Logo Cap, Jerseys). Le risque d'approvisionnement observé est ainsi concentré sur des fournisseurs que l'approche statistique ne couvre pas.

**Impact** : les 19 produits signalés sont des **alertes à vérifier**, pas des ruptures avérées. L'indicateur sert à prioriser (tri par couverture croissante), pas à prévoir une date de rupture. La taille de l'échantillon (76 produits) interdit toute généralisation statistique.

---

## Synthèse des recommandations

| Axe | Recommandation |
|---|---|
| Fournisseurs « Peu d'historique » (7) et « Sans commande » (18) | Ne pas interpréter comme « sans risque » ; réévaluer une fois l'historique d'achats enrichi |
| Couverture des données de stock | Vérifier auprès du système source pourquoi 72 produits finis n'ont aucun enregistrement de stock ; ne pas les traiter comme stock nul |
| Cohérence `reorderpoint`/`safetystocklevel` | Ne pas généraliser les seuils observés à un contexte de gestion de stock réel |
| Fournisseurs à l'origine des 19 produits à risque (5 fournisseurs « Peu d'historique », dont 1636) | Revue qualitative prioritaire de ces 5 fournisseurs (délais, stocks de sécurité, double sourcing), le clustering ne pouvant pas les évaluer |
| Risque de rupture | Piloter les réapprovisionnements par la couverture en jours (19 produits à risque sur 76) plutôt que par le seul `reorderpoint` (5 produits) ; intégrer les commandes en cours et la saisonnalité si le projet est reconduit |
| Vente à perte sur produits à forte rotation | Mettre en avant dans le dashboard (KPI marge par produit/catégorie) ; recommandation métier : revoir la politique de remise sur Road-650 et gammes textile logotypées |
| Fournisseur à l'origine de pertes classé « Peu d'historique » (vendorid 1636, 10 lignes d'achat, non évalué par le clustering) | Revue qualitative ciblée des fournisseurs « Peu d'historique » liés à des ventes à perte, en complément du clustering statistique |

---

*Document rédigé dans le cadre du projet S14 « AdventureWorks Supply Chain Analysis » — à intégrer aux livrables du dossier de risques.*
