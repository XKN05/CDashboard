# CDashboard

Dashboard crypto en **un seul fichier `index.html`** (HTML/JS), déployé sur GitHub Pages.
Pages : Home, ARCA Fundamentals, Artemis Factor Model, Ichimoku Technical, Strategy Builder, DeFi Ecosystem.
**Tout ce qui est affiché sur le dashboard est en anglais** (textes, libellés, messages d'erreur). Les échanges avec Tim restent en français.
**Circuit de mise en ligne** : toute modification part d'abord dans `Test.html` (servi sur https://xkn05.github.io/CDashboard/Test.html). Tim vérifie sur le vrai réseau ; seulement après son feu vert, `Test.html` est copié tel quel dans `index.html` (PR séparée). `index.html` n'est jamais modifié directement.

## Façon de travailler
- Français, ton informel et concis.
- Un changement à la fois, validé par Tim, testé entre chaque. Pas de refonte non demandée.
- Réponses complètes (implémentation entière d'un coup) plutôt que mini-étapes.
- Données : signaler les chiffres douteux plutôt que les accepter.
- Échec propre (log + continuer), pas de boucles de retry. Fetch parallèles avec `Promise.allSettled()`.
- Bumper `DASH_BUILD` à chaque patch : affiché en bas de la page d'accueil pour vérifier quel fichier est chargé.

## Les trois reviewers
Claude joue trois rôles. Les deux premiers passent sur **chaque patch de `index.html`**, avant le push. Le rapport est séparé en « Technique » et « Méthode & données ».

### 1. Reviewer technique (chaque patch)
Cherche activement les bugs dans son propre patch.
1. Relire le diff (`git diff`) : régressions, cas limites, courses entre requêtes, ids DOM inexistants, effets sur les autres pages.
2. Syntaxe JS : extraire les `<script>` inline et lancer `node --check`.
3. Test navigateur headless (Playwright, réseau simulé, Chromium dans `/opt/pw-browsers/chromium`) quand le changement touche aux fetch, à la sélection de token ou à l'affichage. Zéro `pageerror`.
4. `DASH_BUILD` bumpé.
5. Rapport honnête : ce qui est vérifié, ce qui ne l'est pas (tout ce qui dépend du vrai réseau Binance/Hyperliquid), risques restants.
6. Patch appliqué à `Test.html` ; push sur la branche de travail uniquement ; fusion dans `main` par une PR validée par Tim. Promotion vers `index.html` = copie à l'identique de `Test.html` validé, dans une PR à part.

### 2. Reviewer méthode & données (chaque patch qui touche à un calcul, une source ou un affichage de chiffres ; sauté pour le purement visuel)
- Calculs : Ichimoku, RSI, MACD, score ARCA… conformes à la définition standard, ou écart voulu et documenté.
- Données : source, fraîcheur, doublons, valeurs aberrantes, chiffres douteux à signaler.
- Méthode : biais de survie, taille d'échantillon, sur-ajustement, comparabilité entre tokens.
- Ne valide pas une stratégie comme rentable (seul un backtest / le bilan de janvier 2027 le dira), pas de conseil d'investissement.

### 3. Penseur (session dédiée, toutes les 2 semaines)
Propose, ne modifie rien. Produit une note de 3 à 5 propositions classées par intérêt / effort ; Tim choisit, on implémente une par une avec les reviewers 1 et 2.
- Vision globale du dashboard, refontes, nouvelles pages utiles.
- Scan de nouveaux tokens éligibles au score ARCA.
- Veille : nouveautés ARCA sur https://www.ar.ca/blog, publications DeFi (blogs, docs, gouvernance). Posts X : pas d'accès direct sans API.
- Le scoring du dashboard peut évoluer ; tout changement de score est décidé par Tim, un par un.

**Rappel** : au début de chaque conversation, si la dernière session penseur ci-dessous date de plus de 14 jours (ou n'a jamais eu lieu), le rappeler à Tim. Mettre la date à jour après chaque session penseur.

Dernière session penseur : 2026-10-24 (note : `docs/penseur/2026-10-24.md`)

## Règles métier
- Ichimoku de référence : Tenkan 20, Kijun 60, SpanB 120, Displacement 30.
- **Le projet, c'est le dashboard (`index.html`)** : tous les scores y sont calculés en live dans le navigateur et peuvent évoluer.
- `arca_snapshot.py` (pipeline Python local de Tim, Task Scheduler, hors repo) enregistre des snapshots des scores pour analyse ultérieure (bot éventuel). Il réplique la logique du dashboard, mais n'est resynchronisé que **tous les 3 à 6 mois**, volontairement, pour garder des datasets cohérents et mesurer si les changements de scoring ont été utiles.
- Le test v1 / v2 (colonne « v2 test ») et le bilan de janvier 2027 concernent les **snapshots**, pas le dashboard. Ne pas y toucher sans demande de Tim.

## Sources de données
Binance spot + futures, Hyperliquid (HYPE via `candleSnapshot`, repli Binance), DefiLlama, CoinGecko, alternative.me, mempool.space, allorigins.win (proxy CORS, en premier).
Binance et Hyperliquid sont injoignables depuis la sandbox Claude Code : le test sur le vrai réseau se fait côté Tim.

## À faire / points ouverts
- Format réel de `candleSnapshot` jamais observé (basé sur la doc Hyperliquid).
- Retry sur 429/418 dans `fetchBinanceCandles` absent du build actuel : à remettre si les « — » persistent sur les badges multi-TF.
- `HL_INTERVAL_MS` ne couvre que 1h, 4h, 1d, 1w (autre intervalle → repli Binance).
- Décision : `arca_snapshot.py` lit-il aussi HYPE sur Hyperliquid, ou on accepte l'écart avec les bougies Binance ?
- **Tâche : vue « Prix vs fondamentaux »** — pour chaque token ARCA, variation du revenu 30 j (DefiLlama) vs variation du prix ; faire ressortir les divergences. Validée par Tim le 24 oct. 2026, pas démarrée.
- **Lot B (méthode, modifie les scores — une décision de Tim par point)** :
  - Valorisation relative ARCA (±12 pts) basée sur le `localStorage` → score différent selon l'appareil ; `ARCA_REL_SEED` pollué (~20 % de valeurs de repli répétées : TRX, AERO, ENA, MET, PENDLE, RAY, SYRUP).
  - Real Yield Net du score = `realYield` statique − `inflation` statique alors que `liveRealYield` existe ; `protocolAge` calculé avec `2026` en dur.
  - Artemis : « DAU Growth » = croissance des frais ; MC/Fees avec la market cap actuelle sur tout l'historique ; historique synthétique fabriqué en repli ; SMA 20W BTC exclut la dernière semaine clôturée.
  - DeFi : frais par chaîne répartis à parts égales entre les chaînes d'un protocole ; DAU / wallets / devs datés d'avril 2025.
- Pistes hors bug : données SYRUP à revérifier, bot de trading Hyperliquid (seulement si le scoring ARCA + Ichimoku est prouvé), tracker de positions DeFi (pas démarré).
