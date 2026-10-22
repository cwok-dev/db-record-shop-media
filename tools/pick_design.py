"""아침 시안에서 사용자가 고른 안으로 design.json을 만들고 선택 기록을 남긴다.

python3 -I tools/pick_design.py posts/<id>/options.json "album=A,1=B,2=A,..."
→ posts/<id>/design.json, posts/design_log.jsonl 에 한 줄씩 추가 (빠진 카드는 A)
"""
import datetime, json, pathlib, sys

opt_path = pathlib.Path(sys.argv[1])
picks = dict(kv.split("=") for kv in sys.argv[2].replace(" ", "").split(",") if kv)
opt = json.load(open(opt_path, encoding="utf-8"))
album_id = opt_path.parent.name
cards, log = {}, []
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec="minutes")
for card, options in opt["cards"].items():
    k = picks.get(card, "A").upper()
    i = "ABC".index(k)
    cards[card] = options[i]
    log.append({"at": now, "album": album_id, "card": card, "picked": k, "by": "user" if card in picks else "default",
                "options": [{x: o.get(x) for x in ("template", "shape", "props", "basis", "why")} for o in options]})
design = {"photos": opt.get("photos", {}), "cards": cards}
(opt_path.parent / "design.json").write_text(json.dumps(design, ensure_ascii=False, indent=1), encoding="utf-8")
with open(opt_path.parent.parent / "design_log.jsonl", "a", encoding="utf-8") as f:
    for row in log:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
print(json.dumps({c: picks.get(c, "A").upper() for c in opt["cards"]}, ensure_ascii=False))
