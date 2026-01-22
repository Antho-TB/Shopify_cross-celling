# Scripts de Test - Documentation

## 🎯 Scripts de Production (à garder)

### 1. **list_all_collections.py**
Récupère et affiche **toutes les collections** Shopify du store.
- Génère un fichier `collections_list.txt` avec format CSV
- Utile pour trouver les IDs de collection

```bash
python azure_function/list_all_collections.py
```

### 2. **test_recent_forges.py** ⭐
Lance la recherche des clients ayant acheté de la collection "Forgés" dans les **30 derniers jours**.
- Affiche: Email, Nom, Nombre de produits achetés
- Montre les recommandations disponibles

```bash
python azure_function/test_recent_forges.py
```

**Résultats attendus (dernière exécution):**
- 4 clients trouvés
- Tous avec 3 recommandations disponibles

### 3. **debug_customer_retrieval.py** 🔍
Diagnostic complet du processus de récupération des clients.
- Affiche toutes les commandes de la période
- Filtre celles de la collection cible
- Montre les détails d'achat de chaque client
- Vérifie le calcul des recommandations

```bash
python azure_function/debug_customer_retrieval.py
```

---

## 🛠️ Scripts Existants (anciens)

- **test_simulation.py** - Test général
- **test_real_update.py** - Test de mise à jour réelle
- **find_last_buyer.py** - Cherche le dernier acheteur Louis
- **find_10_buyers.py** - Cherche 10 acheteurs Louis
- **production_run.py** - Exécution production
- **debug_auth.py** - Debug authentification
- **debug_orders.py** - Debug commandes

---

## 📝 Configuration

Les variables d'environnement requises dans `.env`:
```
SHOPIFY_STORE_URL=tbgroupe-fr.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpca_...
SHOPIFY_CLIENT_ID=...
SHOPIFY_CLIENT_SECRET=shpss_...
TARGET_COLLECTION_ID=299133665432 (Louis)
FORGED_PREMIUM_COLLECTION_ID=298781474968 (Forgés)
```

---

## 🎯 Cas d'usage

**Pour relancer les clients Forgés ayant acheté récemment (0-30 jours):**
```bash
python azure_function/test_recent_forges.py
```

**Pour lister toutes les collections (ex: trouver un nouvel ID):**
```bash
python azure_function/list_all_collections.py
```

**Pour déboguer le processus:**
```bash
python azure_function/debug_customer_retrieval.py
```

---

## ✅ Validation des données

Le script `debug_customer_retrieval.py` valide que:
- ✓ Les produits de la collection sont bien identifiés
- ✓ Les commandes de la période sont récupérées
- ✓ Le filtrage par collection fonctionne
- ✓ Le calcul des recommandations est correct
- ✓ L'historique d'achat client est précis
