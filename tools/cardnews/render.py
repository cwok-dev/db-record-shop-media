"""카드뉴스 HTML 템플릿을 1080x1350 PNG로 렌더링."""
import base64, html, mimetypes, pathlib
from playwright.sync_api import sync_playwright
from point_color import point_colors, alt_colors, WHITE, BLACK
import graphics

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE / "template_card.html"
STAR = '<path d="M12 1.5l3.1 6.6 7.2.9-5.3 5 1.4 7.1L12 17.6 5.6 21.1 7 14 1.7 9l7.2-.9z"/>'


def stars_svg(score, size=None):
    """5점 만점, 0.5 단위 별점. 색은 포인트 컬러(--pt)."""
    out = []
    for i in range(5):
        fill = max(0.0, min(1.0, score - i)) * 100  # 100, 50, 0
        gid = f"g{i}"
        style = f' style="width:{size}px;height:{size}px"' if size else ""
        out.append(
            f'<svg viewBox="0 0 24 24"{style}><defs><linearGradient id="{gid}">'
            f'<stop offset="{fill}%" stop-color="var(--pt)"/><stop offset="{fill}%" stop-color="transparent"/>'
            f'</linearGradient></defs><g fill="url(#{gid})" stroke="var(--pt)" stroke-width="1.6" '
            f'stroke-linejoin="round">{STAR}</g></svg>')
    return "".join(out)


def rec_html(recommended):
    """추천 트랙이면 그림 좌상단에 인덱스 표시. 아니면 표시하지 않음."""
    return '<div class="idx">추천</div>' if recommended else ""


def noise_tile(size=160, seed=7, alpha=14):
    """프레임·견출지에 까는 미세한 질감 타일(투명 바탕에 흑백 점)."""
    import io, numpy as np
    from PIL import Image
    rng = np.random.default_rng(seed)
    v = rng.random((size, size))
    rgba = np.zeros((size, size, 4), np.uint8)
    rgba[..., :3] = np.where(v[..., None] > .5, 255, 0)
    rgba[..., 3] = (np.abs(v - .5) * 2 * alpha).astype(np.uint8)
    buf = io.BytesIO(); Image.fromarray(rgba).save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


NOISE = None


def data_uri(path):
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(pathlib.Path(path).read_bytes()).decode()


def html_to_png(doc, out_png, size=(1080, 1350), transparent=False):
    tmp = HERE / "_render.html"
    tmp.write_text(doc, encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": size[0], "height": size[1]})
        pg.goto(tmp.as_uri(), wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        if 'data-ready' in doc or "dataset.ready" in doc:
            pg.wait_for_function("document.body.dataset.ready === '1'")
        pg.screenshot(path=str(HERE / out_png), omit_background=transparent)
        b.close()
    tmp.unlink()


def render_card(out_png, *, cover, artist, title, oneline, score, page,
                theme="album", recommended=None, media=None):
    """album: media 없이 표지 사용 / track: media에 그래픽 SVG, recommended에 True/False."""
    """theme: album(흰 배경) / track(검은 배경) / alt(두 번째 게시물 커버, 포인트 컬러 배경)"""
    alt_bg, alt_ink = alt_colors(HERE / cover)
    if theme == "alt":
        pt, pt_label = alt_ink, point_colors(HERE / cover, WHITE)[1]
    else:
        pt, pt_label = point_colors(HERE / cover, WHITE if theme == "album" else BLACK)
    media = media or f'<img src="{data_uri(HERE / cover)}">'
    global NOISE
    NOISE = NOISE or noise_tile()
    doc = TEMPLATE.read_text(encoding="utf-8")
    for k, v in {
        "NOISE": NOISE, "ALT_BG": alt_bg, "ALT_INK": alt_ink,
        "THEME": theme, "PAGE": page, "POINT": pt, "POINT_LABEL": pt_label, "MEDIA": media, "REC": rec_html(recommended),
        "STARS": stars_svg(score), "ARTIST": html.escape(artist), "TITLE": html.escape(title),
        "ONELINE": html.escape(oneline),
    }.items():
        doc = doc.replace("{{" + k + "}}", v)
    html_to_png(doc, out_png)
    return pt, pt_label


if __name__ == "__main__":
    common = dict(cover="sample_cover.png", artist="ARTIST NAME", score=3.5,
                  oneline="한 줄 평이 들어갈 자리입니다. 최대 세 줄까지 왼쪽 정렬로 표시되며, 넘치면 말줄임 처리됩니다.")
    pt, _ = point_colors(HERE / "sample_cover.png", BLACK)
    render_card("mock_album.png", title="Album Title Here", page="01/06", theme="album", **common)
    render_card("mock_album_alt.png", title="Album Title Here", page="01/04", theme="alt", **common)
    render_card("mock_track_ribbon.png", title="Fact Check", page="02/06", theme="track", recommended=True,
                media=graphics.ribbon("Fact Check", BLACK, pt), **{**common, "artist": "NCT 127"})
    render_card("mock_track_streaks.png", title="대동단결", page="03/06", theme="track", recommended=False,
                media=graphics.streaks("대동단결", BLACK, WHITE), **{**common, "artist": "MONSTA X"})
    print("done")
