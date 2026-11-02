import json, os, hashlib, datetime as dt, statistics as st
B=os.path.dirname(os.path.abspath(__file__)); C=B+"/cache"
def key(u): return hashlib.md5(u.encode()).hexdigest()
CG={"HYPE":"hyperliquid","JUP":"jupiter-exchange-solana","UNI":"uniswap","AAVE":"aave","PUMP":"pump-fun","ONDO":"ondo-finance","MET":"meteora","ASTER":"aster-2",
    "SYRUP":"syrup","AERO":"aerodrome-finance","PENDLE":"pendle","ENA":"ethena","RAY":"raydium","MORPHO":"morpho","MEGA":"megaeth","TRX":"tron","KNTQ":"kinetiq",
    "LDO":"lido-dao","LIT":"lighter","DRV":"derive","PONS":"pons","SKY":"sky","BTC":"bitcoin"}
def prices(i):
    p=C+"/"+key(f"https://api.coingecko.com/api/v3/coins/{i}/market_chart?vs_currency=usd&days=365&interval=daily")
    if not os.path.exists(p): return None
    d=json.load(open(p)); 
    if d["status"]!=200: return None
    return json.loads(d["body"])["prices"]
def at(s,t):
    pts=[x for x in s if x[0]<=t]; return pts[-1][1] if pts else None
S=json.load(open(B+"/scores.json")); now=dt.datetime(2026,11,2,tzinfo=dt.timezone.utc).timestamp()*1000
P={k:prices(v) for k,v in CG.items()}
def spearman(x,y):
    rk=lambda v:[sorted(v).index(a)+1 for a in v]
    rx,ry=rk(x),rk(y); n=len(x); d=sum((a-b)**2 for a,b in zip(rx,ry)); return 1-6*d/(n*(n*n-1))
for H in (30,90):
    rows=[]; ics=[]; btc=[]
    for D,res in S.items():
        t=dt.datetime.fromisoformat(D+"T00:00:00+00:00").timestamp()*1000; t2=t+H*864e5
        if t2>now: continue
        cur=[]
        for tok,v in res.items():
            if not v or not P.get(tok): continue
            p0,p1=at(P[tok],t),at(P[tok],t2)
            if not p0 or not p1: continue
            cur.append((tok,v["score"],v["signal"],p1/p0-1))
        if len(cur)<5: continue
        ew=st.mean(r for *_,r in cur)
        for tok,sc,sig,r in cur: rows.append((D,tok,sc,sig,r,r-ew))
        ics.append(spearman([c[1] for c in cur],[c[3] for c in cur]))
        b0,b1=at(P["BTC"],t),at(P["BTC"],t2); btc.append(b1/b0-1)
    print(f"\n=== Horizon {H}d : {len(set(r[0] for r in rows))} dates, {len(rows)} observations ===")
    print(f"BTC mean {st.mean(btc)*100:+.1f}%   equal-weight universe mean {st.mean(r[4] for r in rows)*100:+.1f}%")
    for sig in ("BUY","NEUTRAL","AVOID"):
        g=[r for r in rows if r[3]==sig]
        if g: print(f"{sig:8} n={len(g):3}  mean {st.mean(x[4] for x in g)*100:+6.1f}%  median {st.median(x[4] for x in g)*100:+6.1f}%  excess vs universe {st.mean(x[5] for x in g)*100:+6.1f}%  beats universe {sum(x[5]>0 for x in g)/len(g)*100:4.0f}%")
    for lo,hi,lab in ((65,101,"score>=65"),(50,65,"50-64"),(0,50,"<50")):
        g=[r for r in rows if lo<=r[2]<hi]
        if g: print(f"{lab:9} n={len(g):3}  excess {st.mean(x[5] for x in g)*100:+6.1f}%")
    print(f"Rank correlation score vs forward return (IC), mean over dates: {st.mean(ics):+.2f}  (dates positive: {sum(i>0 for i in ics)}/{len(ics)})")
json.dump({"note":"see console"},open(B+"/done.json","w"))
