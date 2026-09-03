# 📦 AdventureWorks Supply Chain Analysis

Projet final — Analyse de l'impact de la performance fournisseurs sur la rotation des stocks et la marge commerciale, du diagnostic à la restitution.

## 🎯 Problématique

Comment la performance des fournisseurs et la rotation des stocks influencent-elles la marge commerciale, de l'achat jusqu'à la vente ?

## 🗂️ Structure du projet

```
ProjetFinal/
├── database/           ← adventureworks.db + instawdb.sql (ignoré par git)
├── docs/                ← documents (dictionnaire de données, etc.)
├── raw_data/             ← données brutes CSV (achat/produit/vente, ignoré par git)
├── clean_data/           ← données nettoyées (ignoré par git)
├── src/                  ← scripts Python
│   ├── nettoyage.py      ← nettoyage + ajout des en-têtes (raw_data → clean_data)
│   ├── chargement.py     ← chargement des CSV nettoyés dans SQLite
│   └── test.py
├── venv/                 ← environnement virtuel Python (ignoré par git)
├── .gitignore
├── requirements.txt      ← dépendances Python (pip freeze)
└── README.md
```

## 🔄 Pipeline de données

1. **`src/nettoyage.py`** : lit les CSV bruts dans `raw_data/`, ajoute les en-têtes officielles (schéma `instawdb.sql`), nettoie les données (valeurs manquantes, types, doublons), écrit les CSV nettoyés dans `clean_data/`.
2. **`src/chargement.py`** : lit les CSV nettoyés dans `clean_data/`, charge chaque table dans la base SQLite `database/adventureworks.db`, en respectant l'ordre des dépendances de clés étrangères.

## ⚙️ Installation

```bash
python -m venv venv
source venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## ▶️ Utilisation

```bash
python src/nettoyage.py
python src/chargement.py
```

## 📊 Dataset

[AdventureWorks](https://github.com/Microsoft/sql-server-samples/releases/tag/adventureworks) — jeu de données open-source officiel de Microsoft.

## ✅ Suivi de projet

Tableau Trello : [adventureworks-supply-chain-analysis](https://trello.com/b/udYAed3U/adventureworks-supply-chain-analysis)