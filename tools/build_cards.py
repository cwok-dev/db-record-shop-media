"""리뷰 하나로 캐러셀 카드(JPEG)와 캡션을 만든다. 릴스는 만들지 않는다. 디자인은 사양서 4장.

게시용
python3 -I tools/build_cards.py --album <albums JSON> --review <reviews JSON> --cover <표지> --out <폴더>
    [--design posts/<id>/design.json]

아침 시안 (카드마다 A·B·C를 나란히 놓은 미리보기)
python3 -I tools/build_cards.py --album <albums JSON> --cover <표지> --out <폴더>
    --options <options.json> [--review <reviews JSON>]

design.json  {"photos": {"p1": {"url": ..., "page": 기사 주소}}, "cards": {"album": 사양, "1": 사양, ...}}
options.json {"photos": {...}, "cards": {"album": [A, B, C], "1": [A, B, C], ...}}
사양         {"template": sleeve|glyph|polaroid|cutout|grid|player|full, "photo": "p1", "crop": [x0, y0, x1, y1](비율),
              "bg": paper|ink|spot(타이포 카드), "shape": circle|arch|frame|wide(cutout, wide는 화면 폭 전체·"aspect" 높이/폭 비율, 기본 0.5), "props": ["sparkle"|"wave"|"motif:<이름>"],
              "wide": true|false(한 줄 평 6칸), "lines": ["Moon", "light"](제목 줄바꿈 직접 지정),
              "basis": 제목|소개|위치|평, "why": 의도 한 문장}
design.json·options.json의 "credit": 사진 출처(소속사명). 사진을 쓴 카드가 있으면 캡션에 "사진: <credit>"을 넣는다.
사양이 없는 카드는 표지로 만든다(앨범 sleeve, 트랙은 타이포 cutout·사진 full을 번갈아).

출력: <out>/p1_01.jpg …, p2_…, premix_…, caption_<post>.txt, manifest.json (warnings 포함)
"""
import argparse, json, pathlib, re, sys, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
CARD = HERE / "cardnews"
sys.path.insert(0, str(CARD))

FONTS = {
    "Paperlogy-6SemiBold.woff2": "https://raw.githubusercontent.com/projectnoonnu/2408-3/main/Paperlogy-6SemiBold.woff2",
    "Paperlogy-8ExtraBold.woff2": "https://raw.githubusercontent.com/projectnoonnu/2408-3/main/Paperlogy-8ExtraBold.woff2",
    "Paperlogy-9Black.woff2": "https://raw.githubusercontent.com/projectnoonnu/2408-3/main/Paperlogy-9Black.woff2",
    "S-CoreDream-3Light.woff": "https://raw.githubusercontent.com/projectnoonnu/noonfonts_six/master/S-CoreDream-3Light.woff",
    "S-CoreDream-4Regular.woff": "https://raw.githubusercontent.com/projectnoonnu/noonfonts_six/master/S-CoreDream-4Regular.woff",
    "S-CoreDream-5Medium.woff": "https://raw.githubusercontent.com/projectnoonnu/noonfonts_six/master/S-CoreDream-5Medium.woff",
    "S-CoreDream-6Bold.woff": "https://raw.githubusercontent.com/projectnoonnu/noonfonts_six/master/S-CoreDream-6Bold.woff",
    "ChosunGu.woff": "https://raw.githubusercontent.com/projectnoonnu/noonfonts_20-04/master/ChosunGu.woff",
    "SpaceMono-Bold.woff2": "https://fonts.gstatic.com/s/spacemono/v17/i7dMIFZifjKcF5UAWdDRaPpZUFWaHg.woff2",
}

POST_ORDER = [1, 2, "remix"]


def fetch_fonts():
    d = CARD / "fonts"
    d.mkdir(exist_ok=True)
    for name, url in FONTS.items():
        if not (d / name).exists():
            urllib.request.urlretrieve(url, d / name)


def tag(s):
    return "#" + "".join(ch for ch in s if ch.isalnum())


def hashtags(album):
    titles = [t["title"] for t in album["tracks"] if t.get("isTitle")]
    out, seen = [], set()
    for t in ["#케이팝리뷰", "#앨범리뷰", tag(album["artist"]), tag(album["title"])] + ([tag(titles[0])] if titles else []):
        if len(t) > 1 and t.lower() not in seen:
            seen.add(t.lower()); out.append(t)
    return " ".join(out[:5])


def stars_text(s):
    return f"{float(s):.1f}"


def captions(album, review, posts, credit=None):
    a = review["album"]
    tags = hashtags(album)
    head = f"★ {stars_text(a['stars'])} | {a['oneline']}"
    recs = [t["title"] for t in sorted(album["tracks"], key=lambda t: t["n"])
            if review.get("tracks", {}).get(str(t["n"]), {}).get("rec")]
    first = [f"{album['artist']} 『{album['title']}』",
             f"{album['type']} · {album['releaseDate'].replace('-', '.')}", "", head]
    if recs:
        first += ["", "추천 트랙: " + ", ".join(recs)]
    photo = [f"사진: {credit}"] if credit else []
    if photo:
        first += [""] + photo
    first += ["", tags]
    out = {}
    for i, p in enumerate(posts, 1):
        out[p] = "\n".join(first) if p == 1 else \
            "\n".join([f"『{album['title']}』 리뷰 {i}/{len(posts)}", "", head] + ([""] + photo if photo else []) + ["", tags])
    return out


def default_spec(kind, i):
    """사양이 없을 때: 표지 사진으로 앨범은 sleeve, 트랙은 타이포(cutout)·사진(full)을 번갈아."""
    if kind == "album":
        return {"template": "sleeve"}
    return {"template": "cutout"} if i % 2 == 1 else {"template": "full"}


def check_rules(group, specs, warns):
    """게시물 안 규칙: 이웃 카드가 같은 계열이면 리듬이 깨진다(경고만). 37종 모티프 소품은 한 게시물에서 겹치지 않는다."""
    from layout import TYPO
    fam = [("typo" if s["template"] in TYPO else "photo") for s in specs]
    for i in range(1, len(fam)):
        if fam[i] == fam[i - 1]:
            warns.append(f"트랙 {group[i]['n']}: 앞 카드와 같은 {fam[i]} 계열(리듬 규칙)")
    seen = set()
    for t, s in zip(group, specs):
        for p in s.get("props", []):
            if p.startswith("motif:"):
                if p in seen:
                    sys.exit(f"이 게시물에서 이미 쓴 모티프 소품: {p} (트랙 {t['n']})")
                seen.add(p)


def make_card(layout, photo, *, kind, spec, photos, cover, cache, ctx, warns, label, used=None):
    """사양 하나로 Card를 만든다. 사진을 못 받으면 표지로 바꾸고 경고를 남긴다. used: 사진을 실제로 쓴 카드 이름 모음."""
    src = cover
    if spec.get("photo"):
        src = photos.get(spec["photo"], {}).get("url") or photos.get(spec["photo"], {}).get("file") or cover
    crop = spec.get("crop") if src != cover else None

    def img(w, h, cell=7):
        nonlocal src, crop
        try:
            uri = photo.slot(src, crop, w, h, cache, cell).as_uri()
            if src != cover and used is not None:
                used.add(label)
            return uri
        except photo.PhotoError as e:
            warns.append(f"{label}: 사진을 못 받아 표지로 대신함 ({e})")
            src, crop = cover, None
            return photo.slot(src, None, w, h, cache, cell).as_uri()

    return layout.Card(kind=kind, spec=spec, img=img, bg=spec.get("bg"), **ctx)


def build(args, album, review, posts_specs, photos, out, preview=False):
    import layout, photo
    from PIL import Image
    cover = pathlib.Path(args.cover).resolve()
    cache = out / ".cache"; cache.mkdir(parents=True, exist_ok=True)
    spot = layout.spot_color(cover)
    prop = layout.prop_color(spot)
    tracks = sorted(album["tracks"], key=lambda t: t["n"])
    year = album["releaseDate"][:4]
    common = dict(cover=cover.as_uri(), spot=spot, prop=prop, artist=album["artist"], album=album["title"], year=year)
    a = (review or {}).get("album")
    posts = [p for p in POST_ORDER if any(t.get("post") == p for t in tracks)]
    jobs, manifest, warns, used = [], [], [], {}
    for p in posts:
        group = [t for t in tracks if t.get("post") == p][:19]
        total = 1 + len(group)
        key = f"p{p}"
        variants = posts_specs(p, group)  # [(이름, 앨범 사양, [트랙 사양])]
        files = {}
        for vname, aspec, tspecs in variants:
            check_rules(group, tspecs, warns)
            aspec = {**aspec, "type": album.get("type", ""), "date": album["releaseDate"].replace("-", ".")}
            if p != 1:
                aspec.setdefault("bg", "ink")
            png = out / f"{key}_01{vname}.png"
            jobs.append((make_card(layout, photo, kind="album", spec=aspec, photos=photos, cover=cover, cache=cache,
                                   warns=warns, label=f"{key} 앨범", used=used.setdefault(p, set()), ctx={**common, "page": f"01/{total:02d}", "review": a}), png))
            files.setdefault(1, []).append(png)
            typo_i = 0
            for i, (t, s) in enumerate(zip(group, tspecs), 2):
                r = (review or {}).get("tracks", {}).get(str(t["n"])) if review else None
                if s["template"] in layout.TYPO and not s.get("bg"):
                    s = {**s, "bg": ["paper", "ink", "spot"][typo_i % 3]}
                if s["template"] in layout.TYPO:
                    typo_i += 1
                png = out / f"{key}_{i:02d}{vname}.png"
                ctx = {**common, "page": f"{i:02d}/{total:02d}", "n": t["n"], "total": len(tracks), "title": t["title"],
                       "is_title": bool(t.get("isTitle")), "review": r}
                jobs.append((make_card(layout, photo, kind="track", spec=s, photos=photos, cover=cover, cache=cache,
                                       warns=warns, label=f"{key} 트랙 {t['n']}", used=used.setdefault(p, set()), ctx=ctx), png))
                files.setdefault(i, []).append(png)
        manifest.append((p, key, group, files))
    rw = layout.render(jobs, out)
    warns += [f"{k}: {v}" for k, v in rw.items()]
    return manifest, warns, used


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--album", required=True)
    ap.add_argument("--review")
    ap.add_argument("--cover", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--design", help="posts/<id>/design.json")
    ap.add_argument("--options", help="아침 시안용 options.json")
    args = ap.parse_args()

    load = lambda f: (lambda d: d.get("data", d))(json.load(open(f, encoding="utf-8")))
    album = load(args.album)
    review = load(args.review) if args.review else None
    out = pathlib.Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    fetch_fonts()
    from PIL import Image

    if args.options:
        opt = json.load(open(args.options, encoding="utf-8"))
        cards = opt["cards"]

        def specs(p, group):
            n = max(len(cards.get("album", [])), *(len(cards.get(str(t["n"]), [])) for t in group), 1)
            pick = lambda lst, k, d: (lst[k] if k < len(lst) else lst[0]) if lst else d
            return [("ABC"[k], pick(cards.get("album", []), k, default_spec("album", 0)),
                     [pick(cards.get(str(t["n"]), []), k, default_spec("track", i)) for i, t in enumerate(group, 1)]) for k in range(n)]

        manifest, warns, _ = build(args, album, review, specs, opt.get("photos", {}), out, preview=True)
        from PIL import ImageDraw
        sheets = []
        for p, key, group, files in manifest:
            names = ["앨범"] + [t["title"] for t in group]
            for i, pngs in sorted(files.items()):
                Wt, Ht = 432, 540
                s = Image.new("RGB", (len(pngs) * (Wt + 16) + 16, Ht + 72), "#2a2a2a")
                d = ImageDraw.Draw(s)
                for k, f in enumerate(pngs):
                    s.paste(Image.open(f).convert("RGB").resize((Wt, Ht), Image.LANCZOS), (16 + k * (Wt + 16), 56))
                    d.text((16 + k * (Wt + 16), 20), "ABC"[k], fill="#fff")
                sp = out / f"sheet_{key}_{i:02d}.jpg"
                s.save(sp, quality=86)
                sheets.append({"card": "album" if i == 1 else str(group[i - 2]["n"]), "post": p, "name": names[i - 1], "sheet": sp.name})
        (out / "sheets.json").write_text(json.dumps({"sheets": sheets, "warnings": warns}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps({"sheets": [x["sheet"] for x in sheets], "warnings": warns}, ensure_ascii=False))
        return

    if not review:
        sys.exit("게시용 렌더링에는 --review가 필요합니다")
    design = json.load(open(args.design, encoding="utf-8")) if args.design else {"cards": {}, "photos": {}}
    dc = design.get("cards", {})

    def specs(p, group):
        return [("", dc.get("album", default_spec("album", 0)),
                 [dc.get(str(t["n"]), default_spec("track", i)) for i, t in enumerate(group, 1)])]

    manifest, warns, used = build(args, album, review, specs, design.get("photos", {}), out)
    credit = design.get("credit") if any(used.values()) else None
    if any(used.values()) and not design.get("credit"):
        warns.append("사진을 썼지만 design.json에 credit(소속사명)이 없어 캡션에 출처를 넣지 못함")
    caps = captions(album, review, [m[0] for m in manifest], credit)
    result = []
    for p, key, group, files in manifest:
        names = []
        for i, pngs in sorted(files.items()):
            jpg = out / f"{key}_{i:02d}.jpg"
            Image.open(pngs[0]).convert("RGB").save(jpg, "JPEG", quality=94, subsampling=0)
            pngs[0].unlink()
            names.append(jpg.name)
        (out / f"caption_{p}.txt").write_text(caps[p], encoding="utf-8")
        result.append({"post": p, "files": names, "caption": f"caption_{p}.txt",
                       "design": {"album": dc.get("album", default_spec("album", 0)),
                                  **{str(t["n"]): dc.get(str(t["n"]), default_spec("track", i)) for i, t in enumerate(group, 1)}}})
    (out / "manifest.json").write_text(json.dumps({"posts": result, "warnings": warns}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"posts": [{k: r[k] for k in ("post", "files", "caption")} for r in result], "warnings": warns}, ensure_ascii=False))


if __name__ == "__main__":
    main()
