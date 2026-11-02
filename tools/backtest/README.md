# Backtest du score ARCA

Rejoue le vrai code du dashboard (`Test.html`) à des dates passées, avec des réponses d'API reconstituées « telles qu'à la date » (horloge du navigateur figée, historiques tronqués).

1. `python3 record.py ../../Test.html` : enregistre les URLs appelées par la page ARCA (`urls.json`).
2. `python3 download.py` : met en cache les historiques DefiLlama et CoinGecko (CoinGecko gratuit = 365 jours max ; relancer si des 429 restent).
3. `python3 replay.py ../../Test.html 2025-12-01,2026-01-01,...` : score et signal par token et par date (`scores.json`).
4. `python3 analyze.py` : performance à 30 / 90 j par signal et par tranche de score.

Limites : tables manuelles (inflation, value accrual, risk flags) = valeurs d'aujourd'hui (biais d'anticipation) ; univers = tokens actuels (biais de survie) ; Binance non utilisé (prix CoinGecko).
