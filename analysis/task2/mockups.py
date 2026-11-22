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

from PIL import Image, ImageDraw, ImageFilter, ImageFont

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

def _status_bar(d, w, color=(255, 255, 255), y=0):
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
    src = Image.open(ROOT / 'private_submission/2030/glow_endcard_submission.png').convert('RGB')
    product = src.crop((150, 700, 930, 1215))
    scale = (hero_h * 0.94) / product.height
    product = product.resize((int(product.width * scale), int(hero_h * 0.94)), Image.LANCZOS)
    band = Image.new('RGB', (w, hero_h), (253, 246, 247))
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
                            fill=(250, 248, 246), outline=LINE)
        d.ellipse([w * 0.105, y + h * 0.018, w * 0.122, y + h * 0.038], outline=CRIMSON, width=max(2, int(w * 0.005)))
        text(d, (w * 0.142, y + h * 0.010), label, int(w * 0.036), INK, True)
        text(d, (w * 0.142, y + h * 0.033), sub, int(w * 0.029), MUTED)
        y += int(h * 0.066)

    # 온사이트 배너 — 이탈 지점에서 다시 부르는 자리
    by = h - int(h * 0.232)
    d.rounded_rectangle([w * 0.06, by, w * 0.94, by + int(h * 0.150)], w * 0.024, fill=CRIMSON)
    text(d, (w * 0.10, by + h * 0.018), '내 피부 고민별 5가지 모드', int(w * 0.042), (255, 255, 255), True)
    text(d, (w * 0.10, by + h * 0.054), '숏폼에서 보던 모드를 앱에서 이어서', int(w * 0.030), (245, 226, 228))
    d.rounded_rectangle([w * 0.10, by + h * 0.088, w * 0.62, by + h * 0.134], int(h * 0.023), fill=(255, 255, 255))
    text(d, (w * 0.36, by + h * 0.111), '내 모드 확인하기', int(w * 0.032), CRIMSON, True, anchor='mm')
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
    d.rounded_rectangle([w * 0.08, cy + ch * 0.12, w * 0.08 + w * 0.11, cy + ch * 0.12 + w * 0.11], w * 0.022, fill=CRIMSON)
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


def build_all(verbose=False):
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = []

    # 2030 — 숏폼 3컷·엔드카드
    for i, name in enumerate(('pic_shot1_final.png', 'pic_shot2_final.png', 'pic_shot3_final.png'), start=1):
        screen = Image.open(ROOT / 'shots' / name).convert('RGB')
        jobs.append(phone(screen, OUT / f'phone_shot{i}.png', 900))
    jobs.append(phone(Image.open(ROOT / 'private_submission/2030/glow_endcard_submission.png'),
                      OUT / 'phone_endcard.png', 1100))
    jobs.append(phone(screen_on_site_banner(760, 1648), OUT / 'phone_banner.png', 1100))
    jobs.append(phone(screen_lock('보던 모드 가이드, 앱에서 이어 보기',
                                  '고민별 5가지 모드를 한 번에 비교합니다.',
                                  760, 1648, ROOT / 'shots/pic_shot3_final.png'),
                      OUT / 'phone_push_d1.png', 1100))
    jobs.append(phone(screen_lock('오늘 루틴 한 번만 확인해 보세요',
                                  '젤 크림과 함께 쓰는 순서까지 안내합니다.',
                                  760, 1648, ROOT / 'shots/pic_shot2_final.png'),
                      OUT / 'phone_push_d7.png', 1100))
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
                      ('design/glow_2030_bridge_01_bright.png', 'print_bridge1.png'),
                      ('design/glow_2030_bridge_02_modes_bright.png', 'print_bridge2.png'),
                      ('design/glow_2030_bridge_03_time_bright.png', 'print_bridge3.png')):
        jobs.append(paper(ROOT / src, OUT / name))

    if verbose:
        for p in jobs:
            print(p.relative_to(ROOT))
    return jobs


if __name__ == '__main__':
    build_all(verbose=True)
