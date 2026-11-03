import json, os, subprocess, hashlib, time, re, sys
B=os.path.dirname(os.path.abspath(__file__)); C=B+"/cache"
def key(u): return hashlib.md5(u.encode()).hexdigest()
def get(u, sleep=0):
    p=C+"/"+key(u)
    if os.path.exists(p): return
    r=subprocess.run(["curl","-s","-m","60","-w","\n%{http_code}",u],capture_output=True,text=True)
    body,_,code=r.stdout.rpartition("\n")
    json.dump({"url":u,"status":int(code or 0),"body":body},open(p,"w"))
    if sleep: time.sleep(sleep)
    return int(code or 0)
urls=json.load(open(B+"/urls.json"))
extra=[]
for u in urls:
    if "llama.fi/summary" in u or "llama.fi/overview/fees/" in u: extra.append(u)
    m=re.match(r"https://api.llama.fi/tvl/(.+)",u)
    if m: extra.append("https://api.llama.fi/protocol/"+m.group(1))
for ch in ["Tron","MegaETH"]: extra.append("https://api.llama.fi/v2/historicalChainTvl/"+ch)
for u in extra: get(u)
mk=[u for u in urls if "coins/markets" in u][0]
ids=re.search(r"ids=([^&]+)",mk).group(1).split(",")+["bitcoin"]
for i in ids:
    u=f"https://api.coingecko.com/api/v3/coins/{i}/market_chart?vs_currency=usd&days=365&interval=daily"
    for attempt in range(3):
        if os.path.exists(C+"/"+key(u)):
            d=json.load(open(C+"/"+key(u)))
            if d["status"]==200: break
            os.remove(C+"/"+key(u))
        st=get(u, sleep=7); print(i, st, flush=True)
        if st==200: break
        time.sleep(30)
print("done")
