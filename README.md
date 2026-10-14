# 📦 AdventureWorks Supply Chain Analysis
<table>
  <tr>
    <td width="140"><img src="img/logo_adventureworks.png" alt="AdventureWorks" width="120"></td>
    <td>Analyse de l'impact de la performance fournisseurs et de la rotation des stocks sur la marge commerciale, du diagnostic à la restitution.</td>
  </tr>
</table>

[![Power BI](https://img.shields.io/badge/Power_BI-Voir_le_rapport_en_ligne-F2C811?logo=powerbi&logoColor=black)](https://app.powerbi.com/view?r=eyJrIjoiMDZlNzNhMDMtYmE1NC00NDc3LTgzODktZjYxNDJkMTkwMjMzIiwidCI6IjQ3YTE4ODE2LTIwNDMtNGNkMC04YmY0LWUwYzk0MmQ4YzJkNiIsImMiOjN9)

[![Dashboard](img/dashboard_vue_ensemble.png)](https://app.powerbi.com/view?r=eyJrIjoiMDZlNzNhMDMtYmE1NC00NDc3LTgzODktZjYxNDJkMTkwMjMzIiwidCI6IjQ3YTE4ODE2LTIwNDMtNGNkMC04YmY0LWUwYzk0MmQ4YzJkNiIsImMiOjN9)

## 🎯 Problématique

> Comment la performance des fournisseurs et la rotation des stocks influencent-elles la marge commerciale, de l'achat jusqu'à la vente ?

## 💡 Résultats clés

- **Le prix d'achat réel érode la marge** : sur les produits achetés puis revendus, la marge passe de 27,7 % (coût standard) à 18,3 % (prix d'achat réel), soit **−9,4 points**. L'écart se creuse : −10,4 pts en 2024, −14,2 pts au 1er semestre 2025.
- **Les composants cumulent les difficultés** : achetés environ 75 % au-dessus du coût standard, 436 jours de couverture de stock, 4,2 % de marge.
- **Le délai fournisseur n'est pas le facteur limitant** (9 jours en moyenne) ; le risque porte sur la qualité : les 10 premiers fournisseurs (43 % des achats) appartiennent tous au segment « Gros volumes », qui a le taux de rejet le plus élevé (3,4 %).
- **Le seuil de réapprovisionnement fixe masque le risque de rupture** : seuls 5 produits achetés sont sous leur seuil, mais l'indicateur de couverture en jours (stock ÷ ventes par jour, comparé au délai fournisseur) en signale **19 sur 76**. Tous viennent de 5 fournisseurs « Peu d'historique » (moins de 30 lignes d'achat), que le clustering ne peut pas évaluer.
- **Action prioritaire** : renégocier les prix d'achat des composants et des pneus.

## 🗂️ Structure du projet

```
ProjetFinal/
├── raw_data/                     ← CSV bruts Microsoft à télécharger (lien dans la section Dataset)
├── clean_data/                   ← CSV avec en-têtes (généré par `add_headers.py`)
├── database/                     ← base SQLite générée (généré par `creat_bdd.py`)
├── docs/
│   └── AdventureWorks_Dictionnaire_de_donnees.md
├── img/                          ← captures et schémas
├── src/
│   ├── add_headers.py            ← ajout des en-têtes aux CSV bruts
│   ├── creat_bdd.py              ← création de la base SQLite
│   ├── import_csv.py             ← import des CSV dans SQLite
│   ├── creat_api.py              ← API FastAPI (CRUD) sur la base
│   ├── eda.ipynb                 ← analyse exploratoire
│   ├── check_missing.py          ← contrôle des valeurs manquantes
│   ├── nettoyage.py              ← traitement des valeurs manquantes
│   └── export_clean_parquet.py   ← export des tables utiles en Parquet
├── ml/
│   ├── clustering_fournisseur.ipynb   ← segmentation des fournisseurs
│   ├── risque_rupture_couverture.ipynb ← risque de rupture : couverture de stock en jours
│   └── outputs/
├── parquet_for_powerbi/          ← fichiers Parquet chargés dans Power BI (générés par `export_clean_parquet.py`)
├── AdventureWorks.pbix           ← dashboard Power BI
├── AdventureWorks_theme.json     ← thème Power BI
├── requirements.txt
└── README.md
```

## 🔄 Pipeline

```
CSV bruts → Python (pandas) → SQLite → Parquet → Power BI
                                  ↘ API FastAPI
                                  ↘ Machine learning (scikit-learn)
```

1. **Récupération** des CSV AdventureWorks et stockage dans `raw_data/`.
2. **`src/add_headers.py`** : ajoute les en-têtes officiels et écrit les CSV dans `clean_data/`.
3. **`src/creat_bdd.py`** : crée la base SQLite `database/adventureworks.db` en respectant l'ordre des clés étrangères.
4. **`src/import_csv.py`** : importe les 15 CSV de `clean_data/` dans la base (valeurs nulles marquées `null`).
5. **`src/creat_api.py`** : expose la base via une API FastAPI (opérations CRUD).
6. **`src/eda.ipynb`** et **`src/check_missing.py`** : analyse exploratoire (valeurs manquantes, cohérence des dates, intégrité référentielle : 11 contrôles validés).
7. **`src/nettoyage.py`** : traitement des valeurs manquantes et suppression des colonnes sans valeur analytique.
8. **`src/export_clean_parquet.py`** : export en Parquet des **13 tables utilisées** par le modèle Power BI (types corrigés : entiers, dates).
9. **`ml/clustering_fournisseur.ipynb`** : génère `parquet_for_powerbi/vendor_segments.parquet`.
10. **`ml/risque_rupture_couverture.ipynb`** : calcule la couverture de stock en jours (stock ÷ ventes par jour, comparé au délai fournisseur) et génère `parquet_for_powerbi/produits_a_risque.parquet`.
11. **Power BI** : chargement des fichiers Parquet, modélisation en étoile, mesures DAX, 4 pages de restitution.

### Schéma de la base
![Schéma AdventureWorks](img/adventureworks.png)

### API FastAPI
Vérification : le chiffre d'affaires renvoyé par l'API est identique à celui obtenu en SQL.

| Requête API | Requête SQL |
|---|---|
| ![API](img/API/API_Get_ca.png) | ![SQL](img/API/SQL_ca.png) |

## 📊 Dashboard Power BI

🔗 **[Voir le rapport interactif en ligne](https://app.powerbi.com/view?r=eyJrIjoiYjBlYTViNGYtZDRlMi00ODhkLWIyNDctNjJmMzExZTgxMjcxIiwidCI6IjQ3YTE4ODE2LTIwNDMtNGNkMC04YmY0LWUwYzk0MmQ4YzJkNiIsImMiOjN9)** (aucun compte requis) · ou télécharger [`AdventureWorks.pbix`](AdventureWorks.pbix)

| Page | Question | Contenu principal |
|---|---|---|
| **Vue d'ensemble** | Répond à la problématique | KPI avec évolution N-1, marge réelle vs standard, rotation vs marge, constats clés |
| **Achat** | Quels fournisseurs performent ? | Top 10 fournisseurs, segmentation des 104 fournisseurs, volume vs taux de rejet |
| **Produit** | Le stock est-il sain ? | Valeur et couverture du stock, produits sous le seuil, surcoût d'achat |
| **Vente** | D'où vient la marge ? | CA par pays, top produits, canal en ligne vs hors ligne, marge par sous-catégorie |

Modèle : 3 tables de faits (achats, ventes, stock), dimensions produit, fournisseur, client, territoire et calendrier. Comparaisons N-1 à période équivalente (`DATEADD`), les années 2022 et 2025 étant incomplètes.


### Achat
![Achat](img/dashboard_achat.png)

### Produit
![Produit](img/dashboard_produit.png)

### Vente
![Vente](img/dashboard_vente.png)



## 🤖 Machine learning

| Modèle | Méthode | Résultat |
|---|---|---|
| **Segmentation des fournisseurs** | K-Means (K = 3) sur les 79 fournisseurs ayant au moins 30 lignes d'achat, règles métier pour les 25 autres | 5 segments : Gros volumes (44), Petites séries (22), Sans commande (18), Généralistes (13), Peu d'historique (7) |
| **Risque de rupture de stock** | Seuil de réapprovisionnement fixe : 5 produits sur 83 seulement, trop peu pour une classification. Remplacé par un indicateur de **couverture en jours** (stock ÷ ventes par jour, comparé au délai fournisseur) sur les 76 produits achetés avec ventes | 19 produits à risque sur 76, tous issus de 5 fournisseurs « Peu d'historique » (moins de 30 lignes d'achat), non évalués par le clustering |

## 🔐 Données et RGPD

Les données AdventureWorks sont **fictives**. La démarche appliquée est celle d'un contexte réel : principe de **minimisation** (RGPD, art. 5.1.c). La table `Person` (noms, données démographiques) n'est pas exportée vers Power BI, et les colonnes sans usage analytique sont retirées du modèle. Les fichiers de données ne sont pas versionnés.

## ⚙️ Installation et exécution

```bash
python -m venv venv
source venv/Scripts/activate        # Windows (Git Bash)
pip install -r requirements.txt

python src/add_headers.py
python src/creat_bdd.py
python src/import_csv.py
python src/nettoyage.py
python src/export_clean_parquet.py
```

Puis exécuter `ml/clustering_fournisseur.ipynb` (génère `vendor_segments.parquet`) et `ml/risque_rupture_couverture.ipynb` (génère `produits_a_risque.parquet`), puis ouvrir `AdventureWorks.pbix` dans Power BI Desktop (Accueil → Actualiser).

## ⚠️ Limites

- Coût standard fixe, sans historique des coûts.
- Stock disponible uniquement à date (pas de stock moyen).
- Achats en cartons ou bidons, nomenclature en unités : pas de facteur de conversion.
- Couverture en jours : ventes moyennes sans saisonnalité, commandes en cours non prises en compte ; 72 produits fabriqués n'ont aucun enregistrement de stock et sont hors périmètre.
- Ventes de mai 2022 à juin 2025, achats jusqu'en septembre 2025.

## 📚 Dataset

[AdventureWorks](https://github.com/microsoft/sql-server-samples/tree/master/samples/databases/adventure-works/oltp-install-script) — jeu de données open source de Microsoft.

## ✅ Suivi de projet

Tableau Trello : [adventureworks-supply-chain-analysis](https://trello.com/b/udYAed3U/adventureworks-supply-chain-analysis)

## Autrice

Xiaoqing ZHOU GRANDCOING — [Portfolio](https://xiaoqinggdc.github.io/) · [GitHub](https://github.com/XiaoqingGdc) · [LinkedIn](https://www.linkedin.com/in/xiaoqingzhougrandcoing)
