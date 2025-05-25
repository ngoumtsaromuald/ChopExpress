**Nom du projet : ChopExpress – Bot de Commande & Livraison via WhatsApp**
**Nom du bot : ChopExpress**

**1. Contexte & Vision**
Dans un Cameroun en pleine digitalisation, les utilisateurs recherchent des solutions familières et rapides pour commander leurs repas. En s’appuyant sur WhatsApp — l’application de messagerie la plus utilisée — ce projet vise à créer un bot intelligent qui facilite l’expérience « restaurant à la maison » tout en dotant les établissements d’outils puissants de gestion de commandes et de fidélisation.

**2. Objectifs**

* Offrir aux clients une expérience de commande 100 % conversationnelle, sans installation requise
* Permettre aux restaurants d’optimiser la réception et le suivi des commandes
* Fournir aux administrateurs une vue d’ensemble en temps réel et des indicateurs de performance

**3. Périmètre Fonctionnel**

| Rôle               | Fonctionnalités clés                                             |
| ------------------ | ---------------------------------------------------------------- |
| **Client**         | • Recherche par géolocalisation et type de cuisine               |
|                    | • Menu interactif (images, descriptions, prix)                   |
|                    | • Panier avec personnalisation (notes, quantités)                |
|                    | • Options de livraison ou retrait                                |
|                    | • Paiement sécurisé via CinetPay                                 |
|                    | • Notifications de statut (préparation, livraison)               |
|                    | • Suivi en temps réel (interface carte)                          |
|                    | • Historique de commandes & évaluations                          |
| **Restaurant**     | • Réception automatique des commandes                            |
|                    | • Gestion des statuts (en préparation, prêt, retard, annulé)     |
|                    | • Contrôle dynamique du menu (stocks, promotions, plats du jour) |
|                    | • Messagerie intégrée avec le client pour précisions             |
| **Administrateur** | • Tableau de bord global (commandes, revenus, taux d’annulation) |
|                    | • Gestion des litiges et remboursements                          |
|                    | • Modération (approbation des restaurants, filtrage des avis)    |
|                    | • Support intégré via chat                                       |

**4. Scénarios d’Utilisation**

* *Client* : Envoie « Commander » → choisit un restaurant → compose son panier → paie via CinetPay → reçoit une confirmation + estimation de temps
* *Restaurant* : Reçoit une alerte « Commande #45 » → clique sur « Préparer » → définit un délai → le client est notifié en temps réel
* *Admin* : Reçoit une alerte litige → consulte l’historique de commande → échange avec les parties concernées → déclenche un remboursement partiel depuis l’interface

**5. Architecture Technique**

* **Interface Bot** : API WhatsApp Business (Node.js + Express webhook)
* **Back-end** : Node.js (NestJS) ou Python (FastAPI) avec support complet i18n (i18next ou équivalent)
* **Base de données** : Supabase (PostgreSQL géré + Auth + Stockage) pour utilisateurs, menus, commandes, traductions
* **Tableau de bord Admin** : React + TypeScript + TailwindCSS + react-i18next
* **Paiement** : Intégration de l’API CinetPay
* **Géolocalisation** : APIs Mapbox ou OpenStreetMap pour les calculs de distance et le suivi de livraison
* **Notifications** : Webhooks WhatsApp pour la messagerie proactive, SMS de secours en option
* **CI/CD** : GitHub Actions pour les tests, le linting, et le déploiement direct vers Supabase Edge Functions ou Vercel/Netlify (sans Docker)
* **Hébergement** : Cloud sans serveur (Supabase Edge Functions, Vercel ou Netlify)

**6. Internationalisation (i18n)**

* Détection automatique de la langue basée sur les paramètres de l’utilisateur ou le premier message
* Traductions stockées dans la table `translations` de Supabase
* Chargement dynamique des fichiers de langue côté front-end et back-end
* Langue de secours configurable par module/message
* Tests de bout en bout couvrant toutes les variantes linguistiques
* **Multilingue pour le Cameroun** : Prise en charge complète du français et de l’anglais camerounais (terminologies locales incluses)

**7. Modèle de Données & Workflow**

1. *Le client* demande un menu →

   * Le bot interroge Supabase pour les restaurants et menus disponibles
   * Le bot retourne des options de menu interactives
2. *Le client* ajoute des articles au panier →

   * Mise à jour des stocks en temps réel
3. *Déclenchement du paiement* →

   * Redirection vers CinetPay → webhook notifie le back-end → mise à jour du statut de commande
4. *Confirmation de commande* →

   * Notification envoyée au restaurant via webhook
5. *Livraison* →

   * Position du livreur suivie et affichée au client

**8. Gestion des Risques**

* **Limitations WhatsApp** : implémenter des stratégies de réessai et de temporisation, rappels par SMS de secours
* **Scalabilité** : mise à l’échelle automatique serverless, file de messages pour absorber les pics
* **Sécurité & Conformité** : chiffrement TLS, coffre-fort sécurisé pour les secrets, respect des normes locales de protection des données

**9. Indicateurs de Succès (KPIs)**

* Taux de conversion (session chat → commande)
* Temps moyen de préparation + livraison
* Taux de fidélisation des clients (commandes récurrentes)
* Indices de satisfaction client (notes, commentaires)

**10. Évolutions Futures**

* Réservations de table via le bot
* Commandes groupées avec paiements partagés
* Programme de fidélité ludique (points, niveaux)
* Intégration de partenaires de livraison tiers
