# Guide de Mise en Production : Recommendation Engine 🚀

Ce document explique comment le système fonctionne en mode automatique et comment vous pouvez piloter la mise en service réelle.

## 1. Fonctionnement Automatique (Automation)
Le moteur peut être déclenché de deux façons :
- **Azure Timer** : Configuré par défaut chaque Lundi à 02:00.
- **Shopify Flow (Recommandé)** : Vous pouvez désormais déclencher le scan **directement depuis Shopify**.

## 1bis. Nouveau : Contrôle via Shopify Flow
Pour donner la main à votre collègue sur le déclenchement :
1.  **Créer un nouveau Flow** dans Shopify.
2.  **Trigger** : Choisir "Scheduled time" (ex: Chaque Lundi à 09:00).
3.  **Action** : Choisir "Send HTTP request".
    - **URL** : `https://func-shopify-crossselling-dev.azurewebsites.net/api/run_global_scan?code=VOTRE_CLE`
    - **Méthode** : `POST`
4.  **Résultat** : En activant/désactivant ce Flow dans Shopify, votre collègue pilote entièrement le moteur sans toucher au code Azure.

## 2. Comment "Mettre en Pause" ou "Lancer"
Le système est actuellement **en pause de fait** car vous avez le contrôle total via Shopify Flow.

- **Pour rester en pause** : Laissez votre Flow Shopify ("Cross-sell Tag Added") sur **OFF (Désactivé)**. Même si la fonction Azure tourne le lundi, aucun mail ne partira.
- **Pour passer en production** : Une fois que votre collègue a fini le design, passez simplement le Flow sur **ON (Activé)**. 

## 3. Procédure de Mise en Production (Go-Live)
Le code est déjà déployé et prêt. Voici les étapes pour un lancement propre :

1.  **Template Final** : Copiez le code Liquid final dans votre modèle d'email Shopify.
2.  **Test Final** : Faites un dernier test sur votre mail via le dashboard (ou en rajoutant manuellement le tag `trigger_reco` à votre fiche client).
3.  **Activation Flow** : Activez le Flow dans Shopify. Dès le lundi suivant, les premiers clients réels commenceront à recevoir leurs emails.

## 4. Maintenance & Surveillance
- **Logs** : Vous pouvez consulter les rapports d'exécution dans le dossier `azure_function/reports` (via le portail Azure ou en local).
- **Dashboard** : Si vous avez besoin de refaire des tests, le code du dashboard est archivé dans `azure_function/Doc/dashboard_archive.html`. Il peut être réactivé en 2 minutes en modifiant `function_app.py`.
- **Sécurité** : N'oubliez pas que les URLs de test (`/api/dry_run`, etc.) demandent désormais la **Function Key** d'Azure.

---
*Le système est maintenant stable, sécurisé et prêt à l'emploi. Vous avez les clés en main !* 🏁
