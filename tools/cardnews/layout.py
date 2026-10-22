"""카드 레이아웃 (사양서 4장).

재료(모든 장 공통): 포인트 컬러 하나 + 잉크 + 종이 회색, 하프톤 사진, 검은 테두리 라벨, 글꼴 셋.
리듬: 트랙 카드는 타이포 카드와 사진 카드를 번갈아 둔다. 액센트: 장마다 소품 하나(소품색).

그리드 (1080x1350)
- 바깥 여백 M=48 (인스타 프로필 격자의 3:4 잘림 34px보다 안쪽)
- 가로 6칸: 칸 144, 사이 24, 내용 폭 984. 칸 시작 x = 48 + 168·i
- 세로 단위 8. 상단 라벨 y=48(높이 40), 제목 시작 y=136, 한 줄 평은 아래 48에 붙인다.
- 한 줄 평 폭은 4칸(648) 또는 6칸(984). 그림과 한 줄 평 사이는 48 이상.
- 제목과 한 줄 평 사이에 남는 세로 공간에서 그림 묶음은 가운데에 둔다.
- 별 터짐 모양은 추천 표시에만 쓴다.
"""
import colorsys, hashlib, html, math, pathlib
from point_color import base_color, contrast, _hls, _hex, _rgb, _is_achromatic

HERE = pathlib.Path(__file__).resolve().parent
W, H = 1080, 1350
M, COL, GUT = 48, 144, 24
X = [M + i * (COL + GUT) for i in range(6)]
TOP_HEAD, TOP_TITLE = 48, 136
INK, PAPER = "#111111", "#e6e6e2"
PINK, LIME = "#ff4f9a", "#d7ff3d"
SPOT_FALLBACK = "#ffd23f"  # 흑백 표지
TYPO = {"polaroid", "cutout", "grid"}
PHOTO = {"player", "full"}
BURST = ("polygon(50% 0,58% 30%,85% 12%,70% 40%,100% 45%,72% 58%,92% 85%,60% 70%,52% 100%,42% 72%,"
         "12% 90%,28% 60%,0 50%,28% 40%,10% 14%,40% 30%)")
STAR = "M50 4 L62 37 L97 38 L69 59 L79 93 L50 73 L21 93 L31 59 L3 38 L38 37 Z"
SPARK = "M50 0 C54 34 66 46 100 50 C66 54 54 66 50 100 C46 66 34 54 0 50 C34 46 46 34 50 0 Z"


def span(n):
    return n * COL + (n - 1) * GUT


def spot_color(cover):
    """포인트 컬러: 표지의 주 유채색과 같은 색상(H), 채도 0.6 이상, 잉크 글씨와 7:1 이상 되도록 밝힌다."""
    rgb = _rgb(base_color(cover))
    if _is_achromatic(rgb):
        return SPOT_FALLBACK
    h, l, s = _hls(rgb)
    s, l = max(s, 0.6), 0.6
    c = _hex(v * 255 for v in colorsys.hls_to_rgb(h, l, s))
    while contrast(c, INK) < 7 and l < 0.92:
        l += 0.03
        c = _hex(v * 255 for v in colorsys.hls_to_rgb(h, l, s))
    return c


def prop_color(spot):
    """소품색: 핫핑크. 포인트 컬러가 핑크 계열(색상 차 36° 미만)이면 라임."""
    h = _hls(_rgb(spot))[0]
    ph = _hls(_rgb(PINK))[0]
    d = min(abs(h - ph), 1 - abs(h - ph))
    return LIME if d < 0.1 else PINK


def esc(s):
    return html.escape(str(s or ""))


def split_lines(title, max_lines=2):
    """제목 줄바꿈: 짧으면 한 줄, 길면 단어 경계에서 두 줄로 고르게 나눈다."""
    words = title.split()
    if len(words) < 2 or len(title) <= 8 or max_lines < 2:
        return [title]
    best = min(range(1, len(words)), key=lambda i: max(len(" ".join(words[:i])), len(" ".join(words[i:]))))
    return [" ".join(words[:best]), " ".join(words[best:])]


def stars_svg(v, size, fill, empty, stroke, gap=8):
    out = []
    for i in range(5):
        f = round(max(0.0, min(1.0, (v or 0) - i)) * 2) / 2
        sid = f"s{i}{size}{fill[1:]}{empty[1:] if empty.startswith('#') else 'n'}"
        out.append(f"<svg width='{size}' height='{size}' viewBox='0 0 100 100' style='margin-right:{gap}px'>"
                   f"<defs><clipPath id='{sid}'><rect width='{100 * f}' height='100'/></clipPath></defs>"
                   f"<path d='{STAR}' fill='{empty}' stroke='{stroke}' stroke-width='4'/>"
                   f"<path d='{STAR}' fill='{fill}' clip-path='url(#{sid})'/></svg>")
    return "<div style='display:flex'>" + "".join(out) + "</div>"


def fonts_css():
    rows = [("Paperlogy", 600, "Paperlogy-6SemiBold.woff2"), ("Paperlogy", 800, "Paperlogy-8ExtraBold.woff2"),
            ("Paperlogy", 900, "Paperlogy-9Black.woff2"), ("SCDream", 300, "S-CoreDream-3Light.woff"),
            ("SCDream", 400, "S-CoreDream-4Regular.woff"), ("SCDream", 500, "S-CoreDream-5Medium.woff"),
            ("SCDream", 700, "S-CoreDream-6Bold.woff"), ("Chosun", 400, "ChosunGu.woff"),
            ("SpaceMono", 700, "SpaceMono-Bold.woff2")]
    return "".join(f"@font-face{{font-family:'{f}';font-weight:{w};src:url('{(HERE / 'fonts' / n).as_uri()}')}}" for f, w, n in rows)


GRAIN = ("url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'>"
         "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/>"
         "<feColorMatrix values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 .55 0'/></filter>"
         "<rect width='100%' height='100%' filter='url(%23n)'/></svg>\")")

# 제목 맞춤, 그림 묶음 배치, 추천 도장 위치를 브라우저에서 계산한다.
SCRIPT = """
function fit(){document.querySelectorAll('[data-fit]').forEach(el=>{const mw=+el.dataset.maxw,mh=+el.dataset.maxh;
 let fs=parseFloat(getComputedStyle(el).fontSize),g=0;
 while((el.scrollWidth>mw+1||el.getBoundingClientRect().height>mh+1)&&fs>28&&g++<300){fs-=2;el.style.fontSize=fs+'px';}})}
function zones(){const f=document.querySelector('.foot');const limit=f.getBoundingClientRect().top-48;const warn=[];
 document.querySelectorAll('[data-zone]').forEach(el=>{const mode=el.dataset.zone;
  if(mode==='center'||mode==='after'){const a=document.querySelector(el.dataset.after);const top0=a.getBoundingClientRect().bottom+48;
   el.style.top='0px';const h=el.getBoundingClientRect().height;let t=top0;
   if(mode==='center')t=top0+Math.max(0,(limit-top0-h)/2);el.style.top=Math.floor(t/8)*8+'px';}
  if(mode==='above-foot'){const h=el.getBoundingClientRect().height;el.style.top=Math.floor((limit-h)/8)*8+'px';}
  const r=el.getBoundingClientRect();if(r.bottom>limit+1){const s=Math.max(.45,(limit-r.top)/r.height);
   el.style.transformOrigin=el.dataset.origin||'top center';el.style.transform='scale('+s.toFixed(3)+')';warn.push(el.className+' 축소 '+s.toFixed(2));}});
 return warn}
function stamp(){const s=document.querySelector('.recst'),a=document.querySelector('.anchor');if(!s||!a)return;
 const r=a.getBoundingClientRect();let cx=r.left+.85*r.width,cy=r.top+.15*r.height;
 cx=Math.min(Math.max(cx,158),1080-158);cy=Math.min(Math.max(cy,236),1350-158);
 s.style.left=(cx-150)+'px';s.style.top=(cy-150)+'px';}
document.fonts.ready.then(()=>{fit();const w=zones();stamp();document.body.dataset.warn=w.join('; ');document.body.dataset.ready='1';});
"""


class Card:
    """카드 한 장의 값. img(w, h, cell)은 이 카드 사진 칸의 파일 URI를 돌려준다."""

    def __init__(self, *, kind, spec, spot, prop, artist, album, year, page, n=None, total=None, title="",
                 is_title=False, review=None, bg=None, img=None):
        self.__dict__.update(locals()); del self.__dict__["self"]

    @property
    def rec(self):
        return bool(self.review and self.review.get("rec"))


def base_css(c, bg):
    acc = c.prop
    return f"""{fonts_css()}
*{{margin:0;padding:0;box-sizing:border-box}} html,body{{width:{W}px;height:{H}px;overflow:hidden}}
body{{position:relative;background:{bg};font-family:'SCDream';word-break:keep-all}}
.abs{{position:absolute}} .grain{{position:absolute;inset:0;background:{GRAIN};pointer-events:none;opacity:.3}}
.mono{{font:700 22px/1 'SpaceMono';letter-spacing:.04em}}
.lbl{{display:inline-block;border:3px solid {INK};padding:8px 12px 6px;background:{PAPER};color:{INK}}}
.head{{left:{M}px;right:{M}px;top:{TOP_HEAD}px;display:flex;justify-content:space-between;gap:24px;z-index:6}}
.head .lbl{{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:760px}}
.foot{{left:{M}px;bottom:{M}px;z-index:6}}
.rate{{display:inline-flex;background:{INK};padding:14px 18px}}
.one{{background:{PAPER};border:3px solid {INK};padding:22px 26px;font:500 34px/1.5 'SCDream';color:{INK};margin-top:-3px}}
.one.ph{{color:#8c8c8c;font-weight:400}}
.recst{{position:absolute;width:300px;height:300px;transform:rotate(-12deg);z-index:7}}
.recst .sh,.recst .ol,.recst .fg{{position:absolute;clip-path:{BURST}}}
.recst .sh{{inset:0;background:{INK};transform:translate(10px,10px)}}
.recst .ol{{inset:-6px;background:{INK}}} .recst .fg{{inset:0;background:{acc}}}
.recst .tx{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff}}
.recst .tx b{{font:400 92px/1 'Chosun';-webkit-text-stroke:10px {INK};paint-order:stroke fill;letter-spacing:-.02em}}
.recst .tx i{{font:700 20px/1 'SpaceMono';font-style:normal;color:{INK};background:#fff;border:3px solid {INK};padding:5px 8px 3px;margin-bottom:8px}}
.tape{{position:absolute;width:120px;height:40px;background:{acc};opacity:.92;border:2px solid {INK}}}
"""


def head(c, dark=False):
    style = f" style='background:{INK};color:{PAPER};border-color:{PAPER}'" if dark else ""
    left = "DB RECORD SHOP" if c.kind == "album" else f"{c.artist} — {c.album} · TRACK {c.n:02d}"
    return f"<div class='abs head mono'><span class='lbl'{style}>{esc(left)}</span><span class='lbl'{style}>{esc(c.page)}</span></div>"


def foot(c, wide=False, dark=False):
    w = span(6 if wide else 4)
    b = f"border:3px solid {PAPER};" if dark else ""
    if c.review:
        rate = stars_svg(c.review.get("stars"), 54, c.spot, INK, c.spot)
        one = f"<div class='one'>{esc(c.review.get('oneline'))}</div>"
    else:  # 아침 시안: 리뷰 작성 전
        rate = stars_svg(0, 54, c.spot, INK, c.spot)
        one = "<div class='one ph'>한 줄 평은 리뷰를 쓰고 나면 이 자리에 들어갑니다.</div>"
    return f"<div class='abs foot' style='width:{w}px'><div class='rate' style='{b}'>{rate}</div>{one}</div>"


def rec_stamp(c):
    if not c.rec:
        return ""
    return ("<div class='recst' style='left:0;top:0'><div class='sh'></div><div class='ol'></div><div class='fg'></div>"
            "<div class='tx'><i>DB PICK</i><b>추천</b></div></div>")


def typo_colors(bg):
    """타이포 카드: 배경별 제목색. 잉크 배경에서는 포인트 컬러 제목이 사진 위에서 반전된다."""
    return {"ink": ("spot", "difference"), "paper": ("ink", "normal"), "spot": ("ink", "normal")}[bg]


def resolve(c, name):
    return {"ink": INK, "paper": PAPER, "spot": c.spot}[name]


def title_block(c, size, maxw, maxh, color, blend="normal", left=M - 8, top=TOP_TITLE - 16, lh=.84):
    lines = "<br>".join(esc(x) for x in (c.spec.get("lines") or split_lines(c.title)))
    return (f"<div class='abs title' data-fit data-maxw='{maxw}' data-maxh='{maxh}' style='left:{left}px;top:{top}px;"
            f"font:900 {size}px/{lh} Paperlogy;letter-spacing:-.05em;color:{color};mix-blend-mode:{blend};width:max-content;z-index:4'>{lines}</div>")


def label_title(c, size, maxw, maxh, top):
    spans = "<br>".join(f"<span class='lbl' style='background:{c.spot};padding:14px 22px 2px;margin-bottom:-3px'>{esc(x)}</span>"
                        for x in (c.spec.get("lines") or split_lines(c.title)))
    return (f"<div class='abs title' data-fit data-maxw='{maxw}' data-maxh='{maxh}' style='left:{M}px;top:{top}px;"
            f"font:900 {size}px/1 Paperlogy;letter-spacing:-.03em;line-height:0;width:max-content;z-index:4'>"
            f"<div style='line-height:1'>{spans}</div></div>")


# ---------- 템플릿 ----------

def t_glyph(c):
    """앨범 카드: 앨범명 첫 글자가 곧 그림. 글자 안의 사진이 '이 앨범 = 이 사람들'을 말한다."""
    main = c.bg != "ink"
    bg = c.spot if main else INK
    stroke = INK if main else PAPER
    g = next((ch for ch in c.album if ch.isalnum()), "?")
    sub = f"{c.spec.get('type', '')}"
    css = f"""
.G{{left:0;top:0;width:{W}px;height:{H}px;padding:{TOP_TITLE + 26}px 0 0 {M - 16}px;font:900 940px/.78 'Paperlogy';letter-spacing:-.06em;
background:{PAPER} url('{c.img(W, H)}') 0 0/{W}px {H}px;-webkit-background-clip:text;background-clip:text;color:transparent;-webkit-text-stroke:4px {stroke}}}
.name{{right:{M}px;top:{TOP_TITLE}px;text-align:right;z-index:4}}
.name .big{{font:900 96px/1 'Paperlogy';padding:10px 18px 4px}}
.type{{display:inline-block;margin-top:24px;background:{c.prop};border:3px solid {INK};box-shadow:6px 6px 0 {INK};padding:10px 16px 8px;font:700 28px 'SCDream';transform:rotate(-4deg)}}
"""
    body = f"""<div class='grain'></div><div class='abs G'>{esc(g)}</div>{head(c, dark=not main)}
<div class='abs name'><div data-fit data-maxw='560' data-maxh='140' class='lbl big' style='width:max-content;margin-left:auto'>{esc(c.artist)}</div>
<div class='lbl' style='font:700 26px SCDream;padding:10px 14px 8px;margin-top:-3px'>{esc(c.album)} · {esc(c.spec.get('date', ''))}</div><br>
<div class='type'>{esc(sub)}</div></div>{foot(c, dark=not main)}"""
    return bg, css, body


def t_polaroid(c):
    """타이포 카드 + 테이프로 붙인 폴라로이드: 기념사진처럼 남겨 둘 장면(첫 곡, 출발, 기억 등)."""
    bgname = c.bg or "paper"
    bg = resolve(c, bgname)
    color = resolve(c, typo_colors(bgname)[0])
    w = span(3)
    css = f"""
.zone{{left:{X[3]}px;width:{w}px}}
.pol{{position:relative;padding:14px 14px 54px;background:#fff;border:3px solid {INK};box-shadow:8px 8px 0 {INK};transform:rotate(4deg)}}
.pol .ph{{height:296px;background:{PAPER} url('{c.img(w - 28, 296)}') 0 0/cover;border:2px solid {INK}}}
.pol p{{position:absolute;left:18px;bottom:14px;font:700 20px 'SpaceMono'}}
"""
    body = f"""<div class='grain'></div>{title_block(c, 250, 992, 430, color)}
<div class='abs zone' data-zone='center' data-after='.title' data-origin='top right'><div class='pol anchor'><div class='ph'></div>
<p>{esc(c.artist)} — {esc(c.year)}</p></div>
<div class='tape' style='left:-34px;top:-8px;transform:rotate(-24deg)'></div><div class='tape' style='right:-14px;top:12px;transform:rotate(30deg)'></div></div>
{head(c, dark=bgname == 'ink')}{foot(c, wide=c.spec.get('wide', False), dark=bgname == 'ink')}"""
    return bg, css, body


def t_cutout(c):
    """타이포 카드 + 모양으로 오린 사진: 제목·소개 속 사물(달, 해, 창, 무대)을 모양으로 옮긴다."""
    bgname = c.bg or "ink"
    bg = resolve(c, bgname)
    color_name, blend = typo_colors(bgname)
    ring = c.spot if bgname != "spot" else INK
    d = span(4)
    shape = c.spec.get("shape", "circle")
    radius = {"circle": "50%", "arch": f"{d // 2}px {d // 2}px 0 0", "frame": "0"}[shape]
    css = f"""
.shape{{left:{W - M - d}px;top:{TOP_TITLE + 160}px;width:{d}px;height:{d}px;border-radius:{radius};
background:{PAPER} url('{c.img(d, d)}') 0 0/cover;box-shadow:0 0 0 16px {ring}}}
"""
    # 잉크 배경: 제목이 사진 위에서 반전되며 겹친다. 그 밖의 배경: 겹치면 읽기 어려워 제목 아래 남는 공간 가운데에 둔다.
    zone = "data-zone='fixed'" if bgname == "ink" else "data-zone='center' data-after='.title'"
    body = f"""<div class='abs shape anchor' {zone} data-origin='top right'></div>
{title_block(c, 236, 992, 410, resolve(c, color_name), blend)}<div class='grain' style='opacity:.25'></div>
{head(c, dark=bgname == 'ink')}{foot(c, wide=c.spec.get('wide', False), dark=bgname == 'ink')}"""
    return bg, css, body


def t_grid(c):
    """타이포 카드 + 같은 사진 18칸 중 한 칸만 짚기: 반복·흔함·버전 차이(반주곡, 리믹스, 다른 언어)."""
    bgname = c.bg or "spot"
    bg = resolve(c, bgname)
    color = resolve(c, typo_colors(bgname)[0])
    main, _, rest = c.title.partition("(")
    sub = f"({rest}" if rest else f"TRACK {c.n:02d}"
    th = 108
    h = int(hashlib.sha1(c.title.encode()).hexdigest(), 16)
    pick = (1, 1 + h % 4)
    tile = c.img(COL, th, 4)
    tiles = "".join(
        f"<div class='tile{' on anchor' if (r, k) == pick else ''}' style='left:{X[k] - M}px;top:{r * (th + GUT)}px'></div>"
        for r in range(3) for k in range(6))
    px = X[pick[1]] - M + COL + GUT
    css = f"""
.sub{{left:{M}px;z-index:4}} .sub .lbl{{font:900 64px/1 'Paperlogy';padding:10px 16px 2px}}
.zone{{left:{M}px;width:{span(6)}px;height:{3 * th + 2 * GUT}px}}
.tile{{position:absolute;width:{COL}px;height:{th}px;background:{PAPER} url('{tile}') 0 0/cover;border:3px solid {INK}}}
.tile.on{{background-color:{c.prop};background-blend-mode:multiply;border-width:6px;box-shadow:8px 8px 0 {INK};transform:scale(1.18);z-index:2}}
.pin{{position:absolute;left:{px}px;top:{pick[0] * (th + GUT) + 34}px;z-index:3;background:{c.prop};border:3px solid {INK};padding:8px 12px 6px;font:700 22px 'SpaceMono'}}
"""
    c2 = Card(**{**c.__dict__, "title": main.strip(), "spec": {k: v for k, v in c.spec.items() if k != "lines"}})
    body = f"""<div class='grain'></div>{title_block(c2, 300, 992, 260, color)}
<div class='abs sub' data-zone='after' data-after='.title'><span class='lbl'>{esc(sub)}</span></div>
<div class='abs zone' data-zone='center' data-after='.sub'>{tiles}<div class='pin'>◀ THIS ONE</div></div>
{head(c, dark=bgname == 'ink')}{foot(c, wide=c.spec.get('wide', True), dark=bgname == 'ink')}"""
    return bg, css, body


def t_player(c):
    """사진 카드 + 뮤직비디오 플레이어: 사진이 MV 장면일 때. 진행 막대 = 앨범 안에서 이 곡의 위치."""
    pct = c.n / c.total * 100
    css = f"""
.photo{{inset:0;background:url('{c.img(W, H)}') 0 0/cover;mix-blend-mode:multiply}}
.bar{{left:{M}px;right:{M}px;top:{TOP_HEAD}px;height:56px;background:{c.prop};border:3px solid {INK};box-shadow:6px 6px 0 {INK};display:flex;align-items:center;justify-content:space-between;gap:16px;padding:0 10px 0 16px;font:700 24px 'SpaceMono';color:{INK};z-index:6}}
.bar span:first-child{{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.bar i{{display:inline-block;width:34px;height:32px;border:3px solid {INK};background:{PAPER};font:700 18px/26px 'SpaceMono';text-align:center;font-style:normal;margin-left:6px}}
.flag{{left:{M}px;background:{INK};color:{c.spot};padding:8px 14px;z-index:4}}
.prog{{left:{M}px;right:{M}px;display:flex;align-items:center;gap:8px;z-index:4}}
.prog .k{{border:3px solid {INK};background:{PAPER};padding:6px 14px 4px;font:700 26px 'SpaceMono'}}
.rail{{flex:1;height:24px;border:3px solid {INK};background:{PAPER};position:relative;margin:0 16px}}
.fill{{position:absolute;left:0;top:0;bottom:0;width:{pct}%;background:{c.prop}}}
.headp{{position:absolute;left:calc({pct}% - 18px);top:-12px;width:36px;height:36px;border-radius:50%;background:#fff;border:4px solid {INK}}}
"""
    flag = ("TITLE · " if c.is_title else "") + f"TRACK {c.n:02d}"
    body = f"""<div class='abs photo'></div><div class='grain'></div>
<div class='abs bar'><span>{esc(c.title)} — MV · {esc(c.artist)}</span><span style='white-space:nowrap'>{esc(c.page)}&nbsp;<i>_</i><i>□</i><i>×</i></span></div>
{label_title(c, 190, 984, 440, TOP_TITLE + 16).replace("class='abs title'", "class='abs title anchor'")}
<div class='abs flag mono' data-zone='after' data-after='.title' style='margin-top:-32px'>{flag}</div>
<div class='abs prog' data-zone='above-foot'><span class='k'>◀◀</span><span class='k'>▶</span><span class='k'>▶▶</span>
<div class='rail'><div class='fill'></div><div class='headp'></div></div><span class='k'>{c.n:02d} / {c.total:02d}</span></div>
{foot(c, wide=c.spec.get('wide', True))}"""
    return PAPER, css, body


def prop_html(c, p, i):
    """사진 카드의 소품. sparkle: 반짝이 별 셋 / wave: 파형 / motif:<이름>: 37종 그래픽 액자."""
    if p == "sparkle":
        def star(x, y, s, r):
            return (f"<svg class='abs' style='left:{x}px;top:{y}px;transform:rotate({r}deg);z-index:5' width='{s}' height='{s}' viewBox='-4 -4 108 108'>"
                    f"<path d='{SPARK}' fill='{c.prop}' stroke='{INK}' stroke-width='{400 / s:.1f}'/></svg>")
        return star(X[4] + 24, TOP_TITLE + 16, 190, 8) + star(X[4] - 72, TOP_TITLE + 264, 90, -12) + star(X[5] + 40, TOP_TITLE + 330, 60, 20)
    if p == "wave":
        y0 = TOP_TITLE + 384
        pts = " ".join(f"{i / 120 * W:.0f},{y0 + 110 * math.exp(-((i - 60) / 28) ** 2) * math.sin(i * .9) * math.cos(i * .23):.0f}" for i in range(121))
        return (f"<svg class='abs' style='left:0;top:0;z-index:5' width='{W}' height='{H}'><polyline points='{pts}' fill='none' stroke='{INK}' stroke-width='16' stroke-linejoin='round'/>"
                f"<polyline points='{pts}' fill='none' stroke='{c.prop}' stroke-width='9' stroke-linejoin='round'/></svg>")
    if p.startswith("motif:"):
        import base64, graphics
        name = p.split(":", 1)[1]
        png = graphics.draw_png(name, c.title, INK, c.prop, style=graphics.STYLES_FOR[name][0], palette="mono")
        uri = "data:image/png;base64," + base64.b64encode(png).decode()
        return (f"<div class='abs' style='left:{X[4]}px;top:{TOP_TITLE + 16}px;width:{span(2)}px;height:{span(2)}px;border:3px solid {INK};"
                f"box-shadow:8px 8px 0 {INK};background:{INK} url({uri}) 0 0/cover;transform:rotate(3deg);z-index:5'></div>")
    return ""


def t_full(c):
    """사진 카드 + 소품: 사진 한 장이 곡의 장면일 때. 위 띠는 포인트 컬러, 소품은 곡의 근거 하나에서 고른다."""
    css = f"""
.photo{{inset:0;background:url('{c.img(W, H)}') 0 0/cover;mix-blend-mode:multiply}}
.band{{left:0;top:0;width:{W}px;height:{TOP_TITLE + 384}px;background:{c.spot};mix-blend-mode:multiply}}
"""
    props = "".join(prop_html(c, p, i) for i, p in enumerate(c.spec.get("props", [])))
    body = f"""<div class='abs photo'></div><div class='abs band'></div><div class='grain'></div>
{label_title(c, 140, 700 if c.spec.get('props') else 984, 360, TOP_TITLE).replace("class='abs title'", "class='abs title anchor'")}
{props}{head(c)}{foot(c, wide=c.spec.get('wide', False))}"""
    return PAPER, css, body


TEMPLATES = {"glyph": t_glyph, "polaroid": t_polaroid, "cutout": t_cutout, "grid": t_grid, "player": t_player, "full": t_full}


def page_html(c):
    bg, css, body = TEMPLATES[c.spec["template"]](c)
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{base_css(c, bg)}{css}</style></head>"
            f"<body>{body}{rec_stamp(c)}<script>{SCRIPT}</script></body></html>")


def render(cards, out_dir):
    """[(Card, 출력 png 경로)]를 렌더링하고 경고 목록을 돌려준다."""
    from playwright.sync_api import sync_playwright
    out_dir = pathlib.Path(out_dir)
    warns = {}
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        pg = b.new_page(viewport={"width": W, "height": H})
        for c, png in cards:
            f = out_dir / (pathlib.Path(png).stem + ".html")
            f.write_text(page_html(c), encoding="utf-8")
            pg.goto(f.as_uri())
            pg.wait_for_function("document.body.dataset.ready === '1'", timeout=30000)
            pg.wait_for_timeout(150)
            w = pg.evaluate("document.body.dataset.warn")
            if w:
                warns[pathlib.Path(png).name] = w
            pg.screenshot(path=str(png))
            f.unlink()
        b.close()
    return warns
