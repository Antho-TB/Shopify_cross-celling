# Shopify Cross-Sell Automation (Azure Function + Flow)

Ce projet vise à automatiser l'envoi d'emails de cross-selling personnalisés pour les clients des boutiques TB Outdoor et TB1648, sans utiliser d'applications tierces payantes.

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

## 📋 Pré-requis (Ce qu'il manque pour lancer)

Avant de commencer le développement, les éléments suivants sont nécessaires :

1. **Confirmation du forfait Shopify** : 
   - L'action "Send HTTP Request" dans Flow requiert un forfait **Advanced** ou **Plus**. Si vous êtes sur un forfait Basic, nous devons changer d'approche.
2. **Accès API Shopify** :
   - Créer une "App personnalisée" (Custom App) sur chaque instance Shopify avec les scopes : `read_products`, `read_orders`, `read_customers`, `write_customers`.
3. **Azure Sandbox** :
   - Accès aux credentials pour déployer l'Azure Function.
4. **Design des Emails** :
   - Préparer un template dans *Shopify Email* capable de recevoir des variables dynamiques (Liquid).

## 🗺 Liste des Tâches (Task List)

### Phase 1 : Infrastructure & Logic (Middleware)
- [ ] Initialiser le projet Azure Function (Python).
- [ ] Développer la logique de filtrage (Différence entre Collection API et Historique Client).
- [ ] Implémenter la gestion de la "mémoire" via les Metafields.

### Phase 2 : Shopify Configuration
- [ ] Créer les Custom Apps pour l'accès API.
- [ ] Configurer les déclencheurs (Triggers) dans Shopify Flow.
- [ ] Designer le template "Recap & Collection Update" dans Shopify Email.

### Phase 3 : Tests & Mise en production
- [ ] Tests unitaires sur la sélection des produits.
- [ ] Test "End-to-End" avec un client test.
- [ ] Déploiement sur l'instance Azure de production.

---
> [!NOTE]
> Ce projet est conçu pour être évolutif. On peut facilement ajouter de nouvelles collections (Gamme Guy Savoy, Furtif, etc.) sans modifier la structure globale.
