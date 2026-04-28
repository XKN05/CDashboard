#!/usr/bin/env python3
"""
ARCA Daily Snapshot — CDashboard
Repo : https://github.com/XKN05/CDashboard
Run  : python arca_snapshot.py  (via Cowork scheduler, once/day)

Ce script :
  1. Fetch le prix + change 24h depuis Binance (ou Hyperliquid pour HYPE)
  2. Fetch TVL + fees/revenue depuis DefiLlama
  3. Fetch market cap depuis CoinGecko
  4. Recalcule le score ARCA (Business 50% / Valuation 35% / Capital Risk 15%)
  5. Enregistre le snapshot dans snapshots.json
  6. Commit + push sur GitHub

Configuration : édite la section CONFIG ci-dessous.
"""

import json
import math
import os
import time
import base64
import datetime
import requests

# ═══════════════════════════════════════════════════════
# CONFIG — édite ces valeurs
# ═══════════════════════════════════════════════════════
GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN", "COLLE_TON_TOKEN_ICI")
GITHUB_OWNER  = "XKN05"
GITHUB_REPO   = "CDashboard"
SNAPSHOTS_FILE = "snapshots.json"   # chemin dans le repo
# ═══════════════════════════════════════════════════════

TODAY = datetime.date.today().isoformat()   # "2025-04-28"

# ── Tokens ARCA — synchronisés avec index.html ────────────────
ARCA_ASSETS = [
    {
        "id": "HYPE", "source": "hyperliquid", "binanceSymbol": "HYPEUSDT",
        "defillamaSlug": "hyperliquid", "coingeckoId": "hyperliquid",
        "buybackLevel": "programmatic", "protocolAge": 2023,
        "inflation": 2.0, "realYield": 10.0,
        "staticCircSupply": 333.33e6, "staticTotalSupply": 1000e6,
    },
    {
        "id": "JUP", "source": "binance", "binanceSymbol": "JUPUSDT",
        "defillamaSlug": "jupiter", "coingeckoId": "jupiter-exchange-solana",
        "buybackLevel": "programmatic", "protocolAge": 2022,
        "inflation": 4.0, "realYield": 3.0,
        "staticCircSupply": 1.7e9, "staticTotalSupply": 10e9,
    },
    {
        "id": "UNI", "source": "binance", "binanceSymbol": "UNIUSDT",
        "defillamaSlug": "uniswap", "coingeckoId": "uniswap",
        "buybackLevel": "programmatic", "protocolAge": 2020,
        "inflation": 2.0, "realYield": 0.0,
        "staticCircSupply": 600e6, "staticTotalSupply": 1000e6,
    },
    {
        "id": "AAVE", "source": "binance", "binanceSymbol": "AAVEUSDT",
        "defillamaSlug": "aave", "coingeckoId": "aave",
        "buybackLevel": "programmatic", "protocolAge": 2020,
        "inflation": 0.5, "realYield": 4.0,
        "staticCircSupply": 15e6, "staticTotalSupply": 16e6,
    },
    {
        "id": "PUMP", "source": "binance", "binanceSymbol": "PUMPUSDT",
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
        "id": "ONDO", "source": "binance", "binanceSymbol": "ONDOUSDT",
        "defillamaSlug": "ondo-finance", "coingeckoId": "ondo-finance",
        "buybackLevel": "none", "protocolAge": 2023,
        "inflation": 18.0, "realYield": 1.0,
        "staticCircSupply": 3.2e9, "staticTotalSupply": 10e9,
        "useFeesAsRevenue": True,
    },
    {
        "id": "MET", "source": "binance", "binanceSymbol": "METUSDT",
        "defillamaSlug": "meteora", "coingeckoId": "meteora",
        "buybackLevel": "programmatic", "protocolAge": 2023,
        "inflation": 3.0, "realYield": 8.0,
        "staticCircSupply": 510e6, "staticTotalSupply": 1000e6,
    },
    {
        "id": "ASTER", "source": "binance", "binanceSymbol": "ASTERUSDT",
        "defillamaSlug": "aster", "coingeckoId": "aster-2",
        "buybackLevel": "programmatic", "protocolAge": 2025,
        "inflation": 8.0, "realYield": 12.0,
        "staticCircSupply": 2.5e9, "staticTotalSupply": 8e9,
    },
    {
        "id": "SYRUP", "source": "binance", "binanceSymbol": "SYRUPUSDT",
        "defillamaSlug": "maple", "coingeckoId": "maple-finance",
        "buybackLevel": "programmatic", "protocolAge": 2021,
        "inflation": 1.0, "realYield": 3.0,
        "staticCircSupply": 1.2e9, "staticTotalSupply": 1.22e9,
    },
    {
        "id": "AERO", "source": "binance", "binanceSymbol": "AEROUSDT",
        "defillamaSlug": "aerodrome", "coingeckoId": "aerodrome-finance",
        "buybackLevel": "programmatic", "protocolAge": 2023,
        "inflation": 25.0, "realYield": 14.0,
        "staticCircSupply": 920e6, "staticTotalSupply": 1.86e9,
    },
    {
        "id": "PENDLE", "source": "binance", "binanceSymbol": "PENDLEUSDT",
        "defillamaSlug": "pendle", "coingeckoId": "pendle",
        "buybackLevel": "programmatic", "protocolAge": 2021,
        "inflation": 3.0, "realYield": 12.0,
        "staticCircSupply": 258e6, "staticTotalSupply": 281e6,
    },
    {
        "id": "ENA", "source": "binance", "binanceSymbol": "ENAUSDT",
        "defillamaSlug": "ethena", "coingeckoId": "ethena",
        "buybackLevel": "programmatic", "protocolAge": 2024,
        "inflation": 25.0, "realYield": 0.0,
        "staticCircSupply": 8.5e9, "staticTotalSupply": 15e9,
    },
    {
        "id": "RAY", "source": "binance", "binanceSymbol": "RAYUSDT",
        "defillamaSlug": "raydium", "coingeckoId": "raydium",
        "buybackLevel": "programmatic", "protocolAge": 2021,
        "inflation": 5.0, "realYield": 12.0,
        "staticCircSupply": 270e6, "staticTotalSupply": 555e6,
    },
    {
        "id": "MORPHO", "source": "binance", "binanceSymbol": "MORPHOUSDT",
        "defillamaSlug": "morpho", "coingeckoId": "morpho",
        "buybackLevel": "none", "protocolAge": 2022,
        "inflation": 6.0, "realYield": 5.0,
        "staticCircSupply": 550e6, "staticTotalSupply": 1000e6,
        "useFeesAsRevenue": True,
    },
]

# ═══════════════════════════════════════════════════════
# DATA FETCHERS
# ═══════════════════════════════════════════════════════

def safe_get(url, params=None, timeout=10):
    """GET with retry on failure."""
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print(f"  [retry {attempt+1}] {url} — {e}")
            time.sleep(2)
    return None

def safe_post(url, payload, timeout=10):
    for attempt in range(3):
        try:
            r = requests.post(url, json=payload, timeout=timeout)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print(f"  [retry {attempt+1}] POST {url} — {e}")
            time.sleep(2)
    return None

def fetch_binance_price(symbol):
    """Returns (price, change_24h_pct) or (None, None)."""
    data = safe_get("https://api.binance.com/api/v3/ticker/24hr", {"symbol": symbol})
    if not data:
        return None, None
    return float(data.get("lastPrice", 0) or 0), float(data.get("priceChangePercent", 0) or 0)

def fetch_hyperliquid_price(symbol="HYPE"):
    """Returns (price, change_24h_pct) or (None, None)."""
    data = safe_post(
        "https://api.hyperliquid.xyz/info",
        {"type": "metaAndAssetCtxs"}
    )
    if not data or not isinstance(data, list) or len(data) < 2:
        return None, None
    universe = data[0].get("universe", [])
    ctxs     = data[1]
    for i, asset in enumerate(universe):
        if asset.get("name") == symbol and i < len(ctxs):
            ctx   = ctxs[i]
            price = float(ctx.get("markPx", 0) or 0)
            prev  = float(ctx.get("prevDayPx", 0) or 0)
            chg   = ((price - prev) / prev * 100) if prev > 0 else 0
            return price, chg
    return None, None

def fetch_binance_volume(symbol):
    """Returns 24h quote volume in USD."""
    data = safe_get("https://api.binance.com/api/v3/ticker/24hr", {"symbol": symbol})
    if not data:
        return 0
    return float(data.get("quoteVolume", 0) or 0)

def fetch_defillama_fees(slug):
    """Returns (fees_24h, fees_7d, fees_30d, revenue_24h, revenue_30d)."""
    data = safe_get(f"https://api.llama.fi/summary/fees/{slug}")
    if not data:
        return 0, 0, 0, 0, 0
    total   = data.get("total24h", 0) or 0
    total7d = (data.get("total7d", 0) or 0)
    total30 = data.get("total30d", 0) or 0
    rev24   = data.get("revenue24h", 0) or data.get("totalRevenue24h", 0) or 0
    rev30   = data.get("revenue30d", 0) or data.get("totalRevenue30d", 0) or 0
    # Annualise from 30d if available
    return float(total), float(total7d), float(total30), float(rev24), float(rev30)

def fetch_defillama_tvl(slug):
    """Returns current TVL in USD."""
    data = safe_get(f"https://api.llama.fi/tvl/{slug}")
    if data is None:
        return 0
    try:
        return float(data)
    except (TypeError, ValueError):
        return 0

def fetch_coingecko_mc(cg_id):
    """Returns (market_cap, circ_supply, total_supply, fdv)."""
    data = safe_get(
        f"https://api.coingecko.com/api/v3/coins/{cg_id}",
        {"localization": "false", "tickers": "false",
         "market_data": "true", "community_data": "false",
         "developer_data": "false"}
    )
    if not data:
        return 0, 0, 0, 0
    md = data.get("market_data", {})
    mc    = md.get("market_cap",          {}).get("usd", 0) or 0
    circ  = md.get("circulating_supply",  0) or 0
    total = md.get("total_supply",        0) or 0
    fdv   = md.get("fully_diluted_valuation", {}).get("usd", 0) or 0
    return float(mc), float(circ), float(total), float(fdv)

# ═══════════════════════════════════════════════════════
# SCORING — réplique exacte de getConvictionScore() JS
# ═══════════════════════════════════════════════════════

def log_score(v, floor, mult, cap):
    if not v or v < floor:
        return 0
    return min(cap, mult * math.log10(v / floor))

def get_signal_label(score):
    if score >= 80: return "STRONG BUY"
    if score >= 65: return "BUY"
    if score >= 50: return "MODERATE"
    if score >= 35: return "RISKY"
    return "AVOID"

def calc_conviction(price, asset, m):
    """
    m = dict with live metrics:
      rev_ann_30d, rev_24h, tvl, real_yield_net,
      pe, ps, mc_tvl, circ_mc, vol_mc_ratio,
      emissions_unlock_30d_pct, data_completeness
    """
    if m.get("data_completeness", 1) < 0.4:
        return {"total": 10, "business": 0, "valuation": 0, "capital_risk": 0}

    inflation_pct = asset.get("inflation", 0)

    # ── PILLAR 1 — BUSINESS QUALITY (50%) ──────────────────
    f_biz = 30.0
    rev_24h       = m.get("rev_24h", 0) or 0
    rev_ann_30d   = m.get("rev_ann_30d", 0) or 0
    rev30d_daily  = rev_ann_30d / 365 if rev_ann_30d else 0
    daily_rev     = rev_24h if rev_24h > 0 else rev30d_daily

    if rev_ann_30d <= 0:
        f_biz -= 15
    else:
        rev_pts = round(log_score(daily_rev, 50000, 28, 55))
        f_biz  += rev_pts

    # Revenue momentum
    if rev30d_daily > 0 and rev_24h > 0:
        mom = (rev_24h - rev30d_daily) / rev30d_daily
        mom_pts = 10 if mom > 0.3 else 5 if mom > 0.1 else -10 if mom < -0.3 else -5 if mom < -0.1 else 0
        f_biz += mom_pts

    # TVL
    tvl = m.get("tvl", 0) or 0
    tvl_pts = 12 if tvl > 10e9 else 8 if tvl > 3e9 else 4 if tvl > 500e6 else 1 if tvl > 100e6 else -3 if tvl <= 0 else 0
    f_biz += tvl_pts

    # Real yield
    ry = m.get("real_yield_net", 0) or 0
    ry_pts = 10 if ry > 10 else 6 if ry > 5 else 2 if ry > 0 else -10 if ry < -10 else -5 if ry < -5 else -2 if ry < 0 else 0
    f_biz += ry_pts

    # Buyback
    bb = asset.get("buybackLevel", "none")
    bb_pts = 12 if bb == "programmatic" else 4 if bb == "opportunistic" else -12
    f_biz += bb_pts

    # Risk flags bizMalus
    for rf in asset.get("riskFlags", []):
        f_biz += rf.get("bizMalus", 0)

    f_biz = max(5, min(98, f_biz))

    # ── PILLAR 2 — VALUATION (35%) ──────────────────────────
    f_val = 50.0
    pe = m.get("pe")
    if pe is not None:
        pe_pts = 95 if pe < 5 else 82 if pe < 10 else 65 if pe < 18 else 45 if pe < 30 else 25 if pe < 50 else 12 if pe < 80 else 5
        f_val  = float(pe_pts)
    else:
        f_val = 50.0

    # P/S
    ps = m.get("ps")
    if ps is not None:
        ps_pts = 12 if ps < 2 else 6 if ps < 5 else -12 if ps > 40 else -6 if ps > 20 else 0
        f_val  = max(5, min(98, f_val + ps_pts))

    # MC/TVL
    mc_tvl = m.get("mc_tvl")
    if mc_tvl is not None:
        mct_pts = 10 if mc_tvl < 0.5 else 5 if mc_tvl < 1 else -8 if mc_tvl > 15 else -4 if mc_tvl > 7 else 0
        f_val   = max(5, min(98, f_val + mct_pts))

    # Price vs Strike (dynamic strike = annualRev/circSupply * 10)
    strike = m.get("dynamic_strike", 0) or 0
    if price > 0 and strike > 0:
        ratio      = price / strike
        strike_pts = 8 if ratio < 1.0 else 3 if ratio < 1.5 else -8 if ratio > 4 else -4 if ratio > 2.5 else 0
        f_val      = max(5, min(98, f_val + strike_pts))

    # Rev/MC anomaly guard
    circ_mc    = m.get("circ_mc", 0) or 0
    rev_mc_ratio = (rev_ann_30d / circ_mc) if circ_mc > 0 and rev_ann_30d > 0 else 0
    if rev_mc_ratio > 5:
        val_cap = max(35, round(50 - math.log10(rev_mc_ratio / 5) * 12))
        f_biz   = min(50, f_biz)
        f_val   = min(val_cap, f_val)

    f_val = max(5, min(98, f_val))

    # ── PILLAR 3 — CAPITAL RISK (15%) ───────────────────────
    f_risk = 55.0

    # Net dilution
    bb_offset   = 6 if bb == "programmatic" else 2 if bb == "opportunistic" else 0
    net_dilution = max(0, inflation_pct - bb_offset)
    dil_pts = 15 if net_dilution < 2 else 8 if net_dilution < 5 else 0 if net_dilution < 10 else -10 if net_dilution < 20 else -20
    f_risk += dil_pts

    # Unlocks
    em_unlock = m.get("emissions_unlock_30d_pct")
    if em_unlock is not None:
        em_pts = 8 if em_unlock < 0.5 else -5 if em_unlock < 2 else -18 if em_unlock > 5 else -8
        f_risk += em_pts

    # Liquidity Vol/MC
    vol_mc = m.get("vol_mc_ratio")
    if vol_mc is not None:
        liq_pts = 12 if vol_mc > 0.15 else 6 if vol_mc > 0.05 else 0 if vol_mc > 0.01 else -12
        f_risk  += liq_pts

    # Protocol age
    age     = (2026 - asset.get("protocolAge", 2024)) if asset.get("protocolAge") else 0
    age_pts = 8 if age >= 5 else 4 if age >= 3 else 0 if age >= 2 else -8
    f_risk  += age_pts

    # Risk flags riskMalus
    for rf in asset.get("riskFlags", []):
        f_risk += rf.get("riskMalus", 0)

    f_risk = max(5, min(98, f_risk))

    # ── COMPOSITE ───────────────────────────────────────────
    total = round(max(5, min(98, f_biz * 0.50 + f_val * 0.35 + f_risk * 0.15)))
    return {
        "total":        total,
        "business":     round(f_biz),
        "valuation":    round(f_val),
        "capital_risk": round(f_risk),
    }

# ═══════════════════════════════════════════════════════
# GITHUB — lecture / écriture de snapshots.json
# ═══════════════════════════════════════════════════════

GH_API = "https://api.github.com"
GH_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

def github_read_file(path):
    """Returns (content_dict, sha) or ({}, None)."""
    url = f"{GH_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}"
    r = requests.get(url, headers=GH_HEADERS, timeout=10)
    if r.status_code == 404:
        return {}, None
    if r.status_code != 200:
        print(f"  GitHub read error {r.status_code}: {r.text[:200]}")
        return {}, None
    data = r.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return json.loads(content), data["sha"]

def github_write_file(path, content_dict, sha, commit_msg):
    """Write JSON to GitHub repo. sha=None for new file."""
    url  = f"{GH_API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}"
    body = {
        "message": commit_msg,
        "content": base64.b64encode(
            json.dumps(content_dict, indent=2, ensure_ascii=False).encode("utf-8")
        ).decode("utf-8"),
    }
    if sha:
        body["sha"] = sha
    r = requests.put(url, headers=GH_HEADERS, json=body, timeout=15)
    if r.status_code in (200, 201):
        print(f"  ✅ GitHub: {path} updated ({commit_msg})")
        return True
    print(f"  ❌ GitHub write error {r.status_code}: {r.text[:300]}")
    return False

# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════

def run():
    print(f"\n{'='*55}")
    print(f"  ARCA Snapshot — {TODAY}")
    print(f"{'='*55}")

    # 1. Charger l'historique existant depuis GitHub
    print("\n[1/3] Reading snapshots.json from GitHub…")
    snapshots, sha = github_read_file(SNAPSHOTS_FILE)

    if TODAY in snapshots:
        print(f"  ⚠️  Snapshot for {TODAY} already exists — skipping.")
        return

    # 2. Fetch données pour chaque token
    print("\n[2/3] Fetching live data…")
    today_snapshot = {}

    # CoinGecko — 1 requête groupée pour les MC (rate-limit friendly)
    cg_ids = ",".join(a["coingeckoId"] for a in ARCA_ASSETS)
    cg_data_raw = safe_get(
        "https://api.coingecko.com/api/v3/simple/price",
        {"ids": cg_ids, "vs_currencies": "usd",
         "include_market_cap": "true",
         "include_24hr_vol": "true",
         "include_24hr_change": "true"}
    ) or {}

    for asset in ARCA_ASSETS:
        aid = asset["id"]
        print(f"\n  → {aid}")

        # Prix
        if asset["source"] == "hyperliquid":
            price, chg24 = fetch_hyperliquid_price("HYPE")
        else:
            price, chg24 = fetch_binance_price(asset["binanceSymbol"])

        if not price:
            print(f"    ⚠️  No price — skipping {aid}")
            continue

        # Volume 24h (pour vol/mc ratio)
        vol24 = fetch_binance_volume(asset["binanceSymbol"]) if asset["source"] == "binance" else 0

        # CoinGecko MC
        cg = cg_data_raw.get(asset["coingeckoId"], {})
        circ_mc = cg.get(f"usd_market_cap", 0) or 0

        # DefiLlama fees/revenue
        fees24, fees7d, fees30d, rev24, rev30 = fetch_defillama_fees(asset.get("defillamaSlug", ""))
        time.sleep(0.3)  # éviter rate-limit DefiLlama

        # DefiLlama TVL
        tvl = fetch_defillama_tvl(asset.get("defillamaSlug", ""))
        time.sleep(0.3)

        # Calcul métriques
        use_fees_as_rev  = asset.get("useFeesAsRevenue", False)
        rev_ann_30d = (fees30d * 12) if (use_fees_as_rev and fees30d) else (rev30 * 12 if rev30 else fees30d * 12 * 0.3)
        rev_24h_val      = fees24 if use_fees_as_rev else rev24

        circ_supply = asset.get("staticCircSupply", 0)
        annual_rev  = rev_ann_30d or 0

        pe        = round(circ_mc / annual_rev, 2) if annual_rev > 0 and circ_mc > 0 else None
        ps        = round(circ_mc / annual_rev, 2) if annual_rev > 0 and circ_mc > 0 else None  # proxy P/S
        mc_tvl    = round(circ_mc / tvl, 3)        if tvl > 0 and circ_mc > 0 else None
        vol_mc    = round(vol24 / circ_mc, 4)      if circ_mc > 0 and vol24 > 0 else None

        # Dynamic strike = annual_rev / circ_supply * 10 (P/E = 10×)
        dyn_strike = (annual_rev / circ_supply * 10) if circ_supply > 0 and annual_rev > 0 else 0

        # Real yield net (static)
        real_yield_net = asset.get("realYield", 0) - asset.get("inflation", 0)

        # Data completeness
        filled = sum([1 for x in [price, circ_mc, annual_rev, tvl] if x])
        data_completeness = filled / 4

        m = {
            "rev_ann_30d":             annual_rev,
            "rev_24h":                 rev_24h_val,
            "tvl":                     tvl,
            "real_yield_net":          real_yield_net,
            "pe":                      pe,
            "ps":                      ps,
            "mc_tvl":                  mc_tvl,
            "circ_mc":                 circ_mc,
            "vol_mc_ratio":            vol_mc,
            "dynamic_strike":          dyn_strike,
            "emissions_unlock_30d_pct": None,   # non dispo sans API spécifique
            "data_completeness":       data_completeness,
        }

        # Score ARCA
        conviction = calc_conviction(price, asset, m)
        signal     = get_signal_label(conviction["total"])

        today_snapshot[aid] = {
            "price":        round(price, 6),
            "change24h":    round(chg24, 2),
            "score":        conviction["total"],
            "signal":       signal,
            "business":     conviction["business"],
            "valuation":    conviction["valuation"],
            "capital_risk": conviction["capital_risk"],
            "pe":           pe,
            "mc_tvl":       mc_tvl,
            "tvl":          round(tvl, 0) if tvl else None,
            "circ_mc":      round(circ_mc, 0) if circ_mc else None,
            "rev_ann_30d":  round(annual_rev, 0) if annual_rev else None,
            "vol_mc":       vol_mc,
            "ts":           datetime.datetime.utcnow().isoformat() + "Z",
        }

        print(f"    price=${price:.4f}  score={conviction['total']}  signal={signal}")

    if not today_snapshot:
        print("\n⚠️  No data collected — aborting.")
        return

    # 3. Push sur GitHub
    print(f"\n[3/3] Pushing snapshot to GitHub…")
    snapshots[TODAY] = today_snapshot
    commit_msg = f"snapshot: {TODAY} ({len(today_snapshot)} tokens)"
    github_write_file(SNAPSHOTS_FILE, snapshots, sha, commit_msg)

    print(f"\n{'='*55}")
    print(f"  Done — {len(today_snapshot)} tokens saved for {TODAY}")
    print(f"{'='*55}\n")

if __name__ == "__main__":
    run()
