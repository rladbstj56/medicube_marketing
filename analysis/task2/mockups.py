# -*- coding: utf-8 -*-
"""포트폴리오용 디바이스 목업 생성 — PIL로 스마트폰·태블릿·브라우저 프레임과 CRM 화면.

Behance식 포트폴리오는 시안을 '화면 안에 놓인 모습'으로 보여 준다. 이 모듈은
`tmp/portfolio/mockups/`에 다음을 만든다.

- 스마트폰 프레임(다이내믹 아일랜드·베젤·그림자)에 숏폼 3컷·엔드카드·CRM 화면을 합성
- 태블릿(iPad) 프레임에 포스터·내부 개선안·홈쇼핑 1–2면 지면을 합성
- 브라우저 창 프레임(상단 크롬)에 웹 지면을 합성
- CRM 화면 자체(온사이트 배너·앱푸시 2종·배송 후 알림 2종)를 새로 그린다

화면 문구는 저장소 현행 문서의 CRM 표에 적힌 문장만 쓴다. 발송·집행 기록이
없는 설계안이므로 화면은 '시안'이며, 실제 앱 캡처가 아니다.
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'tmp/portfolio/mockups'
FONT_R = str(HERE / 'fonts/NotoSansKR-Regular.ttf')
FONT_B = str(HERE / 'fonts/NotoSansKR-Bold.ttf')

INK = (24, 24, 27)
PAPER = (248, 247, 245)
CRIMSON = (155, 27, 39)
MUTED = (128, 122, 116)
LINE = (222, 216, 209)
BLUSH = (253, 244, 245)

# 2030 파트 화면용 아쿠아 팔레트 — 포스터·엔드카드 v3의 물빛과 같은 계열
TEAL = (22, 100, 116)          # #166474 — 딥 워터 틸(CTA·아이콘)
AQUA_MIST = (232, 243, 247)    # #E8F3F7 — 미스트 아쿠아(히어로 띠)
AQUA_LINE = (207, 227, 234)    # #CFE3EA

SCREEN_RATIO = 0.4613          # iPhone 15 Pro 1179×2556


def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT_R, size)


def text(d, xy, s, size, color=INK, bold=False, anchor='la', spacing=1.0):
    f = font(size, bold)
    if spacing != 1.0:
        # 자간이 필요한 짧은 라벨은 글자별로 그린다
        x, y = xy
        for ch in s:
            d.text((x, y), ch, font=f, fill=color, anchor=anchor)
            x += d.textlength(ch, font=f) + size * (spacing - 1)
        return
    d.text(xy, s, font=f, fill=color, anchor=anchor)


def wrap(d, s, size, width, bold=False):
    f = font(size, bold)
    lines, cur = [], ''
    for word in s.split(' '):
        trial = word if not cur else cur + ' ' + word
        if d.textlength(trial, font=f) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def rounded_mask(size, radius):
    mask = Image.new('L', size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius, fill=255)
    return mask


def compose_with_shadow(body, blur=14, alpha=78, offset=(0, 12), pad=48):
    """기기 실루엣을 그대로 흐려 바닥 그림자로 깔고, 그 위에 기기를 얹는다."""
    silhouette = body.split()[3]
    layer = Image.new('RGBA', (body.width + 2 * pad, body.height + 2 * pad), (0, 0, 0, 0))
    tint = Image.new('RGBA', body.size, (0, 0, 0, 255))
    tint.putalpha(silhouette.point(lambda v: int(v * alpha / 255)))
    layer.alpha_composite(tint, (pad + offset[0], pad + offset[1]))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    layer.alpha_composite(body, (pad, pad))
    return layer.crop(layer.getbbox())


# ── 화면 그리기 ──────────────────────────────────────────────────────────────

def _status_bar(d, w, color=(255, 255, 255), y=0, clock=True):
    if clock:
        text(d, (w * 0.10, y + w * 0.055), '9:41', int(w * 0.052), color, True, anchor='lm')
    for i, bw in enumerate((0.020, 0.014, 0.010)):
        d.rounded_rectangle([w * 0.80 + i * w * 0.035, y + w * 0.048,
                             w * 0.80 + i * w * 0.035 + bw * w, y + w * 0.048 + w * 0.022],
                            w * 0.004, fill=color)
    d.rounded_rectangle([w * 0.90, y + w * 0.046, w * 0.95, y + w * 0.062],
                        w * 0.004, outline=color, width=max(2, int(w * 0.004)))


def _gradient(w, h, top, bottom):
    img = Image.new('RGB', (w, h), top)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img


def shot_crop(path, size):
    im = path.convert('RGB') if isinstance(path, Image.Image) else Image.open(path).convert('RGB')
    tw, th = size
    scale = max(tw / im.width, th / im.height)
    im = im.resize((int(im.width * scale) + 1, int(im.height * scale) + 1), Image.LANCZOS)
    left = (im.width - tw) // 2
    top = (im.height - th) // 2
    return im.crop((left, top, left + tw, top + th))


def screen_on_site_banner(w, h):
    """자사몰 온사이트 배너 시안 — 비교 랜딩을 나온 고객에게 5가지 모드를 다시 보여준다."""
    img = Image.new('RGB', (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)
    _status_bar(d, w)
    text(d, (w * 0.5, h * 0.042), 'MEDICUBE', int(w * 0.030), INK, True, anchor='ma', spacing=1.6)
    text(d, (w * 0.5, h * 0.074), 'AGE-R', int(w * 0.024), MUTED, anchor='ma', spacing=1.4)

    # 제품 사진만 쓱 떼어 쓴다 — 포스터 문구를 화면 위에서 겹쳐 쓰지 않는다
    hero_h = int(h * 0.272)
    src = Image.open(ROOT / 'private_submission/2030/glow_endcard_aqua_v3.png').convert('RGB')
    product = src.crop((150, 700, 930, 1215))
    scale = (hero_h * 0.94) / product.height
    product = product.resize((int(product.width * scale), int(hero_h * 0.94)), Image.LANCZOS)
    band = Image.new('RGB', (w, hero_h), AQUA_MIST)
    band.paste(product, ((w - product.width) // 2, int(hero_h * 0.03)))
    img.paste(band, (0, int(h * 0.098)))
    d = ImageDraw.Draw(img)

    y = int(h * 0.098) + hero_h + int(h * 0.030)
    text(d, (w * 0.08, y), '내 피부 고민부터', int(w * 0.058), INK, True)
    text(d, (w * 0.08, y + int(h * 0.042)), '고르는 5가지 모드', int(w * 0.058), INK, True)
    y += int(h * 0.098)
    for label, sub in (('속건조 · 보습', '아침 기초 뒤 당김'), ('탄력 · 리프팅', '야근 다음 날 처짐'),
                       ('물광 · 피부결', '화장 전 푸석함')):
        d.rounded_rectangle([w * 0.08, y, w * 0.92, y + h * 0.056], w * 0.018,
                            fill=(250, 250, 251), outline=AQUA_LINE)
        d.ellipse([w * 0.105, y + h * 0.018, w * 0.122, y + h * 0.038], outline=TEAL, width=max(2, int(w * 0.005)))
        text(d, (w * 0.142, y + h * 0.010), label, int(w * 0.036), INK, True)
        text(d, (w * 0.142, y + h * 0.033), sub, int(w * 0.029), MUTED)
        y += int(h * 0.066)

    # 온사이트 배너 — 이탈 지점에서 다시 부르는 자리
    by = h - int(h * 0.232)
    d.rounded_rectangle([w * 0.06, by, w * 0.94, by + int(h * 0.150)], w * 0.024, fill=TEAL)
    text(d, (w * 0.10, by + h * 0.018), '내 피부 고민별 5가지 모드', int(w * 0.042), (255, 255, 255), True)
    text(d, (w * 0.10, by + h * 0.054), '숏폼에서 보던 모드를 앱에서 이어서', int(w * 0.030), (214, 236, 243))
    d.rounded_rectangle([w * 0.10, by + h * 0.088, w * 0.62, by + h * 0.134], int(h * 0.023), fill=(255, 255, 255))
    text(d, (w * 0.36, by + h * 0.111), '내 모드 확인하기', int(w * 0.032), TEAL, True, anchor='mm')
    _tab_bar(d, w, h)
    return img


def _tab_bar(d, w, h):
    y = h - int(h * 0.085)
    d.line([(0, y), (w, y)], fill=LINE, width=max(2, int(w * 0.004)))
    labels = ('홈', '쇼핑', '루틴', '마이')
    for i, label in enumerate(labels):
        cx = w * (0.135 + i * 0.245)
        d.ellipse([cx - w * 0.018, y + h * 0.018, cx + w * 0.018, y + h * 0.042], outline=MUTED, width=max(2, int(w * 0.004)))
        text(d, (cx, y + h * 0.050), label, int(w * 0.028), MUTED, anchor='ma')


def screen_lock(title, body, w, h, photo):
    """앱푸시 시안 — 잠금화면 위 알림 카드."""
    bg = shot_crop(str(photo), (w, h))
    bg = bg.filter(ImageFilter.GaussianBlur(int(w * 0.05)))
    dark = Image.new('RGBA', (w, h), (14, 12, 12, 150))
    img = Image.alpha_composite(bg.convert('RGBA'), dark).convert('RGB')
    d = ImageDraw.Draw(img)
    _status_bar(d, w)
    text(d, (w * 0.5, h * 0.14), '9:41', int(w * 0.20), (255, 255, 255), True, anchor='mm')
    text(d, (w * 0.5, h * 0.205), '11월 22일 토요일', int(w * 0.036), (236, 230, 224), anchor='mm')

    cy = h * 0.30
    ch = h * 0.20
    d.rounded_rectangle([w * 0.05, cy, w * 0.95, cy + ch], w * 0.035, fill=(250, 249, 247))
    d.rounded_rectangle([w * 0.08, cy + ch * 0.12, w * 0.08 + w * 0.11, cy + ch * 0.12 + w * 0.11], w * 0.022, fill=TEAL)
    text(d, (w * 0.08 + w * 0.055, cy + ch * 0.12 + w * 0.055), 'M', int(w * 0.055), (255, 255, 255), True, anchor='mm')
    text(d, (w * 0.215, cy + ch * 0.14), '메디큐브', int(w * 0.036), MUTED, True)
    text(d, (w * 0.92, cy + ch * 0.14), '지금', int(w * 0.030), MUTED, anchor='ra')
    y = cy + ch * 0.30
    for line in wrap(d, title, int(w * 0.046), w * 0.70, True)[:2]:
        text(d, (w * 0.215, y), line, int(w * 0.046), INK, True)
        y += int(w * 0.058)
    for line in wrap(d, body, int(w * 0.038), w * 0.70)[:3]:
        text(d, (w * 0.215, y), line, int(w * 0.038), (86, 82, 78))
        y += int(w * 0.048)

    text(d, (w * 0.5, h * 0.90), '알림을 열려면 위로 쓸어올리세요', int(w * 0.030), (228, 222, 216), anchor='mm')
    return img


def screen_message_list(w, h):
    """배송 후 CRM 시안 — 스냅푸시(D+0)와 알림톡(D+14)."""
    img = _gradient(w, h, (242, 240, 236), (232, 228, 222))
    d = ImageDraw.Draw(img)
    _status_bar(d, w, (40, 40, 44))
    text(d, (w * 0.08, h * 0.075), '메시지', int(w * 0.070), INK, True)
    text(d, (w * 0.92, h * 0.085), '편집', int(w * 0.034), MUTED, anchor='ra')

    cards = (
        ('스냅푸시 · D+0', '큰 글씨 사용법',
         '손잡이는 아래쪽을 잡으면 버튼이 덜 눌립니다. 사용 전 확인할 3가지를 큰 글씨로 안내합니다.', '방금'),
        ('알림톡 · D+14', '2주차 체감 안내',
         '사용 2주, 체감 시기와 강도는 피부 상태에 따라 다릅니다. 단계별 사용 강도를 안내합니다.', '2주 전'),
    )
    y = h * 0.145
    for tag, title, body, when in cards:
        ch = h * 0.30
        d.rounded_rectangle([w * 0.05, y, w * 0.95, y + ch], w * 0.035, fill=(255, 255, 255))
        d.rounded_rectangle([w * 0.085, y + ch * 0.10, w * 0.085 + w * 0.10, y + ch * 0.10 + w * 0.10], w * 0.022, fill=CRIMSON)
        text(d, (w * 0.085 + w * 0.05, y + ch * 0.10 + w * 0.05), 'M', int(w * 0.050), (255, 255, 255), True, anchor='mm')
        text(d, (w * 0.215, y + ch * 0.10), tag, int(w * 0.030), CRIMSON, True)
        text(d, (w * 0.92, y + ch * 0.10), when, int(w * 0.030), MUTED, anchor='ra')
        text(d, (w * 0.215, y + ch * 0.18), title, int(w * 0.044), INK, True)
        yy = y + ch * 0.31
        for line in wrap(d, body, int(w * 0.034), w * 0.66)[:3]:
            text(d, (w * 0.215, yy), line, int(w * 0.034), (96, 92, 88))
            yy += int(w * 0.046)
        d.rounded_rectangle([w * 0.215, y + ch * 0.76, w * 0.62, y + ch * 0.90], int(ch * 0.07), fill=BLUSH)
        text(d, (w * 0.4175, y + ch * 0.83), '사용법 확인', int(w * 0.032), CRIMSON, True, anchor='mm')
        y += ch + h * 0.022
    return img


# ── 디바이스 프레임 ──────────────────────────────────────────────────────────

def phone(screen, out, height=1200):
    sw = int(height * SCREEN_RATIO)
    sh = height
    screen = screen.convert('RGB').resize((sw, sh), Image.LANCZOS)
    bezel = max(6, int(sw * 0.034))
    bw, bh = sw + bezel * 2, sh + bezel * 2
    body = Image.new('RGBA', (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    r = int(bw * 0.125)
    d.rounded_rectangle([0, 0, bw - 1, bh - 1], r, fill=(26, 26, 29))
    d.rounded_rectangle([bezel * 0.35, bezel * 0.35, bw - bezel * 0.35, bh - bezel * 0.35], int(r * 0.93),
                        fill=(8, 8, 10))
    # 화면
    sr = int(r * 0.80)
    body.paste(screen, (bezel, bezel))
    mask = rounded_mask((sw, sh), sr)
    body.paste(screen, (bezel, bezel), mask)
    # 다이내믹 아일랜드
    d = ImageDraw.Draw(body)
    iw, ih = int(sw * 0.26), int(sw * 0.070)
    d.rounded_rectangle([bezel + (sw - iw) // 2, bezel + int(sw * 0.022),
                         bezel + (sw + iw) // 2, bezel + int(sw * 0.022) + ih], ih // 2, fill=(6, 6, 8))
    # 측면 버튼
    d.rounded_rectangle([-bezel * 0.16, bh * 0.20, 0, bh * 0.28], bezel * 0.16, fill=(64, 62, 60))
    d.rounded_rectangle([bw - 1, bh * 0.24, bw + bezel * 0.16, bh * 0.34], bezel * 0.16, fill=(64, 62, 60))
    compose_with_shadow(body, blur=max(10, int(bw * 0.035)), alpha=80,
                        offset=(0, int(bw * 0.03))).save(out)
    return out


def tablet(screen, out, width=1400, bezel_ratio=0.038, radius_ratio=0.045):
    screen = screen.convert('RGB')
    ratio = screen.height / screen.width
    sw = width
    sh = int(width * ratio)
    screen = screen.resize((sw, sh), Image.LANCZOS)
    bezel = int(sw * bezel_ratio)
    bw, bh = sw + bezel * 2, sh + bezel * 2
    body = Image.new('RGBA', (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    r = int(bw * radius_ratio)
    d.rounded_rectangle([0, 0, bw - 1, bh - 1], r, fill=(30, 30, 33))
    d.rounded_rectangle([bezel * 0.4, bezel * 0.4, bw - bezel * 0.4, bh - bezel * 0.4], int(r * 0.92), fill=(10, 10, 12))
    body.paste(screen, (bezel, bezel), rounded_mask((sw, sh), int(r * 0.82)))
    d = ImageDraw.Draw(body)
    d.ellipse([bw // 2 - bezel * 0.10, bezel * 0.28, bw // 2 + bezel * 0.10, bezel * 0.48], fill=(52, 50, 54))
    compose_with_shadow(body, blur=max(10, int(bw * 0.02)), alpha=76,
                        offset=(0, int(bw * 0.014))).save(out)
    return out


def browser(page, out, width=1600):
    page = page.convert('RGB')
    top = int(width * 0.055)
    sw = width
    sh = int(width * page.height / page.width)
    page = page.resize((sw, sh), Image.LANCZOS)
    bh = sh + top
    r = int(width * 0.012)
    body = Image.new('RGBA', (sw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    d.rounded_rectangle([0, 0, sw - 1, bh - 1], r, fill=(238, 236, 233))
    d.rounded_rectangle([0, 0, sw - 1, top], r, fill=(228, 225, 221))
    d.rectangle([0, top // 2, sw - 1, top], fill=(228, 225, 221))
    for i in range(3):
        cx = int(width * 0.026) + i * int(width * 0.020)
        d.ellipse([cx - width * 0.006, top * 0.42 - width * 0.006,
                   cx + width * 0.006, top * 0.42 + width * 0.006],
                  fill=((214, 108, 100), (222, 180, 96), (140, 178, 128))[i])
    d.rounded_rectangle([width * 0.10, top * 0.24, width * 0.62, top * 0.76], int(top * 0.26), fill=(248, 247, 245))
    body.paste(page, (0, top))
    compose_with_shadow(body, blur=max(10, int(width * 0.012)), alpha=74,
                        offset=(0, int(width * 0.008))).save(out)
    return out


def paper(path, out, pad_ratio=0.035):
    """인쇄물처럼 — 흰 여백을 두르고 그림자를 붙인다."""
    im = Image.open(path).convert('RGB')
    p = max(6, int(min(im.size) * pad_ratio))
    card = Image.new('RGBA', (im.width + 2 * p, im.height + 2 * p), (255, 255, 255, 255))
    card.paste(im, (p, p))
    compose_with_shadow(card, blur=8, alpha=64, offset=(0, 7), pad=30).save(out)
    return out


# ── 프리미엄 아이폰 프레임 ────────────────────────────────��─────────────────
# 2026-11-22 사용자 지시: 슬랙 `#pickle`에 올린 Pinterest 레퍼런스 3종
# (핑크 배경 정면 · 투명 배경 흑백 · Floating Angled iPhone Mockup)을 직접 열어 보고
# 베젤을 세 겹(금속 밴드 → 블랙 글래스 → 화면)으로 쌓고, 밴드에 세로 그라데이션과
# 대각선 유리 광택·모서리 하이라이트를 넣었다. 그림자는 바닥에 가까운 진한 그림자와
# 넓게 퍼지는 주변광 그림자를 두 겹으로 깔아 기기가 떠 있는 느낌을 만든다.
# 2030 파트(4~7쪽)만 이 프레임을 쓰고, 5060·부록 쪽은 기존 `phone()`을 그대로 쓴다.

METAL = {
    # 흑연 티타늄 — 밴드는 어둡고, 바깥 모서리에만 얇은 반사가 선다
    'natural': ((96, 100, 108), (226, 231, 236), (58, 60, 68),
                (34, 35, 41), (20, 21, 26), (44, 46, 54), (16, 17, 21)),
    # 2030용 — 아쿠아 키비주얼 옆에서 살짝 푸르게 도는 흑연
    'aqua': ((86, 104, 114), (216, 232, 238), (48, 64, 74),
             (26, 36, 44), (15, 21, 26), (40, 54, 64), (14, 19, 24)),
}


def _ramp(size, stops, axis='x'):
    """stops((위치, 값)…)를 선형 보간해 그라데이션 이미지를 만든다."""
    w, h = size
    n = w if axis == 'x' else h
    pos = np.linspace(0.0, 1.0, n)
    at = np.array([s[0] for s in stops])
    cols = np.array([s[1] for s in stops], dtype=float)
    line = np.stack([np.interp(pos, at, cols[:, c]) for c in range(3)], axis=1)
    arr = (np.repeat(line[None, :, :], h, axis=0) if axis == 'x'
           else np.repeat(line[:, None, :], w, axis=1))
    return Image.fromarray(arr.clip(0, 255).astype('uint8'))


def _alpha_grad(size, stops, axis='x'):
    """회색조 그라데이션(알파 마스크용)."""
    return _ramp(size, [(t, (v, v, v)) for t, v in stops], axis).convert('L')


def _iphone_body(screen, height=1200, tint='natural'):
    """베젤·금속 밴드·유리·측면 버튼·다이내믹 아일랜드를 갖춘 아이폰 본체(RGBA).

    Pinterest 레퍼런스처럼 베젤을 **금속 밴드 → 블랙 글래스 → 화면** 세 겹으로 쌓고,
    밴드에는 왼쪽 위에서 들어오는 빛(대각선 광택)과 바깥 모서리 하이라이트를 얹는다.
    """
    sw = int(round(height * SCREEN_RATIO))
    sh = int(height)
    screen = ImageOps.fit(screen.convert('RGB'), (sw, sh), Image.LANCZOS)

    band = max(3, int(round(sw * 0.025)))     # 금속 밴드 두께
    glass = max(2, int(round(sw * 0.019)))    # 블랙 글래스 베젤
    W, H = sw + 2 * (band + glass), sh + 2 * (band + glass)
    r_screen = int(round(sw * 0.130))
    r_out = r_screen + band + glass

    body = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    body_mask = rounded_mask((W, H), r_out)

    # 빛의 방향 — 왼쪽 위 모서리에서 대각선으로 퍼진다
    xs = np.arange(W)[None, :] / W
    ys = np.arange(H)[:, None] / H
    diag = np.clip(xs * 0.62 + ys * 0.38, 0, 1)
    bloom = np.exp(-((diag / 0.20) ** 2)) * 255          # 왼쪽 위 광택
    rim_light = np.clip(1.0 - diag * 1.35, 0, 1) ** 1.3  # 모서리 하이라이트

    # 1) 금속 밴드 — 바깥 모서리에만 얇은 반사, 안쪽은 어두운 흑연.
    #    밴드 폭이 화면 폭의 3%뿐이라 그 비율 안에서 그라데이션을 잡는다.
    edge, bright, soft, mid, dark, deeper, back = METAL.get(tint, METAL['natural'])
    bf = band / W
    metal = _ramp((W, H), (
        (0.0, edge), (bf * 0.06, bright), (bf * 0.20, soft),
        (bf * 0.44, mid), (bf * 1.02, dark),
        (1 - bf * 1.02, dark), (1 - bf * 0.30, back), (1 - bf * 0.06, bright), (1.0, deeper)))
    glow = Image.fromarray(np.stack([bloom] * 3, axis=-1).clip(0, 255).astype('uint8'))
    metal = Image.composite(glow, metal, Image.fromarray((bloom * 0.12).astype('uint8')))
    body.paste(metal, (0, 0), body_mask)

    # 2) 블랙 글래스 베젤 — 위쪽이 살짝 밝은 유리
    inner_mask = rounded_mask((W - 2 * band, H - 2 * band), r_out - band)
    glass_img = _ramp((W - 2 * band, H - 2 * band),
                      ((0.0, (8, 9, 11)), (0.42, (28, 29, 34)), (1.0, (9, 10, 12))), axis='y')
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    layer.paste(glass_img, (band, band), inner_mask)
    body = Image.alpha_composite(body, layer)

    # 3) 화면 — 유리 둥근 모서리 그대로
    sx, sy = band + glass, band + glass
    screen_layer = Image.new('RGBA', (sw, sh), (0, 0, 0, 255))
    screen_layer.paste(screen, (0, 0))
    body.paste(screen_layer, (sx, sy), rounded_mask((sw, sh), r_screen))

    # 3b) 유리 광택 — 화면 왼쪽 위에서 대각선으로 스치는 반사
    sheen = np.clip(1.0 - diag * 1.55, 0, 1) ** 2 * 18
    sheen_img = Image.fromarray(np.stack([sheen] * 3, axis=-1).astype('uint8'))
    body.paste(Image.new('RGB', (sw, sh), (255, 255, 255)), (sx, sy),
               ImageChops.multiply(Image.fromarray(sheen.astype('uint8')),
                                   rounded_mask((sw, sh), r_screen)))

    d = ImageDraw.Draw(body)
    # 4) 외곽 모서리 하이라이트 — 빛 받는 쪽만 밝다
    rim = Image.new('L', (W, H), 0)
    ImageDraw.Draw(rim).rounded_rectangle([0, 0, W - 1, H - 1], r_out, outline=255,
                                          width=max(1, int(W * 0.0045)))
    rim = ImageChops.multiply(rim, Image.fromarray((rim_light * 205).astype('uint8')))
    body.paste(Image.new('RGBA', (W, H), (255, 255, 255, 255)), (0, 0), rim)

    # 5) 밴드 안쪽 어두운 선 — 금속과 유리의 경계
    d.rounded_rectangle([band, band, W - band - 1, H - band - 1], r_out - band,
                        outline=(13, 13, 16, 205), width=max(1, int(band * 0.42)))

    # 6) 측면 버튼 — 금속 밴드에 붙은 너브(왼쪽: 음량·무음, 오른쪽: 전원)
    for y0, y1 in ((0.150, 0.196), (0.222, 0.292), (0.308, 0.378)):
        d.rounded_rectangle([0, H * y0, band * 0.92, H * y1], band * 0.34, fill=(*back, 240))
        d.line([(band * 0.10, H * y0 + band * 0.5), (band * 0.10, H * y1 - band * 0.5)],
               fill=(230, 236, 238, 150), width=max(1, int(band * 0.16)))
    for y0, y1 in ((0.243, 0.348),):
        d.rounded_rectangle([W - band * 0.92, H * y0, W, H * y1], band * 0.34, fill=(*back, 240))
        d.line([(W - band * 0.10, H * y0 + band * 0.5), (W - band * 0.10, H * y1 - band * 0.5)],
               fill=(230, 236, 238, 150), width=max(1, int(band * 0.16)))

    # 7) 다이내믹 아일랜드 — 유리에 얹힌 검은 캡슐과 렌즈 점
    iw, ih = int(sw * 0.255), int(sw * 0.072)
    ix, iy = sx + (sw - iw) // 2, sy + int(sh * 0.0135)
    d.rounded_rectangle([ix, iy, ix + iw, iy + ih], ih // 2, fill=(5, 5, 7, 255))
    d.ellipse([ix + iw - ih * 0.70, iy + ih * 0.26, ix + iw - ih * 0.24, iy + ih * 0.74],
              fill=(22, 24, 30, 255))
    return body


def _float_shadow(body, tight=(0.010, 90, 0.014), ambient=(0.030, 46, 0.055), pad=0.06):
    """바닥 가까운 진한 그림자와 넓게 퍼지는 주변광 그림자를 두 겹으로 깐다.

    tight/ambient = (아래로 내리는 비율, 알파, 흐림 반경 비율).
    """
    W, H = body.size
    p = int(W * pad)
    canvas = Image.new('RGBA', (W + 2 * p, H + 2 * p), (0, 0, 0, 0))
    sil = body.split()[3]
    for drop, alpha, blur in (ambient, tight):
        layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        tint = Image.new('RGBA', body.size, (12, 16, 20, 255))
        tint.putalpha(sil.point(lambda v: int(v * alpha / 255)))
        layer.alpha_composite(tint, (p, p + int(H * drop)))
        layer = layer.filter(ImageFilter.GaussianBlur(max(2, int(W * blur))))
        canvas.alpha_composite(layer)
    canvas.alpha_composite(body, (p, p))
    return canvas.crop(canvas.getbbox())


def iphone(screen, out, height=1200, tint='aqua'):
    """정면 아이폰 — 금속 밴드·유리 광택·두 겹 그림자."""
    body = _iphone_body(screen, height, tint)
    _float_shadow(body).save(out, optimize=True)
    return out


def _perspective(img, inset=0.012):
    """위에서 살짝 내려다본 원근 — 위 폭이 좁고 아래 모서리가 살짝 나온다."""
    W, H = img.size
    src = [(0, 0), (W, 0), (W, H), (0, H)]
    dst = [(W * inset * 1.6, H * inset * 0.5), (W * (1 - inset * 0.6), 0),
           (W * (1 - inset * 0.1), H), (W * inset * 0.1, H * (1 - inset * 0.4))]

    # 출력 좌표 → 입력 좌표 계수를 4점 대응으로 푼다
    A, bx = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        bx.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        bx.append(v)
    coeffs = np.linalg.solve(np.array(A, dtype=float), np.array(bx, dtype=float))
    return img.transform((W, H), Image.PERSPECTIVE, tuple(coeffs), Image.BICUBIC)


def iphone_angled(screen, out, height=1800, tint='aqua', tilt=13.0, depth=0.009):
    """Floating Angled 스타일 — 원근으로 세운 뒤 기울이고, 측면 두께와 그림자를 얹는다."""
    body = _perspective(_iphone_body(screen, height, tint))
    body = body.rotate(tilt, resample=Image.BICUBIC, expand=True)

    # 측면 두께 — 실루엣을 왼쪽 아래로 밀어 쌓아 금속 옆면을 만든다
    W, H = body.size
    step = max(1, int(H * depth / 8))
    sil = body.split()[3]
    thick = Image.new('RGBA', (W + step * 10, H + step * 10), (0, 0, 0, 0))
    td = ImageDraw.Draw(thick)
    for k in range(9, 0, -1):
        tone = int(58 - k * 4)
        plate = Image.new('RGBA', body.size, (tone, tone + 3, tone + 6, 255))
        plate.putalpha(sil)
        thick.alpha_composite(plate, (step * (9 - k), step * k + 0))
    thick.alpha_composite(body, (step * 9, 0))
    thick = thick.crop(thick.getbbox())
    _float_shadow(thick, tight=(0.018, 78, 0.009), ambient=(0.060, 46, 0.040)).save(out, optimize=True)
    return out


# ── 디지털 클리닉 앱 UI 시안(6쪽) ────────────────────────────────────────────
# 사용자 지시: "실제 있는 메디큐브 디지털 클리닉 앱을 더 업그레이드해서 루틴을
# 관리하고 푸시를 제공하도록 — 고객의 '루틴'을 만들어 디바이스가 루틴이 되게."
# ① 루틴·알림 시간 설정 ② 설정 시간에 오는 데일리 푸시 ③ 달성 트래커·리포트.
# 화면 문구는 기획 시안이므로 효능·성과를 주장하지 않고 시간·횟수·모드만 쓴다.

UI_INK = (18, 38, 46)
UI_MUTED = (92, 120, 131)
UI_HAIR = (207, 227, 234)
UI_TEAL = (22, 91, 114)
UI_MIST = (226, 240, 245)
UI_BG = (250, 252, 253)


def _app_head(d, w, h, title, right=None):
    """앱 상단 바 — 뒤로가기·화면 이름·오른쪽 액션(상태 바 아래)."""
    y = h * 0.078
    text(d, (w * 0.058, y), '\u2039', int(w * 0.070), UI_TEAL, False, anchor='lm')
    text(d, (w * 0.5, y), title, int(w * 0.040), UI_INK, True, anchor='mm')
    if right:
        text(d, (w * 0.942, y), right, int(w * 0.036), UI_TEAL, True, anchor='rm')


def _chip(d, x, y, label, w, hh, on=False):
    d.rounded_rectangle([x, y, x + w, y + hh], hh / 2,
                        fill=UI_TEAL if on else (255, 255, 255),
                        outline=None if on else UI_HAIR, width=max(1, int(hh * 0.06)))
    text(d, (x + w / 2, y + hh / 2 - hh * 0.04), label, int(hh * 0.46),
         (255, 255, 255) if on else UI_MUTED, on, anchor='mm')


def _tab_bar_app(d, w, h, active=1):
    y = h - int(h * 0.080)
    d.line([(0, y), (w, y)], fill=UI_HAIR, width=max(2, int(w * 0.0028)))
    for i, label in enumerate(('홈', '루틴', '리포트', '마이')):
        cx = w * (0.145 + i * 0.237)
        cy = y + h * 0.030
        on = i == active
        col = UI_TEAL if on else UI_MUTED
        lw = max(2, int(w * 0.0045))
        if i == 0:                                   # 홈 — 지붕이 있는 사각형
            d.line([(cx - w * 0.021, cy), (cx, cy - h * 0.016), (cx + w * 0.021, cy)],
                   fill=col, width=lw, joint='curve')
            d.rounded_rectangle([cx - w * 0.015, cy, cx + w * 0.015, cy + h * 0.013],
                                w * 0.004, outline=col, width=lw)
        elif i == 1:                                 # 루틴 — 고리
            d.ellipse([cx - w * 0.018, cy - h * 0.016, cx + w * 0.018, cy + h * 0.016],
                      outline=col, width=lw)
            if on:
                d.ellipse([cx - w * 0.007, cy - h * 0.005, cx + w * 0.007, cy + h * 0.005], fill=col)
        elif i == 2:                                 # 리포트 — 막대 셋
            for k, bh in enumerate((0.010, 0.020, 0.014)):
                bx = cx - w * 0.016 + k * w * 0.014
                d.rounded_rectangle([bx, cy + h * 0.014 - h * bh, bx + w * 0.008, cy + h * 0.014],
                                    lw, fill=col)
        else:                                        # 마이 — 사람
            d.ellipse([cx - w * 0.011, cy - h * 0.016, cx + w * 0.011, cy + h * 0.001],
                      outline=col, width=lw)
            d.arc([cx - w * 0.019, cy + h * 0.002, cx + w * 0.019, cy + h * 0.022],
                  200, 340, fill=col, width=lw)
        text(d, (cx, y + h * 0.048), label, int(w * 0.029), col, on, anchor='ma')


def screen_routine_setup(w, h):
    """① 사용자 맞춤 루틴·알림 시간 설정 — 매일 밤 10:30 / 주 5회 / 고민 모드 연동."""
    img = Image.new('RGB', (w, h), UI_BG)
    d = ImageDraw.Draw(img)
    _status_bar(d, w, UI_INK)
    _app_head(d, w, h, '루틴 설정', '저장')

    text(d, (w * 0.058, h * 0.128), '매일 밤 10시 30분', int(w * 0.090), UI_INK, True)
    text(d, (w * 0.058, h * 0.196), '내 피부 고민에 맞춘 12분 루틴', int(w * 0.033), UI_MUTED)

    # 알림 시간 카드
    top = int(h * 0.236)
    card_h = int(h * 0.186)
    d.rounded_rectangle([w * 0.055, top, w * 0.945, top + card_h], w * 0.035, fill=UI_MIST)
    text(d, (w * 0.098, top + h * 0.024), '알림 시간', int(w * 0.033), UI_MUTED, True)
    text(d, (w * 0.096, top + h * 0.048), '오후 10:30', int(w * 0.112), UI_TEAL, True)
    text(d, (w * 0.902, top + h * 0.062), '매일', int(w * 0.032), UI_MUTED, anchor='ra')
    for i, (day, on) in enumerate(zip('월화수목금토일', (1, 1, 1, 1, 1, 0, 0))):
        cx = w * (0.132 + i * 0.1226)
        cy = top + h * 0.148
        r = w * 0.036
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=UI_TEAL if on else (255, 255, 255),
                  outline=None if on else UI_HAIR, width=max(1, int(w * 0.003)))
        text(d, (cx, cy - r * 0.08), day, int(w * 0.032),
             (255, 255, 255) if on else UI_MUTED, bool(on), anchor='mm')

    # 고민 모드 카드
    top2 = top + card_h + int(h * 0.018)
    card2_h = int(h * 0.158)
    d.rounded_rectangle([w * 0.055, top2, w * 0.945, top2 + card2_h], w * 0.035,
                        fill=(255, 255, 255), outline=UI_HAIR, width=max(1, int(w * 0.004)))
    text(d, (w * 0.098, top2 + h * 0.020), '내 피부 고민 모드', int(w * 0.037), UI_INK, True)
    cw, chh = w * 0.186, h * 0.038
    for i, (label, on) in enumerate((('속건조', 0), ('탄력', 0), ('물광', 1), ('피부결', 0))):
        _chip(d, w * 0.098 + i * (cw + w * 0.020), top2 + h * 0.056, label, cw, chh, on)
    text(d, (w * 0.098, top2 + h * 0.114), '고른 모드에 맞춰 루틴 단계가 바뀝니다',
         int(w * 0.028), UI_MUTED)

    # 오늘의 루틴
    top3 = top2 + card2_h + int(h * 0.030)
    text(d, (w * 0.058, top3), '오늘의 루틴', int(w * 0.037), UI_INK, True)
    text(d, (w * 0.942, top3 + h * 0.004), '총 12분', int(w * 0.030), UI_TEAL, True, anchor='ra')
    steps = (('1', '준비', '세안 후 물기 정리', '3분'),
             ('2', '글로우', '물방울 초음파 케어', '6분'),
             ('3', '마무리', '보습 크림 흡수', '3분'))
    y = top3 + h * 0.028
    for no, name, desc, mins in steps:
        d.rounded_rectangle([w * 0.055, y, w * 0.945, y + h * 0.056], w * 0.026, fill=(255, 255, 255),
                            outline=UI_HAIR, width=max(1, int(w * 0.003)))
        d.ellipse([w * 0.082, y + h * 0.014, w * 0.082 + w * 0.028, y + h * 0.042], fill=UI_MIST)
        text(d, (w * 0.096, y + h * 0.028), no, int(w * 0.023), UI_TEAL, True, anchor='mm')
        text(d, (w * 0.134, y + h * 0.008), name, int(w * 0.030), UI_INK, True)
        text(d, (w * 0.134, y + h * 0.033), desc, int(w * 0.024), UI_MUTED)
        text(d, (w * 0.900, y + h * 0.028), mins, int(w * 0.028), UI_TEAL, True, anchor='rm')
        y += h * 0.064

    d.rounded_rectangle([w * 0.055, h * 0.860, w * 0.945, h * 0.906], h * 0.023, fill=UI_TEAL)
    text(d, (w * 0.5, h * 0.883), '이 루틴으로 저장', int(w * 0.039), (255, 255, 255), True, anchor='mm')
    _tab_bar_app(d, w, h, active=1)
    return img


def screen_daily_push(w, h):
    """② 설정 시간에 발송되는 데일리 푸시 — 잠금화면 위 알림 카드."""
    img = _gradient(w, h, (9, 27, 36), (26, 80, 98))
    for cx, cy, r, a in ((0.18, 0.20, 0.34, 40), (0.90, 0.34, 0.32, 30),
                         (0.10, 0.80, 0.36, 26), (0.86, 0.90, 0.30, 22),
                         (0.50, 0.62, 0.46, 24)):
        glow = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse([w * (cx - r), h * (cy - r), w * (cx + r), h * (cy + r)],
                                     fill=(132, 200, 222, a))
        img = Image.alpha_composite(img.convert('RGBA'),
                                    glow.filter(ImageFilter.GaussianBlur(w * 0.09))).convert('RGB')
    d = ImageDraw.Draw(img)
    _status_bar(d, w, (255, 255, 255), clock=False)
    text(d, (w * 0.5, h * 0.108), '10:30', int(w * 0.190), (255, 255, 255), True, anchor='mm')
    text(d, (w * 0.5, h * 0.166), '11월 22일 일요일', int(w * 0.034), (200, 224, 233), anchor='mm')

    # 접혀 있는 지난 알림
    d.rounded_rectangle([w * 0.045, h * 0.226, w * 0.955, h * 0.272], w * 0.026, fill=(243, 249, 251))
    text(d, (w * 0.5, h * 0.2495), '메디큐브 · 오늘 루틴 4일째', int(w * 0.029),
         UI_MUTED, anchor='mm')

    # 데일리 푸시 카드
    cy, chh = h * 0.296, h * 0.164
    d.rounded_rectangle([w * 0.045, cy, w * 0.955, cy + chh], w * 0.042, fill=(250, 252, 253))
    ix, iy = w * 0.082, cy + h * 0.022
    d.rounded_rectangle([ix, iy, ix + w * 0.098, iy + w * 0.098], w * 0.023, fill=UI_TEAL)
    text(d, (ix + w * 0.049, iy + w * 0.046), 'M', int(w * 0.052), (255, 255, 255), True, anchor='mm')
    text(d, (ix + w * 0.118, iy + w * 0.010), '메디큐브', int(w * 0.031), UI_INK, True)
    text(d, (w * 0.922, iy + w * 0.012), '지금', int(w * 0.027), UI_MUTED, anchor='ra')
    ty = iy + w * 0.052
    for line in ('윤서님, 오늘 밤 10:30', '글로우 12분 루틴 시간이에요'):
        text(d, (ix + w * 0.118, ty), line, int(w * 0.041), UI_INK, True)
        ty += int(w * 0.052)
    text(d, (ix + w * 0.118, ty + w * 0.008), '2단계부터 시작해요. 12분이면 끝나요.',
         int(w * 0.029), UI_MUTED)

    # 지난 밤 알림 — 흐리게
    ny = cy + chh + h * 0.016
    d.rounded_rectangle([w * 0.045, ny, w * 0.955, ny + h * 0.070], w * 0.026, fill=(232, 242, 246, 255))
    d.rounded_rectangle([w * 0.082, ny + h * 0.018, w * 0.082 + w * 0.056, ny + h * 0.052],
                        w * 0.014, fill=(150, 178, 190))
    text(d, (w * 0.168, ny + h * 0.024), '어제 오후 10:30 · 3단계까지 마쳤어요',
         int(w * 0.028), UI_MUTED)

    # 잠금화면 위젯 — 오늘의 루틴을 12분 단위로 미리 보여 준다
    wy = h * 0.660
    d.rounded_rectangle([w * 0.045, wy, w * 0.955, wy + h * 0.112], w * 0.030, fill=(26, 66, 84))
    text(d, (w * 0.082, wy + h * 0.016), '오늘의 루틴', int(w * 0.030), (196, 222, 232), True)
    text(d, (w * 0.918, wy + h * 0.016), '12분', int(w * 0.030), (255, 255, 255), True, anchor='ra')
    for i, (label, mins) in enumerate((('준비', '3분'), ('글로우', '6분'), ('마무리', '3분'))):
        bx = w * 0.082 + i * w * 0.276
        d.rounded_rectangle([bx, wy + h * 0.050, bx + w * 0.256, wy + h * 0.094], w * 0.018,
                            fill=(40, 96, 116))
        text(d, (bx + w * 0.018, wy + h * 0.061), label, int(w * 0.027), (228, 242, 248))
        text(d, (bx + w * 0.238, wy + h * 0.061), mins, int(w * 0.027), (255, 255, 255), True, anchor='ra')

    # 잠금화면 하단 — 손전등·카메라·홈 인디케이터
    for cx, glyph in ((w * 0.115, 'flash'), (w * 0.885, 'cam')):
        d.ellipse([cx - w * 0.042, h * 0.875, cx + w * 0.042, h * 0.875 + w * 0.084],
                  fill=(44, 92, 110))
        if glyph == 'flash':
            d.rounded_rectangle([cx - w * 0.008, h * 0.895, cx + w * 0.008, h * 0.920], w * 0.004,
                                fill=(214, 234, 242))
        else:
            d.rounded_rectangle([cx - w * 0.018, h * 0.896, cx + w * 0.018, h * 0.919], w * 0.005,
                                outline=(214, 234, 242), width=max(2, int(w * 0.004)))
    d.rounded_rectangle([w * 0.36, h * 0.962, w * 0.64, h * 0.968], w * 0.004, fill=(226, 240, 246))
    return img


def screen_habit_report(w, h):
    """③ 루틴 달성 트래커·리포트 — 디바이스 사용이 매일의 습관이 되게."""
    img = Image.new('RGB', (w, h), UI_BG)
    d = ImageDraw.Draw(img)
    _status_bar(d, w, UI_INK)
    _app_head(d, w, h, '이번 주 리포트', '공유')
    text(d, (w * 0.058, h * 0.132), '이번 주 루틴 5일', int(w * 0.092), UI_INK, True)
    text(d, (w * 0.058, h * 0.202), '지난주보다 하루 더 이어 갔어요', int(w * 0.034), UI_MUTED)

    # 요일 스트립
    day_y = h * 0.268
    for i, (day, on) in enumerate(zip('월화수목금토일', (1, 1, 1, 1, 1, 0, 0))):
        cx = w * (0.132 + i * 0.1226)
        r = w * 0.038
        d.ellipse([cx - r, day_y - r, cx + r, day_y + r],
                  fill=UI_TEAL if on else (255, 255, 255),
                  outline=None if on else UI_HAIR, width=max(1, int(w * 0.003)))
        if on:
            d.line([(cx - r * 0.40, day_y), (cx - r * 0.08, day_y + r * 0.32),
                    (cx + r * 0.42, day_y - r * 0.34)], fill=(255, 255, 255),
                   width=max(2, int(w * 0.009)), joint='curve')
        text(d, (cx, day_y + r * 1.55), day, int(w * 0.029), UI_MUTED, bool(on), anchor='ma')

    # 하루 12분 막대
    base = h * 0.452
    top_h = h * 0.088
    for i, mins in enumerate((12, 12, 12, 12, 12, 0, 0)):
        bx = w * (0.113 + i * 0.1226) - w * 0.024
        bh = top_h * (mins / 12) if mins else h * 0.005
        d.rounded_rectangle([bx, base - bh, bx + w * 0.048, base], w * 0.013,
                            fill=UI_TEAL if mins else UI_HAIR)
        if mins:
            text(d, (bx + w * 0.024, base - bh - h * 0.014), '12분', int(w * 0.025),
                 UI_TEAL, True, anchor='mm')
    d.line([(w * 0.055, base + h * 0.004), (w * 0.945, base + h * 0.004)], fill=UI_HAIR,
           width=max(1, int(w * 0.003)))

    # 요약 카드 2장
    y0 = base + h * 0.026
    card = h * 0.128
    d.rounded_rectangle([w * 0.055, y0, w * 0.492, y0 + card], w * 0.032, fill=UI_MIST)
    text(d, (w * 0.092, y0 + h * 0.018), '연속 루틴', int(w * 0.030), UI_MUTED, True)
    text(d, (w * 0.092, y0 + h * 0.046), '12일', int(w * 0.090), UI_TEAL, True)
    text(d, (w * 0.092, y0 + h * 0.104), '가장 길게 이어진 기록', int(w * 0.025), UI_MUTED)

    d.rounded_rectangle([w * 0.508, y0, w * 0.945, y0 + card], w * 0.032,
                        fill=(255, 255, 255), outline=UI_HAIR, width=max(1, int(w * 0.004)))
    text(d, (w * 0.545, y0 + h * 0.018), '이번 주 사용 모드', int(w * 0.030), UI_MUTED, True)
    for i, (label, n) in enumerate((('물광', 3), ('탄력', 2))):
        yy = y0 + h * 0.048 + i * h * 0.036
        text(d, (w * 0.545, yy), label, int(w * 0.034), UI_INK, True)
        text(d, (w * 0.908, yy), f'{n}회', int(w * 0.034), UI_TEAL, True, anchor='ra')

    # 주간 합계
    y1 = y0 + card + h * 0.018
    d.rounded_rectangle([w * 0.055, y1, w * 0.945, y1 + h * 0.086], w * 0.026,
                        fill=(255, 255, 255), outline=UI_HAIR, width=max(1, int(w * 0.004)))
    text(d, (w * 0.092, y1 + h * 0.015), '이번 주 총 60분 · 5회 완주', int(w * 0.032), UI_INK, True)
    text(d, (w * 0.092, y1 + h * 0.050), '하루 12분이면 채워지는 기록입니다',
         int(w * 0.026), UI_MUTED)

    # 다음 루틴 — 푸시와 리포트가 같은 시간으로 이어진다
    ny = h * 0.712
    d.rounded_rectangle([w * 0.055, ny, w * 0.945, ny + h * 0.068], w * 0.026, fill=UI_MIST)
    text(d, (w * 0.092, ny + h * 0.014), '다음 루틴', int(w * 0.027), UI_MUTED, True)
    text(d, (w * 0.092, ny + h * 0.036), '오늘 밤 10:30 · 글로우 12분', int(w * 0.032), UI_TEAL, True)
    text(d, (w * 0.908, ny + h * 0.030), '알림 켜짐', int(w * 0.026), UI_TEAL, True, anchor='rm')

    d.rounded_rectangle([w * 0.055, h * 0.858, w * 0.945, h * 0.906], h * 0.024, fill=UI_TEAL)
    text(d, (w * 0.5, h * 0.882), '다음 주도 같은 시간에', int(w * 0.038), (255, 255, 255), True,
         anchor='mm')
    _tab_bar_app(d, w, h, active=2)
    return img


def build_all(verbose=False):
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = []

    # 2030 — 샷 3컷은 프리미엄 프레임(4·5쪽), 엔드카드는 앵글드 히어로(4쪽)
    for i, name in enumerate(('pic_shot1_final.png', 'pic_shot2_final.png', 'pic_shot3_final.png'),
                              start=1):
        jobs.append(iphone(Image.open(ROOT / 'shots' / name), OUT / f'phone_shot{i}.png', 1000))
    jobs.append(iphone_angled(Image.open(ROOT / 'private_submission/2030/glow_endcard_aqua_v3.png'),
                              OUT / 'phone_endcard_angled.png', 1700))
    # 6쪽 — 디지털 클리닉 앱 업그레이드 3화면
    jobs.append(iphone(screen_routine_setup(760, 1648), OUT / 'phone_app_setup.png', 1000))
    jobs.append(iphone(screen_daily_push(760, 1648), OUT / 'phone_app_push.png', 1000))
    jobs.append(iphone(screen_habit_report(760, 1648), OUT / 'phone_app_report.png', 1000))
    # 5060 — 배송 후 메시지
    jobs.append(phone(screen_message_list(760, 1648), OUT / 'phone_messages.png', 1100))

    # 태블릿·브라우저
    jobs.append(tablet(Image.open(ROOT / 'design/glow_2030_main_poster.png'),
                       OUT / 'tablet_poster.png', 1000))
    jobs.append(tablet(Image.open(ROOT / 'design/gs_x2_internal_improvement_brief.png'),
                       OUT / 'tablet_brief.png', 1400))
    jobs.append(browser(Image.open(ROOT / 'private_submission/5060/x2_page13_placement.png'),
                        OUT / 'browser_x2_spread.png', 1600))
    jobs.append(tablet(Image.open(ROOT / 'private_submission/2030/kitty_edition_portfolio_poster.png'),
                       OUT / 'tablet_kitty.png', 800))

    # 인쇄물(여백+그림자)
    for src, name in (('private_submission/5060/x2_teaser_submission.png', 'print_teaser.png'),
                      ('private_submission/5060/x2_details_submission.png', 'print_details.png'),
                      ('design/glow_2030_main_poster.png', 'print_poster.png'),
                      ('private_submission/2030/kitty_edition_portfolio_poster.png', 'print_kitty.png'),
                      ('private_submission/2030/glow_endcard_aqua_v3.png', 'print_endcard.png'),
                      ('private_submission/2030/glow_bridge_01_aqua_v2.png', 'print_bridge1.png'),
                      ('private_submission/2030/glow_bridge_02_aqua_v2.png', 'print_bridge2.png'),
                      ('private_submission/2030/glow_bridge_03_aqua_v2.png', 'print_bridge3.png'),
                      ('private_submission/2030/glow_main_photo_water_harmonized_v3.png',
                       'print_keyvisual.png')):
        jobs.append(paper(ROOT / src, OUT / name))

    # 인쇄·화면에 필요한 해상도까지만 남긴다(긴 변 1100px ≈ 250dpi 상당)
    keep = {OUT / 'phone_endcard_angled.png'}
    for path in jobs:
        if path in keep:
            continue
        im = Image.open(path)
        if max(im.size) > 1100:
            scale = 1100 / max(im.size)
            im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
            im.save(path, optimize=True)

    if verbose:
        for p in jobs:
            print(p.relative_to(ROOT))
    return jobs


if __name__ == '__main__':
    build_all(verbose=True)
