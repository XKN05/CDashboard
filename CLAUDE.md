# CDashboard

Dashboard crypto en **un seul fichier `index.html`** (HTML/JS), déployé sur GitHub Pages.
Pages : Home, Crypto Macro, ARCA, Ichimoku, Strategy Builder.
`Test.html` est une ancienne copie de test, à ne pas modifier sans accord.

## Façon de travailler
- Français, ton informel et concis.
- Un changement à la fois, validé par Tim, testé entre chaque. Pas de refonte non demandée.
- Réponses complètes (implémentation entière d'un coup) plutôt que mini-étapes.
- Données : signaler les chiffres douteux plutôt que les accepter.
- Échec propre (log + continuer), pas de boucles de retry. Fetch parallèles avec `Promise.allSettled()`.
- Bumper `BUILD` (footer Ichimoku) à chaque patch pour vérifier quel fichier est chargé.

## Les trois reviewers
Claude joue trois rôles. Les deux premiers passent sur **chaque patch de `index.html`**, avant le push. Le rapport est séparé en « Technique » et « Méthode & données ».

### 1. Reviewer technique (chaque patch)
Cherche activement les bugs dans son propre patch.
1. Relire le diff (`git diff`) : régressions, cas limites, courses entre requêtes, ids DOM inexistants, effets sur les autres pages.
2. Syntaxe JS : extraire les `<script>` inline et lancer `node --check`.
3. Test navigateur headless (Playwright, réseau simulé, Chromium dans `/opt/pw-browsers/chromium`) quand le changement touche aux fetch, à la sélection de token ou à l'affichage. Zéro `pageerror`.
4. `BUILD` bumpé.
5. Rapport honnête : ce qui est vérifié, ce qui ne l'est pas (tout ce qui dépend du vrai réseau Binance/Hyperliquid), risques restants.
6. Push sur la branche de travail uniquement ; la fusion dans `main` passe par une PR validée par Tim.

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
- Toute proposition touchant au scoring ARCA attend le bilan de janvier 2027.

**Rappel** : au début de chaque conversation, si la dernière session penseur ci-dessous date de plus de 14 jours (ou n'a jamais eu lieu), le rappeler à Tim. Mettre la date à jour après chaque session penseur.

Dernière session penseur : jamais

## Règles métier
- Ichimoku de référence : Tenkan 20, Kijun 60, SpanB 120, Displacement 30.
- `arca_snapshot.py` (pipeline Python local, Task Scheduler) doit répliquer exactement la logique du dashboard (TF_SCALES inclus). Il n'est pas dans ce repo.
- Score ARCA v2 en test parallèle (colonne « v2 test »), v1 reste officielle. Pas de modification du scoring avant le bilan de début janvier 2027.

## Sources de données
Binance spot + futures, Hyperliquid (HYPE via `candleSnapshot`, repli Binance), DefiLlama, CoinGecko, alternative.me, mempool.space, allorigins.win (proxy CORS, en premier).
Binance et Hyperliquid sont injoignables depuis la sandbox Claude Code : le test sur le vrai réseau se fait côté Tim.

## À faire / points ouverts
- Format réel de `candleSnapshot` jamais observé (basé sur la doc Hyperliquid).
- Retry sur 429/418 dans `fetchBinanceCandles` absent du build actuel : à remettre si les « — » persistent sur les badges multi-TF.
- Si toutes les sources échouent pour un token, la page Ichimoku garde le prix/l'analyse du token précédent sous le nouveau nom (seul un bandeau d'erreur s'affiche).
- `HL_INTERVAL_MS` ne couvre que 1h, 4h, 1d, 1w (autre intervalle → repli Binance).
- Décision : `arca_snapshot.py` lit-il aussi HYPE sur Hyperliquid, ou on accepte l'écart avec les bougies Binance ?
- Pistes hors bug : données SYRUP à revérifier, bot de trading Hyperliquid (seulement si le scoring ARCA + Ichimoku est prouvé), tracker de positions DeFi (pas démarré).
