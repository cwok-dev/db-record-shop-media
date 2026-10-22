"""리뷰 하나로 캐러셀 카드(JPEG)와 캡션을 만든다. 릴스는 만들지 않는다.

python3 -I tools/build_cards.py --album <albums 문서 JSON> --review <reviews 문서 JSON>
    --cover <표지 파일> --out <출력 폴더> [--motifs "1=ribbon/grain/accent/glow,2=rings/glow/split"]

--motifs: 트랙 번호=모티프[/질감[/팔레트[/glow]]]. 질감 기본 grain, 팔레트 기본 accent, glow를 쓰면 배경 빛을 켠다.
지정하지 않은 트랙은 트랙 제목으로 고정한 난수로 고른다.
한 게시물 안에서는 모든 모티프를 한 번씩 쓰기 전에는 다시 쓰지 않고, 이웃 카드끼리는 같은 모티프를 쓰지 않는다.

출력: <out>/p1_01.jpg …, p2_…, premix_…, caption_<post>.txt, manifest.json
"""
import argparse, json, pathlib, re, sys, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
CARD = HERE / "cardnews"
sys.path.insert(0, str(CARD))

FONTS = {
    "Paperlogy-6SemiBold.woff2": "https://raw.githubusercontent.com/projectnoonnu/2408-3/main/Paperlogy-6SemiBold.woff2",
    "Paperlogy-8ExtraBold.woff2": "https://raw.githubusercontent.com/projectnoonnu/2408-3/main/Paperlogy-8ExtraBold.woff2",
    "S-CoreDream-3Light.woff": "https://raw.githubusercontent.com/projectnoonnu/noonfonts_six/master/S-CoreDream-3Light.woff",
    "S-CoreDream-4Regular.woff": "https://raw.githubusercontent.com/projectnoonnu/noonfonts_six/master/S-CoreDream-4Regular.woff",
    "S-CoreDream-5Medium.woff": "https://raw.githubusercontent.com/projectnoonnu/noonfonts_six/master/S-CoreDream-5Medium.woff",
    "S-CoreDream-6Bold.woff": "https://raw.githubusercontent.com/projectnoonnu/noonfonts_six/master/S-CoreDream-6Bold.woff",
    "ChosunGu.woff": "https://raw.githubusercontent.com/projectnoonnu/noonfonts_20-04/master/ChosunGu.woff",
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


def captions(album, review, posts):
    a = review["album"]
    tags = hashtags(album)
    head = f"★ {stars_text(a['stars'])} | {a['oneline']}"
    recs = [t["title"] for t in sorted(album["tracks"], key=lambda t: t["n"])
            if review.get("tracks", {}).get(str(t["n"]), {}).get("rec")]
    first = [f"{album['artist']} 『{album['title']}』",
             f"{album['type']} · {album['releaseDate'].replace('-', '.')}", "", head]
    if recs:
        first += ["", "추천 트랙: " + ", ".join(recs)]
    first += ["", tags]
    out = {}
    for i, p in enumerate(posts, 1):
        out[p] = "\n".join(first) if p == 1 else \
            f"『{album['title']}』 리뷰 {i}/{len(posts)}\n\n{head}\n\n{tags}"
    return out


def parse_specs(text, graphics):
    specs = {}
    for kv in filter(None, (s.strip() for s in text.split(","))):
        n, spec = kv.split("=")
        parts = spec.split("/")
        motif = parts[0]
        style = parts[1] if len(parts) > 1 and parts[1] else "grain"
        palette = parts[2] if len(parts) > 2 and parts[2] else "accent"
        glow = len(parts) > 3 and parts[3] == "glow"
        if motif not in graphics.MOTIFS:
            sys.exit(f"알 수 없는 모티프: {motif} (트랙 {n})")
        if style not in graphics.STYLES_FOR[motif]:
            sys.exit(f"{motif}에는 {graphics.STYLES_FOR[motif]} 질감만 쓴다 (트랙 {n})")
        if palette not in graphics.PALETTES:
            sys.exit(f"알 수 없는 팔레트: {palette} (트랙 {n})")
        specs[n.strip()] = {"motif": motif, "style": style, "palette": palette, "bg_glow": glow}
    return specs


def plan_graphics(group, specs, graphics):
    """게시물 하나의 트랙별 그래픽. 모든 모티프를 한 번씩 쓰기 전엔 재사용 금지, 이웃끼리는 항상 다르게."""
    import random
    plan, used, prev = [], set(), None
    reserved = {specs[str(t["n"])]["motif"] for t in group if str(t["n"]) in specs}
    for t in group:
        if len(used) == len(graphics.MOTIFS):
            used = set()
        g = specs.get(str(t["n"]))
        if g is None:
            rng = random.Random(t["title"])
            free = [m for m in graphics.MOTIFS if m not in used and m != prev]
            motif = rng.choice(sorted([m for m in free if m not in reserved] or free))
            g = {"motif": motif, "style": rng.choice(graphics.STYLES_FOR[motif]),
                 "palette": rng.choice(graphics.PALETTES if motif in graphics.AREA else ["accent", "split"]),
                 "bg_glow": False}
        elif g["motif"] == prev:
            sys.exit(f"이웃 카드와 모티프가 같다: {g['motif']} (트랙 {t['n']})")
        elif g["motif"] in used:
            sys.exit(f"이 게시물에서 이미 쓴 모티프: {g['motif']} (트랙 {t['n']})")
        used.add(g["motif"]); prev = g["motif"]
        plan.append(g)
    return plan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--album", required=True)
    ap.add_argument("--review", required=True)
    ap.add_argument("--cover", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--motifs", default="", help='트랙 번호=모티프[/질감[/팔레트[/glow]]], 예 "1=ribbon/grain/accent/glow,2=rings/glow/split"')
    args = ap.parse_args()

    album = json.load(open(args.album, encoding="utf-8"))
    review = json.load(open(args.review, encoding="utf-8"))
    album, review = album.get("data", album), review.get("data", review)
    cover = pathlib.Path(args.cover).resolve()
    out = pathlib.Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)

    fetch_fonts()
    from render import render_card
    from point_color import point_colors, BLACK, WHITE
    import graphics
    from PIL import Image

    specs = parse_specs(args.motifs, graphics)
    pt_dark = point_colors(cover, BLACK)[0]
    tracks = sorted(album["tracks"], key=lambda t: t["n"])
    posts = [p for p in POST_ORDER if any(t.get("post") == p for t in tracks)]
    caps = captions(album, review, posts)
    a = review["album"]
    manifest = []
    for p in posts:
        group = [t for t in tracks if t.get("post") == p][:19]
        total = 1 + len(group)
        key = f"p{p}"
        files = []

        def save(png, i):
            jpg = out / f"{key}_{i:02d}.jpg"
            Image.open(png).convert("RGB").save(jpg, "JPEG", quality=94, subsampling=0)
            pathlib.Path(png).unlink()
            files.append(jpg.name)

        png = out / f"{key}_01.png"
        render_card(png, cover=cover, artist=album["artist"], title=album["title"], oneline=a["oneline"],
                    score=float(a["stars"]), page=f"01/{total:02d}", theme="album" if p == 1 else "alt")
        save(png, 1)
        plan = plan_graphics(group, specs, graphics)
        for i, (t, g) in enumerate(zip(group, plan), 2):
            r = review.get("tracks", {}).get(str(t["n"]), {})
            media = graphics.draw(g["motif"], t["title"], BLACK, pt_dark, style=g["style"], accent=WHITE,
                                  palette=g["palette"], bg_glow=g["bg_glow"])
            png = out / f"{key}_{i:02d}.png"
            render_card(png, cover=cover, artist=album["artist"], title=t["title"], oneline=r.get("oneline", ""),
                        score=float(r.get("stars", 0)), page=f"{i:02d}/{total:02d}", theme="track",
                        recommended=bool(r.get("rec")), media=media)
            save(png, i)
        (out / f"caption_{p}.txt").write_text(caps[p], encoding="utf-8")
        manifest.append({"post": p, "files": files, "caption": f"caption_{p}.txt",
                         "graphics": {str(t["n"]): g for t, g in zip(group, plan)}})
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
