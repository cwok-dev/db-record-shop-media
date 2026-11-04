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
# 중복 방지: 실패 응답을 받고도 실제로 올라간 경우가 있어, 같은 캡션의 게시물이 이미 있으면 다시 올리지 않고 그 게시물을 성공으로 돌려준다.
same = [x for x in call("GET", f"/{UID}/media", fields="id,caption,permalink,timestamp", limit="50").get("data", [])
        if (x.get("caption") or "").strip() == caption]
if same:
    print(f"already posted: same caption x{len(same)}")
    for y in same: print(" ", y.get("timestamp"), y.get("permalink"))
    x = same[-1]  # 가장 먼저 올라간 것
    print(json.dumps({"media_id": x["id"], "permalink": x.get("permalink"), "timestamp": x.get("timestamp"), "already": len(same)}))
    sys.exit(0)
if sys.argv[3:] == ["--check"]: sys.exit("not posted yet")  # 확인만 하고 끝냄(게시하지 않음)
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
