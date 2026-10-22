"""트랙 카드 중앙 그래픽 생성기.

그림 = 모양(모티프) × 질감(스타일). 모티프는 밝기 필드를 만들고, 스타일은 그 필드를 점·선·빛으로 옮긴다.
- 모티프 37개: MOTIFS 참고. 면으로 된 모티프(AREA)와 가는 선·작은 도형으로 된 모티프로 나뉜다.
- 스타일 4개: grain(점묘 그레인), halftone(하프톤), lines(가는 선 해칭), glow(빛 번짐).
  면 모티프는 넷 다, 선 모티프는 grain·glow만 쓴다(STYLES_FOR).
- 색: 포인트 컬러(fg)와 두 번째 색(accent, 보통 화이트)을 팔레트 5가지(mono, accent, duotone, split, tones)로 칠한다.
  배경 가운데에 포인트 컬러를 옅게 번지게 할 수 있다(bg_glow).
- 구도: 모양은 항상 가운데 축에 맞춘다. 트랙 제목으로 고정한 난수로 가운데 축 기준 크기·회전만 모티프마다 정해진 범위 안에서 바꾼다.

    draw("rings", "Kerosene", "#111111", "#7b84ac", style="glow", accent="#ffffff", palette="duotone", bg_glow=True)
"""
import base64, colorsys, io, zlib
import numpy as np
from PIL import Image, ImageDraw

S = 704  # 화면 프레임 안쪽 크기(px)


def _rng(seed):
    return np.random.default_rng(zlib.crc32(str(seed).encode()))


def _hex(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], dtype=float)


def _blur(f, r):
    """가우시안 흐림 (가로·세로 분리 합성곱)."""
    k = np.arange(-int(3 * r) - 1, int(3 * r) + 2)
    k = np.exp(-(k / r) ** 2 / 2)
    k /= k.sum()
    f = np.apply_along_axis(lambda a: np.convolve(a, k, "same"), 0, f)
    return np.apply_along_axis(lambda a: np.convolve(a, k, "same"), 1, f)


def _coords(rng, rot_max, scale=(0.88, 1.12)):
    """구도 변주: 가운데 축을 기준으로 키우거나 줄이고 돌린 좌표 (0~1). 위치는 옮기지 않는다."""
    y, x = np.mgrid[0:S, 0:S] / S
    k = rng.uniform(*scale)
    t = np.deg2rad(rng.uniform(-rot_max, rot_max))
    u, v = x - 0.5, y - 0.5
    u, v = (u * np.cos(t) + v * np.sin(t)) / k, (-u * np.sin(t) + v * np.cos(t)) / k
    return u + 0.5, v + 0.5


def _plot(points, sizes, blur=0.0):
    """점 목록을 필드로 찍는다 (4배로 그린 뒤 줄여 가장자리를 부드럽게)."""
    n = S * 4
    img = Image.new("L", (n, n), 0)
    d = ImageDraw.Draw(img)
    for (px, py), r in zip(points, sizes):
        cx, cy, rr = px * n, py * n, max(r * n, 1.0)
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=255)
    f = np.asarray(img.resize((S, S), Image.LANCZOS), dtype=float) / 255
    return _blur(f, blur) if blur else f


def _place(rng, xs, ys, rot_max, scale=(0.88, 1.08)):
    """곡선 점에 구도 변주(가운데 축 기준 크기·회전)를 준다."""
    k = rng.uniform(*scale)
    t = np.deg2rad(rng.uniform(-rot_max, rot_max))
    u, v = xs - 0.5, ys - 0.5
    return 0.5 + k * (u * np.cos(t) - v * np.sin(t)), 0.5 + k * (u * np.sin(t) + v * np.cos(t))


def _curve(xs, ys, width):
    """연속 곡선을 가는 선으로 찍는다."""
    return _plot(list(zip(xs, ys)), [width] * len(xs))


# ---------- 모티프: (주 필드, 강조 필드 또는 None) ----------

def m_ribbon(rng):
    """S자 리본. 한쪽 가장자리는 또렷하고 반대쪽은 번진다. 밝은 테두리선과 희미한 뒤쪽 주름."""
    x, y = _coords(rng, 25)
    phase = rng.uniform(0, np.pi)
    cx = 0.56 + 0.2 * np.sin(2 * np.pi * 1.3 * y + phase)  # 번지는 쪽(왼쪽)을 감안해 덩어리 중심을 가운데에
    w = 0.09 + 0.05 * np.sin(np.pi * y + phase)
    d = (x - cx) / w
    core = np.exp(-np.clip(d, 0, None) ** 2 * 1.6) * np.exp(-np.clip(-d, 0, None) ** 2 * 0.35)
    edge = np.exp(-((d - 0.15) ** 2) * 60) * 0.6
    ghost = 0.12 * np.exp(-((x - (cx + 0.32)) / 0.16) ** 2)
    return core + ghost, edge


def m_streaks(rng, cols=7):
    """가운데 또렷한 띠(세로 42%)에서 위아래로 번져 사라지는 빛기둥. 기둥은 겹치지 않는다."""
    x, y = _coords(rng, 6)
    w = rng.uniform(0.04, 0.12, cols)
    g = rng.uniform(0.015, 0.05, cols - 1)
    left = (1 - w.sum() - g.sum()) / 2
    field = np.zeros((S, S))
    mid, half = 0.42, 0.05
    for i in range(cols):
        a, b = left, left + w[i]
        left = b + (g[i] if i < cols - 1 else 0)
        col = np.clip((x - a) / 0.006, 0, 1) * np.clip((b - x) / 0.006, 0, 1)
        up, down = rng.uniform(0.08, 0.22), rng.uniform(0.05, 0.14)
        dist = np.abs(y - mid) - half
        trail = np.where(dist <= 0, 1.0, np.exp(-dist / np.where(y < mid, up, down)) * 0.9)
        field = np.maximum(field, col * trail)
    glow = 0.18 * np.exp(-((y - mid) / 0.18) ** 2)
    line = np.exp(-((y - mid) / 0.004) ** 2) * (np.abs(x - 0.5) < 0.45)
    return np.maximum(field, glow), line


def m_rings(rng):
    """동심원. 가운데에서 퍼져 나가며 바깥으로 사라지는 가는 고리."""
    x, y = _coords(rng, 0)
    d = np.hypot(x - 0.5, y - 0.5)
    pitch = rng.uniform(0.045, 0.06)
    ring = (0.5 + 0.5 * np.cos(2 * np.pi * d / pitch)) ** 10
    return ring * np.exp(-d / 0.22), np.exp(-(d / 0.05) ** 2)


def m_sun_horizon(rng):
    """해와 수평선. 수평선에 걸린 반원은 위가 밝고 아래로 옅어지며, 아래에 반사 띠가 흐려진다."""
    x, y = _coords(rng, 4)
    h, r = 0.62, rng.uniform(0.17, 0.21)
    d = np.hypot(x - 0.5, y - h)
    above = y < h
    disc = np.clip((r - d) / 0.004, 0, 1) * above * (0.12 + 0.6 * np.clip((h - y) / r, 0, 1) ** 1.5)
    glow = 0.35 * np.exp(-np.maximum(d - r, 0) / 0.08) * above
    below = y - h
    bands = (0.5 + 0.5 * np.cos(2 * np.pi * below / 0.028)) ** 6
    refl = np.where(below > 0, bands * np.exp(-below / 0.12) * np.exp(-((x - 0.5) / (r * 0.9)) ** 2), 0)
    line = np.exp(-((y - h) / 0.003) ** 2) * np.clip((0.45 - np.abs(x - 0.5)) / 0.08, 0, 1)
    return disc + glow + 0.6 * refl, line


def m_wave_lines(rng):
    """가는 세로선 물결. 일정한 간격의 세로선이 가운데에서 크게 휘어진다."""
    x, y = _coords(rng, 15)
    pitch = 0.028
    amp = 0.035 * np.exp(-((y - 0.5) / 0.28) ** 2)
    xs = x + amp * np.sin(2 * np.pi * (y * 1.4 + x * 0.6) + rng.uniform(0, 2 * np.pi))
    lines = (0.5 + 0.5 * np.cos(2 * np.pi * xs / pitch)) ** 16
    env = np.exp(-((x - 0.5) / 0.24) ** 2) * np.exp(-((y - 0.5) / 0.3) ** 2)
    hero = np.exp(-((xs - 0.5 - pitch / 2) / 0.0035) ** 2) * np.exp(-((y - 0.5) / 0.32) ** 2)
    return lines * env, hero


def m_radial(rng):
    """가는 선의 방사형·타원. 한 점에서 뻗는 가는 선과 그 점을 지나는 기울어진 타원 몇 개."""
    x, y = _coords(rng, 90)
    dx, dy = x - 0.5, y - 0.5
    d, th = np.hypot(dx, dy), np.arctan2(dy, dx)
    rays = (0.5 + 0.5 * np.cos(36 * th)) ** 40 * np.exp(-d / 0.25) * (d > 0.02)
    ell = np.zeros_like(d)
    for k, (a, b) in enumerate([(0.42, 0.14), (0.36, 0.22), (0.30, 0.30)]):
        t = k * np.pi / 3
        u, v = dx * np.cos(t) + dy * np.sin(t), -dx * np.sin(t) + dy * np.cos(t)
        ell = np.maximum(ell, 0.8 * np.exp(-((np.sqrt((u / a) ** 2 + (v / b) ** 2) - 1) / 0.012) ** 2))
    return rays + np.exp(-(d / 0.03) ** 2), ell


def m_scope(rng):
    """오실로스코프 파형. 겹친 가는 파형 여러 줄, 가운데가 가장 크다."""
    seed = rng.integers(1 << 30)
    xs = np.linspace(0.06, 0.94, 2400)
    env = np.exp(-((xs - 0.5) / 0.22) ** 2)
    main = np.zeros((S, S))
    for k in range(5):
        pl = np.random.default_rng(seed)  # 모든 줄에 같은 구도
        f1, f2 = rng.uniform(6, 14), rng.uniform(20, 40)
        ys = 0.5 + (0.22 - k * 0.035) * env * (np.sin(2 * np.pi * f1 * xs + k) * 0.7 + 0.3 * np.sin(2 * np.pi * f2 * xs))
        main = np.maximum(main, (1 - k * 0.15) * _curve(*_place(pl, xs, ys, 8), 0.0016))
    center = _curve(*_place(np.random.default_rng(seed), xs, np.full_like(xs, 0.5), 8), 0.0012) * 0.8
    return np.maximum(main, _blur(main, 6) * 0.8), center


def m_equalizer(rng):
    """이퀄라이저 막대. 아래 기준선에서 솟은 막대는 위로 갈수록 밝고, 위에 떠 있는 피크 표시가 있다."""
    x, y = _coords(rng, 0)
    n, base = 15, 0.72
    edges = np.linspace(0.12, 0.88, n + 1)
    h = np.convolve(rng.uniform(0.1, 0.5, n), [0.25, 0.5, 0.25], "same")
    main, caps = np.zeros((S, S)), np.zeros((S, S))
    for i in range(n):
        a, b = edges[i] + 0.006, edges[i + 1] - 0.006
        col = np.clip((x - a) / 0.003, 0, 1) * np.clip((b - x) / 0.003, 0, 1)
        top = base - h[i]
        main = np.maximum(main, col * ((y > top) & (y < base)) * (0.25 + 0.75 * np.clip((base - y) / h[i], 0, 1)))
        caps = np.maximum(caps, col * np.exp(-((y - (top - 0.025)) / 0.004) ** 2))
    return main, caps


def m_spiral(rng):
    """소용돌이. 가는 나선 하나가 겹겹이 돈다."""
    t = np.linspace(0, 1, 20000)
    turns = rng.uniform(6, 9)
    th = 2 * np.pi * turns * t + rng.uniform(0, 2 * np.pi)
    r = 0.02 + 0.40 * t
    xs, ys = _place(rng, 0.5 + r * np.cos(th), 0.5 + r * np.sin(th) * rng.uniform(0.75, 1.0), 180)
    main = _curve(xs, ys, 0.0016)
    return main + _blur(main, 10) * 0.5, _plot([(xs[0], ys[0])], [0.012], blur=3)


def m_lissajous(rng):
    """리사주 곡선. 두 진동이 겹쳐 그리는 매듭 모양."""
    t = np.linspace(0, 1, 20000)
    a, b = rng.choice([(3, 2), (5, 4), (3, 4), (5, 6)])
    th = 2 * np.pi * t
    xs, ys = _place(rng, 0.5 + 0.40 * np.sin(a * th + np.pi / 2), 0.5 + 0.40 * np.sin(b * th), 20)
    main = _curve(xs, ys, 0.0016)
    return main + _blur(main, 10) * 0.5, None


def _hills(rng, x, y):
    hgt = np.zeros((S, S))
    c = rng.uniform(0.22, 0.78, (5, 2))
    c += 0.5 - c.mean(0)  # 언덕 묶음의 중심을 가운데에
    for cx, cy in c:
        s = rng.uniform(0.07, 0.15)
        hgt += rng.uniform(0.5, 1.0) * np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * s ** 2))
    return hgt / hgt.max()


def m_contour(rng):
    """등고선 지형. 묵직한 덩어리를 같은 높이의 선으로만 보여 준다."""
    x, y = _coords(rng, 30)
    hgt = _hills(rng, x, y)
    main = (0.5 + 0.5 * np.cos(2 * np.pi * hgt * 14)) ** 24 * np.clip((hgt - 0.08) / 0.1, 0, 1)
    peak = (hgt > 0.97).astype(float)
    return main * (0.4 + 0.6 * hgt), _blur(peak, 2)


def m_warp_grid(rng):
    """휘어진 격자. 높은 곳이 앞으로 솟은 것처럼 격자가 밀린다."""
    x, y = _coords(rng, 30)
    hgt = _hills(rng, x, y)
    gy, gx = np.gradient(hgt)  # 휘어진 격자: 높은 곳이 앞으로 솟은 것처럼 격자를 민다
    u, v = x - gx * 12, y - gy * 12 - hgt * 0.05
    pitch = 0.04
    grid = np.maximum((0.5 + 0.5 * np.cos(2 * np.pi * u / pitch)) ** 30, (0.5 + 0.5 * np.cos(2 * np.pi * v / pitch)) ** 30)
    env = np.clip((0.46 - np.maximum(np.abs(x - 0.5), np.abs(y - 0.5))) / 0.06, 0, 1)
    return grid * env * (0.3 + 0.7 * hgt), None


def m_particles(rng):
    """입자·파편 흩날림. 가운데에서 터져 나가며 멀수록 작고 옅어진다."""
    ang = rng.uniform(0, 2 * np.pi)
    ox, oy = 0.5, 0.5  # 가운데에서 터져 나가고, 한쪽으로 조금 더 멀리 흩어진다
    n = 9000
    a = rng.uniform(0, 2 * np.pi, n)
    dist = rng.exponential(0.12, n) * (1 + 0.6 * np.cos(a - ang)) + 0.01
    pts = np.stack([ox + dist * np.cos(a), oy + dist * np.sin(a)], 1)
    keep = (pts[:, 0] > 0.04) & (pts[:, 0] < 0.96) & (pts[:, 1] > 0.04) & (pts[:, 1] < 0.96)
    pts, dist = pts[keep], dist[keep]
    sizes = 0.0010 + 0.0035 * np.exp(-dist / 0.18) * rng.random(len(dist))
    main = _plot(pts, sizes) * 0.9 + _plot([(ox, oy)], [0.08], blur=30) * 0.9
    big = rng.choice(len(pts), 9, replace=False)
    frags = _plot(pts[big], rng.uniform(0.006, 0.012, 9))
    return main, frags


# ---------- 레퍼런스에서 가져온 모티프 (사용자 제공 참고 이미지 2026-10-22) ----------

class _Pen:
    """4배 크기 캔버스에 0~1 좌표로 그리고, 구도 변주를 준 뒤 S 크기 필드로 줄인다."""

    def __init__(self):
        self.n = S * 4
        self.img = Image.new("L", (self.n, self.n), 0)
        self.d = ImageDraw.Draw(self.img)

    def _p(self, x, y):
        return x * self.n, y * self.n

    def line(self, x0, y0, x1, y1, w=0.003, v=255):
        self.d.line([self._p(x0, y0), self._p(x1, y1)], fill=v, width=max(1, round(w * self.n)))

    def circle(self, cx, cy, r, w=None, v=255):
        box = [*self._p(cx - r, cy - r), *self._p(cx + r, cy + r)]
        if w is None:
            self.d.ellipse(box, fill=v)
        else:
            self.d.ellipse(box, outline=v, width=max(1, round(w * self.n)))

    def rect(self, x0, y0, x1, y1, v=255):
        self.d.rectangle([*self._p(x0, y0), *self._p(x1, y1)], fill=v)

    def poly(self, pts, w=None, v=255):
        pts = [self._p(x, y) for x, y in pts]
        if w is None:
            self.d.polygon(pts, fill=v)
        else:
            self.d.line(pts + [pts[0]], fill=v, width=max(1, round(w * self.n)), joint="curve")

    def path(self, xs, ys, w=0.003, v=255):
        self.d.line([self._p(x, y) for x, y in zip(xs, ys)], fill=v, width=max(1, round(w * self.n)), joint="curve")

    def done(self, rng, rot_max=0, scale=(0.9, 1.05)):
        img = self.img
        k = rng.uniform(*scale)
        m = round(self.n * k)
        img = img.resize((m, m), Image.BICUBIC)
        canvas = Image.new("L", (self.n, self.n), 0)
        canvas.paste(img, ((self.n - m) // 2, (self.n - m) // 2))
        canvas = canvas.rotate(rng.uniform(-rot_max, rot_max), resample=Image.BICUBIC)
        return np.asarray(canvas.resize((S, S), Image.LANCZOS), dtype=float) / 255


def _varied(rot_max, scale=(0.9, 1.06)):
    """필드로 그리는 모티프에 구도 변주(가운데 축 기준 크기·회전)를 준다. 주 필드와 강조 필드에 같은 변주."""
    def wrap(fn):
        def run(rng):
            main, acc = fn(rng)
            k, t = rng.uniform(*scale), rng.uniform(-rot_max, rot_max)

            def move(f):
                if f is None:
                    return None
                img = Image.fromarray((np.clip(f, 0, 1) * 255).astype(np.uint8))
                m = round(S * k)
                img = img.resize((m, m), Image.BICUBIC)
                c = Image.new("L", (S, S), 0)
                c.paste(img, ((S - m) // 2, (S - m) // 2))
                return np.asarray(c.rotate(t, resample=Image.BICUBIC), dtype=float) / 255
            return move(main), move(acc)
        run.__doc__ = fn.__doc__
        return run
    return wrap


def _ramp(kind, i, j, g):
    """격자 칸 (i, j)의 0~1 값. kind 0: 대각선, 1: 위→아래, 2: 가운데가 큼."""
    u, v = i / (g - 1), j / (g - 1)
    if kind == 0:
        return (u + v) / 2
    if kind == 1:
        return v
    return 1 - min(1, np.hypot(u - 0.5, v - 0.5) / 0.7)


def m_dot_grid(rng):
    """점 격자. 한쪽으로 갈수록 점이 커진다 (Geometric Gradient: London, Paris, Miami)."""
    p, g = _Pen(), int(rng.choice([11, 13, 15]))
    kind = rng.integers(3)
    for i in range(g):
        for j in range(g):
            t = _ramp(kind, i, j, g)
            x, y = 0.12 + 0.76 * i / (g - 1), 0.12 + 0.76 * j / (g - 1)
            p.circle(x, y, (0.76 / (g - 1)) * 0.46 * (0.12 + 0.88 * t))
    return p.done(rng, 0), None


def m_square_grid(rng):
    """사각형 격자. 한쪽으로 갈수록 사각형이 커진다 (New York, Madrid)."""
    p, g = _Pen(), int(rng.choice([9, 11, 13]))
    kind = rng.integers(3)
    for i in range(g):
        for j in range(g):
            t = _ramp(kind, i, j, g)
            x, y = 0.12 + 0.76 * i / (g - 1), 0.12 + 0.76 * j / (g - 1)
            h = (0.76 / (g - 1)) * 0.44 * (0.1 + 0.9 * t)
            p.rect(x - h, y - h, x + h, y + h)
    return p.done(rng, 0), None


def m_line_fan(rng):
    """선 엮기. 두 변을 잇는 직선들이 곡선 테두리를 만든다 (Berlin, Zurich)."""
    p, n = _Pen(), int(rng.integers(26, 40))
    a, b = 0.1, 0.9
    for k in range(n + 1):
        t = k / n
        p.line(a, a + (b - a) * t, a + (b - a) * t, b, 0.0022)
    if rng.random() < 0.6:  # 반대쪽 모서리에도 한 벌
        for k in range(n + 1):
            t = k / n
            p.line(b, b - (b - a) * t, b - (b - a) * t, a, 0.0022)
    return p.done(rng, 90), None


def m_stripe_ramp(rng):
    """줄무늬 굵기 그라데이션. 한쪽은 굵은 띠, 반대쪽은 머리카락처럼 가늘다 (Porto, Barcelona, Ratcliffe)."""
    p = _Pen()
    n = int(rng.integers(12, 20))
    gaps = np.geomspace(1, rng.uniform(6, 12), n)
    gaps = gaps / gaps.sum() * 0.8
    y = 0.1
    for k in range(n):
        th = gaps[k] * rng.uniform(0.35, 0.6)
        p.rect(0.1, y, 0.9, y + th)
        y += gaps[k]
    return p.done(rng, 0), None


def m_circle_lattice(rng):
    """겹친 원 격자. 한쪽으로 갈수록 원이 커져 서로 겹친다 (Belfast)."""
    p, g = _Pen(), 7
    for i in range(g):
        for j in range(g):
            x, y = 0.14 + 0.72 * i / (g - 1), 0.14 + 0.72 * j / (g - 1)
            r = 0.72 / (g - 1) * (0.35 + 0.55 * (i + j) / (2 * g - 2))
            p.circle(x, y, r, 0.0035)
    return p.done(rng, 180, scale=(0.85, 0.95)), None


def m_nested_polygon(rng):
    """중첩 다각형. 바깥에서 안으로 굵은 테두리가 점점 가늘고 촘촘해진다 (Rome)."""
    p = _Pen()
    sides = int(rng.choice([3, 4, 6]))
    rot = rng.uniform(0, np.pi)
    r, k = 0.42, 0
    while r > 0.02:
        w = 0.022 * (r / 0.42) + 0.002
        pts = [(0.5 + r * np.cos(rot + 2 * np.pi * i / sides), 0.5 + r * np.sin(rot + 2 * np.pi * i / sides)) for i in range(sides)]
        p.poly(pts, w)
        r -= w * 2.2 + 0.006
        k += 1
    return p.done(rng, 0), None


def m_dash_field(rng):
    """짧은 선 필드. 격자 위 짧은 선의 각도가 흐르듯 바뀐다 (Brussel, Ratcliffe)."""
    p = _Pen()
    g = int(rng.integers(11, 15))
    mode = rng.integers(2)
    for i in range(g):
        for j in range(g):
            x, y = 0.1 + 0.8 * i / (g - 1), 0.1 + 0.8 * j / (g - 1)
            if mode == 0:  # 가로로 갈수록 기울기가 변한다
                ang, L = np.pi * (0.05 + 0.4 * i / (g - 1)), 0.5
            else:  # 가운데를 둘러싸며 휘어진다
                ang, L = np.arctan2(y - 0.5, x - 0.5) + np.pi / 2, 0.3 + 0.5 * np.hypot(x - 0.5, y - 0.5)
            h = 0.8 / (g - 1) * L
            p.line(x - h * np.cos(ang), y - h * np.sin(ang), x + h * np.cos(ang), y + h * np.sin(ang), 0.004)
    return p.done(rng, 20), None


def m_nested_corners(rng):
    """중첩 꺾쇠. 한 모서리에서 L자 선이 겹겹이 퍼지며 간격이 벌어진다 (Helsinki)."""
    p = _Pen()
    n = int(rng.integers(14, 22))
    for k in range(n):
        t = (k / (n - 1)) ** 1.6
        c = 0.70 * t  # 왼쪽 아래 모서리에서 떨어진 거리
        w = 0.002 + 0.01 * (1 - t)
        p.line(0.12 + c, 0.12, 0.12 + c, 0.88 - c, w)
        p.line(0.12 + c, 0.88 - c, 0.88, 0.88 - c, w)
    return p.done(rng, 0), None


@_varied(30)
def m_sliced_circle(rng):
    """줄무늬 원. 원 안을 사선 줄무늬로 채우고 굵기가 한쪽으로 커진다 (Tokyo)."""
    y, x = np.mgrid[0:S, 0:S] / S
    t = np.deg2rad(rng.uniform(25, 65))
    u = (x - 0.5) * np.cos(t) + (y - 0.5) * np.sin(t)
    pitch = 0.04
    duty = 0.15 + 0.7 * np.clip(u / 0.84 + 0.5, 0, 1)
    stripe = ((u / pitch) % 1 < duty).astype(float)
    disc = np.clip((0.4 - np.hypot(x - 0.5, y - 0.5)) * S, 0, 1)
    return stripe * disc, None


def m_sunburst(rng):
    """짧은 선의 방사형. 가운데를 비우고 여러 겹의 짧은 선이 바깥으로 뻗는다 (Ratcliffe)."""
    p = _Pen()
    n = int(rng.integers(40, 64))
    for k in range(n):
        a = 2 * np.pi * k / n
        r0 = rng.uniform(0.08, 0.2)
        L = rng.uniform(0.08, 0.26)
        p.line(0.5 + r0 * np.cos(a), 0.5 + r0 * np.sin(a), 0.5 + (r0 + L) * np.cos(a), 0.5 + (r0 + L) * np.sin(a), 0.0025)
    return p.done(rng, 0), None


def m_subdivided_grid(rng):
    """분할 격자. 오른쪽으로 갈수록 칸이 반씩 쪼개진다 (Ratcliffe)."""
    p = _Pen()
    x, w, rows = 0.1, 0.4, 1
    while x < 0.9 and w > 0.006:
        p.line(x, 0.1, x, 0.9, 0.0025)
        for r in range(1, rows):
            p.line(x, 0.1 + 0.8 * r / rows, min(0.9, x + w), 0.1 + 0.8 * r / rows, 0.0025)
        x += w
        w /= 2
        rows *= 2
    p.line(0.1, 0.1, 0.9, 0.1, 0.0025)
    p.line(0.1, 0.9, 0.9, 0.9, 0.0025)
    return p.done(rng, 0), None


@_varied(0)
def m_skyline(rng):
    """솟은 그림자. 바닥에서 솟은 기둥들이 위로 부드럽게 사라지고, 위에 원 하나가 뜬다 (Sonnet 001, 051)."""
    y, x = np.mgrid[0:S, 0:S] / S
    f = np.zeros((S, S))
    edges = np.sort(rng.uniform(0.08, 0.92, 6))
    edges = np.concatenate([[0.08], edges, [0.92]])
    for a, b in zip(edges[:-1], edges[1:]):
        top = rng.uniform(0.35, 0.8)
        col = (x >= a) & (x < b)
        f = np.maximum(f, col * np.clip((y - top) / 0.18, 0, 1) * (y < 0.9))
    cx, cy, r = 0.5, rng.uniform(0.15, 0.25), 0.07
    sun = np.clip((r - np.hypot(x - cx, y - cy)) * S, 0, 1)
    return f * 0.9, sun


@_varied(0)
def m_eclipse(rng):
    """밀린 원. 같은 원이 한 방향으로 밀리며 겹치고, 각 원은 한쪽이 밝다 (Sonnet 059, 153)."""
    y, x = np.mgrid[0:S, 0:S] / S
    ang = rng.uniform(0, 2 * np.pi)
    dx, dy = np.cos(ang), np.sin(ang)
    f = np.zeros((S, S))
    n = int(rng.integers(4, 7))
    for k in range(n):
        r = 0.34 - k * 0.04
        cx, cy = 0.5 + dx * (k - (n - 1) / 2) * 0.035, 0.5 + dy * (k - (n - 1) / 2) * 0.035
        inside = np.hypot(x - cx, y - cy) < r
        shade = np.clip(0.5 + ((x - cx) * dx + (y - cy) * dy) / (2 * r), 0, 1)
        f = np.where(inside, shade * (0.4 + 0.6 * (k + 1) / n), f)
    return f, None


@_varied(0)
def m_tunnel(rng):
    """사각 터널. 겹친 사각형이 안쪽으로 갈수록 밝아지며 깊이감을 만든다 (Sonnet 115)."""
    y, x = np.mgrid[0:S, 0:S] / S
    cy = rng.uniform(0.4, 0.55)
    d = np.maximum(np.abs(x - 0.5) / 0.42, np.abs(y - cy) / 0.32)
    steps = int(rng.integers(6, 10))
    level = np.floor(np.clip(1 - d, 0, 1) * steps) / steps
    fade = np.clip((y - (cy - 0.32)) / 0.64, 0, 1) ** 0.7
    return np.where(d < 1, level * (0.35 + 0.65 * fade), 0), None


@_varied(180)
def m_petals(rng):
    """회전 꽃잎. 원 여러 개가 중심을 돌며 겹쳐 소용돌이 꽃을 만든다 (Sonnet 094)."""
    y, x = np.mgrid[0:S, 0:S] / S
    n = int(rng.integers(5, 9))
    f = np.zeros((S, S))
    for k in range(n):
        a = 2 * np.pi * k / n
        cx, cy = 0.5 + 0.11 * np.cos(a), 0.5 + 0.11 * np.sin(a)
        dd = np.hypot(x - cx, y - cy)
        inside = dd < 0.2
        shade = np.clip(0.5 + ((x - cx) * np.cos(a + 1.2) + (y - cy) * np.sin(a + 1.2)) / 0.4, 0, 1)
        f = np.where(inside, np.maximum(f, shade * 0.85), f)
    return f, None


@_varied(0)
def m_blur_dots(rng):
    """흐린 점 격자. 크기가 제각각인 흐린 점이 줄지어 있다 (Sonnet 012)."""
    pts, sizes = [], []
    g = int(rng.choice([4, 5]))
    for i in range(g):
        for j in range(g):
            pts.append((0.16 + 0.68 * i / (g - 1), 0.16 + 0.68 * j / (g - 1)))
            sizes.append(rng.uniform(0.03, 0.07))
    return _plot(pts, sizes, blur=10) * 0.95, None


def m_dial(rng):
    """계기판. 원, 눈금, 십자선, 끊긴 호로 만든 기술 도면 같은 기호 (HUD 아이콘)."""
    p = _Pen()
    R = 0.34
    p.circle(0.5, 0.5, R, 0.003)
    p.circle(0.5, 0.5, R * rng.uniform(0.55, 0.7), 0.002)
    n = int(rng.choice([36, 48, 60]))
    for k in range(n):
        a = 2 * np.pi * k / n
        L = 0.035 if k % (n // 12) == 0 else 0.015
        p.line(0.5 + R * np.cos(a), 0.5 + R * np.sin(a), 0.5 + (R + L) * np.cos(a), 0.5 + (R + L) * np.sin(a), 0.0025)
    p.line(0.5 - R * 1.25, 0.5, 0.5 + R * 1.25, 0.5, 0.0018)
    p.line(0.5, 0.5 - R * 1.25, 0.5, 0.5 + R * 1.25, 0.0018)
    a0 = rng.uniform(0, 2 * np.pi)
    ts = np.linspace(a0, a0 + rng.uniform(1.2, 2.4), 200)
    acc = _Pen()
    acc.path(0.5 + R * 0.85 * np.cos(ts), 0.5 + R * 0.85 * np.sin(ts), 0.008)
    acc.circle(0.5 + R * np.cos(ts[-1]), 0.5 + R * np.sin(ts[-1]), 0.012)
    st = rng.bit_generator.state
    main = p.done(rng, 0)
    rng.bit_generator.state = st
    return main, acc.done(rng, 0)


def _wire(p, pts3, tilt, w):
    """3D 점 목록을 기울여 2D로 그린다."""
    x, y, z = pts3
    y2 = y * np.cos(tilt) - z * np.sin(tilt)
    p.path(0.5 + x, 0.5 + y2, w)


def m_wire_sphere(rng):
    """와이어프레임 구. 위도·경도 선으로 짠 기울어진 공 (수학 도형)."""
    p = _Pen()
    R, tilt = 0.34, rng.uniform(0.3, 0.7)
    t = np.linspace(0, 2 * np.pi, 400)
    for lat in np.linspace(-0.8, 0.8, 7):
        r = R * np.cos(lat * np.pi / 2)
        _wire(p, (r * np.cos(t), np.full_like(t, R * np.sin(lat * np.pi / 2)), r * np.sin(t)), tilt, 0.0022)
    for lon in np.linspace(0, np.pi, 8, endpoint=False):
        _wire(p, (R * np.cos(t) * np.cos(lon), R * np.sin(t), R * np.cos(t) * np.sin(lon)), tilt, 0.0022)
    return p.done(rng, 30), None


def m_hyperboloid(rng):
    """모래시계 실 엮기. 위아래 두 원을 비튼 직선으로 이어 가운데가 잘록해진다 (수학 도형)."""
    p = _Pen()
    n, R, H = int(rng.integers(36, 56)), 0.3, 0.32
    twist = rng.uniform(2.2, 2.8)
    tilt = rng.uniform(0.15, 0.35)
    for k in range(n):
        a = 2 * np.pi * k / n
        x0, z0 = R * np.cos(a), R * np.sin(a)
        x1, z1 = R * np.cos(a + twist), R * np.sin(a + twist)
        _wire(p, (np.array([x0, x1]), np.array([-H, H]), np.array([z0, z1])), tilt, 0.0018)
    t = np.linspace(0, 2 * np.pi, 300)
    for yy in (-H, H):
        _wire(p, (R * np.cos(t), np.full_like(t, yy), R * np.sin(t)), tilt, 0.003)
    return p.done(rng, 20), None


def m_coil(rng):
    """겹친 고리. 같은 고리가 한 방향으로 밀리며 이어진다 (슬링키, 수학 도형)."""
    p = _Pen()
    n = int(rng.integers(12, 20))
    t = np.linspace(0, 2 * np.pi, 300)
    for k in range(n):
        cx = 0.28 + 0.44 * k / (n - 1)
        p.path(cx + 0.14 * np.cos(t) * 0.45, 0.5 + 0.2 * np.sin(t), 0.0022)
    return p.done(rng, 45), None


@_varied(180)
def m_venn(rng):
    """겹친 원. 원 두세 개가 겹치고 교집합만 촘촘한 선으로 채운다 (수학 도형)."""
    y, x = np.mgrid[0:S, 0:S] / S
    n = int(rng.choice([2, 3]))
    r = 0.22
    cs = [(0.5 + 0.12 * np.cos(2 * np.pi * k / n + 0.3), 0.5 + 0.12 * np.sin(2 * np.pi * k / n + 0.3)) for k in range(n)]
    ring = np.zeros((S, S))
    inside = np.ones((S, S), bool)
    for cx, cy in cs:
        d = np.hypot(x - cx, y - cy)
        ring = np.maximum(ring, np.exp(-((d - r) / 0.0025) ** 2))
        inside &= d < r
    hatch = ((((x + y) / 0.014) % 1) < 0.3) * inside
    return ring, hatch.astype(float)


@_varied(15)
def m_sparkle(rng):
    """반짝임. 오목한 네 갈래 별 하나와 작은 별 몇 개 (별 모양 레퍼런스)."""
    y, x = np.mgrid[0:S, 0:S] / S

    def star(cx, cy, r, p=0.45):
        u, v = np.abs(x - cx) / r, np.abs(y - cy) / r
        return np.clip((1 - (u ** p + v ** p)) * 40, 0, 1)

    main = star(0.5, 0.5, rng.uniform(0.32, 0.4))
    acc = np.zeros((S, S))
    for _ in range(int(rng.integers(2, 4))):
        acc = np.maximum(acc, star(rng.uniform(0.15, 0.85), rng.uniform(0.15, 0.85), rng.uniform(0.04, 0.08)))
    acc *= main < 0.5
    return main, acc


@_varied(180)
def m_swirl_star(rng):
    """소용돌이 별. 원 안의 날개가 바깥으로 갈수록 휘어진다 (별 모양 레퍼런스)."""
    y, x = np.mgrid[0:S, 0:S] / S
    d = np.hypot(x - 0.5, y - 0.5)
    th = np.arctan2(y - 0.5, x - 0.5)
    n = int(rng.integers(8, 16))
    twist = rng.uniform(4, 9) * rng.choice([-1, 1])
    blades = (np.cos(n * (th + twist * d)) > rng.uniform(-0.2, 0.3)).astype(float)
    disc = np.clip((0.36 - d) * S, 0, 1) * np.clip((d - 0.04) * S, 0, 1)
    return blades * disc, None


@_varied(180)
def m_blob(rng):
    """흐린 덩어리. 울퉁불퉁한 덩어리의 한쪽 가장자리가 번진다 (grainy shapes)."""
    y, x = np.mgrid[0:S, 0:S] / S
    th = np.arctan2(y - 0.5, x - 0.5)
    d = np.hypot(x - 0.5, y - 0.5)
    r = 0.26 * np.ones_like(th)
    for k in range(2, 6):
        r += rng.uniform(0, 0.06) / k * 2 * np.cos(k * th + rng.uniform(0, 2 * np.pi))
    soft = 0.01 + 0.08 * (0.5 + 0.5 * np.cos(th - rng.uniform(0, 2 * np.pi)))  # 한쪽만 번진다
    return np.clip((r - d) / soft + 0.5, 0, 1), None


MOTIFS = {"ribbon": m_ribbon, "streaks": m_streaks, "rings": m_rings, "sun_horizon": m_sun_horizon,
          "wave_lines": m_wave_lines, "radial": m_radial, "scope": m_scope, "equalizer": m_equalizer,
          "spiral": m_spiral, "lissajous": m_lissajous, "contour": m_contour, "warp_grid": m_warp_grid,
          "particles": m_particles,
          "dot_grid": m_dot_grid,
          "square_grid": m_square_grid,
          "line_fan": m_line_fan,
          "stripe_ramp": m_stripe_ramp,
          "circle_lattice": m_circle_lattice,
          "nested_polygon": m_nested_polygon,
          "dash_field": m_dash_field,
          "nested_corners": m_nested_corners,
          "sliced_circle": m_sliced_circle,
          "sunburst": m_sunburst,
          "subdivided_grid": m_subdivided_grid,
          "skyline": m_skyline,
          "eclipse": m_eclipse,
          "tunnel": m_tunnel,
          "petals": m_petals,
          "blur_dots": m_blur_dots,
          "dial": m_dial,
          "wire_sphere": m_wire_sphere,
          "hyperboloid": m_hyperboloid,
          "coil": m_coil,
          "venn": m_venn,
          "sparkle": m_sparkle,
          "swirl_star": m_swirl_star,
          "blob": m_blob}


# ---------- 스타일: 필드(0~1) → 칠할 비율(0~1) ----------

def grain(f, rng, amount=0.55):
    """점묘 그레인: 밝기 확률로 점을 찍고 원래 그라데이션과 섞는다."""
    return np.clip((1 - amount) * f + amount * (rng.random(f.shape) < f), 0, 1)


def halftone(f, rng, pitch=9.0, angle=45):
    """하프톤: 45° 격자의 점 크기로 명암을 낸다."""
    y, x = np.mgrid[0:S, 0:S].astype(float)
    t = np.deg2rad(angle)
    u, v = x * np.cos(t) + y * np.sin(t), -x * np.sin(t) + y * np.cos(t)
    du, dv = (u % pitch) - pitch / 2, (v % pitch) - pitch / 2
    d = np.hypot(du, dv)
    r = pitch * 0.62 * np.sqrt(_blur(f, 2))
    return np.clip(r - d + 0.5, 0, 1)


def lines(f, rng, pitch=7.0, angle=35):
    """가는 선 해칭: 기울어진 평행선의 굵기로 명암을 낸다."""
    y, x = np.mgrid[0:S, 0:S].astype(float)
    t = np.deg2rad(angle)
    u = x * np.cos(t) + y * np.sin(t)
    dist = np.abs((u % pitch) - pitch / 2)
    w = pitch * 0.5 * _blur(f, 1.5)
    return np.clip(w - dist + 0.5, 0, 1) * (f > 0.02)


def glow(f, rng):
    """빛 번짐: 점 없이 넓게 퍼진 빛과 또렷한 심을 겹친다."""
    g = 0.55 * _blur(f, 22) + 0.6 * _blur(f, 5) + 0.7 * f
    return 1 - np.exp(-1.6 * g)


STYLES = {"grain": grain, "halftone": halftone, "lines": lines, "glow": glow}

# 면으로 된 모티프는 네 스타일 모두, 가는 선으로 된 모티프는 하프톤·해칭을 쓰면 선이 끊겨 사라지므로 grain·glow만 쓴다.
AREA = {"ribbon", "streaks", "sun_horizon", "particles", "equalizer",
        "skyline", "eclipse", "tunnel", "petals", "blur_dots", "blob", "sparkle"}
STYLES_FOR = {m: (list(STYLES) if m in AREA else ["grain", "glow"]) for m in MOTIFS}


# ---------- 색 칠하기 ----------
# 팔레트 (fg = 포인트 컬러, accent = 두 번째 색. 보통 화이트)
#   mono    : 모두 fg 한 색
#   accent  : 모양은 fg, 테두리·중심선 같은 세부는 accent
#   duotone : 어두운 곳은 fg, 가장 밝은 곳은 accent로 자연스럽게 넘어간다
#   split   : 모양을 반으로 가르거나(half) 동심 띠로 나눠(bands) 번갈아 fg / accent
#   tones   : fg의 명도를 어둡게·원래·밝게 3단계로 나눠 밝기에 따라 칠한다
# bg_glow=True면 배경 가운데에 fg가 아주 옅게 번진다.
PALETTES = ["mono", "accent", "duotone", "split", "tones"]


def _shift_l(color, d):
    h, l, s = colorsys.rgb_to_hls(*(_hex(color) / 255))
    r, g, b = colorsys.hls_to_rgb(h, min(max(l + d, 0), 1), s)
    return np.array([r, g, b]) * 255


def _mix(a, b, t):
    return a[None, None] * (1 - t[..., None]) + b[None, None] * t[..., None]


def _to_img(layers, base):
    rgb = base
    for v, color in layers:  # color: (3,) 또는 (S, S, 3)
        c = color if color.ndim == 3 else color[None, None]
        rgb = rgb * (1 - v[..., None]) + c * v[..., None]
    buf = io.BytesIO()
    Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(buf, "PNG")
    return buf.getvalue()


def draw_png(motif, seed, bg, fg, style="grain", accent=None, palette="accent", bg_glow=False):
    if style not in STYLES_FOR[motif]:
        raise ValueError(f"{motif}에는 {STYLES_FOR[motif]} 스타일만 쓴다")
    rng = _rng(seed)
    main, acc = MOTIFS[motif](rng)
    main = np.clip(main, 0, 1)
    v = STYLES[style](main, rng)
    a = _hex(accent or "#ffffff")
    p = _hex(fg)
    y, x = np.mgrid[0:S, 0:S] / S
    base = np.broadcast_to(_hex(bg), (S, S, 3)).copy()
    if bg_glow:
        base = base + (p - _hex(bg))[None, None] * 0.26 * np.exp(-((x - 0.5) ** 2 + (y - 0.5) ** 2) / 0.09)[..., None]

    if palette == "duotone":
        color = _mix(p, a, np.clip((_blur(main, 2) - 0.55) / 0.4, 0, 1))
    elif palette == "split":
        if rng.random() < 0.5:  # 반으로 가르기 (가운데를 지나는 선, 각도는 곡마다)
            t = rng.uniform(0, np.pi)
            mask = ((x - 0.5) * np.cos(t) + (y - 0.5) * np.sin(t)) > 0
        else:  # 가운데에서 퍼지는 동심 띠
            mask = (np.hypot(x - 0.5, y - 0.5) // rng.uniform(0.07, 0.12)) % 2 == 1
        color = _mix(p, a, mask.astype(float))
    elif palette == "tones":
        tones = [_shift_l(fg, -0.15), p, _shift_l(fg, 0.18)]
        lv = np.digitize(_blur(main, 2), [0.35, 0.7])
        color = np.stack(tones)[lv]
    else:
        color = p
    layers = [(v, color)]
    if acc is not None and palette != "mono":
        av = glow(np.clip(acc, 0, 1), rng) if style == "glow" else np.clip(acc, 0, 1)
        layers.append((av, a if palette in ("accent", "duotone", "tones") else p))
    elif acc is not None:
        layers.append((np.clip(acc, 0, 1), p))
    return _to_img(layers, base)


def draw(motif, seed, bg, fg, style="grain", accent=None, palette="accent", bg_glow=False):
    """카드 템플릿의 MEDIA 자리에 넣는 <img> 태그."""
    png = draw_png(motif, seed, bg, fg, style, accent, palette, bg_glow)
    return '<img src="data:image/png;base64,' + base64.b64encode(png).decode() + '">'


def ribbon(seed, bg, fg):  # 이전 호출 방식 호환
    return draw("ribbon", seed, bg, fg, palette="mono")


def streaks(seed, bg, fg):
    return draw("streaks", seed, bg, fg, palette="mono")
