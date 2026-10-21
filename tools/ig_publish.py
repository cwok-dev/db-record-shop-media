import os, sys, json, time, urllib.request, urllib.parse
TOK, UID = os.environ["IG_ACCESS_TOKEN"], os.environ["IG_USER_ID"]
H = "https://graph.instagram.com"
def call(method, path, **p):
    p["access_token"] = TOK
    data = urllib.parse.urlencode(p).encode()
    req = urllib.request.Request(H + path + ("" if method == "POST" else "?" + data.decode()),
                                 data=data if method == "POST" else None, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace").replace(TOK, "***")
        sys.exit(f"HTTP {e.code} {path.replace(UID,'<IG_USER_ID>')}: {body}")
base, caption = sys.argv[1], open(sys.argv[2], encoding="utf-8").read().strip()
print("limit:", json.dumps(call("GET", f"/{UID}/content_publishing_limit", fields="quota_usage,config")))
kids = [call("POST", f"/{UID}/media", image_url=f"{base}/{f}", is_carousel_item="true")["id"] for f in sys.argv[3:]]
print("children", len(kids))
c = call("POST", f"/{UID}/media", media_type="CAROUSEL", children=",".join(kids), caption=caption)["id"]
for i in range(6):
    st = call("GET", f"/{c}", fields="status_code").get("status_code"); print(f"t+{i}min", st)
    if st in ("FINISHED", "ERROR", "EXPIRED"): break
    time.sleep(60)
if st != "FINISHED": sys.exit(f"container not finished: {st}")
m = call("POST", f"/{UID}/media_publish", creation_id=c)["id"]
print(json.dumps({"media_id": m, **call("GET", f"/{m}", fields="permalink,timestamp")}))
