# TÂCHES SUIVANTES - ROADMAP PRODUCTION

## Phase: Intégration Shopify Flow

### Tâche 1: Configuration Shopify
**Objectif**: Préparer les Custom Apps et variables Shopify

```
[ ] Créer Custom App sur tbgroupe-fr.myshopify.com
    → Admin API scopes: read_products, read_orders, read_customers, write_customers
    → Copier ACCESS_TOKEN
    
[ ] Créer Metafield dans Shopify Admin
    → Namespace: cross_sell
    → Key: next_recommendations
    → Type: single_line_text_field
    
[ ] Créer Metafield pour "recommandations envoyées" (optionnel)
    → Namespace: cross_sell
    → Key: last_recommendations_sent
    → Type: date_time
```

**Durée estimée**: 15 min
**Responsable**: Admin Shopify
**Validation**: Vérifier dans Admin → Custom App que les scopes sont OK

---

### Tâche 2: Configuration Azure & Déploiement
**Objectif**: Déployer la Function sur Azure

```
[ ] Créer ressources Azure
    → az group create --name rg-shopify --location westeurope
    → az storage account create
    → az functionapp create
    
[ ] Déployer le code
    → func azure functionapp publish func-shopify-cross-sell
    
[ ] Configurer les variables d'environnement
    → SHOPIFY_STORE_URL
    → SHOPIFY_ACCESS_TOKEN
    → TARGET_COLLECTION_ID
    → ORDER_DELAY_DAYS_START/END
    
[ ] Tester le trigger HTTP
    → curl -X POST https://func-shopify-cross-sell.azurewebsites.net/api/check_recommendations
```

**Durée estimée**: 30 min
**Responsable**: DevOps/Azure Admin
**Validation**: HTTP 200 avec JSON valide

---

### Tâche 3: Designer Email Template (Shopify Email)
**Objectif**: Créer le template de relance

```
[ ] Accéder à Shopify Email dans Admin
    
[ ] Créer nouveau template: "Relance 6 mois - Recommandations"
    
[ ] Structure du email:
    Header: "Continuez votre collection [Collection Name]"
    
    Recap:
      - "Vous avez acheté"
      - [Lister 2-3 derniers produits achetés]
      - "Vérifier votre historique"
    
    Recommandations:
      - "Nous vous proposons:"
      - [3 produits avec images]
      - CTA: "Découvrir"
    
    Footer standard

[ ] Variables Liquid à supporter:
    {{ customer.first_name }}
    {{ customer.email }}
    {{ collection.title }}
    {{ recommendations }}  (JSON parsé)
```

**Durée estimée**: 45 min
**Responsable**: Marketing
**Validation**: Aperçu + test send

---

### Tâche 4: Configurer Shopify Flow
**Objectif**: Créer l'automatisation de relance

```
[ ] Accéder à Shopify Flow (Admin → Automations → Flow)

[ ] Créer nouveau Flow: "Relance Cross-Selling 6 mois"

[ ] Trigger: 
    Customer tag added = "trigger_reco"
    (Tags injectés par la Function)

[ ] Actions:
    1. Send HTTP request
       URL: https://func-shopify-cross-sell.azurewebsites.net/api/check_recommendations?code=[FUNCTION_KEY]
       Method: POST
       Body: {
         "customer_id": "{{ customer.id }}",
         "collection_id": "298781474968"
       }
    
    2. Parse JSON response
    
    3. Send email via Shopify Email
       Template: "Relance 6 mois - Recommandations"
       To: {{ customer.email }}
       Variables: ... (mapper la réponse HTTP)
    
    4. Update customer tag
       Remove: trigger_reco
       Add: cross_sell_email_sent
    
    5. Update metafield
       cross_sell.last_recommendations_sent = NOW

[ ] Tester avec un client test
```

**Durée estimée**: 60 min
**Responsable**: Shopify Admin + Developer
**Validation**: Envoyer email test + vérifier tags/metafields

---

### Tâche 5: Test End-to-End Complet
**Objectif**: Valider le flux complet

```
[ ] Créer script test_e2e.py:
    1. Ajouter tag "trigger_reco" à un client test
    2. Attendre 30 secondes (Flow trigger)
    3. Vérifier que le metafield a été mis à jour
    4. Vérifier que le tag a été retiré
    5. Afficher le contenu du métafield injecté

[ ] Exécuter le test
    python tests/test_e2e.py

[ ] Valider les résultats:
    ✓ Email reçu (vérifier spam)
    ✓ Tags mis à jour dans Shopify Admin
    ✓ Metafield contient les bonnes recommandations
    ✓ Logs Azure affichent les détails
```

**Durée estimée**: 45 min
**Responsable**: QA + Developer
**Validation**: Rapport de test

---

## Phase: Mise en Production

### Tâche 6: Mise en place du Scanner Quotidien
**Objectif**: Activer le scan automatique 12-18 mois

```
[ ] Configuration Azure Function:
    → Activer le trigger planifié daily_cross_sell_scanner
    → Horaire: 0 0 2 * * * (2h du matin)
    → ORDER_DELAY_DAYS_START = 365 (12 mois)
    → ORDER_DELAY_DAYS_END = 548 (18 mois)

[ ] Monitoring setup:
    → Configurer Application Insights
    → Créer alertes pour les erreurs
    → Notification email si scan échoue

[ ] Tester le timing:
    → Modifier la scheduled expression pour tester à heure proche
    → Vérifier que la Function se déclenche bien
```

**Durée estimée**: 30 min
**Responsable**: DevOps
**Validation**: Logs confirmant l'exécution

---

### Tâche 7: Documentation & Handover
**Objectif**: Documenter et former l'équipe

```
[ ] Créer guide d'utilisation:
    - Comment ajouter une nouvelle collection
    - Comment debug un client
    - Comment consulter les logs
    - Troubleshooting courant

[ ] Documentation maintenance:
    - Procédure de mise à jour du code
    - Procédure backup metafields
    - Procédure rollback en cas de problème

[ ] Formation équipe:
    - Demo du système
    - Explication du flow
    - Exercices pratiques
    - Q&A
```

**Durée estimée**: 90 min
**Responsable**: Tech Lead
**Validation**: Documentation revue + formation complétée

---

### Tâche 8: Optimisations & Maintenance
**Objectif**: Améliorer le système en production

```
[ ] Monitoring après 1 semaine:
    → Analyser les logs
    → Vérifier les taux de succès/erreur
    → Identifier les problèmes

[ ] Optimisations possibles:
    → Ajouter caching (collections)
    → Améliorer la stratégie de recommandations
    → Ajouter A/B testing
    → Optimiser les appels API

[ ] Planifier les améliorations futures:
    → Support multi-collections
    → Personnalisation par segment client
    → Analytics & reporting
```

**Durée estimée**: Ongoing
**Responsable**: Tech Team
**Validation**: Métriques d'amélioration

---

## CHRONOLOGIE RECOMMANDÉE

```
Jour 1-2:    Tâches 1, 2 (Shopify + Azure)
Jour 3-4:    Tâche 3 (Email template)
Jour 5:      Tâche 4 (Shopify Flow)
Jour 6:      Tâche 5 (Test E2E)
Jour 7:      Tâche 6 (Production)
Jour 8+:     Tâche 7 (Documentation)
Continu:     Tâche 8 (Maintenance)
```

---

## RISQUES & MITIGATION

| Risque | Impact | Mitigation |
|--------|--------|-----------|
| Function timeout | Clients non traités | Batch processing + retry |
| Token expiration | Production down | Auto-refresh + alertes |
| API rate limit | Erreurs API | Queue system + throttling |
| Email non livré | Clients oubliés | Delivery tracking |
| Bug Shopify Flow | Emails pas envoyés | Flow backup + monitoring |

---

## LIVRABLES ATTENDUS

✅ Function Azure déployée et testée
✅ Shopify Flow configurée et validée
✅ Email template créé et testé
✅ Documentation complète
✅ Métriques de performance
✅ Plan de maintenance

---

**Estimation totale**: 4-5 jours de travail
**Responsables**: DevOps, Shopify Admin, Marketing, QA
**Date cible production**: [À définir]
