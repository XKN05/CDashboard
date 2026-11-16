# Brief : synchroniser `arca_snapshot.py` avec le dashboard

À donner à une session Claude Code lancée **sur le PC de Tim**, dans le dossier qui contient `arca_snapshot.py`.
La référence est le dashboard en ligne : https://xkn05.github.io/CDashboard/ (code : `index.html` du dépôt `XKN05/CDashboard`, branche `main`).

## Règles
- Les snapshots répliquent la logique du dashboard, mais ne sont resynchronisés que tous les 3 à 6 mois : faire **une seule** synchro, complète, puis la dater.
- Ne pas toucher au test v1 / v2 (colonne « v2 test ») ni au bilan de janvier 2027 sans demande de Tim.
- Garder les anciennes colonnes du CSV (`arca_scores.csv`) pour comparer avant / après ; ajouter une colonne `scoring_version` (ex. `2026-11`).
- Avant de remplacer le script : sauvegarde (`arca_snapshot.py.bak-AAAAMMJJ`), puis un run à blanc et une comparaison des scores avec le dashboard du jour (écart attendu : quelques points au plus, à cause de l'heure des données).

## Changements à reporter (fonctions de `index.html`)
1. **Univers** : `ARCA_ASSETS`, 22 tokens. Ajouts : LIT, DRV, PONS, SKY ; VVV retiré.
2. **Score** (`getConvictionScore`) :
   - piliers 45 / 40 / 15 (Business / Valuation / Capital Risk) ;
   - revenu : `logScore(rev/365, 10000, 22, 55)` (dès 10 K$/jour) ;
   - P/E live uniquement, grille <10 / 18 / 30 / 50× ;
   - valorisation relative (multiple actuel / médiane 90 j).
3. **Inflation et real yield** : utiliser les nombres de la table `ARCA_SUPPLY_YIELD` (`inf`, `ry`), plus le parsing du texte. Le real yield live (DefiLlama holders revenue 30 j × 12 / MC) reste prioritaire.
4. **Value accrual** : table `ARCA_VALUE_ACCRUAL` (hardcoded / discretionary / none), utilisée dans la Net dilution.
5. **Liquidité** : pénalité Vol/MC ≤ 1 % calculée sur le **volume du token** (Hyperliquid pour HYPE, sinon CoinGecko), pas sur le volume DEX du protocole.
6. **Critère « 30d Unlocks »** : éteint (l'API DefiLlama `/emission` est payante).
7. **TRX** : revenu DefiLlama live (fees de la chaîne).
8. **HYPE** : lire les bougies et le prix sur Hyperliquid (`candleSnapshot`, `metaAndAssetCtxs`), avec repli Binance — décision de Tim du 16 nov. 2026.
9. **Signal** : BUY ≥ 65, NEUTRAL 50–64, AVOID < 50 (inchangé).

## Hors score (pas besoin de les répliquer)
Matrice Dorman (`ARCA_TOKEN_DESIGN`), graphique des unlocks (`ARCA_UNLOCKS`), bloc Data health.
