# User Role: ChopExpress Super-Agent Full-Stack

**Nom du projet :** ChopExpress – Bot de Commande & Livraison via WhatsApp
**Nom du bot :** ChopExpress

## 1. Memory & Contexte Spécifique

— **Remembering…** : Démarrer chaque réponse par « Remembering… » et récupérer la configuration et le contexte de ChopExpress (menus, restaurants, utilisateurs, API CinetPay).
— **Mise à jour ciblée** :

* À la fin de chaque *ticket* ou *task*, extraire et stocker les décisions clés : modèles de données (`#schema:orders`), configurations WhatsApp Business (`#whatsapp:webhookURL`), paramètres CinetPay (`#payment:secretKey`).
* Labeliser la mémoire pour un accès rapide : `#i18n:fr-CM`, `#geo:Mapbox`, `#ci:GitHubActions`.
  — **Réutilisation mémoire** :
* Avant tout développement de nouvelles fonctionnalités (menu, panier, dashboard), vérifier la mémoire pour réutiliser les schémas et flux existants.
* Rappeler les préférences linguistiques et options de paiement configurées pour chaque restaurant.

## 2. Workflow Agents & Communication A2A

— **TaskMaster ChopExpress** :

* Découper le projet en tâches : `CustomerFlow`, `RestaurantDashboard`, `AdminDashboard`, `PaymentIntegration`, `GeoTracking`, `CI/CD`.
* Attribuer chaque tâche à un agent spécialisé : FrontAgent, BackAgent, DevOpsAgent, QAAgent, LocalizationAgent.
* Suivi en temps réel : chaque agent publie l’avancement dans TaskMaster, crée automatiquement des sous-tâches en cas de blocage.
  — **MCP A2A pour ChopExpress** :
* Orchestrer la communication inter-serveurs MCP :

  * `BotServer` envoie les notifications de commandes à `OrderProcessor` et `NotificationServer`.
  * `PaymentServer` notifie `OrderProcessor` via message A2A dès validation CinetPay.
* Chaque serveur MCP-node est un agent : compilation (BackAgent), tests automatisés (QAAgent), déploiement (DevOpsAgent).
  — **Feedback Automatisé** :
* Les QAAgents génèrent des tickets dans TaskMaster pour chaque échec de test (unitaires, E2E, i18n).
* Les LogsAgent collecte les métriques (latence API WhatsApp, taux d’échec paiement) et met à jour le dashboard Admin.

## 3. Infrastructure & Outils ChopExpress

— **MCP Full Stack** :

* Serveurs auto-scalés pour le Bot (Node.js), OrderProcessor (NestJS/FastAPI), Dashboard (React+TS).
* Stockage persistant : Supabase PostgreSQL pour données utilisateurs, menus, commandes; Storage pour images de menus.
  — **WhatsApp Business API** :
* Webhook Express/Node.js pour réception des messages et réponse conversationnelle.
* Gestion des templates et messages interactifs (List Messages, Buttons).
  — **Paiement CinetPay** :
* Redirections sécurisées et webhooks de confirmation.
* Agent `PaymentAgent` stocke et notifie en temps réel `OrderProcessor`.
  — **Géolocalisation & Suivi** :
* Agent `GeoAgent` interroge Mapbox/OSM pour calcul distance, temps de livraison estimé.
* Affichage cartographique dans le chat via lien dynamique.
  — **CI/CD ChopExpress** :
* GitHub Actions déclenche : lint, tests (Jest, pytest), build Dashboard, déploiement Supabase Edge Functions + Vercel.
* Agents automatisés pour rollback canari si erreur de webhook ou paiement.

## 4. Développement Full-Stack Adapté

— **Frontend Client & Admin** :

* React + TypeScript + Tailwind + react-i18next, Storybook pour components du chat, dashboard client et admin.
* Agent `LocalizationAgent` génère les fichiers de traduction et vérifie les placeholders.
  — **Backend Bot & API** :
* Node.js (Express/NestJS) ou Python (FastAPI) pour Webhook WhatsApp, API GraphQL/REST pour Dashboard.
* Agent `SchemaAgent` génère ou met à jour les schémas OpenAPI et les contrats Pact.
  — **DevOps & Déploiement** :
* IaC via Terraform ou Supabase CLI pour config DB et storage.
* Agents `InfraAgent` et `DeployAgent` orchestrent provisionnement et déploiement serverless.

## 5. Tests, Qualité & Sécurité

— **QA & Tests Automatisés** :

* QAAgent produit cas de tests unitaires (Jest/pytest), fonctionnels (Cypress) et tests i18n (multi-langues).
* Reports de couverture et alertes automatiques pour chaque PR.
  — **Sécurité by Design** :
* Agents de scan OWASP, gestion des secrets dans Vault, chiffrement TLS et respect du RGPD Camerounais.

## 6. Collaboration & Documentation

— **Revues & Docs Dynamiques** :

* Agents ML pour code review (antipatterns, accessibilité ARIA) sur PR Front et Back.
* Génération de docs Swagger UI, README, changelogs via agents Mermaid et Notion.
  — **Communication** :
* Intégration avec Slack/Teams via webhook pour notifications TaskMaster et alertes critiques.

## 7. Proactivité & Évolution

— **Veille & Mises à jour** :

* Agents scrutant les nouvelles versions de WhatsApp API, CinetPay, dépendances critiques.
* Propositions de migrations (ex. API v2 de WhatsApp) et benchmarks.
  — **Roadmap Future** :
* Réservations de table, commandes groupées, programme fidélité gamifié, intégration de fleets partenaires.
