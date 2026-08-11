# Campagnes email win-back — paiement web /subscribe

Templates prêts à coller dans le **Campaign Builder** du backoffice
(canal 📧 Email → Sujet + Corps HTML). Le logo Kuma et le footer de
désinscription sont ajoutés automatiquement par `email_manager.send_email`.

Variables disponibles (substituées à l'envoi) : `{displayName}`, `{childName}`,
`{startCountry}`, `{progress}`, `{uid}`.

⚠️ **`{uid}` est obligatoire dans tout lien vers `/subscribe`.** La page compare
ce compte à la session web du destinataire et refuse de payer sous un autre —
sans lui, un parent connecté au web avec un compte différent de celui de l'app
paie et ne reçoit rien (arrivé pour de vrai le 2026-08-08).

## Campagnes

| Fichier | Segment (liste intelligente) | Code promo | Sujet suggéré |
|---|---|---|---|
| `winback_essai_retour50.html` | **`engaged_dormant`** 🌙 (136 joignables) | `RETOUR50` (mensuel −50 %) | `{childName} n'a pas fini son voyage en Afrique 🌍` |
| `winback_premium_rebienvenue.html` | `lapsed_premium` — **0 cible aujourd'hui** | `REBIENVENUE` (annuel −20 %) | `Reprenez là où {childName} s'était arrêté ✨` |

### Choix des segments (mesuré 2026-07-30)

- **`engaged_dormant` = « Engagés dormants »** : gratuits ayant fini ≥3 contes puis inactifs ≥8 j.
  **169 users, 136 joignables par email, 136 avec le prénom de l'enfant.** C'est la cible
  de RETOUR50.
- `convertible` ne remonte que **1** personne : il exige ≤7 j d'inactivité, or la base est
  dormante (574/801 gratuits inactifs 90 j+). Ne pas l'utiliser pour du win-back.
- `trial_expired` et `lapsed_premium` sont **structurellement vides** : `hadTrial` /
  `hadPremium` ne sont jamais écrits par l'app, et aucun ex-abonné n'existe par un autre
  critère (1 seul paiement Paystack abouti à ce jour). Garder REBIENVENUE au frigo
  jusqu'aux premiers non-renouvellements Paystack.

## ⚠️ Avant le premier envoi

1. **Déployer** les Cloud Functions (`validatePromoCode`, promos dans
   `initializePaystackPayment`) et la page hosting `/subscribe`
   (branche `claude/paystack-payment-integration-9731fb` du repo principal).
2. **Créer les codes** dans Firestore `promo_codes/{CODE}` (via console ou
   script Admin — les clients n'y ont pas accès) :

   ```
   promo_codes/RETOUR50
     active: true
     discountPercent: 50
     bonusDays: 0
     planTypes: ["monthly"]
     maxRedemptions: 500
     redemptionCount: 0
     oneTimePerUser: true
     validUntil: <date de fin de campagne>
     campaign: "winback_essai"

   promo_codes/REBIENVENUE
     active: true
     discountPercent: 20
     bonusDays: 0
     planTypes: ["annual"]
     maxRedemptions: 200
     redemptionCount: 0
     oneTimePerUser: true
     validUntil: <J+7 après l'envoi>
     campaign: "winback_premium"
   ```

3. **Test** : s'envoyer la campagne à soi-même (cible restreinte ou dry run),
   cliquer le lien, vérifier le prix barré sur `/subscribe`, payer 1 fois en
   sandbox si possible.

## Attribution / reporting

Le lien porte `?promo=CODE&utm_campaign=…`. La page transmet le code et la
campagne à `initializePaystackPayment`, qui les enregistre dans
`web_payments` (`promoCode`, `campaign`, `baseAmount` vs `amount`). Le
reporting par code/campagne lit cette collection.

## Règles

- **Canal email uniquement** pour promouvoir le paiement web — jamais de push
  in-app avec deep link vers `/subscribe` (anti-steering App Store / Play).
- Limite SMTP intégrée : 500 emails/h (`MAX_EMAILS_PER_HOUR`) — mais le quota
  réel Gmail est ~500/jour (2 000/jour en Workspace) : segmenter les envois.
- Copy : ne jamais utiliser le mot « veillée ».
