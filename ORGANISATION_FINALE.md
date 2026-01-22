# 📋 ORGANISATION FINALE DU PROJET

## Structure

```
azure_function/
├── core/                          ⭐ FICHIERS INDISPENSABLES
│   ├── shopify_helper.py         (Helper API Shopify)
│   └── function_app.py           (Azure Function point d'entrée)
│
├── tests/                         🧪 SCRIPTS DE TEST/DEBUG
│   ├── test_recent_forges.py     (Principal: clients 0-30j)
│   ├── debug_customer_retrieval.py (Diagnostic)
│   ├── list_all_collections.py   (Lister collections)
│   └── [autres tests...]
│
├── core/requirements.txt          ⚙️ Dépendances
├── .env                           🔐 Secrets (NE PAS COMMITER)
├── .env.template                  Template variables
├── local.settings.json            Config locale
├── host.json                      Config Azure
├── .funcignore                    Ignore liste
│
├── STRUCTURE.md                   Documentation structure
├── TESTS_README.md                Guide tests
├── README.md                      Documentation générale
└── (config files)

```

## ✅ Tri terminé

### ⭐ INDISPENSABLES (core/)
| Fichier | Rôle |
|---------|------|
| `shopify_helper.py` | Helper API Shopify (cœur) |
| `function_app.py` | Azure Function HTTP Trigger |
| `requirements.txt` | Dépendances Python |

### 🧪 TESTS & DEBUG (tests/)

#### Tests Validation (À utiliser)
- `test_recent_forges.py` - Clients Forgés 0-30 jours ⭐ PRINCIPAL
- `debug_customer_retrieval.py` - Diagnostic complet 🔍
- `list_all_collections.py` - Liste collections 📋

#### Tests Généraux
- `test_simulation.py` - Simulation test
- `test_real_update.py` - Mise à jour réelle
- `production_run.py` - Exécution production

#### Tests Spécifiques (Louis)
- `find_last_buyer.py` - Dernier acheteur
- `find_10_buyers.py` - 10 acheteurs

#### Debug
- `debug_auth.py` - Authentification
- `debug_orders.py` - Commandes
- `oauth_capture.py` - OAuth
- `manual_exchange.py` - Échange

---

## 🚀 Utilisation

### Lancer un test:
```bash
cd azure_function
python tests/test_recent_forges.py
```

### Importer le helper:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.shopify_helper import ShopifyHelper
```

### Lancer la fonction Azure:
```bash
func start
```

---

## 📦 Requirements

Déplacer dans `core/requirements.txt`:
```
shopify
requests
python-dotenv
```

---

## ✅ Vérifications effectuées

- ✓ Dossiers créés (core/ et tests/)
- ✓ Fichiers déplacés
- ✓ Imports mis à jour
- ✓ Tests fonctionnels
- ✓ Imports de core validés
- ✓ Structure documentée

---

## 🎯 Prochaines étapes

1. Commiter l'organisation
2. Mettre à jour `function_app.py` si nécessaire
3. Documenter dans le README principal
4. Valider avec l'équipe

