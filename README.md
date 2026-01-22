# Shopify Cross-Sell Automation (Azure Function + Flow)

Ce projet vise à automatiser l'envoi d'emails de cross-selling personnalisés pour les clients des boutiques TB Outdoor et TB1648, sans utiliser d'applications tierces payantes.

---

## 🚀 Le Concept

Lorsqu'un client achète un produit d'une collection spécifique (ex: collection Louis), le système attend un délai défini (ex: 6 mois) puis lui envoie un email récapitulant ses achats actuels et lui proposant 2 ou 3 produits complémentaires qu'il ne possède pas encore.

## 🏗 Architecture Technique

Le système repose sur trois piliers :
1. **Shopify Flow** : Le chef d'orchestre qui gère les triggers (événements) et l'envoi final des emails via *Shopify Email*.
2. **Azure Function (Python)** : Le "cerveau" qui calcule la différence entre les produits de la collection et les achats effectifs du client.
3. **Shopify Metafields** : La "mémoire" du système qui stocke l'historique des recommandations pour éviter les répétitions.

```mermaid
graph TD
    A[Shopify Flow: Relance 6 mois] --> B(Action: HTTP Request)
    B --> C[Azure Function Python]
    C --> D{API Shopify}
    D --> E[Récupérer: Achats client + Précédentes Recommandations]
    E --> F[Calcul: Collection - (Achats + Recommandés)]
    F --> G[Sélection: Top 3 produits]
    G --> H[Retourne JSON: Recap + Recommendations]
    H --> I[Shopify Flow: Envoyer Email]
    I --> J[Action: Update Metafield 'Recommandations Envoyées']
```

---

## 📋 Organisation du Projet

### Structure des fichiers

```
.
├── azure_function/
│   ├── core/                      ⭐ PRODUCTION (à garder)
│   │   ├── shopify_helper.py     (Helper API - cœur du système)
│   │   ├── function_app.py       (Azure Function - point d'entrée)
│   │   └── requirements.txt      (Dépendances)
│   │
│   ├── tests/                     🧪 DEVELOPMENT (tests & debug)
│   │   ├── test_recent_forges.py           (⭐ Principal: clients 0-30j)
│   │   ├── debug_customer_retrieval.py    (🔍 Diagnostic)
│   │   ├── list_all_collections.py       (📋 Lister collections)
│   │   └── [autres tests...]
│   │
│   ├── .env                       (🔐 Secrets - NE PAS COMMITER)
│   ├── .env.template              (📝 Template variables)
│   ├── local.settings.json        (⚙️ Config locale)
│   ├── host.json                  (⚙️ Config Azure)
│   └── .funcignore                (Fichiers à ignorer)
│
└── README.md                       (Cette documentation)

```

---

## ⭐ FICHIERS INDISPENSABLES (core/)

### 1. **shopify_helper.py**

Le cœur du système. Classe de gestion de l'API Shopify contenant:
- `ShopifyHelper` - Classe principale
- `get_collection_products()` - Récupère les produits d'une collection
- `get_customer_purchase_history()` - Historique d'achat client
- `get_eligible_customers()` - Filtre clients par période et collection
- `update_customer_recommendations()` - Met à jour les metafields

### 2. **function_app.py**

Point d'entrée Azure Function (HTTP Trigger).
Intègre `ShopifyHelper` pour traiter les requêtes entrantes.

### 3. **requirements.txt**

Dépendances Python:
```
shopify
requests
python-dotenv
```

---

## 🧪 SCRIPTS DE TEST/DEBUG (tests/)

### ✅ Tests Validation (À utiliser)

#### **test_recent_forges.py** ⭐ PRINCIPAL
Cherche les clients ayant acheté de la collection "Forgés" dans les 30 derniers jours.
```bash
python tests/test_recent_forges.py
```
**Affiche:**
- Email, Nom, Nombre de produits achetés
- Recommandations disponibles

**Résultats attendus:**
- 4 clients trouvés
- Tous avec 3 recommandations disponibles

#### **debug_customer_retrieval.py** 🔍
Diagnostic complet du processus de récupération des clients.
```bash
python tests/debug_customer_retrieval.py
```
**Affiche:**
- Toutes les commandes de la période
- Filtrage par collection
- Détails d'achat de chaque client
- Vérification du calcul des recommandations

#### **list_all_collections.py** 📋
Récupère et affiche toutes les collections Shopify du store.
```bash
python tests/list_all_collections.py
```
**Génère:**
- Fichier `collections_list.txt` en format CSV
- Utile pour trouver les IDs de collection

---

### Tests Généraux

- **test_simulation.py** - Simulation test générale
- **test_real_update.py** - Test de mise à jour réelle
- **production_run.py** - Test exécution production

### Tests Spécifiques (Collection Louis)

- **find_last_buyer.py** - Cherche le dernier acheteur
- **find_10_buyers.py** - Cherche 10 acheteurs

### Debug (Développement)

- **debug_auth.py** - Débugage authentification
- **debug_orders.py** - Débugage commandes
- **oauth_capture.py** - Capture OAuth
- **manual_exchange.py** - Échange manuel

---

## ⚙️ Configuration

### Variables d'environnement (.env)

```
# Store Shopify
SHOPIFY_STORE_URL=tbgroupe-fr.myshopify.com

# API Access
SHOPIFY_ACCESS_TOKEN=shpca_...
SHOPIFY_CLIENT_ID=...
SHOPIFY_CLIENT_SECRET=shpss_...

# Collections
TARGET_COLLECTION_ID=299133665432          (Louis)
FORGED_PREMIUM_COLLECTION_ID=298781474968  (Forgés)
```

### Fichiers de configuration

| Fichier | Purpose | À commiter |
|---------|---------|-----------|
| `.env` | Variables secrets | ❌ |
| `.env.template` | Template variables | ✅ |
| `local.settings.json` | Config locale | ❌ |
| `host.json` | Config Azure Function | ✅ |
| `.funcignore` | Fichiers ignorés | ✅ |

---

## 🚀 Utilisation

### Lancer un test

```bash
cd azure_function
python tests/test_recent_forges.py
```

### Importer le helper dans un nouveau script

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.shopify_helper import ShopifyHelper
import os
from dotenv import load_dotenv

load_dotenv()
helper = ShopifyHelper(
    os.getenv("SHOPIFY_STORE_URL"),
    access_token=os.getenv("SHOPIFY_ACCESS_TOKEN")
)
```

### Lancer la fonction Azure

```bash
func start
```

---

## ✅ Validation des données

Le script `debug_customer_retrieval.py` valide que:
- ✓ Les produits de la collection sont bien identifiés
- ✓ Les commandes de la période sont récupérées
- ✓ Le filtrage par collection fonctionne
- ✓ Le calcul des recommandations est correct
- ✓ L'historique d'achat client est précis

### Exemple de résultats (30 derniers jours)

**Clients Forgés trouvés:** 4
| Client | Email | Achats | Forgés | Recos |
|--------|-------|--------|--------|-------|
| Dominique Dubost | dominiquedubost@orange.fr | 2 | 1 | 3 |
| DANIEL LAPINSKI | Dlapinski59@gmail.com | 2 | 1 | 3 |
| Adam PHILIBERT | Adam.phi33@gmail.com | 2 | 1 | 3 |
| melanie Severin | melanie.severin@sfr.fr | 12 | 1 | 3 |

---

## 📝 Configuration requise (Pré-requis)

Avant de commencer le développement, les éléments suivants sont nécessaires :

1. **Confirmation du forfait Shopify** 
   - L'action "Send HTTP Request" dans Flow requiert un forfait **Advanced** ou **Plus**
   
2. **Accès API Shopify**
   - Créer une "App personnalisée" (Custom App) sur chaque instance Shopify
   - Scopes requis: `read_products`, `read_orders`, `read_customers`, `write_customers`

3. **Azure Sandbox**
   - Accès aux credentials pour déployer l'Azure Function

4. **Design des Emails**
   - Template dans *Shopify Email* avec variables Liquid

---

## 🗺 Roadmap

### Phase 1 : Infrastructure & Logic ✅ TERMINÉE
- [x] Initialiser le projet Azure Function (Python)
- [x] Développer la logique de filtrage (Collection vs Historique)
- [x] Implémenter la gestion via Metafields
- [x] Organiser structure core/ et tests/

### Phase 2 : Shopify Configuration
- [ ] Créer les Custom Apps pour l'accès API
- [ ] Configurer les déclencheurs (Triggers) dans Shopify Flow
- [ ] Tester les webhooks
- [ ] Mettre en production

---

## 🔄 Prochaines étapes

1. ✅ Structure du projet organisée
2. ✅ Tests et diagnostic fonctionnels
3. ✅ Documentation consolidée
4. → Mettre à jour `function_app.py` pour la production
5. → Valider avec l'équipe
6. → Déployer sur Azure

---

## 📚 Documentation

Voir les fichiers de documentation pour plus de détails:
- **Docs fusionnées** dans ce README
- **Anciens fichiers** (STRUCTURE.md, TESTS_README.md, ORGANISATION_FINALE.md) conservés à titre informatif

---

**Dernière mise à jour:** 22 janvier 2026
**Status:** 🟢 En développement
**Version:** 1.0-refactor
- [ ] Designer le template "Recap & Collection Update" dans Shopify Email.

### Phase 3 : Tests & Mise en production
- [ ] Tests unitaires sur la sélection des produits.
- [ ] Test "End-to-End" avec un client test.
- [ ] Déploiement sur l'instance Azure de production.

---
> [!NOTE]
> Ce projet est conçu pour être évolutif. On peut facilement ajouter de nouvelles collections (Gamme Guy Savoy, Furtif, etc.) sans modifier la structure globale.
