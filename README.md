# 📦 AdventureWorks Supply Chain Analysis

Projet final — Analyse de l'impact de la performance fournisseurs sur la rotation des stocks et la marge commerciale, du diagnostic à la restitution.

## 🎯 Problématique

Comment la performance des fournisseurs et la rotation des stocks influencent-elles la marge commerciale, de l'achat jusqu'à la vente ?

## 🗂️ Structure du projet

```
ProjetFinal/
├── clean_data/                 
├── database/                    
├── docs/                         
│   ├── AdventureWorks_Dictionnaire_de_donnees.md
├── img/                           ← divers fichiers image
├── parquet_for_powerbi/           
├── raw_data/                      
├── src/                          
│   ├── add_headers.py           
│   ├── creat_api.py              
│   ├── creat_bdd.py             
│   ├── eda.py                    
│   ├── export_clean_parquet.py   
│   ├── import_csv.py             
│   ├── supprimer_valeurnull.py   
│   └── test.py
├── venv/                          
├── .gitignore
├── AdventureWorks.pbix
├── requirements.txt              
└── README.md
```

## 🔄 Étapes du projet

1. Récupération des données GitHub vers `raw_data/`
   ↓
2. **`src/add_headers.py`** : lit les CSV bruts dans `raw_data/`, ajoute les en-têtes officielles, écrit les CSV nettoyés dans `clean_data/`.
   ↓
3. **`src/creat_bdd.py`** : lit les CSV nettoyés dans `clean_data/`, charge chaque table dans la base SQLite `database/adventureworks.db`, en respectant l'ordre des dépendances de clés étrangères.
   ↓
4. **`src/import_csv.py`** : importe les 15 fichiers CSV du dossier `clean_data/`, en-têtes compris, valeurs nulles marquées `null`, dans la base de données (SQLite) créée à l'étape précédente.
   ↓
5. **`src/eda.py`** : analyse exploratoire des données — valeurs manquantes, cohérence des dates, liens entre tables.
   ↓
6. **`src/supprimer_valeurnull.py`** : traitement des valeurs nulles dans les tables, via sqlite3, dans la base de données.
   ↓
7. **`src/export_clean_parquet.py`** : extraction des 15 fichiers au format parquet à partir de `database/adventureworks.db` vers `parquet_for_powerbi/*.parquet`.
   ↓
8. **Power BI** → Obtenir les données → importer les 15 fichiers parquet du dossier `parquet_for_powerbi/`.

## ⚙️ Installation

```bash
python -m venv venv
source venv/Scripts/activate        # Windows
pip install -r requirements.txt
```

## 📊 Dataset

[AdventureWorks](https://github.com/microsoft/sql-server-samples/tree/master/samples/databases/adventure-works/oltp-install-script) — jeu de données open-source officiel de Microsoft.

## ✅ Suivi de projet

Tableau Trello : [adventureworks-supply-chain-analysis](https://trello.com/b/udYAed3U/adventureworks-supply-chain-analysis)
