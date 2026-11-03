import asyncio, json, sys, hashlib, os
from playwright.async_api import async_playwright
B=os.path.dirname(os.path.abspath(__file__))
urls={}
async def handle(route):
    u=route.request.url
    if u.startswith("file:"): return await route.continue_()
    try:
        r=await route.fetch()
        if any(h in u for h in ("llama.fi","coingecko","hyperliquid")):
            urls[u]={"status":r.status,"post":route.request.post_data}
        await route.fulfill(response=r)
    except Exception as e:
        await route.abort()
async def main():
    async with async_playwright() as pw:
        b=await pw.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        pg=await b.new_page()
        pg.on("response", lambda r: urls.__setitem__(r.url, {"status":r.status,"post":r.request.post_data}) if any(h in r.url for h in ("llama.fi","coingecko","hyperliquid")) else None)
        await pg.goto("file://"+sys.argv[1]); await pg.wait_for_timeout(800)
        await pg.evaluate("showPage('arca')"); await pg.wait_for_timeout(50000)
        json.dump(urls, open(B+"/urls.json","w"), indent=0)
        print(len(urls))
        await b.close()
asyncio.run(main())
