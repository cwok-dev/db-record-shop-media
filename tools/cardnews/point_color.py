"""앨범 표지에서 포인트 컬러를 추출하고, 배경에 맞게 대비를 보정.

규칙
1. 표지에서 가장 많이 쓰인 유채색(프라이머리 컬러)을 쓴다. 무채색은 후순위.
2. 표지가 흑백이라 유채색이 없으면 표지의 블랙을 쓴다.
3. 배경 위에서 안 보이는 무채색은 바꾼다: 흰 배경 위의 흰색 → 블랙, 검은 배경 위의 어두운색 → 화이트.
4. 배경과의 명도 대비가 4.5:1 이상이 되도록, HSL의 L을 10씩 위아래로 옮겨
   기준을 넘는 색 중 원본에 가장 가까운 색을 쓴다.
5. 별점은 그림자 없이 색만으로 띄우므로 기준을 7:1로 높인다.
6. alt 배경은 글씨가 블랙일 때 L을 10 밝힌다.
"""
import colorsys
import sys
from PIL import Image

CHROMA_MIN = 0.18   # 이보다 채도가 낮으면 무채색으로 판단
SHARE_MIN = 0.02    # 팔레트 중 비중 2% 미만 색은 '표지에 쓰인 색'으로 보지 않음
CONTRAST_MIN = 4.5
CONTRAST_STAR = 7
ALT_LIFT = 0.1    # alt 배경(글씨 블랙)을 밝히는 양
WHITE, BLACK = "#ffffff", "#111111"


def _palette(path, size=8):
    img = Image.open(path).convert("RGB")
    img.thumbnail((200, 200))
    q = img.quantize(colors=size, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()
    total = img.width * img.height
    out = [(n / total, tuple(pal[i * 3: i * 3 + 3])) for n, i in q.getcolors()]
    return sorted(out, reverse=True)  # 많이 쓰인 순


def _hls(rgb):
    return colorsys.rgb_to_hls(*(c / 255 for c in rgb))


def _is_achromatic(rgb):
    _, l, s = _hls(rgb)
    return s < CHROMA_MIN or l < 0.08 or l > 0.94


def _hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*(round(c) for c in rgb))


def _rgb(hexstr):
    return tuple(int(hexstr[i:i + 2], 16) for i in (1, 3, 5))


def _lum(rgb):
    c = [x / 255 for x in rgb]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    la, lb = sorted([_lum(_rgb(a)), _lum(_rgb(b))], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def base_color(path):
    """보정 전 포인트 컬러: 가장 많이 쓰인 유채색, 없으면 표지의 블랙."""
    used = [c for s, c in _palette(path) if s >= SHARE_MIN]
    chroma = [c for c in used if not _is_achromatic(c)]
    if chroma:
        return _hex(chroma[0])
    return _hex(min(used, key=sum))


def fit_to_background(color, bg, minimum=CONTRAST_MIN):
    """배경 위에서 쓸 수 있도록 보정."""
    rgb = _rgb(color)
    if _is_achromatic(rgb):  # 흑백 표지: 배경 반대색
        return BLACK if _lum(_rgb(bg)) > 0.5 else WHITE
    if contrast(color, bg) >= minimum:
        return color
    h, l, s = _hls(rgb)
    for step in range(1, 11):  # L을 10씩(0.1) 위아래로
        hits = []
        for d in (-step * 0.1, step * 0.1):
            nl = l + d
            if 0 <= nl <= 1:
                cand = _hex(c * 255 for c in colorsys.hls_to_rgb(h, nl, s))
                if contrast(cand, bg) >= minimum:
                    hits.append(cand)
        if hits:  # 같은 거리면 대비가 더 큰 쪽
            return max(hits, key=lambda c: contrast(c, bg))
    return BLACK if _lum(_rgb(bg)) > 0.5 else WHITE


def point_colors(path, bg):
    """카드에 쓰는 포인트 컬러 2개.
    pt: 페이지 배경 위(트랙 그래픽 등) / pt_label: 흰 추천 스티커 위(테두리·글씨)"""
    base = base_color(path)
    return fit_to_background(base, bg), fit_to_background(base, WHITE)


def star_color(path, bg):
    """별점 색: 포인트 컬러를 페이지 배경 기준 7:1로 보정."""
    return fit_to_background(base_color(path), bg, CONTRAST_STAR)


def _adjust_steps(color, other):
    """color의 L을 10씩 옮겨 other와 4.5:1을 넘기는 가장 가까운 색과, 옮긴 단계 수."""
    if contrast(color, other) >= CONTRAST_MIN:
        return color, 0
    h, l, s = _hls(_rgb(color))
    for step in range(1, 11):
        hits = []
        for d in (-step * 0.1, step * 0.1):
            if 0 <= l + d <= 1:
                cand = _hex(c * 255 for c in colorsys.hls_to_rgb(h, l + d, s))
                if contrast(cand, other) >= CONTRAST_MIN:
                    hits.append(cand)
        if hits:
            return max(hits, key=lambda c: contrast(c, other)), step
    return None, 99


def alt_colors(path):
    """두 번째 게시물 커버용: 배경은 포인트 컬러, 글씨는 무채색.
    포인트 컬러를 기준으로 블랙/화이트 중 대비가 맞는 쪽을 고르고,
    둘 다 4.5:1에 못 미치면 포인트 컬러의 L을 가장 적게 옮기는 쪽을 택한다.
    글씨가 블랙이면 배경이 탁해 보이지 않도록 L을 ALT_LIFT만큼 밝힌다(대비도 함께 커진다)."""
    base = base_color(path)
    if _is_achromatic(_rgb(base)):  # 흑백 표지
        bg, ink = base, (WHITE if _lum(_rgb(base)) < 0.5 else BLACK)
    else:
        options = []
        for ink in (BLACK, WHITE):
            bg, steps = _adjust_steps(base, ink)
            if bg:
                options.append((steps, -contrast(bg, ink), bg, ink))
        _, _, bg, ink = min(options)
    if ink == BLACK:
        h, l, s = _hls(_rgb(bg))
        bg = _hex(c * 255 for c in colorsys.hls_to_rgb(h, min(1.0, l + ALT_LIFT), s))
    return bg, ink


if __name__ == "__main__":
    # python3 point_color.py <표지 이미지>  →  리뷰 페이지용 포인트 컬러 JSON
    import json
    path = sys.argv[1]
    light, _ = point_colors(path, WHITE)
    dark, _ = point_colors(path, BLACK)
    print(json.dumps({"base": base_color(path), "pointLight": light, "pointDark": dark}))
