#!/usr/bin/env python3
"""
ARCA Daily Snapshot v3 — CDashboard
Repo : https://github.com/XKN05/CDashboard
Run  : python arca_snapshot_v3.py  (via Cowork, once/day)

Captures:
  - Prix, volume, change 24h
  - Score ARCA total + décomposition complète (Business / Valuation / Capital Risk)
  - Sous-scores détaillés de chaque pilier
  - Contexte marché (BTC price, dominance, Fear & Greed, total MC)
  - Performance forward auto-calculée (J+7, J+30) depuis l'historique existant
  - Métriques fondamentales brutes (rev, TVL, PE, PS, MC/TVL, etc.)
  - Score Ichimoku 1D + 1W (BTC, ETH, SOL, BNB, HYPE)
    · Price vs Cloud, Cloud color, TK Cross, Chikou, RSI 14
    · Score pondéré v5 (TF-differentiated) + bias BULLISH/NEUTRAL/BEARISH
"""

import json, math, os, time, base64, datetime, requests

# ═══════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════
GITHUB_TOKEN   = os.environ.get("GITHUB_TOKEN", "COLLE_TON_TOKEN_ICI")
GITHUB_OWNER   = "XKN05"
GITHUB_REPO    = "CDashboard"
SNAPSHOTS_FILE = "snapshots.json"
# ═══════════════════════════════════════════════════════

TODAY = datetime.date.today().isoformat()

# ── Tokens ARCA ───────────────────────────────────────
ARCA_ASSETS = [
    {
        "id": "HYPE", "sector": "Perps DEX",
        "source": "hyperliquid", "binanceSymbol": "HYPEUSDT",
        "defillamaSlug": "hyperliquid", "coingeckoId": "hyperliquid",
        "buybackLevel": "programmatic", "protocolAge": 2023,
        "inflation": 2.0, "realYield": 10.0,
        "staticCircSupply": 333.33e6, "staticTotalSupply": 1000e6,
    },
    {
        "id": "JUP", "sector": "DEX Aggregator",
        "source": "binance", "binanceSymbol": "JUPUSDT",
        "defillamaSlug": "jupiter", "coingeckoId": "jupiter-exchange-solana",
        "buybackLevel": "programmatic", "protocolAge": 2022,
        "inflation": 4.0, "realYield": 3.0,
        "staticCircSupply": 1.7e9, "staticTotalSupply": 10e9,
    },
    {
        "id": "UNI", "sector": "DEX Protocol",
        "source": "binance", "binanceSymbol": "UNIUSDT",
        "defillamaSlug": "uniswap", "coingeckoId": "uniswap",
        "buybackLevel": "programmatic", "protocolAge": 2020,
        "inflation": 2.0, "realYield": 0.0,
        "staticCircSupply": 600e6, "staticTotalSupply": 1000e6,
    },
    {
        "id": "AAVE", "sector": "DeFi Lending",
        "source": "binance", "binanceSymbol": "AAVEUSDT",
        "defillamaSlug": "aave", "coingeckoId": "aave",
        "buybackLevel": "programmatic", "protocolAge": 2020,
        "inflation": 0.5, "realYield": 4.0,
        "staticCircSupply": 15e6, "staticTotalSupply": 16e6,
    },
    {
        "id": "PUMP", "sector": "Memecoin Launchpad",
        "source": "binance", "binanceSymbol": "PUMPUSDT",
        "defillamaSlug": "pump-fun", "coingeckoId": "pump-fun",
        "buybackLevel": "programmatic", "protocolAge": 2024,
        "inflation": 0.0, "realYield": 8.0,
        "staticCircSupply": 590e9, "staticTotalSupply": 1000e9,
        "useFeesAsRevenue": True,
        "riskFlags": [
            {"bizMalus": -15, "riskMalus": -5},
            {"bizMalus": -10, "riskMalus": 0},
            {"bizMalus": 0,   "riskMalus": -20},
            {"bizMalus": -5,  "riskMalus": -10},
        ],
    },
    {
        "id": "ONDO", "sector": "RWA Tokenization",
        "source": "binance", "binanceSymbol": "ONDOUSDT",
        "defillamaSlug": "ondo-finance", "coingeckoId": "ondo-finance",
        "buybackLevel": "none", "protocolAge": 2023,
        "inflation": 18.0, "realYield": 1.0,
        "staticCircSupply": 3.2e9, "staticTotalSupply": 10e9,
        "useFeesAsRevenue": True,
    },
    {
        "id": "MET", "sector": "DEX / Liquidity",
        "source": "binance", "binanceSymbol": "METUSDT",
        "defillamaSlug": "meteora", "coingeckoId": "meteora",
        "buybackLevel": "programmatic", "protocolAge": 2023,
        "inflation": 3.0, "realYield": 8.0,
        "staticCircSupply": 510e6, "staticTotalSupply": 1000e6,
    },
    {
        "id": "ASTER", "sector": "Perps DEX (BNB)",
        "source": "binance", "binanceSymbol": "ASTERUSDT",
        "defillamaSlug": "aster", "coingeckoId": "aster-2",
        "buybackLevel": "programmatic", "protocolAge": 2025,
        "inflation": 8.0, "realYield": 12.0,
        "staticCircSupply": 2.5e9, "staticTotalSupply": 8e9,
    },
    {
        "id": "SYRUP", "sector": "Institutional Lending",
        "source": "binance", "binanceSymbol": "SYRUPUSDT",
        "defillamaSlug": "maple", "coingeckoId": "maple-finance",
        "buybackLevel": "programmatic", "protocolAge": 2021,
        "inflation": 1.0, "realYield": 3.0,
        "staticCircSupply": 1.2e9, "staticTotalSupply": 1.22e9,
    },
    {
        "id": "AERO", "sector": "DEX Protocol",
        "source": "binance", "binanceSymbol": "AEROUSDT",
        "defillamaSlug": "aerodrome", "coingeckoId": "aerodrome-finance",
        "buybackLevel": "programmatic", "protocolAge": 2023,
        "inflation": 25.0, "realYield": 14.0,
        "staticCircSupply": 920e6, "staticTotalSupply": 1.86e9,
    },
    {
        "id": "PENDLE", "sector": "Yield Trading",
        "source": "binance", "binanceSymbol": "PENDLEUSDT",
        "defillamaSlug": "pendle", "coingeckoId": "pendle",
        "buybackLevel": "programmatic", "protocolAge": 2021,
        "inflation": 3.0, "realYield": 12.0,
        "staticCircSupply": 258e6, "staticTotalSupply": 281e6,
    },
    {
        "id": "ENA", "sector": "Synthetic Dollar",
        "source": "binance", "binanceSymbol": "ENAUSDT",
        "defillamaSlug": "ethena", "coingeckoId": "ethena",
        "buybackLevel": "programmatic", "protocolAge": 2024,
        "inflation": 25.0, "realYield": 0.0,
        "staticCircSupply": 8.5e9, "staticTotalSupply": 15e9,
    },
    {
        "id": "RAY", "sector": "DEX Protocol (Solana)",
        "source": "binance", "binanceSymbol": "RAYUSDT",
        "defillamaSlug": "raydium", "coingeckoId": "raydium",
        "buybackLevel": "programmatic", "protocolAge": 2021,
        "inflation": 5.0, "realYield": 12.0,
        "staticCircSupply": 270e6, "staticTotalSupply": 555e6,
    },
    {
        "id": "MORPHO", "sector": "DeFi Lending",
        "source": "binance", "binanceSymbol": "MORPHOUSDT",
        "defillamaSlug": "morpho", "coingeckoId": "morpho",
        "buybackLevel": "none", "protocolAge": 2022,
        "inflation": 6.0, "realYield": 5.0,
        "staticCircSupply": 550e6, "staticTotalSupply": 1000e6,
        "useFeesAsRevenue": True,
    },
]

# ═══════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════

def safe_get(url, params=None, timeout=12):
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            print(f"    HTTP {r.status_code} — {url}")
        except Exception as e:
            print(f"    [retry {attempt+1}] {e}")
        time.sleep(2 ** attempt)
    return None

def safe_post(url, payload, timeout=12):
    for attempt in range(3):
        try:
            r = requests.post(url, json=payload, timeout=timeout)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print(f"    [retry {attempt+1}] POST {e}")
        time.sleep(2 ** attempt)
    return None

def r2(v):
    """Round to 2 decimals, None-safe."""
    return round(v, 2) if v is not None else None

def r4(v):
    return round(v, 4) if v is not None else None

def ri(v):
    return int(round(v)) if v is not None else None

# ═══════════════════════════════════════════════════════
# DATA FETCHERS
# ═══════════════════════════════════════════════════════

def fetch_binance_ticker(symbol):
    """Returns dict with price, change_24h, vol_24h_usd."""
    data = safe_get("https://api.binance.com/api/v3/ticker/24hr", {"symbol": symbol})
    if not data:
        return None
    return {
        "price":       float(data.get("lastPrice", 0) or 0),
        "change_24h":  float(data.get("priceChangePercent", 0) or 0),
        "vol_24h_usd": float(data.get("quoteVolume", 0) or 0),
        "high_24h":    float(data.get("highPrice", 0) or 0),
        "low_24h":     float(data.get("lowPrice", 0) or 0),
    }

def fetch_hyperliquid_ticker(symbol="HYPE"):
    data = safe_post("https://api.hyperliquid.xyz/info", {"type": "metaAndAssetCtxs"})
    if not data or not isinstance(data, list) or len(data) < 2:
        return None
    universe, ctxs = data[0].get("universe", []), data[1]
    for i, asset in enumerate(universe):
        if asset.get("name") == symbol and i < len(ctxs):
            ctx   = ctxs[i]
            price = float(ctx.get("markPx", 0) or 0)
            prev  = float(ctx.get("prevDayPx", 0) or 0)
            vol   = float(ctx.get("dayNtlVlm", 0) or 0)
            chg   = ((price - prev) / prev * 100) if prev > 0 else 0
            return {"price": price, "change_24h": r2(chg),
                    "vol_24h_usd": vol, "high_24h": 0, "low_24h": 0}
    return None

def fetch_defillama_fees(slug):
    """Returns dict: fees_24h, fees_7d, fees_30d, rev_24h, rev_30d."""
    data = safe_get(f"https://api.llama.fi/summary/fees/{slug}")
    if not data:
        return {}
    return {
        "fees_24h": float(data.get("total24h",    0) or 0),
        "fees_7d":  float(data.get("total7d",     0) or 0),
        "fees_30d": float(data.get("total30d",    0) or 0),
        "rev_24h":  float(data.get("revenue24h",  0) or data.get("totalRevenue24h", 0) or 0),
        "rev_30d":  float(data.get("revenue30d",  0) or data.get("totalRevenue30d", 0) or 0),
    }

def fetch_defillama_tvl(slug):
    data = safe_get(f"https://api.llama.fi/tvl/{slug}")
    try:
        return float(data)
    except (TypeError, ValueError):
        return 0.0

def fetch_coingecko_market(cg_id):
    data = safe_get(
        f"https://api.coingecko.com/api/v3/coins/{cg_id}",
        {"localization": "false", "tickers": "false",
         "market_data": "true", "community_data": "false",
         "developer_data": "false"}
    )
    if not data:
        return {}
    md = data.get("market_data", {})
    return {
        "mc":           float(md.get("market_cap",               {}).get("usd", 0) or 0),
        "fdv":          float(md.get("fully_diluted_valuation",   {}).get("usd", 0) or 0),
        "circ_supply":  float(md.get("circulating_supply",  0) or 0),
        "total_supply": float(md.get("total_supply",         0) or 0),
    }

def fetch_market_context():
    """BTC price, dominance, total MC, Fear & Greed."""
    ctx = {}

    # BTC ticker
    btc = fetch_binance_ticker("BTCUSDT")
    if btc:
        ctx["btc_price"]    = ri(btc["price"])
        ctx["btc_change_24h"] = r2(btc["change_24h"])

    # CoinGecko global
    global_data = safe_get("https://api.coingecko.com/api/v3/global")
    if global_data:
        gd = global_data.get("data", {})
        ctx["total_mc"]       = ri(gd.get("total_market_cap",         {}).get("usd", 0))
        ctx["btc_dominance"]  = r2(gd.get("market_cap_percentage",    {}).get("btc", 0))
        ctx["eth_dominance"]  = r2(gd.get("market_cap_percentage",    {}).get("eth", 0))
        ctx["total_volume_24h"] = ri(gd.get("total_volume",           {}).get("usd", 0))
        ctx["active_cryptos"] = gd.get("active_cryptocurrencies", 0)

    # Fear & Greed
    fg = safe_get("https://api.alternative.me/fng/", {"limit": 1})
    if fg and fg.get("data"):
        d = fg["data"][0]
        ctx["fear_greed"]       = int(d.get("value", 0))
        ctx["fear_greed_label"] = d.get("value_classification", "")

    return ctx

# ═══════════════════════════════════════════════════════
# SCORING v2 — décomposition complète
# Returns all sub-scores for data collection
# ═══════════════════════════════════════════════════════

def log_score(v, floor, mult, cap):
    if not v or v < floor:
        return 0
    return min(cap, mult * math.log10(v / floor))

def get_signal(score):
    if score >= 80: return "STRONG BUY"
    if score >= 65: return "BUY"
    if score >= 50: return "MODERATE"
    if score >= 35: return "RISKY"
    return "AVOID"

def calc_conviction_full(price, asset, m):
    """
    Full scoring with all sub-scores returned for analysis.
    m keys: rev_ann_30d, rev_24h, tvl, pe, ps, mc_tvl,
            circ_mc, vol_mc_ratio, dynamic_strike,
            emissions_unlock_30d_pct, data_completeness
    """
    if m.get("data_completeness", 1) < 0.4:
        return {"total": 10, "business": 0, "valuation": 0, "capital_risk": 0, "detail": {}}

    inflation  = asset.get("inflation", 0)
    bb         = asset.get("buybackLevel", "none")
    rev_ann    = m.get("rev_ann_30d", 0) or 0
    rev_24h    = m.get("rev_24h",     0) or 0
    rev30_daily = rev_ann / 365 if rev_ann else 0
    daily_rev   = rev_24h if rev_24h > 0 else rev30_daily

    detail = {}  # all sub-scores saved for analysis

    # ── BUSINESS (50%) ──────────────────────────────────
    f_biz = 30.0

    # 1a Revenue
    if rev_ann <= 0:
        rev_pts = -15
    else:
        rev_pts = round(log_score(daily_rev, 50000, 28, 55))
    f_biz += rev_pts
    detail["biz_rev_pts"] = rev_pts

    # 1b Revenue momentum
    mom_pts = 0
    mom_pct = None
    if rev30_daily > 0 and rev_24h > 0:
        mom_pct = (rev_24h - rev30_daily) / rev30_daily * 100
        mom_pts = 10 if mom_pct > 30 else 5 if mom_pct > 10 else -10 if mom_pct < -30 else -5 if mom_pct < -10 else 0
        f_biz  += mom_pts
    detail["biz_rev_momentum_pct"] = r2(mom_pct)
    detail["biz_rev_momentum_pts"] = mom_pts

    # 1c TVL
    tvl = m.get("tvl", 0) or 0
    tvl_pts = 12 if tvl > 10e9 else 8 if tvl > 3e9 else 4 if tvl > 500e6 else 1 if tvl > 100e6 else -3 if tvl <= 0 else 0
    f_biz += tvl_pts
    detail["biz_tvl_pts"] = tvl_pts

    # 1d Real yield net
    ry_net = asset.get("realYield", 0) - inflation
    ry_pts = 10 if ry_net > 10 else 6 if ry_net > 5 else 2 if ry_net > 0 else -10 if ry_net < -10 else -5 if ry_net < -5 else -2 if ry_net < 0 else 0
    f_biz += ry_pts
    detail["biz_real_yield_net"] = r2(ry_net)
    detail["biz_real_yield_pts"] = ry_pts

    # 1e Buyback
    bb_pts = 12 if bb == "programmatic" else 4 if bb == "opportunistic" else -12
    f_biz += bb_pts
    detail["biz_buyback_pts"] = bb_pts

    # Risk flags bizMalus
    risk_biz_malus = sum(rf.get("bizMalus", 0) for rf in asset.get("riskFlags", []))
    f_biz += risk_biz_malus
    detail["biz_risk_malus"] = risk_biz_malus

    f_biz = max(5, min(98, f_biz))

    # ── VALUATION (35%) ─────────────────────────────────
    f_val = 50.0
    pe = m.get("pe")
    if pe is not None:
        pe_pts = 95 if pe < 5 else 82 if pe < 10 else 65 if pe < 18 else 45 if pe < 30 else 25 if pe < 50 else 12 if pe < 80 else 5
        f_val  = float(pe_pts)
    detail["val_pe_base"] = round(f_val)

    ps = m.get("ps")
    ps_pts = 0
    if ps is not None:
        ps_pts = 12 if ps < 2 else 6 if ps < 5 else -12 if ps > 40 else -6 if ps > 20 else 0
        f_val  = max(5, min(98, f_val + ps_pts))
    detail["val_ps_pts"] = ps_pts

    mc_tvl = m.get("mc_tvl")
    mct_pts = 0
    if mc_tvl is not None:
        mct_pts = 10 if mc_tvl < 0.5 else 5 if mc_tvl < 1 else -8 if mc_tvl > 15 else -4 if mc_tvl > 7 else 0
        f_val   = max(5, min(98, f_val + mct_pts))
    detail["val_mc_tvl_pts"] = mct_pts

    strike     = m.get("dynamic_strike", 0) or 0
    strike_pts = 0
    vs_strike_pct = None
    if price > 0 and strike > 0:
        ratio         = price / strike
        vs_strike_pct = round((ratio - 1) * 100, 1)
        strike_pts    = 8 if ratio < 1.0 else 3 if ratio < 1.5 else -8 if ratio > 4 else -4 if ratio > 2.5 else 0
        f_val         = max(5, min(98, f_val + strike_pts))
    detail["val_vs_strike_pct"] = vs_strike_pct
    detail["val_strike_pts"]    = strike_pts

    # Rev/MC anomaly guard
    circ_mc    = m.get("circ_mc", 0) or 0
    rev_mc_ratio = (rev_ann / circ_mc) if circ_mc > 0 and rev_ann > 0 else 0
    anomaly_applied = False
    if rev_mc_ratio > 5:
        val_cap = max(35, round(50 - math.log10(rev_mc_ratio / 5) * 12))
        f_biz   = min(50, f_biz)
        f_val   = min(val_cap, f_val)
        anomaly_applied = True
    detail["val_rev_mc_anomaly"] = anomaly_applied

    f_val = max(5, min(98, f_val))

    # ── CAPITAL RISK (15%) ──────────────────────────────
    f_risk = 55.0
    bb_offset    = 6 if bb == "programmatic" else 2 if bb == "opportunistic" else 0
    net_dilution = max(0, inflation - bb_offset)
    dil_pts      = 15 if net_dilution < 2 else 8 if net_dilution < 5 else 0 if net_dilution < 10 else -10 if net_dilution < 20 else -20
    f_risk += dil_pts
    detail["risk_net_dilution"]  = r2(net_dilution)
    detail["risk_dilution_pts"]  = dil_pts

    em_unlock = m.get("emissions_unlock_30d_pct")
    em_pts = 0
    if em_unlock is not None:
        em_pts = 8 if em_unlock < 0.5 else -5 if em_unlock < 2 else -18 if em_unlock > 5 else -8
        f_risk += em_pts
    detail["risk_unlock_30d_pct"] = em_unlock
    detail["risk_unlock_pts"]     = em_pts

    vol_mc  = m.get("vol_mc_ratio")
    liq_pts = 0
    if vol_mc is not None:
        liq_pts = 12 if vol_mc > 0.15 else 6 if vol_mc > 0.05 else 0 if vol_mc > 0.01 else -12
        f_risk  += liq_pts
    detail["risk_vol_mc_pts"] = liq_pts

    age     = (2026 - asset.get("protocolAge", 2024)) if asset.get("protocolAge") else 0
    age_pts = 8 if age >= 5 else 4 if age >= 3 else 0 if age >= 2 else -8
    f_risk += age_pts
    detail["risk_age_pts"]    = age_pts
    detail["risk_protocol_age"] = age

    risk_risk_malus = sum(rf.get("riskMalus", 0) for rf in asset.get("riskFlags", []))
    f_risk += risk_risk_malus
    detail["risk_flags_malus"] = risk_risk_malus

    f_risk = max(5, min(98, f_risk))

    # ── COMPOSITE ────────────────────────────────────────
    total = round(max(5, min(98, f_biz * 0.50 + f_val * 0.35 + f_risk * 0.15)))

    return {
        "total":        total,
        "business":     round(f_biz),
        "valuation":    round(f_val),
        "capital_risk": round(f_risk),
        "detail":       detail,
    }

# ═══════════════════════════════════════════════════════
# FORWARD PERFORMANCE — calcul depuis l'historique
# ═══════════════════════════════════════════════════════

def calc_forward_perf(snapshots, token_id, current_price):
    """
    Looks back in existing snapshots to compute:
      perf_vs_7d_ago, perf_vs_30d_ago
    These represent the return FROM that past date TO today,
    allowing future correlation analysis (did a past signal predict this return?).
    """
    result = {}
    today_dt = datetime.date.fromisoformat(TODAY)

    for days, key in [(7, "perf_vs_7d_ago"), (30, "perf_vs_30d_ago")]:
        target_dt  = today_dt - datetime.timedelta(days=days)
        # Search within ±2 days for the closest available snapshot
        best_date, best_price = None, None
        for delta in range(3):
            for sign in [0, -1, 1]:
                candidate = (target_dt + datetime.timedelta(days=delta * sign)).isoformat()
                if candidate in snapshots and token_id in snapshots[candidate]:
                    p = snapshots[candidate][token_id].get("price")
                    if p and p > 0:
                        best_date  = candidate
                        best_price = p
                        break
            if best_date:
                break
        if best_price and current_price:
            pct = round((current_price - best_price) / best_price * 100, 2)
            result[key] = pct
            result[key.replace("perf_vs_", "price_") ] = round(best_price, 6)
        else:
            result[key] = None

    return result

# ═══════════════════════════════════════════════════════
# ICHIMOKU — tokens tracked (1D + 1W)
# ═══════════════════════════════════════════════════════

ICHIMOKU_TOKENS = [
    {"id": "BTC",  "binanceSymbol": "BTCUSDT",  "source": "binance"},
    {"id": "ETH",  "binanceSymbol": "ETHUSDT",  "source": "binance"},
    {"id": "SOL",  "binanceSymbol": "SOLUSDT",  "source": "binance"},
    {"id": "BNB",  "binanceSymbol": "BNBUSDT",  "source": "binance"},
    {"id": "HYPE", "binanceSymbol": "HYPEUSDT", "source": "binance"},
    # HYPE is available on Binance for klines (listed Jan 2025)
]

# Ichimoku parameters (matches dashboard)
ICH_TENKAN     = 20
ICH_KIJUN      = 60
ICH_SPAN_B     = 120
ICH_DISPLACE   = 30
ICH_RSI_PERIOD = 14

# TF scoring scales — exact replica of calcConfluence v5 in index.html
ICH_TF_SCALES = {
    "1d": {"cloud_pos": 1.2, "chikou": 1.2, "kijun": 1.1, "cloud_color": 1.0,
           "tk_cross": 0.9, "rsi": 1.1, "t1": 0.60, "t2": 0.40,
           "bull_thresh": 58, "bear_thresh": 40},
    "1w": {"cloud_pos": 1.5, "chikou": 1.4, "kijun": 1.3, "cloud_color": 1.2,
           "tk_cross": 0.8, "rsi": 1.2, "t1": 0.65, "t2": 0.35,
           "bull_thresh": 45, "bear_thresh": 42},
}

# ── Klines fetch ─────────────────────────────────────

def fetch_klines(symbol, interval, limit=200):
    """
    Fetch OHLCV from Binance.
    Returns list of dicts: {open, high, low, close, volume}
    interval: '1d' or '1w'
    """
    raw = safe_get(
        "https://api.binance.com/api/v3/klines",
        {"symbol": symbol, "interval": interval, "limit": limit}
    )
    if not raw:
        return []
    return [
        {
            "open":   float(c[1]),
            "high":   float(c[2]),
            "low":    float(c[3]),
            "close":  float(c[4]),
            "volume": float(c[5]),
        }
        for c in raw
    ]

# ── Ichimoku calculation ──────────────────────────────

def highest(candles, period, field="high"):
    vals = [c[field] for c in candles[-period:]]
    return max(vals) if vals else None

def lowest(candles, period, field="low"):
    vals = [c[field] for c in candles[-period:]]
    return min(vals) if vals else None

def calc_ichimoku(candles):
    """
    Calculate Ichimoku components from OHLCV candles.
    Returns dict with all components needed for scoring.
    """
    if len(candles) < ICH_SPAN_B + ICH_DISPLACE:
        return None

    price = candles[-1]["close"]

    # Tenkan-sen (conversion line)
    tenkan = (highest(candles, ICH_TENKAN) + lowest(candles, ICH_TENKAN, "low")) / 2

    # Kijun-sen (base line)
    kijun  = (highest(candles, ICH_KIJUN) + lowest(candles, ICH_KIJUN, "low")) / 2

    # Kijun slope (compare to kijun N candles ago)
    kijun_slope_ref = 5
    if len(candles) >= ICH_KIJUN + kijun_slope_ref:
        past_candles = candles[:-kijun_slope_ref]
        kijun_past = (highest(past_candles, ICH_KIJUN) + lowest(past_candles, ICH_KIJUN, "low")) / 2
        kijun_slope_pct = (kijun - kijun_past) / kijun_past * 100 if kijun_past else 0
    else:
        kijun_slope_pct = 0
    kijun_flat = abs(kijun_slope_pct) < 0.3

    # Senkou Span A (leading span A, displaced forward)
    span_a = (tenkan + kijun) / 2

    # Senkou Span B (leading span B, displaced forward)
    span_b_h = highest(candles, ICH_SPAN_B)
    span_b_l = lowest(candles, ICH_SPAN_B, "low")
    span_b   = (span_b_h + span_b_l) / 2

    cloud_top = max(span_a, span_b)
    cloud_bot = min(span_a, span_b)
    cloud_color = "green" if span_a >= span_b else "red"

    # Price vs cloud
    if price > cloud_top:
        price_vs_cloud = "above"
    elif price < cloud_bot:
        price_vs_cloud = "below"
    else:
        price_vs_cloud = "inside"

    # Chikou span — close displaced back ICH_DISPLACE bars
    chikou_val  = candles[-1]["close"]
    chikou_comp = candles[-1 - ICH_DISPLACE]["close"] if len(candles) > ICH_DISPLACE else None
    chikou_bull = (chikou_val > chikou_comp) if chikou_comp else None

    # TK cross
    tk_bullish = tenkan > kijun

    # Kijun deviation
    kijun_dev_pct = (price - kijun) / kijun * 100 if kijun else 0

    # Volume relative (last bar vs 20-bar avg)
    vol_vals   = [c["volume"] for c in candles[-21:-1]]
    vol_avg    = sum(vol_vals) / len(vol_vals) if vol_vals else 1
    vol_rel    = candles[-1]["volume"] / vol_avg if vol_avg else 1
    vol_high   = vol_rel > 1.5
    vol_low    = vol_rel < 0.7

    # RSI 14 (Wilder's smoothed)
    rsi_val = calc_rsi([c["close"] for c in candles], ICH_RSI_PERIOD)

    return {
        "price":          price,
        "tenkan":         tenkan,
        "kijun":          kijun,
        "kijun_flat":     kijun_flat,
        "kijun_dev_pct":  round(kijun_dev_pct, 2),
        "span_a":         span_a,
        "span_b":         span_b,
        "cloud_top":      cloud_top,
        "cloud_bot":      cloud_bot,
        "cloud_color":    cloud_color,
        "price_vs_cloud": price_vs_cloud,
        "chikou_val":     chikou_val,
        "chikou_comp":    chikou_comp,
        "chikou_bull":    chikou_bull,
        "tk_bullish":     tk_bullish,
        "vol_relative":   round(vol_rel, 2),
        "vol_high":       vol_high,
        "vol_low":        vol_low,
        "rsi":            rsi_val,
    }

def calc_rsi(closes, period=14):
    """Wilder's smoothed RSI."""
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains  = [max(d, 0) for d in deltas]
    losses = [abs(min(d, 0)) for d in deltas]
    # Initial averages
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    # Wilder smoothing
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs  = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 1)

# ── Ichimoku scoring (v5 — TF-differentiated) ────────

def calc_ich_score(ich, tf):
    """
    Replicates calcConfluence v5 from index.html.
    Returns dict: score, bias, signals summary, key components.
    """
    if not ich:
        return None

    sc  = ICH_TF_SCALES.get(tf, ICH_TF_SCALES["1d"])
    pvk = ich["price_vs_cloud"]

    # Signals list: (tier, bull, base_weight, tf_scale)
    signals_t1, signals_t2 = [], []

    # S1 — Price vs Cloud (T1)
    bull_pvk = True if pvk == "above" else (False if pvk == "below" else None)
    w_pvk    = (0.5 if pvk == "inside" else 1.5) * sc["cloud_pos"]
    signals_t1.append((bull_pvk, w_pvk))

    # S2 — Chikou (T1)
    if ich["chikou_bull"] is not None:
        w_chi = 1.5 * sc["chikou"] if ich["chikou_bull"] else 1.0 * sc["chikou"]
        signals_t1.append((ich["chikou_bull"], w_chi))

    # S3 — Kijun (T2)
    kijun_bull = ich["price"] > ich["kijun"]
    w_kijun    = (1.3 if ich["kijun_flat"] else 1.0) * sc["kijun"]
    signals_t2.append((kijun_bull, w_kijun))

    # S4 — Cloud color (T2)
    cloud_bull = ich["cloud_color"] == "green"
    signals_t2.append((cloud_bull, 1.0 * sc["cloud_color"]))

    # S5 — TK Cross (T2) — alignment-based
    tk_aligned = (ich["tk_bullish"] and pvk == "above") or (not ich["tk_bullish"] and pvk == "below")
    tk_contra  = (ich["tk_bullish"] and pvk == "below") or (not ich["tk_bullish"] and pvk == "above")
    w_tk       = (1.3 if tk_aligned else 0.4 if pvk == "inside" else 0.5 if tk_contra else 1.0) * sc["tk_cross"]
    signals_t2.append((ich["tk_bullish"], w_tk))

    # S6 — RSI (T2)
    rsi = ich["rsi"]
    if rsi is not None:
        rsi_bull = None
        w_rsi    = 0.5
        if rsi < 30:   rsi_bull, w_rsi = True,  1.3
        elif rsi < 35: rsi_bull, w_rsi = True,  0.8
        elif rsi > 70: rsi_bull, w_rsi = False, 1.3
        elif rsi > 65: rsi_bull, w_rsi = False, 0.8
        w_rsi *= sc["rsi"]
        signals_t2.append((rsi_bull, w_rsi))

    # Score T1
    t1_bull, t1_total = 0.0, 0.0
    for bull, w in signals_t1:
        t1_total += w
        if bull is True:   t1_bull += w
        elif bull is None: t1_bull += w * 0.5

    # Score T2
    t2_bull, t2_total = 0.0, 0.0
    for bull, w in signals_t2:
        t2_total += w
        if bull is True:   t2_bull += w
        elif bull is None: t2_bull += w * 0.5

    t1_score = (t1_bull / t1_total) if t1_total else 0.5
    t2_score = (t2_bull / t2_total) if t2_total else 0.5
    raw      = (t1_score * sc["t1"] + t2_score * sc["t2"]) * 100

    # Volume modifier ±12%
    if ich["vol_high"]: raw = min(100, raw * 1.12) if raw > 50 else max(0, raw * 0.88)
    if ich["vol_low"]:  raw = max(50,  raw * 0.88) if raw > 50 else min(50, raw * 1.12)

    score = round(max(2, min(98, raw)))
    bias  = "BULLISH" if score >= sc["bull_thresh"] else "BEARISH" if score <= sc["bear_thresh"] else "NEUTRAL"

    return {
        "score":          score,
        "bias":           bias,
        "price_vs_cloud": ich["price_vs_cloud"],
        "cloud_color":    ich["cloud_color"],
        "tk_bullish":     ich["tk_bullish"],
        "chikou_bull":    ich["chikou_bull"],
        "kijun_flat":     ich["kijun_flat"],
        "kijun_dev_pct":  ich["kijun_dev_pct"],
        "rsi":            ich["rsi"],
        "vol_relative":   ich["vol_relative"],
        "tenkan":         round(ich["tenkan"], 4),
        "kijun":          round(ich["kijun"], 4),
        "cloud_top":      round(ich["cloud_top"], 4),
        "cloud_bot":      round(ich["cloud_bot"], 4),
    }

def fetch_ichimoku_snapshot(token):
    """
    Fetch 1D and 1W Ichimoku for a token.
    Returns dict with ich_1d_* and ich_1w_* fields.
    """
    symbol = token["binanceSymbol"]
    result = {}

    for tf, interval, limit in [("1d", "1d", 200), ("1w", "1w", 200)]:
        print(f"    Ichimoku {tf}…", end=" ")
        candles = fetch_klines(symbol, interval, limit)
        time.sleep(0.3)
        if not candles:
            print("no data")
            continue
        ich   = calc_ichimoku(candles)
        score = calc_ich_score(ich, tf)
        if not score:
            print("calc failed")
            continue
        print(f"score={score['score']} {score['bias']}")
        for k, v in score.items():
            result[f"ich_{tf}_{k}"] = v

    # Weighted confluence 1D (40%) + 1W (60%)
    s1d = result.get("ich_1d_score")
    s1w = result.get("ich_1w_score")
    if s1d is not None and s1w is not None:
        result["ich_confluence"] = round(s1d * 0.40 + s1w * 0.60)
    elif s1d is not None:
        result["ich_confluence"] = s1d
    elif s1w is not None:
        result["ich_confluence"] = s1w

    return result

# ═══════════════════════════════════════════════════════
# GITHUB
# ═══════════════════════════════════════════════════════

GH_API     = "https://api.github.com"
GH_HEADERS = {
    "Authorization":        f"Bearer {GITHUB_TOKEN}",
    "Accept":               "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

def github_read(path):
    url = f"{GH_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}"
    r   = requests.get(url, headers=GH_HEADERS, timeout=10)
    if r.status_code == 404:
        return {}, None
    if r.status_code != 200:
        print(f"  GitHub read error {r.status_code}")
        return {}, None
    data    = r.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return json.loads(content), data["sha"]

def github_write(path, content_dict, sha, message):
    url  = f"{GH_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}"
    body = {
        "message": message,
        "content": base64.b64encode(
            json.dumps(content_dict, indent=2, ensure_ascii=False).encode()
        ).decode(),
    }
    if sha:
        body["sha"] = sha
    r = requests.put(url, headers=GH_HEADERS, json=body, timeout=15)
    if r.status_code in (200, 201):
        print(f"  ✅ Committed: {message}")
        return True
    print(f"  ❌ GitHub write error {r.status_code}: {r.text[:200]}")
    return False

# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════

def run():
    print(f"\n{'═'*58}")
    print(f"  ARCA Snapshot v2 — {TODAY}")
    print(f"{'═'*58}")

    # 1. Load existing snapshots
    print("\n[1/4] Reading snapshots.json from GitHub…")
    snapshots, sha = github_read(SNAPSHOTS_FILE)
    print(f"  {len(snapshots)} existing dates found.")

    if TODAY in snapshots:
        print(f"  ⚠️  {TODAY} already exists — skipping.")
        return

    # 2. Market context (BTC, Fear & Greed, total MC)
    print("\n[2/4] Fetching market context…")
    meta = fetch_market_context()
    meta["snapshot_utc"] = datetime.datetime.utcnow().isoformat() + "Z"
    print(f"  BTC=${meta.get('btc_price','?')}  "
          f"Dom={meta.get('btc_dominance','?')}%  "
          f"F&G={meta.get('fear_greed','?')} {meta.get('fear_greed_label','')}")

    # 3. CoinGecko bulk price (rate-limit friendly)
    print("\n[3/5] Fetching token data…")
    cg_ids    = ",".join(a["coingeckoId"] for a in ARCA_ASSETS)
    cg_bulk   = safe_get(
        "https://api.coingecko.com/api/v3/simple/price",
        {"ids": cg_ids, "vs_currencies": "usd",
         "include_market_cap": "true", "include_24hr_vol": "true"}
    ) or {}

    today_snap = {}

    for asset in ARCA_ASSETS:
        aid = asset["id"]
        print(f"\n  ── {aid} ({asset['sector']})")

        # Price + volume
        if asset["source"] == "hyperliquid":
            ticker = fetch_hyperliquid_ticker("HYPE")
        else:
            ticker = fetch_binance_ticker(asset["binanceSymbol"])

        if not ticker or not ticker.get("price"):
            print(f"    ⚠ No price — skipping")
            continue

        price    = ticker["price"]
        change   = ticker["change_24h"]
        vol_24h  = ticker["vol_24h_usd"]
        high_24h = ticker.get("high_24h")
        low_24h  = ticker.get("low_24h")

        # CoinGecko MC
        cg = cg_bulk.get(asset["coingeckoId"], {})
        circ_mc = float(cg.get("usd_market_cap", 0) or 0)
        time.sleep(0.2)

        # DefiLlama fees
        fees = fetch_defillama_fees(asset.get("defillamaSlug", ""))
        time.sleep(0.3)

        # DefiLlama TVL
        tvl = fetch_defillama_tvl(asset.get("defillamaSlug", ""))
        time.sleep(0.3)

        # Compute metrics
        use_fees   = asset.get("useFeesAsRevenue", False)
        fees_30d   = fees.get("fees_30d", 0) or 0
        rev_30d    = fees.get("rev_30d",  0) or 0
        fees_24h   = fees.get("fees_24h", 0) or 0
        rev_24h_v  = fees.get("rev_24h",  0) or 0

        rev_ann_30d = (fees_30d * 12) if use_fees else (rev_30d * 12 if rev_30d else fees_30d * 12 * 0.3)
        rev_24h_val = fees_24h if use_fees else rev_24h_v

        circ_supply = asset.get("staticCircSupply", 0)
        pe          = round(circ_mc / rev_ann_30d, 2)   if rev_ann_30d > 0 and circ_mc > 0 else None
        ps          = round(circ_mc / rev_ann_30d, 2)   if rev_ann_30d > 0 and circ_mc > 0 else None
        mc_tvl      = round(circ_mc / tvl, 3)            if tvl > 0 and circ_mc > 0 else None
        vol_mc      = round(vol_24h / circ_mc, 4)        if circ_mc > 0 and vol_24h > 0 else None
        dyn_strike  = (rev_ann_30d / circ_supply * 10)   if circ_supply > 0 and rev_ann_30d > 0 else 0
        data_comp   = sum(1 for x in [price, circ_mc, rev_ann_30d, tvl] if x) / 4

        m = {
            "rev_ann_30d":             rev_ann_30d,
            "rev_24h":                 rev_24h_val,
            "tvl":                     tvl,
            "real_yield_net":          asset.get("realYield", 0) - asset.get("inflation", 0),
            "pe":                      pe,
            "ps":                      ps,
            "mc_tvl":                  mc_tvl,
            "circ_mc":                 circ_mc,
            "vol_mc_ratio":            vol_mc,
            "dynamic_strike":          dyn_strike,
            "emissions_unlock_30d_pct": None,
            "data_completeness":       data_comp,
        }

        # Score
        conv   = calc_conviction_full(price, asset, m)
        signal = get_signal(conv["total"])

        # Forward performance from past snapshots
        fwd = calc_forward_perf(snapshots, aid, price)

        # 7-day volume average (from past snapshots)
        vol_7d_avg = None
        vols = []
        td = datetime.date.fromisoformat(TODAY)
        for d in range(1, 8):
            dk = (td - datetime.timedelta(days=d)).isoformat()
            if dk in snapshots and aid in snapshots[dk]:
                v = snapshots[dk][aid].get("vol_24h_usd")
                if v:
                    vols.append(v)
        if vols:
            vol_7d_avg = ri(sum(vols) / len(vols))

        # ── Build token snapshot ──────────────────────
        token_snap = {
            # Core
            "price":        round(price, 6),
            "change_24h":   r2(change),
            "high_24h":     r2(high_24h),
            "low_24h":      r2(low_24h),
            "vol_24h_usd":  ri(vol_24h),
            "vol_7d_avg":   vol_7d_avg,
            "sector":       asset["sector"],

            # Signal
            "score":        conv["total"],
            "signal":       signal,

            # Pillar scores
            "business":     conv["business"],
            "valuation":    conv["valuation"],
            "capital_risk": conv["capital_risk"],

            # Business sub-scores
            "biz_rev_pts":           conv["detail"].get("biz_rev_pts"),
            "biz_rev_momentum_pct":  conv["detail"].get("biz_rev_momentum_pct"),
            "biz_rev_momentum_pts":  conv["detail"].get("biz_rev_momentum_pts"),
            "biz_tvl_pts":           conv["detail"].get("biz_tvl_pts"),
            "biz_real_yield_net":    conv["detail"].get("biz_real_yield_net"),
            "biz_real_yield_pts":    conv["detail"].get("biz_real_yield_pts"),
            "biz_buyback_pts":       conv["detail"].get("biz_buyback_pts"),
            "biz_risk_malus":        conv["detail"].get("biz_risk_malus"),

            # Valuation sub-scores
            "val_pe":            r2(pe),
            "val_pe_base":       conv["detail"].get("val_pe_base"),
            "val_ps":            r2(ps),
            "val_ps_pts":        conv["detail"].get("val_ps_pts"),
            "val_mc_tvl":        r4(mc_tvl),
            "val_mc_tvl_pts":    conv["detail"].get("val_mc_tvl_pts"),
            "val_vs_strike_pct": conv["detail"].get("val_vs_strike_pct"),
            "val_strike_pts":    conv["detail"].get("val_strike_pts"),
            "val_dyn_strike":    r2(dyn_strike),
            "val_anomaly":       conv["detail"].get("val_rev_mc_anomaly"),

            # Capital Risk sub-scores
            "risk_net_dilution":  conv["detail"].get("risk_net_dilution"),
            "risk_dilution_pts":  conv["detail"].get("risk_dilution_pts"),
            "risk_vol_mc":        r4(vol_mc),
            "risk_vol_mc_pts":    conv["detail"].get("risk_vol_mc_pts"),
            "risk_age_pts":       conv["detail"].get("risk_age_pts"),
            "risk_flags_malus":   conv["detail"].get("risk_flags_malus"),

            # Fundamentals raw
            "mc":           ri(circ_mc),
            "tvl":          ri(tvl),
            "rev_ann_30d":  ri(rev_ann_30d),
            "rev_daily":    ri(rev_ann_30d / 365) if rev_ann_30d else None,
            "fees_24h":     ri(fees_24h),
            "fees_30d":     ri(fees_30d),
            "data_completeness": r2(data_comp),

            # Forward performance (from past snapshots)
            **fwd,

            "ts": datetime.datetime.utcnow().isoformat() + "Z",
        }

        today_snap[aid] = token_snap
        print(f"    price=${price:.4f}  score={conv['total']}  "
              f"[B:{conv['business']} V:{conv['valuation']} R:{conv['capital_risk']}]  "
              f"signal={signal}")

    if not today_snap:
        print("\n⚠️  No data — aborting.")
        return

    # 4. Ichimoku snapshots (BTC, ETH, SOL, BNB, HYPE)
    print(f"\n[4/5] Fetching Ichimoku (1D + 1W)…")
    ich_snap = {}
    for token in ICHIMOKU_TOKENS:
        tid = token["id"]
        print(f"\n  ── {tid}")
        ich_data = fetch_ichimoku_snapshot(token)
        ich_snap[tid] = ich_data

        # Also attach to ARCA snapshot if token exists there
        if tid in today_snap and ich_data:
            today_snap[tid].update(ich_data)

    # 5. Push to GitHub
    print(f"\n[5/5] Pushing to GitHub…")
    snapshots[TODAY] = {
        "meta":     meta,
        "ichimoku": ich_snap,   # dedicated block for pure Ichimoku tokens
        **today_snap,
    }
    msg = f"snapshot: {TODAY} — {len(today_snap)} tokens + ichimoku"
    github_write(SNAPSHOTS_FILE, snapshots, sha, msg)

    print(f"\n{'═'*58}")
    print(f"  Done — {len(today_snap)} ARCA tokens · {len(ich_snap)} Ichimoku tokens")
    n_fields = len(list(today_snap.values())[0]) if today_snap else 0
    print(f"  Fields per ARCA token: {n_fields}")
    print(f"{'═'*58}\n")

if __name__ == "__main__":
    run()
