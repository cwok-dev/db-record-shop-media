"""카드에 쓸 사진: 내려받기, 크롭, 하프톤 (사양서 4.7).

python3 -I photo.py scrape <폴더> <기사 주소> [<기사 주소> ...]   기사 본문 사진을 받아 <폴더>/index.json에 기록
python3 -I photo.py sheet <폴더> <출력.jpg>                        사진마다 10% 격자를 그린 확인용 한 장
"""
import hashlib, io, json, pathlib, re, sys, urllib.parse, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageOps

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"


class PhotoError(Exception):
    pass


def load(src, cache):
    """URL 또는 파일 경로에서 RGB 이미지를 읽는다. URL은 cache 폴더에 저장해 다시 쓴다."""
    src = str(src)
    if not src.startswith("http"):
        return Image.open(src).convert("RGB")
    cache = pathlib.Path(cache); cache.mkdir(parents=True, exist_ok=True)
    f = cache / (hashlib.sha1(src.encode()).hexdigest()[:16] + ".img")
    if not f.exists():
        err = None
        for _ in range(3):
            try:
                req = urllib.request.Request(src, headers={"User-Agent": UA})
                f.write_bytes(urllib.request.urlopen(req, timeout=25).read())
                err = None
                break
            except Exception as e:  # 막힌 도메인은 프록시가 403으로 끊는다
                err = e
        if err:
            raise PhotoError(f"{src.split('/')[2]}: {err}")
    try:
        return Image.open(f).convert("RGB")
    except Exception as e:
        f.unlink(missing_ok=True)
        raise PhotoError(f"{src}: 이미지가 아님 ({e})")


def fit_crop(im, crop, w, h):
    """crop(비율 x0,y0,x1,y1) 영역 안에서 가운데를 기준으로 w:h 비율의 가장 큰 사각형을 잘라 w×h로 줄인다.
    영역 밖은 쓰지 않으므로 콜라주 사진의 옆 칸이 섞이지 않는다."""
    W, H = im.size
    x0, y0, x1, y1 = crop or (0, 0, 1, 1)
    cx, cy = (x0 + x1) / 2 * W, (y0 + y1) / 2 * H
    bw, bh = (x1 - x0) * W, (y1 - y0) * H
    r = w / h
    if bw / bh > r:
        bw = bh * r
    else:
        bh = bw / r
    left, top = cx - bw / 2, cy - bh / 2
    return im.crop((int(left), int(top), int(left + bw), int(top + bh))).resize((w, h), Image.LANCZOS)


def halftone(im, cell=4, angle=45):
    """흰 바탕에 검은 점. 점 크기가 어두움에 비례한다(45° 격자).
    흰 옷·밝은 배경 사진은 점이 거의 안 찍혀 흐려지므로, 평균 밝기가 0.45를 넘으면 중간톤을 눌러 0.45로 맞춘다."""
    g = ImageOps.autocontrast(ImageOps.grayscale(im), cutoff=1)
    a = np.asarray(g, dtype=float) / 255
    m = a.mean()
    if m > 0.45:
        a = a ** (np.log(0.45) / np.log(m))
        g = Image.fromarray((a * 255).astype(np.uint8))
    k = 3
    r = g.rotate(angle, expand=True, fillcolor=255)
    W, H = r.size
    a = np.asarray(r, dtype=float) / 255
    canvas = Image.new("L", (W * k, H * k), 255)
    d = ImageDraw.Draw(canvas)
    for y in range(0, H, cell):
        for x in range(0, W, cell):
            dark = 1 - a[y:y + cell, x:x + cell].mean()
            rad = cell * k * 0.6 * dark ** 0.9
            if rad > 0.6:
                cx, cy = (x + cell / 2) * k, (y + cell / 2) * k
                d.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=0)
    canvas = canvas.resize((W, H), Image.LANCZOS).rotate(-angle, expand=True, fillcolor=255)
    cw, ch = canvas.size
    return canvas.crop(((cw - im.width) // 2, (ch - im.height) // 2,
                        (cw - im.width) // 2 + im.width, (ch - im.height) // 2 + im.height))


def slot(src, crop, w, h, cache, cell=4):
    """템플릿의 사진 칸 하나: 크롭 → w×h → 하프톤 PNG. 같은 입력이면 같은 파일을 다시 쓴다."""
    key = hashlib.sha1(f"{src}|{crop}|{w}|{h}|{cell}".encode()).hexdigest()[:16]
    out = pathlib.Path(cache) / f"ht_{key}.png"
    if not out.exists():
        halftone(fit_crop(load(src, cache), crop, w, h), cell).save(out)
    return out


def scrape(folder, pages, min_w=600):
    """기사 페이지들의 사진(og:image, 본문 img)을 받는다. 폭 min_w 미만·중복은 버린다.
    index.json: {"photos": {파일명: {url, page, size}}, "blocked": [도메인], "errors": [...]}"""
    folder = pathlib.Path(folder); folder.mkdir(parents=True, exist_ok=True)
    idx_path = folder / "index.json"
    idx = json.loads(idx_path.read_text()) if idx_path.exists() else {"photos": {}, "blocked": [], "errors": []}
    seen = {v["url"] for v in idx["photos"].values()}
    skip = re.compile(r"\.js|push|viewus|adserver|doubleclick|logo|icon|banner|btn|button|/ad[s_/]|profile|sprite|emoji|poll|thumb.*-\d{2,3}x\d{2,3}\.|-\d{3}x\d{3}\.", re.I)

    def note_block(url, e):
        host = urllib.parse.urlparse(url).netloc
        if "403" in str(e) or "Tunnel" in str(e):
            if host not in idx["blocked"]:
                idx["blocked"].append(host)
        else:
            idx["errors"].append(f"{url}: {e}")

    for page in pages:
        try:
            req = urllib.request.Request(page, headers={"User-Agent": UA})
            doc = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "replace")
        except Exception as e:
            note_block(page, e)
            continue
        urls = re.findall(r'(?:src|data-src|data-original|content)="([^"]+?\.(?:jpe?g|png|webp)[^"]*)"', doc, re.I)
        for u in dict.fromkeys(urllib.parse.urljoin(page, u.replace("&amp;", "&")) for u in urls):
            if u in seen or skip.search(u):
                continue
            seen.add(u)
            try:
                req = urllib.request.Request(u, headers={"User-Agent": UA, "Referer": page})
                data = urllib.request.urlopen(req, timeout=25).read()
                im = Image.open(io.BytesIO(data)).convert("RGB")
            except Exception as e:
                note_block(u, e)
                continue
            if im.width < min_w:
                continue
            name = f"{len(idx['photos']) + 1:02d}.jpg"
            im.save(folder / name, quality=92)
            idx["photos"][name] = {"url": u, "page": page, "size": list(im.size)}
    idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=1))
    return idx


def sheet(folder, out, T=420):
    """사진마다 10% 격자(5·10은 빨간 선)를 그려 한 장으로 모은다. 크롭 비율을 정할 때 본다."""
    fs = sorted(p for p in pathlib.Path(folder).iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"))
    cols = 3
    rows = (len(fs) + cols - 1) // cols
    s = Image.new("RGB", (cols * T, rows * (T + 24)), "#222")
    d = ImageDraw.Draw(s)
    for k, f in enumerate(fs):
        im = Image.open(f).convert("RGB")
        size = im.size
        im.thumbnail((T - 8, T - 8))
        g = ImageDraw.Draw(im); w, h = im.size
        for i in range(1, 10):
            c = "red" if i == 5 else "yellow"
            g.line([(w * i / 10, 0), (w * i / 10, h)], fill=c); g.line([(0, h * i / 10), (w, h * i / 10)], fill=c)
            g.text((w * i / 10 + 2, 2), str(i), fill=c); g.text((2, h * i / 10 + 2), str(i), fill=c)
        x, y = (k % cols) * T, (k // cols) * (T + 24)
        s.paste(im, (x + 4, y + 4))
        d.text((x + 6, y + T + 4), f"{f.name} {size[0]}x{size[1]}", fill="#fff")
    s.save(out, quality=85)


if __name__ == "__main__":
    if sys.argv[1:2] == ["sheet"]:
        sheet(sys.argv[2], sys.argv[3])
    elif sys.argv[1:2] == ["scrape"]:
        r = scrape(sys.argv[2], sys.argv[3:])
        print(json.dumps({"photos": len(r["photos"]), "blocked": r["blocked"], "errors": len(r["errors"])}, ensure_ascii=False))
