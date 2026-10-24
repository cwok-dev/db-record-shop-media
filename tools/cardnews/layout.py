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
TYPO = {"polaroid", "cutout", "grid", "serpent", "cinema"}
PHOTO = {"player", "full", "cctv"}
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
  const lim=el.dataset.over==='foot'?1350-48:limit;  // data-over=foot: 한 줄 평 아래로 깔려도 되고 바깥 여백만 지킨다
  const r=el.getBoundingClientRect();if(r.bottom>lim+1){const s=Math.max(.45,(lim-r.top)/r.height);
   el.style.transformOrigin=el.dataset.origin||'top center';el.style.transform='scale('+s.toFixed(3)+')';warn.push(el.className+' 축소 '+s.toFixed(2));}});
 return warn}
function stamp(){const s=document.querySelector('.recst'),a=document.querySelector('.anchor');if(!s||(!a&&s.dataset.pos!=='foot'))return;
 const r=a?a.getBoundingClientRect():{left:0,top:0,width:0,height:0,bottom:0};let cx=r.left+.85*r.width,cy=r.top+.15*r.height;
 if(s.dataset.pos==='below')cy=r.bottom+16+150;  // 사양 stamp: below → 주 그림 아래 16에 붙임
 if(s.dataset.pos==='foot'){const f=document.querySelector('.foot .one')||document.querySelector('.foot');const q=f.getBoundingClientRect();
  cx=q.right+16+150;cy=q.top+q.height/2;}  // 사양 stamp: foot → 한 줄 평 상자 오른쪽 16에 붙여 얼굴을 피함
 cx=Math.min(Math.max(cx,158),1080-158);cy=Math.min(Math.max(cy,236),1350-158);
 s.style.left=(cx-150)+'px';s.style.top=(cy-150)+'px';}
function band(){const b=document.querySelector('.band'),t=document.querySelector('.title');
 if(b&&t)b.style.height=Math.ceil((t.getBoundingClientRect().bottom+48)/8)*8+'px';}
document.fonts.ready.then(()=>{fit();band();const w=zones();stamp();document.body.dataset.warn=w.join('; ');document.body.dataset.ready='1';});
"""


class Card:
    """카드 한 장의 값. img(w, h, cell)은 이 카드 사진 칸의 파일 URI를 돌려준다."""

    def __init__(self, *, kind, spec, spot, prop, artist, album, year, page, n=None, total=None, title="",
                 is_title=False, review=None, bg=None, img=None, cover=None, blurb=None):
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
    pos = f" data-pos='{c.spec['stamp']}'" if c.spec.get("stamp") else ""
    return (f"<div class='recst'{pos} style='left:0;top:0'><div class='sh'></div><div class='ol'></div><div class='fg'></div>"
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


def spin_arcs(s, color):
    """LP 왼쪽 바깥의 호: 판이 도는 움직임(모션 라인). 판 중심을 공유하는 같은 굵기(4px)의 가는 호 6줄을 32 간격으로 긋는다.
    호의 양 끝이 두 직선 위에 놓이도록 길이를 정해, 바깥으로 갈수록 줄어드는 모양이 왼쪽을 향한 삼각형으로 보인다."""
    cx, cy, r0 = -s // 3 + s * 9 // 20, s // 20 + s * 9 // 20, s * 9 // 20
    rs = [r0 + 28 + 32 * i for i in range(6)]
    t1 = math.radians(60)  # 가장 안쪽 호의 반각
    x1, h1 = rs[0] * math.cos(t1), rs[0] * math.sin(t1)  # 판 중심에서 왼쪽으로 잰 거리, 위아래 높이
    xa = rs[-1] + 32  # 삼각형 꼭짓점: 가장 바깥 호 바로 왼쪽
    paths = []
    for r in rs:
        lo, hi = 0.0, t1  # 끝점이 꼭짓점과 안쪽 끝점을 잇는 직선 위에 오는 반각을 이분법으로(바깥 호는 안쪽보다 짧다)
        for _ in range(40):
            t = (lo + hi) / 2
            if r * math.sin(t) > h1 * (xa - r * math.cos(t)) / (xa - x1):
                hi = t
            else:
                lo = t
        x0, y0 = cx - r * math.cos(t), cy - r * math.sin(t)
        paths.append(f"<path d='M{x0:.0f} {y0:.0f} A{r} {r} 0 0 0 {x0:.0f} {2 * cy - y0:.0f}' stroke='{color}' stroke-width='4' fill='none' stroke-linecap='round'/>")
    return f"<svg style='position:absolute;left:0;top:0;overflow:visible' width='1' height='1'>{''.join(paths)}</svg>"


def t_sleeve(c):
    """앨범 카드: 실제 앨범 표지를 레코드 슬리브처럼 크게 놓고, 뒤로 LP가 비어져 나온다. 첫 장에서 어떤 앨범인지 바로 보인다.
    표지는 하프톤으로 바꾸지 않는다(앨범의 얼굴이라 원본 그대로)."""
    main = c.bg != "ink"
    bg = c.spot if main else INK
    s = 584  # 4칸(648)에서 라벨·한 줄 평 사이 공간에 맞춘 정사각(8의 배수)
    css = f"""
.name{{left:{M}px;top:{TOP_TITLE}px;z-index:4}}
.name .big{{font:900 96px/1 'Paperlogy';padding:10px 18px 4px}}
.type{{display:inline-block;margin-top:24px;background:{c.prop};border:3px solid {INK};box-shadow:6px 6px 0 {INK};padding:10px 16px 8px;font:700 28px 'SCDream';transform:rotate(-4deg)}}
.zone{{left:{W - M - s}px;width:{s}px;height:{s}px}}
.disc{{position:absolute;left:-{s // 3}px;top:{s // 20}px;width:{s * 9 // 10}px;height:{s * 9 // 10}px;border-radius:50%;
background:radial-gradient(circle,{c.spot} 0 15%,{INK} 15.5% 17%,transparent 17.5%),repeating-radial-gradient(circle,#1c1c1c 0 3px,#2a2a2a 3px 5px);
border:3px solid {INK};box-shadow:8px 8px 0 rgba(0,0,0,.35)}}
.sleeve{{position:absolute;inset:0;background:{PAPER} url('{c.cover}') 0 0/cover;border:3px solid {INK};box-shadow:10px 10px 0 {INK}}}
"""
    body = f"""<div class='grain'></div>{head(c, dark=not main)}
<div class='abs name'><div data-fit data-maxw='984' data-maxh='140' class='lbl big' style='width:max-content'>{esc(c.artist)}</div><br>
<div class='lbl' style='font:700 26px SCDream;padding:10px 14px 8px;margin-top:-3px'>{esc(c.album)} · {esc(c.spec.get('date', ''))}</div><br>
<div class='type'>{esc(c.spec.get('type', ''))}</div></div>
<div class='abs zone' data-zone='center' data-after='.name' data-origin='top right'>{spin_arcs(s, INK if main else PAPER)}<div class='disc'></div><div class='sleeve anchor'></div></div>
{foot(c, dark=not main)}"""
    return bg, css, body


def t_polaroid(c):
    """타이포 카드 + 테이프로 붙인 폴라로이드: 기념사진처럼 남겨 둘 장면(첫 곡, 출발, 기억 등).
    사진이 화면을 채우도록 크게(폭 720) 두고, 아래쪽은 한 줄 평 상자 밑으로 깔려도 된다."""
    bgname = c.bg or "paper"
    bg = resolve(c, bgname)
    color = resolve(c, typo_colors(bgname)[0])
    w, ph = 720, 520
    css = f"""
.zone{{left:{W - M - w}px;width:{w}px}}
.pol{{position:relative;padding:18px 18px 64px;background:#fff;border:3px solid {INK};box-shadow:8px 8px 0 {INK};transform:rotate(4deg)}}
.pol .ph{{height:{ph}px;background:{PAPER} url('{c.img(w - 36, ph)}') 0 0/cover;border:2px solid {INK}}}
.pol p{{position:absolute;right:22px;bottom:18px;font:700 24px 'SpaceMono'}}
"""
    body = f"""<div class='grain'></div>{title_block(c, 250, 992, 430, color)}
<div class='abs zone' data-zone='after' data-after='.title' data-over='foot' data-origin='top right'><div class='pol anchor'><div class='ph'></div>
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
    shape = c.spec.get("shape", "circle")
    d = span(4) if bgname == "ink" else span(3)  # 제목 아래에 놓일 때는 3칸(줄어들지 않게)
    big = shape == "circle" and bgname != "ink"  # 제목 아래 원: 크게(지름 720) 두고 한 줄 평 상자 밑으로 깔려도 된다
    if big:
        d = 720
    radius = {"circle": "50%", "arch": f"{d // 2}px {d // 2}px 0 0", "frame": "0", "wide": "0"}[shape]
    # wide: 사진 한 칸을 자르지 않고 화면 폭 전체에 띄운다(크롭 비율 그대로).
    w, h, x = (W, round(W * c.spec.get("aspect", .5)), 0) if shape == "wide" else (d, d, W - M - d)
    css = f"""
.shape{{left:{x}px;top:{TOP_TITLE + 160}px;width:{w}px;height:{h}px;border-radius:{radius};
background:{PAPER} url('{c.img(w, h)}') 0 0/cover;box-shadow:0 0 0 16px {ring}}}
"""
    # 잉크 배경: 제목이 사진 위에서 반전되며 겹친다. 그 밖의 배경: 겹치면 읽기 어려워 제목 아래 남는 공간 가운데에 둔다.
    zone = "data-zone='fixed'" if bgname == "ink" and shape != "wide" else "data-zone='center' data-after='.title'"
    if big:
        zone = "data-zone='after' data-after='.title' data-over='foot'"
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
    """사진 카드 + 소품: 사진 한 장이 곡의 장면일 때. 위 띠는 포인트 컬러(제목 아래 48까지), 소품은 곡의 근거 하나에서 고른다."""
    css = f"""
.photo{{inset:0;background:url('{c.img(W, H)}') 0 0/cover;mix-blend-mode:multiply}}
.band{{left:0;top:0;width:{W}px;height:{TOP_TITLE + 384}px;background:{c.spot};mix-blend-mode:multiply}}
"""
    props = "".join(prop_html(c, p, i) for i, p in enumerate(c.spec.get("props", [])))
    body = f"""<div class='abs photo'></div><div class='abs band'></div><div class='grain'></div>
{label_title(c, 140, 700 if c.spec.get('props') else 984, 360, TOP_TITLE).replace("class='abs title'", "class='abs title anchor'")}
{props}{head(c)}{foot(c, wide=c.spec.get('wide', False))}"""
    return PAPER, css, body


def t_serpent(c):
    """세리프 분할 + 뱀(레퍼런스 ②): 포인트 컬러 바탕에 거대한 제목을 두고, 가운데로 사진이 뱀처럼
    비스듬히 감긴다. 가로 종이 띠가 몸통을 끊는다. 곡선·뱀·휘감김이 제목에 있을 때(Cobra 등).
    배경은 포인트 컬러 고정(c.bg 무시)."""
    bg = c.spot
    w = span(3)
    x = (W - w) // 2
    uri = c.img(w, 760)
    css = f"""
.snake{{left:{x}px;top:{TOP_TITLE + 150}px;width:{w}px;height:760px;background:{PAPER} url('{uri}') 0 0/cover;
mix-blend-mode:multiply;border:3px solid {INK};box-shadow:12px 12px 0 rgba(0,0,0,.28);transform:rotate(-5deg);z-index:1}}
.bar{{left:{M}px;width:{span(6)}px;top:{TOP_TITLE + 452}px;background:{PAPER};border:3px solid {INK};box-shadow:8px 8px 0 {INK};
padding:18px 24px;z-index:3;display:flex;justify-content:space-between;align-items:center;font:700 26px 'SpaceMono';color:{INK};transform:rotate(-1.5deg)}}
.bar b{{font-weight:700}} .bar .dot{{width:18px;height:18px;background:{c.prop};border:3px solid {INK};border-radius:50%}}
.ghost{{left:{M - 8}px;bottom:{M + 180}px;font:900 230px/.8 'Paperlogy';letter-spacing:-.05em;color:{INK};opacity:.12;z-index:0;width:max-content}}
"""
    body = f"""<div class='grain'></div>
<div class='abs ghost'>{esc((c.spec.get('lines') or split_lines(c.title))[-1])}</div>
{title_block(c, 234, 992, 300, INK)}
<div class='abs snake'></div>
<div class='abs bar'><span><b>{esc(c.artist)}</b> — {esc(c.album)}</span><span style='display:flex;align-items:center;gap:12px'>TRK {c.n:02d}<span class='dot'></span></span></div>
{head(c)}{foot(c, wide=c.spec.get('wide', False))}"""
    return bg, css, body


def t_cinema(c):
    """시네마 선언문(레퍼런스 ③): 어두운 바탕에 거대한 포인트색 제목, 모노 카테고리 줄, 듀오톤 스틸과
    이름판, 조밀한 본문(곡 소개). 영화적 콘셉트·감독명이 제목일 때(Tarantino 등). 배경 잉크 고정."""
    bg = INK
    blurb = esc(c.blurb or "")
    sw, sh = span(3), 496
    uri = c.img(sw, sh)
    cats = " &nbsp;&nbsp;·&nbsp;&nbsp; ".join([esc(c.artist), esc(c.album), f"TRACK {c.n:02d}", esc(c.year)])
    css = f"""
.cats{{left:{M}px;top:{TOP_TITLE + 268}px;font:700 22px 'SpaceMono';letter-spacing:.04em;color:{c.spot};z-index:5}}
.rule{{left:{M}px;top:{TOP_TITLE + 252}px;width:{span(6)}px;height:3px;background:{c.spot};z-index:5}}
.still{{left:{M}px;top:{TOP_TITLE + 320}px;width:{sw}px;height:{sh}px;background:{c.spot};z-index:2;box-shadow:12px 12px 0 rgba(0,0,0,.5)}}
.still .ph{{position:absolute;inset:0;background:url('{uri}') 0 0/cover;mix-blend-mode:multiply}}
.still .plate{{position:absolute;left:8px;bottom:8px;background:{c.spot};color:{INK};font:900 46px/.9 'Paperlogy';letter-spacing:-.03em;padding:8px 12px 4px;z-index:3}}
.body{{left:{X[3]}px;top:{TOP_TITLE + 320}px;width:{span(3)}px;font:400 22px/1.56 'SCDream';color:{PAPER};text-align:justify;z-index:5}}
.body .lead{{color:{c.spot};font-weight:700}}
"""
    lead, _, rest = (blurb.partition("다.") if "다." in blurb else (blurb, "", ""))
    lead_html = f"<span class='lead'>{lead}{'다.' if rest else ''}</span>{rest}" if blurb else ""
    body = f"""<div class='grain' style='opacity:.5'></div>
{title_block(c, 168, 992, 250, c.spot)}
<div class='abs rule'></div><div class='abs cats'>{cats}</div>
<div class='abs still'><div class='ph'></div><div class='plate'>{esc(c.artist)}</div></div>
<div class='abs body'>{lead_html}</div>
{head(c)}{foot(c, wide=c.spec.get('wide', False))}"""
    return bg, css, body


def t_cctv(c):
    """CCTV 감지(레퍼런스 ⑥): 감시 모니터 프레임. 전면 하프톤 사진 위에 소품색 감지 박스와 모노 라벨,
    모서리 카메라 정보·타임스탬프·장면 번호. 거리·추적·포착 장면일 때(SaWaDiKa 등). 바탕 종이(사진 전면)."""
    bg = PAPER
    uri = c.img(W, H)
    code = hashlib.sha1((c.title + str(c.n)).encode()).hexdigest()[:5].upper()
    ts = f"{(13 + c.n) % 24:02d}:{(c.n * 7) % 60:02d}:{(c.n * 11) % 60:02d}"

    def det(x, y, w, h, label):
        corners = "".join(f"<i class='c {k}'></i>" for k in ("tl", "tr", "bl", "br"))
        return (f"<div class='abs det' style='left:{x}px;top:{y}px;width:{w}px;height:{h}px'>"
                f"<span class='tab'>{esc(label)}</span>{corners}</div>")

    boxes = (det(X[1], TOP_TITLE + 232, span(2) + 48, 336, "OBJECT ▸ " + c.title.upper())
             + det(X[4] - 16, TOP_TITLE + 712, span(2) + 16, 206, "ID ▸ #" + code))
    css = f"""
.photo{{inset:0;background:url('{uri}') 0 0/cover;mix-blend-mode:multiply}}
.scan{{position:absolute;inset:0;background:repeating-linear-gradient(to bottom,rgba(17,17,17,.10) 0 2px,transparent 2px 5px);z-index:3;pointer-events:none}}
.frame{{position:absolute;left:20px;top:20px;right:20px;bottom:20px;border:3px solid {INK};z-index:4;pointer-events:none}}
.frame::before,.frame::after{{content:'';position:absolute;width:26px;height:26px;border:4px solid {INK}}}
.frame::before{{left:-2px;top:-2px;border-right:0;border-bottom:0}} .frame::after{{right:-2px;bottom:-2px;border-left:0;border-top:0}}
.cv{{position:absolute;background:{PAPER};border:2px solid {INK};padding:8px 11px 6px;font:700 20px/1.35 'SpaceMono';color:{INK};letter-spacing:.02em;z-index:6}}
.cv .rec{{display:inline-block;width:14px;height:14px;border-radius:50%;background:{c.prop};margin-right:7px;vertical-align:0}}
.det{{position:absolute;border:3px solid {c.prop};z-index:5}}
.det .tab{{position:absolute;left:-3px;top:-33px;background:{c.prop};color:{INK};font:700 18px/1 'SpaceMono';padding:7px 10px 5px;white-space:nowrap}}
.det .c{{position:absolute;width:13px;height:13px;border:4px solid {c.prop}}}
.det .tl{{left:-4px;top:-4px;border-right:0;border-bottom:0}} .det .tr{{right:-4px;top:-4px;border-left:0;border-bottom:0}}
.det .bl{{left:-4px;bottom:-4px;border-right:0;border-top:0}} .det .br{{right:-4px;bottom:-4px;border-left:0;border-top:0}}
"""
    body = f"""<div class='abs photo'></div><div class='scan'></div><div class='grain' style='opacity:.3'></div><div class='frame'></div>
<div class='cv' style='left:44px;top:40px'><span class='rec'></span>CCTV {c.n:02d}<br>{esc(c.artist)} — {esc(c.album)}</div>
<div class='cv' style='right:44px;top:40px;text-align:right'>CAMERA {c.n} · {esc(c.page)}<br>{ts}</div>
<div class='cv' style='left:44px;top:138px'>{c.n:02d}/{c.total:02d} SCANNING…<br>▸ {esc(c.title)}</div>
{boxes}
{foot(c, wide=c.spec.get('wide', False))}"""
    return bg, css, body


TEMPLATES = {"sleeve": t_sleeve, "glyph": t_glyph, "polaroid": t_polaroid, "cutout": t_cutout, "grid": t_grid,
             "player": t_player, "full": t_full, "serpent": t_serpent, "cinema": t_cinema, "cctv": t_cctv}


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
