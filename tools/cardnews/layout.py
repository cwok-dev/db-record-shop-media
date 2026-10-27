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
TYPO = {"polaroid", "cutout", "grid", "serpent", "cinema", "gable", "motion"}
PHOTO = {"player", "full", "cctv", "clipboard", "desktop", "notch", "issue", "torn"}
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
function stamp(){const s=document.querySelector('.recst'),a=document.querySelector('.anchor'),at=document.querySelector('.stampat');
 if(!s||(!a&&!at&&!/^(foot|mid)/.test(s.dataset.pos||'')))return;
 const r=a?a.getBoundingClientRect():{left:0,top:0,width:0,height:0,bottom:0};let cx=r.left+.85*r.width,cy=r.top+.15*r.height;
 if(at&&!s.dataset.pos){const q=at.getBoundingClientRect();cx=q.left+q.width/2;cy=q.top+q.height/2;}  // 템플릿이 정한 도장 자리
 if(s.dataset.pos==='below')cy=r.bottom+16+150;  // 사양 stamp: below → 주 그림 아래 16에 붙임
 if(s.dataset.pos==='foot'||s.dataset.pos==='footup'){const f=document.querySelector('.foot .one')||document.querySelector('.foot');const q=f.getBoundingClientRect();
  cx=q.right+16+150;cy=q.top+q.height/2-(s.dataset.pos==='footup'?80:0);}  // 사양 stamp: foot → 한 줄 평 상자 오른쪽 16에 붙여 얼굴을 피함 / footup: 그보다 살짝 위
 if(s.dataset.pos==='mid'){cx=1080-48-150;cy=1350/2;}  // 사양 stamp: mid → 오른쪽 가장자리, 카드 세로 가운데(제목·라벨을 가리지 않게)
 cx=Math.min(Math.max(cx,158),1080-158);cy=Math.min(Math.max(cy,236),1350-158);
 s.style.left=(cx-150)+'px';s.style.top=(cy-150)+'px';
 // 자리를 지정하지 않은 도장이 제목·라벨 글자에 겹치면 한 줄 평 상자 옆(foot)으로 옮긴다(사용자 결정 2026-10-27)
 if(s.dataset.pos||!hitsText(s))return '';
 const f=document.querySelector('.foot .one')||document.querySelector('.foot');const q=f&&f.getBoundingClientRect();
 if(!q||q.right+16+300>1080-8)return '추천 도장이 제목에 겹침(한 줄 평 상자가 넓어 foot 불가)';
 s.style.left=(q.right+16)+'px';s.style.top=(Math.min(q.top+q.height/2,1350-158)-150)+'px';return '추천 도장 자동 foot';}
function hitsText(s){const b=s.getBoundingClientRect(),k=40;
 return [...document.querySelectorAll('.title,[data-fit],.head .lbl')].some(e=>{const r=e.getBoundingClientRect();
  return r.width&&b.left+k<r.right&&b.right-k>r.left&&b.top+k<r.bottom&&b.bottom-k>r.top;});}
function band(){const b=document.querySelector('.band'),t=document.querySelector('.title');
 if(b&&t)b.style.height=Math.ceil((t.getBoundingClientRect().bottom+48)/8)*8+'px';}
document.fonts.ready.then(()=>{fit();band();const w=zones();const sw=stamp();if(sw)w.push(sw);document.body.dataset.warn=w.join('; ');document.body.dataset.ready='1';});
"""


class Card:
    """카드 한 장의 값. img(w, h, cell)은 이 카드 사진 칸의 파일 URI를 돌려준다.
    tracks: 앨범 카드에서 수록곡 [(번호, 제목, 타이틀곡 여부)]."""

    def __init__(self, *, kind, spec, spot, prop, artist, album, year, page, n=None, total=None, title="",
                 is_title=False, review=None, bg=None, img=None, cover=None, blurb=None, tracks=None):
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
.one.empty{{color:#8c8c8c;font-weight:400}}
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
        one = "<div class='one empty'>한 줄 평은 리뷰를 쓰고 나면 이 자리에 들어갑니다.</div>"
    return f"<div class='abs foot' style='width:{w}px'><div class='rate' style='{b}'>{rate}</div>{one}</div>"


def rec_stamp(c):
    if not c.rec:
        return ""
    stamp = c.spec.get("stamp") or {"cctv": "footup", "player": "mid"}.get(c.spec["template"])  # cctv: 왼쪽 위 라벨을 가리지 않게(사용자 결정 2026-10-24) / player: 제목을 가리지 않게 세로 가운데(사용자 결정 2026-10-25)
    pos = f" data-pos='{stamp}'" if stamp else ""
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
    arc = ""
    if big:  # 원 둘레 왼쪽 위를 따라 휘는 문구: 곡 소개 첫 문장(없으면 가수·앨범·트랙). 레퍼런스: Unique 포스터
        text = first_sentence(c.blurb) or f"{c.artist} — {c.album} · TRACK {c.n:02d}"
        R, pad = d // 2 + 44, 80
        col = INK if bgname != "ink" else c.spot
        arc = (f"<svg style='position:absolute;left:-{pad}px;top:-{pad}px;overflow:visible' width='{d + 2 * pad}' height='{d + 2 * pad}'>"
               f"<path id='arc' d='M{d // 2 + pad} {d // 2 + pad - R} A{R} {R} 0 1 1 {d // 2 + pad - .1} {d // 2 + pad - R}' fill='none'/>"
               f"<text style='font:700 30px SCDream;fill:{col};letter-spacing:.02em'><textPath href='#arc' startOffset='74%'>{esc(text)}</textPath></text></svg>")
    body = f"""<div class='abs shape anchor' {zone} data-origin='top right'>{arc}</div>
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
    """사진 카드의 소품. sparkle: 반짝이 별 셋 / wave: 파형 / zoom: 별 모양 확대 액자 셋 / motif:<이름>: 37종 그래픽 액자."""
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
    if p == "zoom":  # 별 모양 액자에 사진 일부를 확대(레퍼런스: DANG 포스터). 자리는 사양 zooms로
        pts = ",".join(f"{x}% {y}%" for x, y in ((50, 4), (62, 37), (97, 38), (69, 59), (79, 93), (50, 73), (21, 93), (31, 59), (3, 38), (38, 37)))
        z = zooms(c, [[.3, .08, .7, .4], [.15, .45, .55, .75], [.5, .45, .9, .8]])
        def star(x, y, s, r, sub):
            return (f"<div class='abs' style='left:{x}px;top:{y}px;width:{s}px;height:{s}px;transform:rotate({r}deg);z-index:5;clip-path:polygon({pts});background:{INK}'>"
                    f"<div style='position:absolute;inset:0;clip-path:polygon({pts});transform:scale(.9);background:{c.prop}'></div>"
                    f"<div style='position:absolute;inset:0;clip-path:polygon({pts});transform:scale(.82);background:{PAPER} url(\"{c.img(s, s, sub=sub)}\") 0 0/cover'></div></div>")
        return star(X[3] + 20, TOP_TITLE + 400, 340, 8, z[0]) + star(M - 10, TOP_TITLE + 560, 250, -14, z[1]) + star(X[4] + 10, TOP_TITLE + 700, 220, 18, z[2])
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
    비스듬히 감긴다. 곡선·뱀·휘감김이 제목에 있을 때(Cobra 등). 추천 도장은 사진 몸통 가운데 높이의 오른쪽
    (예전 트랙 정보 띠 자리, 사용자 결정 2026-10-24). 배경은 포인트 컬러 고정(c.bg 무시)."""
    bg = c.spot
    w = span(3)
    x = (W - w) // 2
    uri = c.img(w, 760)
    css = f"""
.snake{{left:{x}px;top:{TOP_TITLE + 150}px;width:{w}px;height:760px;background:{PAPER} url('{uri}') 0 0/cover;
mix-blend-mode:multiply;border:3px solid {INK};box-shadow:12px 12px 0 rgba(0,0,0,.28);transform:rotate(-5deg);z-index:1}}
.ghost{{left:{M - 8}px;bottom:{M + 180}px;font:900 230px/.8 'Paperlogy';letter-spacing:-.05em;color:{INK};opacity:.12;z-index:0;width:max-content}}
"""
    body = f"""<div class='grain'></div>
<div class='abs ghost'>{esc((c.spec.get('lines') or split_lines(c.title))[-1])}</div>
{title_block(c, 234, 992, 300, INK)}
<div class='abs snake'></div>
<div class='abs stampat' style='left:{W - M - 300}px;top:{TOP_TITLE + 337}px;width:300px;height:300px'></div>
{head(c)}{foot(c, wide=c.spec.get('wide', False))}"""
    return bg, css, body


def t_cinema(c):
    """시네마 선언문(레퍼런스 ③): 어두운 바탕에 거대한 포인트색 제목, 모노 카테고리 줄, 내용 폭 전체의
    2.39:1 시네마스코프 듀오톤 스틸과 이름판(곡 소개 본문은 빼고 영화 화면 비율로, 사용자 결정 2026-10-24).
    영화적 콘셉트·감독명이 제목일 때(Tarantino 등). 배경 잉크 고정."""
    bg = INK
    sw = span(6)
    sh = round(sw / 2.39)
    uri = c.img(sw, sh)
    cats = " &nbsp;&nbsp;·&nbsp;&nbsp; ".join([esc(c.artist), esc(c.album), f"TRACK {c.n:02d}", esc(c.year)])
    css = f"""
.cats{{left:{M}px;top:{TOP_TITLE + 268}px;font:700 22px 'SpaceMono';letter-spacing:.04em;color:{c.spot};z-index:5}}
.rule{{left:{M}px;top:{TOP_TITLE + 252}px;width:{span(6)}px;height:3px;background:{c.spot};z-index:5}}
.still{{left:{M}px;top:{TOP_TITLE + 320}px;width:{sw}px;height:{sh}px;background:{c.spot};z-index:2;box-shadow:12px 12px 0 rgba(0,0,0,.5)}}
.still .ph{{position:absolute;inset:0;background:url('{uri}') 0 0/cover;mix-blend-mode:multiply}}
.still .plate{{position:absolute;left:8px;bottom:8px;background:{c.spot};color:{INK};font:900 46px/.9 'Paperlogy';letter-spacing:-.03em;padding:8px 12px 4px;z-index:3}}
"""
    body = f"""<div class='grain' style='opacity:.5'></div>
{title_block(c, 168, 992, 250, c.spot)}
<div class='abs rule'></div><div class='abs cats'>{cats}</div>
<div class='abs still anchor'><div class='ph'></div><div class='plate'>{esc(c.artist)}</div></div>
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

def zooms(c, defaults):
    """사양 "zooms"(사진 안의 확대할 부분, 비율 [x0, y0, x1, y1] 목록). 빈 자리는 템플릿 기본값."""
    z = c.spec.get("zooms") or []
    return [z[i] if i < len(z) and z[i] else d for i, d in enumerate(defaults)]


def tighten(r, f):
    """확대 영역 r을 가운데를 기준으로 f배로 좁힌다(더 줌인)."""
    cx, cy, hw, hh = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2, (r[2] - r[0]) * f / 2, (r[3] - r[1]) * f / 2
    return [cx - hw, cy - hh, cx + hw, cy + hh]


def first_sentence(text):
    """곡 소개의 첫 문장."""
    import re
    t = " ".join((text or "").split())
    m = re.match(r"(.+?[.!?。])(\s|$)", t)
    return m.group(1) if m else t


def t_gable(c):
    """타이포 카드 + 지붕 모양 사진: 거대한 제목 아래로 사진이 박공지붕(오각형)으로 잘려 화면 아래를 가장자리까지 채우고,
    지붕 꼭대기가 제목 둘째 줄로 파고든다. 집·방·공간·장소가 제목이나 소개에 있을 때. 레퍼런스: 모델하우스 포스터."""
    bgname = c.bg or "paper"
    bg = resolve(c, bgname)
    color_name, blend = typo_colors(bgname)
    peak, base, px = TOP_TITLE + 200, TOP_TITLE + 430, X[2] + 40  # 지붕 꼭대기 y, 처마 y, 꼭대기 x
    h = H - peak
    css = f"""
.roof{{left:0;top:{peak}px;width:{W}px;height:{h}px;background:{PAPER} url('{c.img(W, h)}') 0 0/cover;
clip-path:polygon(0 {base - peak}px,{px}px 0,{W}px {base - peak}px,{W}px 100%,0 100%)}}
.eave{{left:0;top:{peak}px;width:{W}px;height:{base - peak}px;z-index:3}}
.info{{right:{M}px;top:{base + 32}px;text-align:right;z-index:5}}
.info .lbl{{display:table;margin-left:auto;margin-bottom:-3px;font:700 24px 'SpaceMono'}}
"""
    edge = f"<svg class='abs eave' viewBox='0 0 {W} {base - peak}' preserveAspectRatio='none'><polyline points='0,{base - peak} {px},2 {W},{base - peak}' fill='none' stroke='{c.spot if bgname != 'spot' else INK}' stroke-width='12'/></svg>"
    body = f"""<div class='abs roof anchor'></div>{edge}<div class='grain' style='opacity:.25'></div>
{title_block(c, 250, 992, 430, resolve(c, color_name), blend)}
<div class='abs info'><span class='lbl' style='background:{c.prop}'>TRACK {c.n:02d}</span><span class='lbl'>{esc(c.artist)} · {esc(c.year)}</span></div>
{head(c, dark=bgname == 'ink')}{foot(c, wide=c.spec.get('wide', False), dark=bgname == 'ink')}"""
    return bg, css, body


def t_clipboard(c):
    """사진 카드 + 벽에 집게로 찍은 종이: 종이 위 하프톤 사진, 클립, 소품색·잉크 이름판(TRACK/제목).
    이름판은 아래 끝을 사진 아래 끝에 맞추고 오른쪽으로 비어져 나온다(사용자 결정 2026-10-24). 레퍼런스: Q&A 메모지."""
    sx, sy, sw, sh = 72, 112, 936, 940  # 종이
    pw, ph = 760, 812  # 사진: 종이 아래 여백 68
    css = f"""
body{{background:#d9d9d4}}
.sheet{{left:{sx}px;top:{sy}px;width:{sw}px;height:{sh}px;background:#f3f3ef;border:3px solid {INK};box-shadow:10px 10px 0 rgba(0,0,0,.25);transform:rotate(-1deg)}}
.ph{{left:{sx + 56}px;top:{sy + 60}px;width:{pw}px;height:{ph}px;background:{PAPER} url('{c.img(pw, ph)}') 0 0/cover;border:3px solid {INK};transform:rotate(-1deg)}}
.plate{{right:{W - (sx + 56 + pw) - 120}px;bottom:{H - (sy + 60 + ph)}px;z-index:4;text-align:right;transform:rotate(-1deg);transform-origin:bottom right}}
.plate .a{{display:inline-block;background:{c.prop};border:3px solid {INK};font:700 30px 'SpaceMono';padding:10px 16px 6px}}
.plate .b{{display:block;width:max-content;margin-left:auto;margin-top:-3px;background:{INK};color:{PAPER};font:900 92px/1 Paperlogy;letter-spacing:-.03em;padding:18px 26px 10px}}
.clip{{left:{W // 2 - 70}px;top:{sy - 50}px;z-index:6}} .pclip{{left:{sx + sw - 130}px;top:{sy - 30}px;z-index:6;transform:rotate(18deg)}}
"""
    clip = (f"<svg class='abs clip' width='140' height='100' viewBox='0 0 140 100'><path d='M30 4 L50 60 M110 4 L90 60' stroke='#777' stroke-width='6' fill='none'/>"
            f"<path d='M10 52 H130 L120 96 H20 Z' fill='{INK}'/><rect x='10' y='52' width='120' height='10' fill='#333'/></svg>")
    pclip = (f"<svg class='abs pclip' width='70' height='170' viewBox='0 0 70 170'><path d='M20 150 V30 a15 15 0 0 1 30 0 V140 a10 10 0 0 1 -20 0 V45' "
             f"stroke='#8a8a86' stroke-width='6' fill='none' stroke-linecap='round'/></svg>")
    body = f"""<div class='grain' style='opacity:.4'></div><div class='abs sheet'></div><div class='abs ph anchor'></div>
<div class='abs plate'><span class='a'>TRACK {c.n:02d}</span><span class='b' data-fit data-maxw='{W - 2 * M - 200}' data-maxh='140'>{esc(c.title)}</span></div>{clip}{pclip}
{head(c)}{foot(c, wide=c.spec.get('wide', False))}"""
    return "#d9d9d4", css, body


def t_desktop(c):
    """사진 카드 + 컴퓨터 화면 콜라주: 사진을 바탕화면처럼 깔고, 같은 사진의 다른 부분을 확대한 사진 창 셋을 겹친다.
    검색창에 곡 제목, 폴더 둘(앨범·트랙), 메뉴 목록. 창틀은 우리 재료(3px 테두리·종이 제목줄). 검색·파일·화면·온라인일 때.
    레퍼런스: 데스크톱 화면 콜라주."""
    def win(x, y, w, h, sub, name, z):
        return (f"<div class='abs win' style='left:{x}px;top:{y}px;width:{w}px;z-index:{z}'><div class='tb'><span>{esc(name)}</span>"
                f"<span><i>_</i><i>□</i><i>×</i></span></div><div style='height:{h}px;background:{PAPER} url(\"{c.img(w - 6, h, sub=sub)}\") 0 0/cover'></div></div>")
    def folder(x, y, label):
        return (f"<div class='abs fd' style='left:{x}px;top:{y}px'><svg width='130' height='100' viewBox='0 0 130 100'><path d='M4 18 h44 l10 12 h68 v66 H4 Z' "
                f"fill='{c.prop}' stroke='{INK}' stroke-width='4'/></svg><span>{esc(label)}</span></div>")
    css = f"""
.photo{{inset:0;background:url('{c.img(W, H)}') 0 0/cover;mix-blend-mode:multiply}}
.win{{border:3px solid {INK};box-shadow:8px 8px 0 {INK};background:{PAPER}}}
.win .tb{{display:flex;justify-content:space-between;align-items:center;height:44px;padding:0 8px 0 14px;border-bottom:3px solid {INK};font:700 20px 'SpaceMono'}}
.win .tb i{{display:inline-block;width:28px;height:26px;border:3px solid {INK};font:700 16px/20px 'SpaceMono';text-align:center;font-style:normal;margin-left:5px}}
.search{{left:{X[2]}px;top:{TOP_TITLE + 8}px;right:{M}px;height:96px;background:{PAPER};border:3px solid {INK};box-shadow:8px 8px 0 {INK};
display:flex;align-items:center;gap:18px;padding:0 24px;z-index:6}}
.search b{{font:900 54px/1 Paperlogy;letter-spacing:-.03em;background:{c.prop};padding:8px 6px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:560px}}
.search u{{width:4px;height:58px;background:{INK}}}
.fd{{z-index:4;text-align:center;width:150px}} .fd span{{display:inline-block;background:{PAPER};border:2px solid {INK};font:700 18px 'SpaceMono';padding:5px 8px 3px;margin-top:4px;max-width:150px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.menu{{left:{M}px;top:{TOP_TITLE + 380}px;width:260px;background:{PAPER};border:3px solid {INK};box-shadow:6px 6px 0 {INK};z-index:7;font:500 24px/1 SCDream;padding:8px 0}}
.menu div{{padding:11px 18px}} .menu .on{{background:{INK};color:{PAPER}}} .menu hr{{border:0;border-top:2px solid {INK};margin:6px 0}}
"""
    z = zooms(c, [[.1, .02, .9, .7], [.45, .1, 1, .75], [.15, .5, .85, 1]])
    menu = (f"<div class='abs menu'><div>열기</div><div class='on'>다시 듣기</div><div>앨범에 추가</div><hr><div>정보 보기</div><div>공유</div></div>")
    body = f"""<div class='abs photo'></div><div class='grain'></div>
<div class='abs search'><svg width='50' height='50' viewBox='0 0 100 100'><circle cx='42' cy='42' r='28' fill='none' stroke='{INK}' stroke-width='10'/>
<path d='M63 63 L90 90' stroke='{INK}' stroke-width='12' stroke-linecap='round'/></svg><b>{esc(c.title)}</b><u></u></div>
{folder(M, TOP_TITLE + 150, c.album)}{folder(X[5] - 30, TOP_TITLE + 170, f"TRACK {c.n:02d}")}
{win(X[1] + 40, TOP_TITLE + 290, 560, 500, z[0], f"IMG_{c.n:02d}01.jpg", 3)}
{win(X[3] + 60, TOP_TITLE + 430, 420, 420, z[1], f"IMG_{c.n:02d}02.jpg", 4)}
{win(X[1] + 120, TOP_TITLE + 640, 380, 300, z[2], f"IMG_{c.n:02d}03.jpg", 5).replace("class='abs win'", "class='abs win anchor'")}
{menu}{head(c)}{foot(c, wide=c.spec.get('wide', False))}"""
    return PAPER, css, body


def t_notch(c):
    """사진 카드 + 홈 파인 액자: 사진이 종이 테두리 안을 거의 채우고, 사진 모서리를 둥글게 파낸 종이 홈에
    제목(왼쪽 위), 트랙 번호(왼쪽), 세로 가수명(오른쪽)을 넣는다. 인물 근접 사진이 좋을 때. 레퍼런스: 인터뷰 포스터."""
    px, py, pw = M, 104, W - 2 * M
    ph = H - M - py
    r = 44
    css = f"""
.ph{{left:{px}px;top:{py}px;width:{pw}px;height:{ph}px;border-radius:{r}px;background:{PAPER} url('{c.img(pw, ph)}') 0 0/cover;border:3px solid {INK}}}
.nt{{background:{PAPER};z-index:4}}
.n1{{left:{px - 3}px;top:{py - 3}px;padding:28px 40px 30px 28px;border-radius:0 0 {r}px 0;border-right:3px solid {INK};border-bottom:3px solid {INK}}}
.n1 .k{{font:700 22px 'SpaceMono';margin-bottom:12px}} .n1 .k b{{color:{c.prop};-webkit-text-stroke:1px {INK}}}
.n2{{left:{px - 3}px;top:{py + 560}px;padding:26px 30px 26px 28px;border-radius:0 {r}px {r}px 0;border:3px solid {INK};border-left:0;text-align:left}}
.n2 b{{display:block;font:900 120px/.9 Paperlogy;letter-spacing:-.04em}} .n2 span{{font:700 22px/1.6 'SpaceMono'}}
.n3{{right:{M - 3}px;top:{py + 300}px;padding:30px 22px;border-radius:{r}px 0 0 {r}px;border:3px solid {INK};border-right:0;
writing-mode:vertical-rl;font:900 64px/1 Paperlogy;letter-spacing:.02em;white-space:nowrap}}
.n3 i{{font-style:normal;color:{c.prop};-webkit-text-stroke:2px {INK};margin-bottom:18px}}
"""
    body = f"""<div class='abs ph'></div><div class='grain' style='opacity:.25'></div>
<div class='abs nt n1 anchor'><div class='k'><b>✱</b> {esc(c.album)} · {esc(c.year)}</div>
<div data-fit data-maxw='640' data-maxh='300' style='font:900 140px/.92 Paperlogy;letter-spacing:-.04em;width:max-content'>{"<br>".join(esc(x) for x in (c.spec.get("lines") or split_lines(c.title)))}</div></div>
<div class='abs nt n2'><b>{c.n:02d}</b><span>/ {c.total:02d}<br>TRACK</span></div>
<div class='abs nt n3' data-fit data-maxw='140' data-maxh='620'><i>✱</i>{esc(c.artist)}</div>
{head(c)}{foot(c, wide=c.spec.get('wide', False))}"""
    return PAPER, css, body

def t_motion(c):
    """타이포 카드 + 흔들린 제목: 스캔라인 종이 위에 포인트 컬러 거대 제목을 가로로 흔들리게(모션 블러) 두고,
    하프톤 사진을 곱하기로 얹어 사진의 밝은 곳으로 제목이 비친다. 구석에 같은 사진의 다른 부분을 확대한 기울어진 액자.
    속도·움직임·춤·질주가 제목이나 소개에 있을 때. 배경은 종이 고정(c.bg 무시). 레퍼런스: Skater 포스터."""
    col = c.spot
    fw, fh = 250, 300
    z = zooms(c, [[.2, .1, .8, .6]])
    lines = "<br>".join(esc(x) for x in (c.spec.get("lines") or split_lines(c.title)))
    css = f"""
body{{background:{PAPER} repeating-linear-gradient(to bottom,rgba(17,17,17,.06) 0 2px,transparent 2px 6px)}}
.mt{{left:{M - 16}px;top:{TOP_TITLE - 10}px;font:900 330px/.8 Paperlogy;letter-spacing:-.05em;color:{col};width:max-content;filter:url(#mb);z-index:1}}
.mt2{{opacity:.55;filter:url(#mb2);transform:translateX(26px)}}
.photo{{left:0;top:{TOP_TITLE + 150}px;width:{W}px;height:{H - TOP_TITLE - 150}px;background:url('{c.img(W, H - TOP_TITLE - 150)}') 0 0/cover;mix-blend-mode:multiply;z-index:2;
-webkit-mask-image:linear-gradient(transparent,#000 22%);mask-image:linear-gradient(transparent,#000 22%)}}
.fr{{right:{M + 10}px;top:{TOP_TITLE + 520}px;width:{fw}px;background:{col};border:3px solid {INK};box-shadow:8px 8px 0 {INK};padding:14px 14px 0;transform:rotate(-7deg);z-index:5}}
.fr div{{height:{fh}px;background:{PAPER} url('{c.img(fw - 34, fh, sub=z[0])}') 0 0/cover;border:2px solid {INK}}}
.fr p{{font:900 30px/1 Paperlogy;padding:12px 2px 12px;text-align:right}}
.num{{left:{M}px;top:{TOP_TITLE + 640}px;font:900 110px/.9 Paperlogy;color:{col};-webkit-text-stroke:3px {INK};paint-order:stroke fill;z-index:5}}
"""
    body = f"""<svg width='0' height='0' style='position:absolute'><filter id='mb' x='-10%' width='120%'><feGaussianBlur stdDeviation='9 0'/></filter>
<filter id='mb2' x='-10%' width='120%'><feGaussianBlur stdDeviation='22 0'/></filter></svg>
<div class='abs mt mt2' data-fit data-maxw='1000' data-maxh='560'>{lines}</div><div class='abs mt title' data-fit data-maxw='1000' data-maxh='560'>{lines}</div>
<div class='abs photo'></div><div class='grain' style='opacity:.25'></div>
<div class='abs fr anchor'><div></div><p>TRACK {c.n:02d}</p></div>
<div class='abs num'>{c.n:02d}<br>/{c.total:02d}</div>
{head(c)}{foot(c, wide=c.spec.get('wide', False))}"""
    return PAPER, css, body


def t_issue(c):
    """사진 카드 + 잡지 표지: 위쪽 종이 띠에 포인트 컬러 거대 제목, 아래는 포인트 컬러 판에 하프톤 사진을 곱하기로.
    큰 트랙 번호, 얼굴 일부를 가늘게 확대한 띠 둘(왼쪽), 작은 확대 사진과 가수명(오른쪽), 오른쪽 아래 바코드.
    인물 사진이 좋은 곡, 앨범을 대표하는 곡(근거: 위치). 레퍼런스: 생일 잡지 표지."""
    top = TOP_TITLE + 260
    z = zooms(c, [[.2, .12, .8, .3], [.25, .3, .75, .45], [.1, .4, .6, 1]])
    z[:2] = [tighten(r, .7) for r in z[:2]]  # 확대 띠 둘: 띠 크기는 그대로 두고 더 줌인(사용자 결정 2026-10-24)
    code = hashlib.sha1((c.title + str(c.n)).encode()).hexdigest()
    bars = "".join(f"<rect x='{i * 6}' y='0' width='{1 + int(code[i % 40], 16) % 4}' height='60' fill='{INK}'/>" for i in range(44))
    css = f"""
.tt{{left:{M - 10}px;top:{TOP_TITLE - 6}px;font:900 260px/.84 Paperlogy;letter-spacing:-.05em;color:{c.spot};-webkit-text-stroke:3px {INK};width:max-content;z-index:3}}
.panel{{left:0;top:{top}px;width:{W}px;height:{H - top}px;background:{c.spot}}}
.photo{{left:0;top:{top}px;width:{W}px;height:{H - top}px;background:url('{c.img(W, H - top)}') 0 0/cover;mix-blend-mode:multiply}}
.big{{left:{M}px;top:{top + 120}px;color:{PAPER};font:900 170px/.85 Paperlogy;-webkit-text-stroke:4px {INK};paint-order:stroke fill;z-index:4}}
.big span{{display:block;font:700 30px 'SpaceMono';-webkit-text-stroke:0;color:{INK};background:{PAPER};border:3px solid {INK};padding:8px 12px 4px;width:max-content;margin-top:10px}}
.sl{{left:{M}px;width:330px;height:96px;border:4px solid {PAPER};outline:3px solid {INK};z-index:4}}
.side{{right:{M}px;top:{top + 90}px;width:230px;z-index:4;text-align:right}}
.side p{{font:900 40px/1 Paperlogy;color:{PAPER};-webkit-text-stroke:2px {INK};paint-order:stroke fill;margin-bottom:12px;white-space:nowrap}}
.side div{{height:300px;border:4px solid {PAPER};outline:3px solid {INK};background:{PAPER} url('{c.img(222, 292, sub=z[2])}') 0 0/cover}}
.bc{{right:{M}px;bottom:{M}px;background:{PAPER};border:3px solid {INK};padding:12px 14px 6px;z-index:6;text-align:center;font:700 16px 'SpaceMono'}}
"""
    body = f"""<div class='abs panel'></div><div class='abs photo'></div><div class='grain'></div>
<div class='abs tt title' data-fit data-maxw='1000' data-maxh='300'>{esc(c.title)}</div>
<div class='abs big anchor'>{c.n:02d}<span>/ {c.total:02d} TRACK</span></div>
<div class='abs sl' style='top:{top + 470}px;background:{PAPER} url("{c.img(322, 88, sub=z[0])}") 0 0/cover'></div>
<div class='abs sl' style='top:{top + 600}px;left:{M + 60}px;background:{PAPER} url("{c.img(322, 88, sub=z[1])}") 0 0/cover'></div>
<div class='abs side'><p data-fit data-maxw='230' data-maxh='44'>{esc(c.artist)}</p><div></div></div>
<div class='abs bc'><svg width='264' height='60'>{bars}</svg><br>{code[:12].upper()}</div>
{head(c)}{foot(c, wide=c.spec.get('wide', False))}"""
    return PAPER, css, body


def t_torn(c):
    """사진 카드 + 찢은 띠: 하프톤 사진 전면 가운데를 종이째 찢어 낸 띠에 같은 사진의 일부(눈 등)를 확대해 붙이고,
    세리프 제목이 띠 위아래로 갈라진다(한 줄 제목이면 아래는 가수명). 띠 가운데 작은 이탤릭 가수명.
    시선·보기·드러냄·비밀이 제목이나 소개에 있을 때. 레퍼런스: HOLD YOUR VISION 포스터."""
    z = zooms(c, [[.15, .12, .85, .38]])
    ln = c.spec.get("lines") or split_lines(c.title)
    up, down = ln[0], (ln[1] if len(ln) > 1 else "")
    sy, sh = TOP_TITLE + 380, 300
    jag = ",".join(f"{x}% {y}%" for x, y in [(0, 6), (5, 0), (11, 7), (17, 2), (24, 8), (31, 1), (38, 6), (46, 0), (53, 7), (61, 2), (68, 8), (76, 1), (83, 6),
          (90, 0), (96, 7), (100, 3), (100, 95), (94, 100), (87, 93), (80, 99), (72, 92), (65, 100), (57, 94), (49, 100), (41, 92), (34, 99), (26, 93), (19, 100), (11, 94), (4, 100), (0, 92)])
    css = f"""
.photo{{inset:0;background:url('{c.img(W, H)}') 0 0/cover;mix-blend-mode:multiply}}
.tear{{left:-30px;top:{sy}px;width:{W + 60}px;height:{sh}px;transform:rotate(-3deg);z-index:3;filter:drop-shadow(0 8px 0 rgba(0,0,0,.25))}}
.tear .ed{{position:absolute;inset:-14px 0;background:#fbfbf8;clip-path:polygon({jag})}}
.tear .im{{position:absolute;inset:0;clip-path:polygon({jag});background:{PAPER} url('{c.img(W + 60, sh, sub=z[0])}') 0 0/cover}}
.tear em{{position:absolute;left:0;right:0;top:50%;transform:translateY(-50%);text-align:center;font:700 54px/1 Chosun;font-synthesis:weight;font-style:italic;color:{PAPER};-webkit-text-stroke:6px {INK};paint-order:stroke fill;z-index:2}}
.tw{{left:50%;transform:translateX(-50%);width:max-content;text-align:center;font:700 220px/.9 Chosun;font-synthesis:weight;color:{c.spot};-webkit-text-stroke:5px {INK};paint-order:stroke fill;z-index:4;white-space:nowrap}}
.side{{right:{M}px;top:{TOP_TITLE}px;border-left:4px solid {INK};border-right:4px solid {INK};padding:6px 14px;font:400 56px/1.05 Chosun;text-align:center;background:{PAPER};z-index:5}}
"""
    body = f"""<div class='abs photo'></div><div class='grain'></div>
<div class='abs tw title' data-fit data-maxw='984' data-maxh='210' style='top:{sy - 220}px'>{esc(up)}</div>
<div class='abs tear anchor'><div class='ed'></div><div class='im'></div><em>{esc(c.artist)}</em></div>
{f"<div class='abs tw' data-fit data-maxw='984' data-maxh='210' style='top:{sy + sh + 30}px'>{esc(down)}</div>" if down else ""}
<div class='abs side'>{c.n:02d}<br>—<br>{c.total:02d}</div>
{head(c)}{foot(c, wide=c.spec.get('wide', False))}"""
    return PAPER, css, body




def ctl_svg(kind, size, color):
    """재생 단추 그림: prev / next / pause / shuffle / repeat."""
    d = {"prev": "M22 20h10v60H22z M78 20v60L36 50z", "next": "M68 20h10v60H68z M22 20v60l42-30z",
         "pause": "M34 28h10v44H34z M56 28h10v44H56z"}
    if kind in d:
        return f"<svg width='{size}' height='{size}' viewBox='0 0 100 100'><path d='{d[kind]}' fill='{color}'/></svg>"
    path = {"shuffle": "M14 30h20l32 40h20 M14 70h20l32-40h20 M78 22l10 8-10 8 M78 62l10 8-10 8",
            "repeat": "M20 56V36h56 M66 26l10 10-10 10 M80 44v20H24 M34 74L24 64l10-10"}[kind]
    return (f"<svg width='{size}' height='{size}' viewBox='0 0 100 100'><path d='{path}' fill='none' stroke='{color}' "
            f"stroke-width='8' stroke-linejoin='round' stroke-linecap='round'/></svg>")


def t_nowplaying(c):
    """앨범 카드: 검은 테두리·어긋난 그림자의 재생 화면 안에 실제 표지(원본), 앨범명·가수, 진행 막대(이 장 / 전체 장), 재생 단추.
    왼쪽에 큰 모노 글자 NOW PLAYING과 앨범 정보. 첫 장의 무난한 기본형. 레퍼런스: 재생 화면 포스터·스티커."""
    main = c.bg != "ink"
    bg = c.spot if main else INK
    fg = INK if main else PAPER
    w, cv = 600, 512
    cur, tot = (int(x) for x in c.page.split("/"))
    pct = cur / tot * 100
    n = len(c.tracks or [])
    css = f"""
.dev{{left:{W - M - w}px;width:{w}px;background:{PAPER};border:3px solid {INK};border-radius:28px;box-shadow:12px 12px 0 {INK};padding:32px 40px 26px}}
.dev .cv{{width:{cv}px;height:{cv}px;background:{PAPER} url('{c.cover}') 0 0/cover;border:3px solid {INK}}}
.dev h2{{font:900 48px/1.1 Paperlogy;letter-spacing:-.03em;margin-top:24px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.dev h3{{font:500 28px SCDream;margin-top:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.rail{{position:relative;height:6px;background:{INK};margin:30px 0 8px}}
.rail .h{{position:absolute;left:calc({pct}% - 12px);top:-9px;width:24px;height:24px;border-radius:50%;background:{INK}}}
.rail:before{{content:'';position:absolute;left:{pct}%;right:0;top:0;bottom:0;background:#bdbdb8}}
.tm{{display:flex;justify-content:space-between;font:700 20px 'SpaceMono'}}
.ctl{{display:flex;justify-content:space-between;align-items:center;margin-top:14px}}
.ctl .pp{{width:88px;height:88px;border-radius:50%;background:{INK};display:flex;align-items:center;justify-content:center}}
.sticker{{position:absolute;left:-44px;top:-40px;width:150px;height:150px;border-radius:50%;background:{c.prop};border:3px solid {INK};
transform:rotate(-14deg);display:flex;flex-direction:column;align-items:center;justify-content:center;font:900 46px/1 Paperlogy;z-index:3}}
.sticker i{{font:700 18px 'SpaceMono';font-style:normal;margin-bottom:6px}}
.np{{left:{M}px;top:{TOP_TITLE}px;font:700 96px/1.02 'SpaceMono';color:{fg};letter-spacing:-.02em}}
.meta{{left:{M}px;width:{W - 2 * M - w - 40}px;z-index:4}}
.meta .lbl{{font:700 30px SCDream;padding:10px 14px 8px;margin-bottom:-3px;display:table}}
"""
    body = f"""<div class='grain'></div>{head(c, dark=not main)}
<div class='abs np'>NOW<br>PLAY<br>ING</div>
<div class='abs meta' data-zone='after' data-after='.np'><span class='lbl' style='background:{c.prop}'>{esc(c.spec.get('type', ''))}</span>
<span class='lbl'>{esc(c.spec.get('date', ''))}</span><span class='lbl'>{n:02d} TRACKS</span></div>
<div class='abs dev anchor' data-zone='fixed' style='top:{TOP_TITLE}px'><div class='sticker'><i>NEW</i>신보</div><div class='cv'></div>
<h2>{esc(c.album)}</h2><h3>{esc(c.artist)}</h3><div class='rail'><div class='h'></div></div>
<div class='tm'><span>{cur:02d}</span><span>{tot:02d}</span></div>
<div class='ctl'>{ctl_svg('shuffle', 48, INK)}{ctl_svg('prev', 56, INK)}<div class='pp'>{ctl_svg('pause', 64, PAPER)}</div>{ctl_svg('next', 56, INK)}{ctl_svg('repeat', 48, INK)}</div></div>
{foot(c, dark=not main)}"""
    return bg, css, body


def t_colorblock(c):
    """앨범 카드: 화면 전체를 포인트 컬러 판으로 쓰고 위쪽에 하프톤 사진(없으면 표지)을 곱하기로 얹는다.
    아래쪽에 앨범명을 거대하게 한 줄로 두되 다 보이도록 폭에 맞춰 줄이고(사용자 결정 2026-10-24), 가수·메타·진행 막대를 붙인다.
    앨범명이 짧고 강할 때. 레퍼런스: 단색 앱 카드 + 큰 제목."""
    main = c.bg != "ink"
    bg = c.spot if main else INK
    fg = INK if main else PAPER
    n = len(c.tracks or [])
    css = f"""
.photo{{left:0;top:0;width:{W}px;height:720px;background:url('{c.img(W, 720)}') 0 0/cover;mix-blend-mode:{'multiply' if main else 'screen'};opacity:{1 if main else .55};
-webkit-mask-image:linear-gradient(#000 45%,transparent 92%);mask-image:linear-gradient(#000 45%,transparent 92%)}}
.blk{{left:{M}px;right:0;color:{fg};z-index:4}}
.blk h1{{font:900 300px/.82 Paperlogy;letter-spacing:-.06em;white-space:nowrap;margin-left:-14px;width:max-content}}
.blk h2{{font:700 64px/1.1 SCDream;margin-top:18px}}
.blk .mt{{display:flex;align-items:center;gap:14px;font:700 24px 'SpaceMono';margin-top:14px}}
.blk .mt i{{width:28px;height:28px;border-radius:50%;background:radial-gradient(circle,{bg} 0 18%,{fg} 20%)}}
.pr{{display:flex;align-items:center;gap:28px;margin:28px {M}px 0 0}}
.pr .rl{{flex:1;height:8px;background:{fg};position:relative}}
.pr .rl:after{{content:'';position:absolute;left:30%;top:-12px;width:32px;height:32px;border-radius:50%;background:{PAPER};border:4px solid {INK}}}
.pr .pb{{width:110px;height:110px;border-radius:50%;background:{PAPER};border:3px solid {INK};box-shadow:6px 6px 0 {INK};display:flex;align-items:center;justify-content:center}}
"""
    body = f"""<div class='abs photo'></div><div class='grain'></div>{head(c, dark=not main)}
<div class='abs blk anchor' data-zone='above-foot'><h1 data-fit data-maxw='{W - 2 * M + 14}' data-maxh='300'>{esc(c.album)}</h1><h2>{esc(c.artist)}</h2>
<div class='mt'><i></i>{esc(c.spec.get('type', ''))} · {esc(c.spec.get('date', ''))} · {n:02d} TRACKS</div>
<div class='pr'><div class='rl'></div><div class='pb'><svg width='54' height='54' viewBox='0 0 100 100'><path d='M30 18v64l56-32z' fill='{INK}'/></svg></div></div></div>
{foot(c, dark=not main)}"""
    return bg, css, body


def barcode(seed, w=264, h=60):
    code = hashlib.sha1(seed.encode()).hexdigest()
    bars = "".join(f"<rect x='{i * 6}' y='0' width='{1 + int(code[i % 40], 16) % 4}' height='{h}' fill='{INK}'/>" for i in range(w // 6))
    return f"<svg width='{w}' height='{h}'>{bars}</svg>", code[:12].upper()


def t_disc(c):
    """앨범 카드: CD 한 장. 잉크 바탕 위에 사진(없으면 표지)을 포인트 컬러 듀오톤으로 찍은 디스크, 가운데 구멍과 무지개 테두리,
    위에 세리프 앨범명, 왼쪽 아래 세로 TRACKS와 따옴표 수록곡 목록, 맨 위 크레디트 줄. 레퍼런스: Never Enough CD 포스터."""
    d = 780
    tr = c.tracks or []
    rows = tr if len(tr) <= 10 else tr[:9]
    lis = "".join(f"<li{' class=t' if t else ''}>“{esc(title)}”</li>" for n, title, t in rows) + (f"<li>+{len(tr) - len(rows)}</li>" if len(tr) > len(rows) else "")
    css = f"""
.cr{{left:{M}px;right:{M}px;top:{TOP_TITLE - 30}px;display:flex;justify-content:space-between;font:700 16px 'SpaceMono';color:{PAPER};letter-spacing:.06em;z-index:4}}
.cr span{{border-top:3px solid {PAPER};padding-top:8px}}
.at{{left:50%;transform:translateX(-50%);top:{TOP_TITLE + 16}px;width:max-content;font:700 150px/1 Chosun;font-synthesis:weight;color:{c.spot};letter-spacing:-.02em;z-index:5;
text-shadow:0 0 18px rgba(255,255,255,.25)}}
.disc{{left:{(W - d) // 2}px;top:{TOP_TITLE + 210}px;width:{d}px;height:{d}px;border-radius:50%;overflow:hidden;background:{c.spot};border:3px solid {INK};box-shadow:0 0 0 2px #333,0 20px 60px rgba(0,0,0,.6)}}
.disc .ph{{position:absolute;inset:0;background:url('{c.img(d, d)}') 0 0/cover;mix-blend-mode:multiply}}
.disc .hub{{position:absolute;left:50%;top:50%;width:260px;height:260px;margin:-130px;border-radius:50%;
background:radial-gradient(circle,{INK} 0 34%,#2a2a2a 35% 44%,#f3f3ef 45% 92%,transparent 93%),conic-gradient({c.prop},{c.spot},#fff,{c.prop});border:3px solid {INK}}}
.disc .ring{{position:absolute;inset:0;border-radius:50%;background:radial-gradient(circle,transparent 60%,rgba(255,255,255,.12) 61%,transparent 62%,transparent 80%,rgba(255,255,255,.1) 81%,transparent 82%)}}
.tl{{left:{M}px;top:{TOP_TITLE + 560}px;display:flex;gap:16px;z-index:5}}
.tl .v{{font:700 26px/1.12 Chosun;color:{PAPER};width:24px;text-align:center}}
.tl ol{{list-style:none;font:700 22px/1.4 'SpaceMono';color:{PAPER};text-transform:uppercase;text-shadow:0 2px 6px rgba(0,0,0,.8)}} .tl li.t{{color:{c.spot}}}
.tl li{{max-width:420px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
"""
    body = f"""<div class='grain' style='opacity:.35'></div>
<div class='abs cr'><span>© {esc(c.year)} {esc(c.artist)}</span><span>{esc(c.spec.get('type', ''))}</span><span>RELEASED {esc(c.spec.get('date', ''))}</span></div>
<div class='abs at title' data-fit data-maxw='984' data-maxh='170'>{esc(c.album)}</div>
<div class='abs disc anchor'><div class='ph'></div><div class='ring'></div><div class='hub'></div></div>
<div class='abs tl'><div class='v'>{"<br>".join("TRACKS")}</div><ol>{lis}</ol></div>
{head(c, dark=True)}{foot(c, dark=True)}"""
    return INK, css, body


def t_flyer(c):
    """앨범 카드: 공연 전단. 종이 바탕에 잉크 거대 앨범명, 가수·앨범 종류 잉크 띠, 포인트 컬러에 하프톤 사진을 곱한 듀오톤 사진판과
    바코드, 3단 정보 줄, 수록곡을 • 로 이은 잉크 띠. 레퍼런스: Saturday Party 전단."""
    ph = 430
    code_svg, code = barcode(c.album + c.artist)
    names = " • ".join(esc(t) for _, t, _ in (c.tracks or []))
    css = f"""
.tt{{left:{M - 6}px;top:{TOP_TITLE - 8}px;font:900 130px/1 Paperlogy;letter-spacing:-.04em;color:{INK};width:max-content;z-index:3}}
.bar{{left:{M}px;right:{M}px;background:{INK};color:{PAPER};display:flex;justify-content:space-between;padding:14px 24px 8px;font:900 64px/1 Paperlogy;z-index:3}}
.pic{{left:{M}px;right:{M}px;height:{ph}px;background:{c.spot};overflow:hidden}}
.pic .ph{{position:absolute;inset:0;background:url('{c.img(W - 2 * M, ph)}') 0 0/cover;mix-blend-mode:multiply}}
.pic .bc{{position:absolute;right:16px;bottom:16px;background:{PAPER};padding:10px 12px 4px;text-align:center;font:700 16px 'SpaceMono'}}
.info{{left:{M}px;right:{M}px;display:flex;justify-content:space-between;font:700 26px/1.45 SCDream;color:{INK};z-index:3}}
.info div:nth-child(2){{text-align:center}} .info div:last-child{{text-align:right}}
.kw{{left:{M}px;background:{INK};color:{PAPER};padding:10px 20px 6px;font:900 34px/1.1 Paperlogy;white-space:nowrap;width:max-content;max-width:{W - 2 * M}px;overflow:hidden;text-overflow:ellipsis;z-index:3}}
"""
    body = f"""<div class='grain' style='opacity:.4'></div>
<div class='abs tt title' data-fit data-maxw='{W - 2 * M + 12}' data-maxh='130'>{esc(c.album)}</div>
<div class='abs bar' data-zone='after' data-after='.title' style='margin-top:-24px'><span>{esc(c.artist)}</span><span>{esc(c.spec.get('type', ''))}</span></div>
<div class='abs pic anchor' style='top:{TOP_TITLE + 250}px'><div class='ph'></div><div class='bc'>{code_svg}<br>{code}</div></div>
<div class='abs info' style='top:{TOP_TITLE + 250 + ph + 26}px'><div>RELEASED<br>{esc(c.spec.get('date', ''))}</div><div>{len(c.tracks or []):02d} TRACKS<br>NEW ALBUM</div><div>DB RECORD SHOP<br>REVIEW</div></div>
<div class='abs kw' data-fit data-maxw='{W - 2 * M}' data-maxh='60' style='top:{TOP_TITLE + 250 + ph + 132}px'>{names}</div>
{head(c)}{foot(c)}"""
    return PAPER, css, body


def t_live(c):
    """앨범 카드: 공연 포스터. 종이 바탕에 큰 하프톤 사진판, 왼쪽 위에 가수명, 오른쪽 아래에 앨범명을 소품색 거대 글자로 사진에 걸치고,
    오른쪽 위에 발매일과 화살표. 레퍼런스: MUSIC LIVE 포스터."""
    pw, ph = 880, 800
    y = TOP_TITLE + 120
    css = f"""
.pic{{left:{M}px;top:{y}px;width:{pw}px;height:{ph}px;background:{PAPER} url('{c.img(pw, ph)}') 0 0/cover;border:3px solid {INK}}}
.w{{font:900 170px/.86 Paperlogy;letter-spacing:-.05em;color:{c.prop};-webkit-text-stroke:4px {INK};paint-order:stroke fill;width:max-content;z-index:4}}
.dt{{right:{M}px;top:{TOP_TITLE + 10}px;text-align:right;font:700 38px/1.15 SCDream;color:{INK};z-index:4}}
.ar{{left:{M + pw - 110}px;top:{y + 30}px;z-index:4}}
"""
    body = f"""<div class='grain' style='opacity:.35'></div><div class='abs pic anchor'></div>
<div class='abs w title' data-fit data-maxw='{pw - 40}' data-maxh='170' style='left:{M - 8}px;top:{TOP_TITLE - 20}px'>{esc(c.artist)}</div>
<div class='abs w' data-fit data-maxw='{pw}' data-maxh='170' style='right:{M}px;top:{y + ph - 190}px'>{esc(c.album)}</div>
<div class='abs dt'>{esc(c.spec.get('date', '')).replace('.', '<br>', 1)}<br><span style='font:700 22px SpaceMono'>{esc(c.spec.get('type', ''))}</span></div>
<svg class='abs ar' width='80' height='80' viewBox='0 0 100 100'><path d='M20 80 L78 22 M36 20 H80 V64' stroke='{PAPER}' stroke-width='14' fill='none' stroke-linecap='square'/></svg>
{head(c)}{foot(c)}"""
    return PAPER, css, body


def t_neon(c):
    """앨범 카드: 클럽 포스터. 어둡게 누른 하프톤 사진 전면 위에 포인트 컬러 세로로 긴 거대 앨범명, 그 아래 좌우 작은 라벨(가수·종류),
    아래쪽에 큰 숫자 둘(발매 월일·곡 수). 레퍼런스: NO SLEEP CLUB 포스터."""
    md = c.spec.get("date", "")[5:] or c.year
    css = f"""
.photo{{inset:0;background:url('{c.img(W, H)}') 0 0/cover;filter:brightness(.42) contrast(1.15)}}
.nt{{left:{M - 6}px;top:{TOP_TITLE - 20}px;font:900 190px/1 Paperlogy;letter-spacing:-.04em;color:{c.spot};transform:scaleY(1.35);transform-origin:top left;width:max-content;z-index:4}}
.sm{{top:{TOP_TITLE + 250}px;font:900 40px/1 Paperlogy;color:{c.spot};z-index:4}}
.big{{top:{TOP_TITLE + 640}px;font:900 150px/1 Paperlogy;letter-spacing:-.03em;color:{c.spot};transform:scaleY(1.3);transform-origin:top;z-index:4}}
.big span{{display:block;font:900 34px/1 Paperlogy;letter-spacing:0;margin-top:6px}}
"""
    body = f"""<div class='abs photo'></div><div class='grain' style='opacity:.3'></div>
<div class='abs nt title anchor' data-fit data-maxw='990' data-maxh='190'>{esc(c.album)}</div>
<div class='abs sm' style='left:{M}px'>{esc(c.artist)}</div><div class='abs sm' style='right:{M}px'>{esc(c.spec.get('type', ''))}</div>
<div class='abs big' style='left:{M}px'>{esc(md)}<span>RELEASED</span></div>
<div class='abs big' style='right:{M}px;text-align:right'>{len(c.tracks or []):02d}<span>TRACKS</span></div>
{head(c, dark=True)}{foot(c, dark=True)}"""
    return INK, css, body


TEMPLATES = {"polaroid": t_polaroid, "cutout": t_cutout, "grid": t_grid,
             "player": t_player, "full": t_full, "serpent": t_serpent, "cinema": t_cinema, "cctv": t_cctv,
             "nowplaying": t_nowplaying, "disc": t_disc, "flyer": t_flyer, "live": t_live, "neon": t_neon, "colorblock": t_colorblock,
             "gable": t_gable, "clipboard": t_clipboard, "desktop": t_desktop, "notch": t_notch,
             "motion": t_motion, "issue": t_issue, "torn": t_torn}


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
