"""트랙 카드 중앙 그래픽 생성기.

참고 이미지에서 뽑은 공통 원칙
- 굵은 덩어리 대신 부드러운 그라데이션 + 고운 노이즈(그레인) 질감
- 단순한 기하 형태 하나에 집중, 넓은 여백
- 색은 배경 무채색 + 한 가지 색(포인트 컬러 또는 화이트)

모티프는 트랙의 장르와 리뷰를 읽고 고른다. 지금은 시안용 2개만 있다.
- ribbon : 곡선 리본 (예: NCT 127 'Fact Check' 참고 이미지)
- streaks: 위아래로 번지는 빛줄기 (예: 몬스타엑스 '대동단결' 참고 이미지)
"""
import base64, io, zlib
import numpy as np
from PIL import Image

S = 704  # 화면 프레임 안쪽 크기(px)


def _rng(seed):
    return np.random.default_rng(zlib.crc32(str(seed).encode()))


def _hex(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], dtype=float)


def _grain(field, rng, amount=0.55):
    """그라데이션 위에 점묘 그레인: 밝기 확률로 점을 찍고 원래 그라데이션과 섞는다."""
    field = np.clip(field, 0, 1)
    dots = (rng.random(field.shape) < field).astype(float)
    return np.clip((1 - amount) * field + amount * dots, 0, 1)


def _to_img(v, bg, fg):
    rgb = _hex(bg)[None, None] * (1 - v[..., None]) + _hex(fg)[None, None] * v[..., None]
    buf = io.BytesIO()
    Image.fromarray(rgb.astype(np.uint8)).save(buf, "PNG")
    return '<img src="data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode() + '">'


def ribbon(seed, bg, fg, waves=1.3):
    """S자 리본. 가장자리 쪽이 밝고 바깥으로 번지는 형태."""
    rng = _rng(seed)
    y, x = np.mgrid[0:S, 0:S] / S
    phase = rng.uniform(0, np.pi)
    cx = 0.5 + 0.2 * np.sin(2 * np.pi * waves * y + phase)
    w = 0.09 + 0.05 * np.sin(np.pi * y + phase)  # 폭 변화
    d = (x - cx) / w
    core = np.exp(-np.clip(d, 0, None) ** 2 * 1.6) * np.exp(-np.clip(-d, 0, None) ** 2 * 0.35)  # 한쪽은 또렷, 한쪽은 번짐
    edge = np.exp(-((d - 0.15) ** 2) * 60) * 0.35  # 밝은 테두리선
    ghost = 0.12 * np.exp(-((x - (cx + 0.32)) / 0.16) ** 2)  # 뒤쪽 희미한 주름
    return _to_img(_grain(core + edge + ghost, rng), bg, fg)


def streaks(seed, bg, fg, cols=7):
    """가운데 또렷한 띠에서 위아래로 빛이 번져 나가는 기둥들."""
    rng = _rng(seed)
    y, x = np.mgrid[0:S, 0:S] / S
    # 겹치지 않게 기둥 폭과 간격을 차례로 배치
    w = rng.uniform(0.04, 0.12, cols)
    g = rng.uniform(0.015, 0.05, cols - 1)
    total = w.sum() + g.sum()
    left = (1 - total) / 2
    field = np.zeros((S, S))
    mid, half = 0.42, 0.05
    for i in range(cols):
        a, b = left, left + w[i]
        left = b + (g[i] if i < cols - 1 else 0)
        soft = 0.006  # 기둥 가장자리를 살짝 부드럽게
        col = np.clip((x - a) / soft, 0, 1) * np.clip((b - x) / soft, 0, 1)
        up, down = rng.uniform(0.08, 0.22), rng.uniform(0.05, 0.14)
        dist = np.abs(y - mid) - half
        trail = np.where(dist <= 0, 1.0, np.exp(-dist / np.where(y < mid, up, down)) * 0.9)
        field = np.maximum(field, col * trail)
    glow = 0.18 * np.exp(-((y - mid) / 0.18) ** 2)
    return _to_img(_grain(np.maximum(field, glow), rng, 0.6), bg, fg)
