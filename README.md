# Crypto Dashboard v4 — ARCA + Ichimoku

Professional-grade crypto trading & analysis dashboard combining institutional Ichimoku technical analysis with ARCA/Dorman-style fundamental valuation.

## Features

### Ichimoku Page (Technical Analysis)
- **Full Ichimoku Kinko Hyo** with crypto-optimized parameters (20/60/120/30)
- **Multi-timeframe bias** (1H, 4H, 1D, 1W) with alignment summary
- **RSI 14** with Wilder's smoothing + divergence detection
- **MACD (12/26/9)** with crossover alerts, integrated as T2 signal
- **Fibonacci retracements** (auto-calculated from 200-bar swing)
- **Session VWAP** with σ bands (disabled on 1W)
- **Volume Profile** with POC, VAH, VAL
- **Confluence scoring** (T1 structural + T2 confirmation)
- **Export function** — structured JSON via clipboard, console, and `window.__ICHIMOKU_EXPORT__`

### ARCA Page (Fundamental Analysis)
- **8 tokens tracked**: HYPE, JUP, UNI, AAVE, PUMP, ONDO, MET, ASTER
- **Dynamic Strike Price** from live DefiLlama revenue + CoinGecko supply
- **Multi-factor conviction score**: Value (40%) + Quality (35%) + Risk (25%)
- **Sector P/E targets** per asset class (DEX, Lending, RWA, etc.)
- **Token unlock donut charts** (circulating vs locked supply)
- **Dorman allocation model** with sector caps and zero-weight thresholds
- **Rich tooltips** on every metric (formula + signal interpretation)
- **Risk & Market metrics**: volatility, volume/MC ratio, 7d/30d changes

## Data Sources (all public, no API keys required)
- **Binance** — real-time prices, 24h tickers, historical candles
- **CoinGecko** — market cap, supply, volume, ATH, price changes
- **DefiLlama** — protocol revenue, fees, TVL
- **Hyperliquid** — HYPE mark price

## Deployment

Single HTML file — just serve `index.html`. No build step, no dependencies.

### GitHub Pages
1. Create a repo, push `index.html`
2. Settings → Pages → Source: main branch → Save
3. Live at `https://username.github.io/repo-name`

### Netlify
1. Drag & drop the file at [app.netlify.com/drop](https://app.netlify.com/drop)
2. Instant URL generated

## License
For personal/educational use. Not financial advice.
