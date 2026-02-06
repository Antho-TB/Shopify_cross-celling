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
│   ├── function_app.py       (Azure Function - point d'entrée)
│   ├── shopify_helper.py     (Helper API - cœur du système)
│   ├── requirements.txt      (Dépendances)
│   ├── host.json             (Config Azure)
│   ├── local.settings.json   (Config locale)
│   ├── .env                  (Secrets - NE PAS COMMITER)
│   ├── .funcignore           (Fichiers à ignorer)
│   └── tests/                🧪 TESTS & DEBUG
│       ├── test_recent_forges.py        (Clients 0-30j)
│       └── test_6months_validation.py  (Validation 6 mois)
│
├── Terraform/                 🏗️ INFRASTRUCTURE
└── README.md                  (Cette documentation)
```

---

## ⏰ LOGIQUE DE RELANCE (6 mois ±7 jours)

Le système recherche les clients ayant acheté **exactement 6 mois avant** (avec une tolérance de ±7 jours) :

- **Fenêtre** : 173 à 180 jours.
- **Timing** : Chaque lundi à 2h du matin (`0 0 2 * * 1`).
- **Mode** : Automatique via Timer Trigger.

### Exemple de flux
Si un client achète le **22 janvier 2025** :
- Le scan du **Lundi 21 juillet 2025** détectera le client.
- L'Azure Function injectera le tag `trigger_reco` et les recommandations dans les Metafields.

---

## 🏗️ Infrastructure (Terraform)

Le projet utilise **Terraform** pour provisionner et gérer automatiquement l'infrastructure sur Azure. Cela garantit une configuration reproductible et conforme aux standards de nommage.

### Ressources gérées
- **Resource Group** : Le conteneur logique (`rg-Shopify-CrossSelling-dev`).
- **Storage Account** : Pour le stockage interne de la fonction.
- **Service Plan** : Plan de consommation (Y1) pour minimiser les coûts.
- **Function App** : L'instance Linux hébergeant le code Python 3.11.

### Utilisation de Terraform
```bash
cd Terraform
terraform init
terraform apply -var-file="local.tfvars"
```

### Principaux fichiers
- `main.tf` : Définition des ressources Azure.
- `variables.tf` : Liste des variables configurables (Location, Environment, etc.).
- `local.tfvars` : Fichier local (non commité) contenant les secrets.

---

## 🚀 Utilisation & Déploiement

### Déploiement
```bash
cd azure_function
func azure functionapp publish func-Shopify-CrossSelling-dev
```

### Test Manuel
Vous pouvez forcer une exécution pour un client spécifique via l'endpoint HTTP :
`POST /api/check_recommendations`
`Body: {"customer_id": "...", "collection_id": "..."}`

### Dashboard de Monitoring 📊
> [!IMPORTANT]
> **Le tableau de bord est actuellement désactivé.**
> Pour des raisons de sécurité et de simplification du système, l'endpoint de monitoring HTML n'est plus accessible. Le suivi s'effectue désormais via les logs Azure et les outils de rapport internes.

---

## 🛠️ Retours d'expérience & Troubleshooting

### 1. Conflits de Déclencheur (Trigger) Shopify Flow
> [!WARNING]
> Lorsque l'Azure Function ajoute un tag (ex: `trigger_reco`), cela déclenche l'événement **"Customer tags added"** dans Shopify.
> Si d'autres flux (ex: Flux de Bienvenue) écoutent cet événement sans filtre précis, ils se déclencheront par erreur.
> **Solution** : Toujours filtrer les flux Shopify par nom de tag spécifique dans les conditions.

### 2. Redirections de Test (Azure Side)
Afin d'éviter tout envoi d'emails intempestifs vers le développeur ou le client lors des phases de test :
- Les redirections automatiques via variables d'environnement (`TEST_CUSTOMER_EMAIL`) ont été désactivées dans le code.
- **Obligation** : Pour tout test manuel via l'API, l'email de destination doit être passé **explicitement** dans le corps de la requête JSON.

---

## ✅ Checklist Final
- [x] Structure de fichiers standard V2 Azure.
- [x] Logging détaillé pour le suivi des opérations.
- [x] Tests de validation 6 mois OK.
- [x] Infrastructure Terraform déployée dans North Europe.
- [x] Sécurisation des redirections de test Azure.

**Dernière mise à jour :** 6 février 2026
**Version :** 1.2.0
