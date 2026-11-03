import asyncio, json, os, sys, hashlib, re, datetime as dt
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright
B=os.path.dirname(os.path.abspath(__file__)); C=B+"/cache"
HTML=sys.argv[1]; DATES=sys.argv[2].split(",")
def key(u): return hashlib.md5(u.encode()).hexdigest()
_mem={}
def cached(u):
    if u in _mem: return _mem[u]
    p=C+"/"+key(u)
    if not os.path.exists(p): _mem[u]=None; return None
    d=json.load(open(p)); 
    try: d["json"]=json.loads(d["body"]) if d["status"]==200 else None
    except Exception: d["json"]=None
    _mem[u]=d; return d
def mc(cgid): 
    d=cached(f"https://api.coingecko.com/api/v3/coins/{cgid}/market_chart?vs_currency=usd&days=365&interval=daily")
    return d["json"] if d and d["json"] else None
def at(series, Tms):
    pts=[p for p in series if p[0]<=Tms]
    return pts[-1][1] if pts else None

def asof_chart(j, Ts):
    j=dict(j)
    ch=[p for p in (j.get("totalDataChart") or []) if p[0]<=Ts]
    if not ch: return None
    vals=[p[1] or 0 for p in ch]
    j["totalDataChart"]=ch; j.pop("totalDataChartBreakdown",None)
    for k in ["totalRevenue30d","revenue30d","totalRevenue24h","revenue24h","revenue7d","revenue1y","change_1d","change_7d","change_1m","totalAllTime"]: j.pop(k,None)
    j["total24h"]=vals[-1]; j["total7d"]=sum(vals[-7:]); j["total30d"]=sum(vals[-30:]); j["total1y"]=sum(vals[-365:])
    return j

async def run_date(b, D):
    T=dt.datetime.fromisoformat(D+"T00:00:00+00:00"); Tms=int(T.timestamp()*1000); Ts=Tms//1000
    async def handle(route):
        u=route.request.url; p=urlparse(u); q=parse_qs(p.query)
        J=lambda body,status=200: route.fulfill(status=status, content_type="application/json", body=json.dumps(body))
        if p.scheme=="file": return await route.continue_()
        if p.netloc=="api.llama.fi":
            if p.path.startswith("/summary/") or p.path.startswith("/overview/fees/"):
                d=cached(u)
                if not d or not d["json"]: return await J({"error":"nf"},404)
                j=asof_chart(d["json"],Ts)
                return await (J(j) if j else J({"error":"nf"},404))
            if p.path.startswith("/tvl/"):
                d=cached("https://api.llama.fi/protocol/"+p.path[5:])
                if not d or not d["json"]: return await J({"error":"nf"},404)
                tv=[x for x in (d["json"].get("tvl") or []) if x["date"]<=Ts]
                return await (J(tv[-1]["totalLiquidityUSD"]) if tv else J({"error":"nf"},404))
            if p.path=="/v2/chains":
                out=[]
                for ch in ["Tron","MegaETH"]:
                    d=cached("https://api.llama.fi/v2/historicalChainTvl/"+ch)
                    if d and d["json"]:
                        tv=[x for x in d["json"] if x["date"]<=Ts]
                        if tv: out.append({"name":ch,"tvl":tv[-1]["tvl"]})
                return await J(out)
            return await J({"error":"nf"},404)
        if p.netloc=="api.coingecko.com":
            if p.path.endswith("/coins/markets"):
                out=[]
                for i in q["ids"][0].split(","):
                    m=mc(i)
                    if not m: continue
                    pr=at(m["prices"],Tms); cap=at(m["market_caps"],Tms); vol=at(m["total_volumes"],Tms)
                    if not pr or not cap: continue
                    p7=at(m["prices"],Tms-7*864e5); p30=at(m["prices"],Tms-30*864e5); p1=at(m["prices"],Tms-864e5)
                    spark=[x[1] for x in m["prices"] if Tms-7*864e5<=x[0]<=Tms]
                    out.append({"id":i,"current_price":pr,"market_cap":cap,"fully_diluted_valuation":None,"circulating_supply":cap/pr,"total_supply":None,
                        "total_volume":vol or 0,"ath":max(x[1] for x in m["prices"] if x[0]<=Tms),"ath_date":"","atl":0,
                        "price_change_percentage_24h":(pr/p1-1)*100 if p1 else 0,
                        "price_change_percentage_7d_in_currency":(pr/p7-1)*100 if p7 else None,"price_change_percentage_30d_in_currency":(pr/p30-1)*100 if p30 else None,
                        "sparkline_in_7d":{"price":spark}})
                return await J(out)
            mm=re.match(r"/api/v3/coins/([^/]+)/market_chart",p.path)
            if mm:
                m=mc(mm.group(1))
                if not m: return await J({"error":"nf"},404)
                days=int(q.get("days",["120"])[0]); lo=Tms-days*864e5
                f=lambda s:[x for x in s if lo<=x[0]<=Tms]
                return await J({"prices":f(m["prices"]),"market_caps":f(m["market_caps"]),"total_volumes":f(m["total_volumes"])})
            return await J({"error":"nf"},404)
        if p.netloc=="api.hyperliquid.xyz":
            body=route.request.post_data or ""
            if "metaAndAssetCtxs" in body:
                m=mc("hyperliquid"); pr=at(m["prices"],Tms) if m else None
                if not pr: return await J({"error":"nf"},500)
                return await J([{"universe":[{"name":"HYPE"}]},[{"markPx":str(pr),"prevDayPx":str(at(m["prices"],Tms-864e5) or pr),"dayNtlVlm":str(at(m["total_volumes"],Tms) or 0)}]])
            return await J({"error":"nf"},500)
        return await route.abort()
    ctx=await b.new_context(); pg=await ctx.new_page(); errs=[]
    pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.clock.set_fixed_time(T)
    await pg.route("**/*", handle)
    await pg.goto("file://"+HTML); await pg.wait_for_timeout(500)
    await pg.evaluate("showPage('arca')")
    for _ in range(60):
        await pg.wait_for_timeout(1000)
        done=await pg.evaluate("!document.getElementById('arcaRefreshBtn')?.disabled")
        if done: break
    res=await pg.evaluate("""Object.fromEntries(ARCA_ASSETS.map(a=>{const m=calcDynamicMetrics(a);const price=arcaPrices[a.id];
        if(!(price>0)||m.dataCompleteness<0.4) return [a.id,null];
        const c=getConvictionScore(price,a,m);const s=getBuySignal(price,m.dynamicStrike,m.pe,c.total);
        return [a.id,{score:c.total,biz:c.business,val:c.valuation,risk:c.capitalRisk,signal:s.label,pe:m.pe,live:m.liveState,price}]}))""")
    await ctx.close()
    return res, errs
async def main():
    out={}
    async with async_playwright() as pw:
        b=await pw.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        for D in DATES:
            r,e=await run_date(b,D); out[D]=r
            n=sum(1 for v in r.values() if v); print(D, n, "tokens scored", "errors:",e[:2], flush=True)
        await b.close()
    json.dump(out, open(B+"/scores.json","w"), indent=0)
asyncio.run(main())
