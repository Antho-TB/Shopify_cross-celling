╔══════════════════════════════════════════════════════════════════════════════╗
║               🔄 IMPLÉMENTATION: RELANCE HEBDOMADAIRE                         ║
║                    6 MOIS ±7 JOURS (173-180 JOURS)                           ║
║                                                                              ║
║                         ✅ CONFIGURATION COMPLÈTE                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 RÉSUMÉ DES CHANGEMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ce qui a changé:
  ✓ Schedule: Quotidien → Hebdomadaire (lundi à 2h)
  ✓ Fenêtre: 365-548j (18-12m) → 173-180j (6m ±7j)
  ✓ Fonction: daily_cross_sell_scanner → weekly_cross_sell_scanner
  ✓ Variables par défaut mises à jour
  ✓ Test de validation créé

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ TIMING DE LA RELANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Schedule: "0 0 2 * * 1"
  0     = Minute 0
  0     = Heure 0
  2     = 2h du matin
  *     = Chaque jour du mois
  *     = Chaque mois
  1     = Lundi (0=Dimanche, 1=Lundi, ..., 6=Samedi)

Fréquence: CHAQUE LUNDI À 2H DU MATIN ⏰

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 FENÊTRE TEMPORELLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Avant (12-18 mois):
  ORDER_DELAY_DAYS_START = 365 jours (12 mois)
  ORDER_DELAY_DAYS_END = 548 jours (18 mois)

Après (6 mois ±7 jours):
  ORDER_DELAY_DAYS_START = 173 jours (6 mois - 7 jours)
  ORDER_DELAY_DAYS_END = 180 jours (6 mois pile)

Fenêtre: 7 jours glissante centrée sur 6 mois ✓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 EXEMPLE DE FLUX RÉEL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Scénario: Client achète une paire de Forgés le 22 janvier 2025

Timeline:
  22 janvier 2025       Client achète (couteau Forgés)
                        ↓
  15 juillet 2025       Début fenêtre de relance (6m - 7j)
  16-21 juillet 2025    Client PEUT recevoir un email
  22 juillet 2025       Fin fenêtre de relance (6m pile)
                        ↓
  LUNDI 21 juillet      SCAN HEBDOMADAIRE
   2h du matin          → Détecte le client dans la fenêtre
                        → Calcule recommandations
                        → Injecte tag "trigger_reco"
                        ↓
  Pendant la nuit       SHOPIFY FLOW
   (quelques min)       → Détecte tag "trigger_reco"
                        → Envoie email de relance
                        → Retire tag + met à jour metafield
                        ✅ DONE

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ AVANTAGES DE CETTE APPROCHE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Email au moment OPTIMAL (6 mois après achat)
✓ Pas d'emails dupliqués (chaque client 1x maximum)
✓ Fréquence réduite (1x/semaine au lieu de quotidien)
✓ Volume prévisible (X clients/semaine)
✓ Facile à debugger (fenêtre connue)
✓ Scalable (ajouter collections sans impact)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 FICHIERS MODIFIÉS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ azure_function/core/function_app.py
  - Renommé: daily_cross_sell_scanner → weekly_cross_sell_scanner
  - Schedule: "0 0 2 * * *" → "0 0 2 * * 1" (lundi)
  - Paramètres: 365-548 → 173-180 jours
  - Docstring: Mis à jour

✓ azure_function/tests/test_6months_weekly_window.py (NOUVEAU)
  - Valide la fenêtre 173-180 jours
  - Teste toutes les collections
  - Affiche détails client + recommandations

✓ README.md
  - Section "LOGIQUE DE RELANCE" ajoutée
  - Explique la fenêtre temporelle
  - Exemple réel inclus
  - local.settings.json mis à jour avec 173-180
  - Instructions test du trigger incluses

✓ LISTE_TACHES.md
  - Indique que la relance est configurée
  - Fenêtre et timing documentés

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 POUR TESTER LOCALEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Option 1: Tester validation (sans déclenchement)
```bash
python tests/test_6months_weekly_window.py
```

Option 2: Tester le trigger planifié
```bash
# Démarrer la function
func start

# Dans un autre terminal, faire une requête (ne fait rien si pas lundi 2h)
# Le trigger se déclenchera le lundi suivant à 2h du matin
```

Option 3: Modifier le schedule pour test
```
Schedule: "0 0 * * * *" (toutes les heures)
Après test: revenir à "0 0 2 * * 1" (lundi 2h)
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 POUR LA PRODUCTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Déployer sur Azure (voir TACHES_SUIVANTES.md):

1. Publier le code
   func azure functionapp publish func-shopify-cross-sell

2. Configurer les variables
   az functionapp config appsettings set \
     --name func-shopify-cross-sell \
     --resource-group rg-shopify \
     --settings \
       SHOPIFY_STORE_URL="tbgroupe-fr.myshopify.com" \
       SHOPIFY_ACCESS_TOKEN="shpca_..." \
       TARGET_COLLECTION_ID="298781474968" \
       ORDER_DELAY_DAYS_START="173" \
       ORDER_DELAY_DAYS_END="180"

3. Tester via HTTP (ne se déclenche pas auto hors lundi)
   curl -X POST https://func-shopify-cross-sell.azurewebsites.net/api/check_recommendations

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 MODIFICATIONS VIA PARAMÈTRES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Si vous voulez changer la fenêtre (ex: 4-6 mois au lieu de 6m ±7j):

Avant (12-18 mois):
  ORDER_DELAY_DAYS_START = "365"
  ORDER_DELAY_DAYS_END = "548"

Après (4-6 mois):
  ORDER_DELAY_DAYS_START = "121"    (4 mois)
  ORDER_DELAY_DAYS_END = "181"      (6 mois)

Pour changer le jour/heure:
  Schedule: "0 0 2 * * 1"
            minute heure jour mois annee jour_semaine
  
  Exemples:
  "0 0 2 * * 1" = Lundi 2h (actuellement)
  "0 9 * * * 1" = Lundi 9h
  "0 0 2 * * 2" = Mardi 2h
  "0 0 2 * * 0" = Dimanche 2h

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ CHECKLIST FINAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Code:
  [x] Function renommée et schedule mis à jour
  [x] Paramètres par défaut changés (173-180)
  [x] Test de validation créé
  [x] Documentation mise à jour
  [x] Git commit effectué

Production-Ready:
  [x] Fenêtre temporelle validée
  [x] Timing de relance configuré
  [x] Test local disponible
  [x] Pas de régression sur code existant

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

         Git commit: "⏰ Implémentation relance hebdomadaire..."
         Date: 22 janvier 2026
         Status: ✅ PRÊT POUR PRODUCTION

Prochaine étape: Tâche 1 (Configuration Shopify) dans TACHES_SUIVANTES.md

╚══════════════════════════════════════════════════════════════════════════════╝
