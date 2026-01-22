# Structure du Projet Shopify Cross-Selling

## 📋 Organisation des Fichiers

```
azure_function/
├── core/                          # ⭐ FICHIERS INDISPENSABLES
│   ├── shopify_helper.py         # Helper API Shopify (cœur du système)
│   ├── function_app.py           # Fonction Azure (point d'entrée)
│   └── requirements.txt           # Dépendances Python
│
├── tests/                         # 🧪 SCRIPTS DE TEST/DÉVELOPPEMENT
│   ├── test_recent_forges.py     # Test: clients Forgés 0-30 jours
│   ├── debug_customer_retrieval.py # Debug: validation du process
│   ├── list_all_collections.py   # Util: lister les collections
│   ├── test_simulation.py        # Test: simulation générale
│   ├── test_real_update.py       # Test: mise à jour réelle
│   ├── find_last_buyer.py        # Test: dernier acheteur Louis
│   ├── find_10_buyers.py         # Test: 10 acheteurs Louis
│   ├── production_run.py         # Test: exécution production
│   ├── debug_auth.py             # Debug: authentification
│   ├── debug_orders.py           # Debug: commandes
│   ├── manual_exchange.py        # Test: échange manuel
│   └── oauth_capture.py          # Test: capture OAuth
│
├── config/                        # ⚙️ FICHIERS DE CONFIGURATION
│   ├── .env                      # Variables d'environnement (À NE PAS COMMITER)
│   ├── .env.template             # Template des variables
│   ├── local.settings.json       # Paramètres locaux Azure
│   ├── host.json                 # Config Azure Function
│   └── .funcignore               # Fichiers à ignorer pour Azure
│
├── STRUCTURE.md                   # Cette documentation
├── TESTS_README.md               # Guide des tests disponibles
└── README.md                      # Documentation générale
```

---

## 🎯 FICHIERS INDISPENSABLES

### Dossier `core/`

#### 1. **shopify_helper.py** ⭐⭐⭐
Le cœur du système. Contient:
- `ShopifyHelper` - Classe de gestion API Shopify
- `get_collection_products()` - Récupère les produits d'une collection
- `get_customer_purchase_history()` - Historique d'achat client
- `get_eligible_customers()` - Filtre clients par période et collection
- `update_customer_recommendations()` - Met à jour les metafields

**Dépend de:** shopify, requests

#### 2. **function_app.py** ⭐⭐
Point d'entrée Azure Function (HTTP Trigger).
Intègre `ShopifyHelper` pour traiter les requêtes entrantes.

**Exécution:** `func start`

#### 3. **requirements.txt**
Liste des dépendances Python:
- shopify
- requests
- python-dotenv (dev)

---

## 🧪 SCRIPTS DE TEST/DEBUG

### Dossier `tests/`

#### **Validation & Diagnostic**
- **test_recent_forges.py** - Cherche clients Forgés (0-30j) ✅ PRINCIPAL
- **debug_customer_retrieval.py** - Diagnostic complet du process 🔍
- **list_all_collections.py** - Liste toutes les collections 📋

#### **Tests Généraux (anciens)**
- **test_simulation.py** - Simulation test
- **test_real_update.py** - Test mise à jour réelle
- **production_run.py** - Test exécution production

#### **Tests Spécifiques (Louis)**
- **find_last_buyer.py** - Dernier acheteur Louis
- **find_10_buyers.py** - 10 acheteurs Louis

#### **Debug (développement)**
- **debug_auth.py** - Débugage authentification
- **debug_orders.py** - Débugage commandes
- **oauth_capture.py** - Capture OAuth
- **manual_exchange.py** - Échange manuel

---

## ⚙️ FICHIERS DE CONFIGURATION

| Fichier | Purpose | Editable | À commiter |
|---------|---------|----------|-----------|
| `.env` | Variables secrets | ✅ | ❌ |
| `.env.template` | Template variables | ✅ | ✅ |
| `local.settings.json` | Config Azure local | ✅ | ❌ |
| `host.json` | Config Azure Function | ✅ | ✅ |
| `.funcignore` | Fichiers ignorés | ✅ | ✅ |

---

## 🚀 Utilisation

### Pour lancer un test:
```bash
cd azure_function
python tests/test_recent_forges.py
```

### Pour importer le helper dans un nouveau script:
```python
from core.shopify_helper import ShopifyHelper
import os
from dotenv import load_dotenv

load_dotenv()
helper = ShopifyHelper(...)
```

### Pour lancer la fonction Azure:
```bash
func start
```

---

## ✅ Checklist Maintenance

- [ ] Fichiers temporaires supprimés
- [ ] Tests archivés dans `tests/`
- [ ] Cœur métier dans `core/`
- [ ] Config centralisée
- [ ] `.gitignore` mis à jour
- [ ] Documentation à jour

