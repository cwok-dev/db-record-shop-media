"""리뷰 하나로 캐러셀 카드(JPEG)와 캡션을 만든다. 릴스는 만들지 않는다. 디자인은 사양서 4장.

게시용
python3 -I tools/build_cards.py --album <albums JSON> --review <reviews JSON> --cover <표지> --out <폴더>
    [--design posts/<id>/design.json]

아침 시안 (카드마다 A·B·C를 나란히 놓은 미리보기)
python3 -I tools/build_cards.py --album <albums JSON> --cover <표지> --out <폴더>
    --options <options.json> [--review <reviews JSON>]

design.json  {"photos": {"p1": {"url": ..., "page": 기사 주소}}, "cards": {"album": 사양, "1": 사양, ...}}
options.json {"photos": {...}, "cards": {"album": [A, B, C], "1": [A, B, C], ...}}
사양         {"template": nowplaying|flyer|live|neon|editorial|layers|stage|polaroid|gable|motion|colorblock|split|stacked|bloom|manga|player|full|cinema|cctv|clipboard|desktop|notch|issue|torn|poster|oval, "photo": "p1", "crop": [x0, y0, x1, y1](비율),
              "bg": paper|ink|spot(타이포 카드), "props": ["sparkle"|"wave"|"zoom"|"motif:<이름>"],
              "zooms": [[x0, y0, x1, y1], ...](크롭 영역 안에서 확대할 부분, 비율: desktop 창 셋·zoom 소품 별 셋·motion 액자·issue 띠 둘+작은 사진·torn 띠·manga 칸 넷),
              "wide": true|false(한 줄 평 6칸), "lines": ["Moon", "light"](제목 줄바꿈 직접 지정),
              "basis": 제목|소개|위치|평, "why": 의도 한 문장}
design.json·options.json의 "credit": 사진 출처(소속사명). 사진을 쓴 카드가 있으면 캡션에 "사진: <credit>"을 넣는다.
사양이 없는 카드가 있으면 렌더링을 멈춘다.

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


def need(spec, name):
    """사양이 없으면 렌더링을 멈춘다(사용자 결정 2026-10-24: 대신 쓰는 기본 사양 없음)."""
    if not spec:
        sys.exit(f"사양 없음: {name} 카드 (design.json·options.json에 넣어야 함)")
    return spec


def photo_key(spec, photos):
    """카드가 실제로 보여 줄 사진 이름. nowplaying·사진 미지정·없는 사진 이름은 표지("cover")다."""
    if spec["template"] == "nowplaying":  # 표지 원본만 쓰는 앨범 템플릿
        return "cover"
    return spec["photo"] if spec.get("photo") in photos else "cover"


def check_rules(group, specs, warns, aspec, photos, strict=True):
    """게시물 안 규칙: 이웃 카드가 같은 계열이면 리듬이 깨진다(경고만). 37종 모티프 소품은 한 게시물에서 겹치지 않는다.
    앨범 카드부터 이어지는 카드에 같은 사진(표지 포함)을 연달아 쓰지 않는다. 아침 시안(strict=False)은 A·B·C가
    따로 골라지는 안이라 경고만 남긴다."""
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
    names = ["앨범"] + [f"트랙 {t['n']}" for t in group]
    keys = [photo_key(s, photos) for s in [aspec] + list(specs)]
    for i in range(1, len(keys)):
        if keys[i] == keys[i - 1]:
            msg = f"{names[i]}: 앞 카드({names[i - 1]})와 같은 사진 {keys[i]} (연속 사진 규칙)"
            if strict:
                sys.exit(msg)
            warns.append(msg)


def sub_crop(crop, sub):
    """크롭 영역 crop 안에서 sub(비율)만큼을 다시 자른 영역."""
    if not sub:
        return crop
    x0, y0, x1, y1 = crop or (0, 0, 1, 1)
    return [x0 + (x1 - x0) * sub[0], y0 + (y1 - y0) * sub[1], x0 + (x1 - x0) * sub[2], y0 + (y1 - y0) * sub[3]]


def make_card(layout, photo, *, kind, spec, photos, cover, cache, ctx, warns, label, used=None, shown=None, key=None):
    """사양 하나로 Card를 만든다. 사진을 못 받으면 표지로 바꾸고 경고를 남긴다. used: 사진을 실제로 쓴 카드 이름 모음.
    shown[key]: 이 카드가 실제로 보여 준 사진 이름(표지 대체 후 연속 사진 확인용)."""
    src = cover
    if spec.get("photo"):
        src = photos.get(spec["photo"], {}).get("url") or photos.get(spec["photo"], {}).get("file") or cover
    crop = spec.get("crop") if src != cover else None
    if shown is not None:
        shown[key] = photo_key(spec, photos)

    def img(w, h, cell=4, sub=None):
        """sub: 크롭 영역 안의 다시 자를 부분(비율). 한 카드 안에서 같은 사진의 다른 부분을 확대해 쓸 때."""
        nonlocal src, crop
        try:
            uri = photo.slot(src, sub_crop(crop, sub), w, h, cache, cell).as_uri()
            if src != cover and used is not None:
                used.add(label)
            return uri
        except photo.PhotoError as e:
            warns.append(f"{label}: 사진을 못 받아 표지로 대신함 ({e})")
            src, crop = cover, None
            if shown is not None:
                shown[key] = "cover"
            return photo.slot(src, sub_crop(None, sub), w, h, cache, cell).as_uri()

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
    jobs, manifest, warns, used, shown, seqs = [], [], [], {}, {}, []
    for p in posts:
        group = [t for t in tracks if t.get("post") == p][:19]
        total = 1 + len(group)
        key = f"p{p}"
        variants = posts_specs(p, group)  # [(이름, 앨범 사양, [트랙 사양])]
        files = {}
        for vname, aspec, tspecs in variants:
            check_rules(group, tspecs, warns, aspec, photos, strict=not preview)
            seq = []
            aspec = {**aspec, "type": album.get("type", ""), "date": album["releaseDate"].replace("-", ".")}
            if p != 1:
                aspec.setdefault("bg", "ink")
            png = out / f"{key}_01{vname}.png"
            jobs.append((make_card(layout, photo, kind="album", spec=aspec, photos=photos, cover=cover, cache=cache,
                                   warns=warns, label=f"{key} 앨범", used=used.setdefault(p, set()), shown=shown, key=png,
                                   ctx={**common, "page": f"01/{total:02d}", "review": a,
                                        "tracks": [(t["n"], t["title"], bool(t.get("isTitle"))) for t in tracks], "blurb": (album.get("description") or {}).get("text")}), png))
            files.setdefault(1, []).append(png)
            seq.append((f"{key} 앨범", png))
            typo_i = 0
            for i, (t, s) in enumerate(zip(group, tspecs), 2):
                r = (review or {}).get("tracks", {}).get(str(t["n"])) if review else None
                if s["template"] in layout.TYPO and not s.get("bg"):
                    s = {**s, "bg": ["paper", "ink", "spot"][typo_i % 3]}
                if s["template"] in layout.TYPO:
                    typo_i += 1
                png = out / f"{key}_{i:02d}{vname}.png"
                ctx = {**common, "page": f"{i:02d}/{total:02d}", "n": t["n"], "total": len(tracks), "title": t["title"],
                       "is_title": bool(t.get("isTitle")), "review": r, "blurb": (t.get("description") or {}).get("text")}
                jobs.append((make_card(layout, photo, kind="track", spec=s, photos=photos, cover=cover, cache=cache,
                                       warns=warns, label=f"{key} 트랙 {t['n']}", used=used.setdefault(p, set()), ctx=ctx,
                                       shown=shown, key=png), png))
                files.setdefault(i, []).append(png)
                seq.append((f"{key} 트랙 {t['n']}", png))
            seqs.append(seq)
        manifest.append((p, key, group, files))
    rw = layout.render(jobs, out)
    warns += [f"{k}: {v}" for k, v in rw.items()]
    for seq in seqs:  # 사진을 못 받아 표지로 대신한 카드가 이웃과 겹치는지(렌더링 뒤에만 알 수 있어 경고)
        for (a, pa), (b, pb) in zip(seq, seq[1:]):
            if shown.get(pa) == shown.get(pb):
                warns.append(f"{b}: 표지 대체로 앞 카드({a})와 같은 사진 {shown[pb]} (연속 사진 규칙)")
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
            pick = lambda lst, k, name: need(lst, name)[k] if k < len(lst) else lst[0]
            return [("ABC"[k], pick(cards.get("album", []), k, "앨범"),
                     [pick(cards.get(str(t["n"]), []), k, f"트랙 {t['n']}") for t in group]) for k in range(n)]

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
        return [("", need(dc.get("album"), "앨범"), [need(dc.get(str(t["n"])), f"트랙 {t['n']}") for t in group])]

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
                       "design": {"album": dc["album"], **{str(t["n"]): dc[str(t["n"])] for t in group}}})
    (out / "manifest.json").write_text(json.dumps({"posts": result, "warnings": warns}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"posts": [{k: r[k] for k in ("post", "files", "caption")} for r in result], "warnings": warns}, ensure_ascii=False))


if __name__ == "__main__":
    main()
