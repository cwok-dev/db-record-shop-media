"""리뷰 하나로 캐러셀 카드(JPEG)와 캡션을 만든다. 릴스는 만들지 않는다.

python3 -I tools/build_cards.py --album <albums 문서 JSON> --review <reviews 문서 JSON>
    --cover <표지 파일> --out <출력 폴더> [--motifs "1=ribbon,2=streaks"]

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--album", required=True)
    ap.add_argument("--review", required=True)
    ap.add_argument("--cover", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--motifs", default="", help='트랙 번호별 모티프, 예 "1=ribbon,2=streaks". 없으면 번갈아 씀')
    args = ap.parse_args()

    album = json.load(open(args.album, encoding="utf-8"))
    review = json.load(open(args.review, encoding="utf-8"))
    album, review = album.get("data", album), review.get("data", review)
    cover = pathlib.Path(args.cover).resolve()
    out = pathlib.Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    motifs = dict(kv.split("=") for kv in args.motifs.split(",") if kv)

    fetch_fonts()
    from render import render_card
    from point_color import point_colors, BLACK, WHITE
    import graphics
    from PIL import Image

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
        for i, t in enumerate(group, 2):
            r = review.get("tracks", {}).get(str(t["n"]), {})
            m = motifs.get(str(t["n"])) or ("ribbon" if i % 2 == 0 else "streaks")
            media = graphics.ribbon(t["title"], BLACK, pt_dark) if m == "ribbon" else graphics.streaks(t["title"], BLACK, WHITE)
            png = out / f"{key}_{i:02d}.png"
            render_card(png, cover=cover, artist=album["artist"], title=t["title"], oneline=r.get("oneline", ""),
                        score=float(r.get("stars", 0)), page=f"{i:02d}/{total:02d}", theme="track",
                        recommended=bool(r.get("rec")), media=media)
            save(png, i)
        (out / f"caption_{p}.txt").write_text(caps[p], encoding="utf-8")
        manifest.append({"post": p, "files": files, "caption": f"caption_{p}.txt"})
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
