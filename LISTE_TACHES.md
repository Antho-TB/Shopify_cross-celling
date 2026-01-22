# 📋 LISTE RAPIDE DES TÂCHES SUIVANTES

## ✅ Ce qui est DONE (Production-Ready)
- ✓ Code Python (Logging + Azure Function)
- ✓ **Relance hebdomadaire configurée** (lundi 2h, fenêtre 6 mois ±7j)
- ✓ Validation 6 mois ±7 jours réussie
- ✓ Tests finalisés et consolidés
- ✓ Documentation complète
- ✓ Projet nettoyé

---

## 📅 CONFIGURATION DE LA RELANCE

**Timing**: Chaque lundi à 2h du matin  
**Fenêtre**: 173-180 jours (6 mois -7 jours à 6 mois pile)  
**Frequence**: 1x par semaine par client  

**Exemple**:
- Client achète le 22 janvier 2025
- Relance le lundi 21 juillet 2025 (6 mois ±7 jours)
- Pas de duplicate (tag de tracking)

---

## ⏳ Ce qui RESTE À FAIRE (8 tâches)

### 1️⃣ Shopify Setup (15 min) - Admin Shopify
- [ ] Créer Custom App (scopes: read_products, read_orders, read_customers, write_customers)
- [ ] Copier le token
- [ ] Créer Metafield: `cross_sell.next_recommendations` (text)
- [ ] Créer Metafield: `cross_sell.last_recommendations_sent` (datetime)

**Validation**: Tokens et metafields visibles dans Admin

---

### 2️⃣ Azure Deploy (30 min) - DevOps
- [ ] Créer ressources Azure (group, storage, functionapp)
- [ ] Publier le code: `func azure functionapp publish`
- [ ] Configurer les 5 variables d'environnement
- [ ] Tester HTTP endpoint

**Validation**: HTTP 200 avec JSON

---

### 3️⃣ Email Template (45 min) - Marketing
- [ ] Accéder à Shopify Email
- [ ] Créer template "Relance 6 mois - Recommandations"
- [ ] Structure: Header + Recap + Recommandations (3 produits) + CTA
- [ ] Tester le preview

**Validation**: Email au bon format, variables Liquid OK

---

### 4️⃣ Shopify Flow (60 min) - Shopify Admin + Developer
- [ ] Créer Flow: "Relance Cross-Selling 6 mois"
- [ ] Trigger: Customer tag added = "trigger_reco"
- [ ] Action 1: HTTP POST à l'Azure Function
- [ ] Action 2: Parse réponse JSON
- [ ] Action 3: Send email via Shopify Email
- [ ] Action 4: Update customer tag (retirer trigger_reco)
- [ ] Action 5: Update metafield (date du send)
- [ ] Tester avec un client test

**Validation**: Email reçu, tags et metafields mis à jour

---

### 5️⃣ Test End-to-End (45 min) - QA + Developer
- [ ] Créer `tests/test_e2e.py`
- [ ] Ajouter tag "trigger_reco" à un client test
- [ ] Vérifier que Flow s'exécute
- [ ] Vérifier que metafield est mis à jour
- [ ] Vérifier que l'email est reçu

**Validation**: Rapport de test signé QA

---

### 6️⃣ Production Setup (30 min) - DevOps
- [ ] Activer le trigger planifié (2h du matin)
- [ ] Configuration: 365-548 jours (12-18 mois)
- [ ] Setup Application Insights pour monitoring
- [ ] Créer alertes pour les erreurs

**Validation**: Scanner se déclenche automatiquement

---

### 7️⃣ Documentation (90 min) - Tech Lead
- [ ] Créer guide utilisateur (comment ajouter collection, debug, logs)
- [ ] Créer runbook maintenance (update code, backup, rollback)
- [ ] Former l'équipe (démo + exercices)
- [ ] Q&A documentation

**Validation**: Équipe capable de faire maintenance basique

---

### 8️⃣ Monitoring (Ongoing) - Tech Team
- [ ] Monitorer logs après 1 semaine
- [ ] Analyser taux de succès/erreur
- [ ] Identifier problèmes
- [ ] Planifier améliorations (cache, A/B test, etc.)

**Validation**: Métriques saines, aucun error

---

## 📊 RÉSUMÉ

| Tâche | Durée | Qui | Statut |
|-------|-------|-----|--------|
| 1. Shopify Setup | 15 min | Admin Shopify | 🔲 TODO |
| 2. Azure Deploy | 30 min | DevOps | 🔲 TODO |
| 3. Email Template | 45 min | Marketing | 🔲 TODO |
| 4. Shopify Flow | 60 min | Admin + Dev | 🔲 TODO |
| 5. Test E2E | 45 min | QA + Dev | 🔲 TODO |
| 6. Production | 30 min | DevOps | 🔲 TODO |
| 7. Documentation | 90 min | Tech Lead | 🔲 TODO |
| 8. Monitoring | Ongoing | Tech Team | 🔲 TODO |
| **TOTAL** | **~5 jours** | **Équipe** | **🔲 TODO** |

---

## 🎯 CHRONOLOGIE RECOMMANDÉE

```
Jour 1 matin:    Tâches 1 + 2
Jour 1 après-m:  Tâche 3
Jour 2 matin:    Tâche 4
Jour 2 après-m:  Tâche 5
Jour 3 matin:    Tâche 6
Jour 3-4:        Tâche 7
Continu:         Tâche 8
```

---

## 📞 CONTACTS

- **Admin Shopify**: Pour Custom Apps + Metafields
- **DevOps/Azure**: Pour déploiement et monitoring
- **Marketing**: Pour email template
- **Developer**: Pour Flow + intégration
- **QA**: Pour tests end-to-end

---

## 🔗 RESSOURCES

- Code prêt: `azure_function/core/`
- Tests disponibles: `azure_function/tests/`
- Docs complètes: `README.md` et `TACHES_SUIVANTES.md`

---

**Dernière mise à jour**: 22 janvier 2026  
**Statut Code**: ✅ Production-Ready  
**Prochain étape**: Tâche 1 (Shopify Setup)
