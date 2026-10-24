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

## Vérifications avant tout push de `index.html`
Claude agit en reviewer : il cherche activement les bugs dans son propre patch avant de pousser.
1. Relire le diff (`git diff`) en cherchant : régressions, cas limites, courses entre requêtes, ids DOM inexistants, effets sur les autres pages.
2. Contrôle de syntaxe JS : extraire les `<script>` et lancer `node --check`.
3. Test navigateur headless (Playwright, réseau simulé) quand le changement touche aux fetch, à la sélection de token ou à l'affichage. Zéro `pageerror` / erreur console.
4. `BUILD` bumpé.
5. Rapport honnête : ce qui est vérifié, ce qui ne l'est pas (notamment tout ce qui dépend du vrai réseau Binance/Hyperliquid), et les risques restants.
6. Push sur la branche de travail uniquement ; la fusion dans `main` passe par une PR validée par Tim.

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
- Label Ichimoku affiche « Hyperliquid » même si la page est passée sur Binance.
- `HL_INTERVAL_MS` ne couvre que 1h, 4h, 1d, 1w (autre intervalle → repli Binance).
- Décision : `arca_snapshot.py` lit-il aussi HYPE sur Hyperliquid, ou on accepte l'écart avec les bougies Binance ?
- Pistes hors bug : données SYRUP à revérifier, bot de trading Hyperliquid (seulement si le scoring ARCA + Ichimoku est prouvé), tracker de positions DeFi (pas démarré).
