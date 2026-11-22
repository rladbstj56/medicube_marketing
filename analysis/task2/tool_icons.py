# -*- coding: utf-8 -*-
"""2쪽 Skill & Tool — 열 툴의 아이콘을 PIL로 그린다.

2026-11-22 사용자 지시로 스킬 레벨 막대를 없애고 툴 아이콘만 남겼다. 아이콘은
작은 크기(약 34pt)로 들어가므로, 100×100 단위 좌표계에 5배 슈퍼샘플(800px)로
그린 뒤 160px로 줄여 가장자리를 매끄럽게 만든다.

- Python · Figma · GA4  각 사가 공개한 로고 도형의 좌표를 그대로 옮겨 채운다
                       (`_svg` — 경로를 0.15단위 폴리곤으로 편 뒤 색을 입힌다).
- SQL                  적층 원기둥(데이터베이스) — 단일 공식 마크가 없어 직접 그린다.
- MCP                  맞물린 두 고리(프로토콜·연결)
- Codex                여섯 고리 매듭(OpenAI 마크 계열의 육각 고리)
- CapCut               검은 둥근 사각형 위 흰 재생·컷 표시

2026-11-22 2차 지시로 **GA4를 빼고 Notion·Higgsfield·Kling·ElevenLabs를 넣어**
열 개가 되었다(2쪽은 5×2 배치). 새 네 종은 공개된 공식 벡터 경로를 그대로 쓰고,
구멍(안쪽 타원·글자)이 비워지도록 pymupdf에 `fill-rule=evenodd`로 렌더한다
(`_svg_mark`) — PIL 폴리곤 채움으로는 겹친 하위 경로의 구멍이 메워지기 때문이다.

- Notion               정육면체 페이지 윤곽 + 안쪽 N (simple-icons `notion.svg`)
- Higgsfield           공식 앱 아이콘(`logos/higgsfield_icon.png`, lime #D1FE17 타일)에서
                       검은 리본 심볼의 알파만 뽑아 잉크색으로 — 페이지의 무채색 팔레트 유지
- Kling                안쪽 타원을 감싸는 두 개의 맞물린 띠 (lobehub `kling.svg`)
- ElevenLabs           세로 막대 두 개 `||` (simple-icons `elevenlabs.svg`)

`python3 tool_icons.py --sheet`로 큰 아이콘 한 장에 모아 눈으로 확인한다.
"""

import math
import re
import sys
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'tmp/portfolio/icons'
LOGO = Path(__file__).resolve().parent / 'logos'    # 공식 벡터·아이콘 원본

SIZE = 160          # PDF에 넣는 PNG 한 변(px)
SUPER = 5           # 슈퍼샘플 배율
U = SIZE * SUPER    # 그리는 캔버스 한 변


def _u(v):
    """0~100 단위 좌표를 캔버스 px로."""
    return v * U / 100.0


def _box(b):
    return [_u(b[0]), _u(b[1]), _u(b[2]), _u(b[3])]


def _canvas():
    return Image.new('RGBA', (U, U), (0, 0, 0, 0))


def _finish(img):
    return img.resize((SIZE, SIZE), Image.LANCZOS)


def _rr(d, box, r, fill):
    d.rounded_rectangle(_box(box), radius=_u(r), fill=fill)


def _disc(d, cx, cy, r, fill):
    d.ellipse([_u(cx - r), _u(cy - r), _u(cx + r), _u(cy + r)], fill=fill)


def _punch(img, draw_fn):
    """mask에 그린 도형만큼 캔버스를 비운다(눈·구멍)."""
    mask = Image.new('L', (U, U), 0)
    draw_fn(ImageDraw.Draw(mask))
    img.paste((0, 0, 0, 0), (0, 0), mask)


def _hex(d, cx, cy, r, fill, rot=-90):
    pts = [(cx + r * math.cos(math.radians(rot + 60 * k)),
            cy + r * math.sin(math.radians(rot + 60 * k))) for k in range(6)]
    d.polygon([(_u(x), _u(y)) for x, y in pts], fill=fill)


# ── SVG 경로 채우기 ─────────────────────────────────────────────────────────
_NUM = re.compile(r'[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?')


def _path_subpaths(d, step=0.15):
    """SVG 경로 문자열을 폴리곤 점 목록으로 편다(M·L·H·V·C·S·Z 지원).

    곡선은 직선 여러 개로 나눠 채우므로, 작은 아이콘에서는 곡률 차이가 보이지
    않는다. 좌표는 경로 자체의 좌표계 그대로 돌려준다.
    """
    tokens = re.findall(r'[MmLlHhVvCcSsZz]|' + _NUM.pattern, d)
    subs, cur, x, y = [], [], 0.0, 0.0
    sx = sy = 0.0
    prev_c = None          # 직전 제어점(S 반사용)
    i = 0
    cmd = None
    while i < len(tokens):
        t = tokens[i]
        if re.fullmatch(r'[A-Za-z]', t):
            cmd = t
            i += 1
            if cmd in 'Zz':
                if len(cur) >= 3:
                    subs.append(cur)
                cur = [(sx, sy)]
                x, y = sx, sy
                prev_c = None
        else:
            rel = cmd.islower()
            def num():
                nonlocal i
                v = float(tokens[i])
                i += 1
                return v
            if cmd in 'Mm':
                if len(cur) >= 3:
                    subs.append(cur)
                if rel:
                    x, y = x + num(), y + num()
                else:
                    x, y = num(), num()
                sx, sy = x, y
                cur = [(x, y)]
                prev_c = None
                cmd = 'l' if rel else 'L'
            elif cmd in 'Ll':
                x, y = (x + num(), y + num()) if rel else (num(), num())
                cur.append((x, y))
                prev_c = None
            elif cmd in 'Hh':
                x = x + num() if rel else num()
                cur.append((x, y))
                prev_c = None
            elif cmd in 'Vv':
                y = y + num() if rel else num()
                cur.append((x, y))
                prev_c = None
            elif cmd in 'CcSs':
                was_smooth = cmd in 'Ss'
                if not was_smooth:
                    p1 = (x + num(), y + num()) if rel else (num(), num())
                else:
                    p1 = (2 * x - prev_c[0], 2 * y - prev_c[1]) if prev_c else (x, y)
                p2 = (x + num(), y + num()) if rel else (num(), num())
                p3 = (x + num(), y + num()) if rel else (num(), num())
                for k in range(1, max(2, int(1 / step)) + 1):
                    t_ = k / max(2, int(1 / step))
                    mt = 1 - t_
                    cur.append((mt ** 3 * x + 3 * mt ** 2 * t_ * p1[0]
                                + 3 * mt * t_ ** 2 * p2[0] + t_ ** 3 * p3[0],
                                mt ** 3 * y + 3 * mt ** 2 * t_ * p1[1]
                                + 3 * mt * t_ ** 2 * p2[1] + t_ ** 3 * p3[1]))
                x, y = p3
                prev_c = p2
                cmd = ('s' if was_smooth else 'c') if rel else ('S' if was_smooth else 'C')
            else:
                i += 1
    if len(cur) >= 3:
        subs.append(cur)
    return subs


def _svg(canvas_img, view_box, paths, scale=None, dx=0.0, dy=0.0):
    """viewBox·경로 목록을 받아 0~100 단위로 맞춰 채운다.

    view_box = (x, y, w, h) — 폭·높이 중 큰 쪽을 100으로 맞추고 가운데 정렬한다.
    """
    vx, vy, vw, vh = view_box
    s = 100.0 / max(vw, vh) if scale is None else scale
    ox = (100.0 - vw * s) / 2 - vx * s + dx
    oy = (100.0 - vh * s) / 2 - vy * s + dy
    d = ImageDraw.Draw(canvas_img)
    for dstr, color in paths:
        for sub in _path_subpaths(dstr):
            d.polygon([(_u(ox + px * s), _u(oy + py * s)) for px, py in sub], fill=color)
    return (s, ox, oy)


# ── 각 툴 ───────────────────────────────────────────────────────────────────
WHITE = (255, 255, 255, 255)
INK = (24, 24, 27, 255)
PAPER = (248, 247, 245, 255)

# Python — 공개 로고(viewBox 0.21 -0.077 110 110) 두 덩이
PY_BLUE = '#387EB8'
PY_YELL = '#FFD43B'
PY_D1 = ('M55.023-0.077c-25.971,0-26.25,10.081-26.25,12.156c0,3.148,0,12.594,0,12.594h26.75'
         'v3.781c0,0-27.852,0-37.375,0c-7.949,0-17.938,4.833-17.938,26.25c0,19.673,7.792,'
         '27.281,15.656,27.281c2.335,0,9.344,0,9.344,0s0-9.765,0-13.125c0-5.491,2.721-15.656,'
         '15.406-15.656c15.91,0,19.971,0,26.531,0c3.902,0,14.906-1.696,14.906-14.406c0-13.452,'
         '0-17.89,0-24.219C82.054,11.426,81.515-0.077,55.023-0.077z'
         'M40.273,8.392c2.662,0,4.813,2.15,4.813,4.813c0,2.661-2.151,4.813-4.813,4.813'
         's-4.813-2.151-4.813-4.813C35.46,10.542,37.611,8.392,40.273,8.392z')
PY_D2 = ('M55.397,109.923c25.959,0,26.282-10.271,26.282-12.156c0-3.148,0-12.594,0-12.594'
         'H54.897v-3.781c0,0,28.032,0,37.375,0c8.009,0,17.938-4.954,17.938-26.25c0-23.322-'
         '10.538-27.281-15.656-27.281c-2.336,0-9.344,0-9.344,0s0,10.216,0,13.125c0,5.491-'
         '2.631,15.656-15.406,15.656c-15.91,0-19.476,0-26.532,0c-3.892,0-14.906,1.896-14.906,'
         '14.406c0,14.475,0,18.265,0,24.219C28.366,100.497,31.562,109.923,55.397,109.923z'
         'M70.148,101.454c-2.662,0-4.813-2.151-4.813-4.813s2.15-4.813,4.813-4.813'
         'c2.661,0,4.813,2.151,4.813,4.813S72.809,101.454,70.148,101.454z')

# Figma — viewBox 0 0 200 300, 다섯 조각
FIG = [('M50 300c27.6 0 50-22.4 50-50v-50H50c-27.6 0-50 22.4-50 50s22.4 50 50 50z', '#0ACF83'),
       ('M0 150c0-27.6 22.4-50 50-50h50v100H50c-27.6 0-50-22.4-50-50z', '#A259FF'),
       ('M0 50C0 22.4 22.4 0 50 0h50v100H50C22.4 100 0 77.6 0 50z', '#F24E1E'),
       ('M100 0h50c27.6 0 50 22.4 50 50s-22.4 50-50 50h-50V0z', '#FF7262'),
       ('M200 150c0 27.6-22.4 50-50 50s-50-22.4-50-50 22.4-50 50-50 50 22.4 50 50z', '#1ABCFE')]

# GA4 — viewBox 0 0 48 48
GA4 = [('M45.3,41.6c0,3.2-2.6,5.9-5.8,5.9c-0.2,0-0.5,0-0.7,0c-3-0.4-5.2-3.1-5.1-6.1V6.6'
        'c-0.1-3,2.1-5.6,5.1-6.1c3.2-0.4,6.1,1.9,6.5,5.1c0,0.2,0,0.5,0,0.7V41.6z', '#F9AB00'),
       ('M8.6,35.9c3.2,0,5.8,2.6,5.8,5.8c0,3.2-2.6,5.8-5.8,5.8s-5.8-2.6-5.8-5.8c0,0,0,0,0,0'
        'C2.7,38.5,5.4,35.9,8.6,35.9z M23.9,18.2c-3.2,0.2-5.7,2.9-5.7,6.1V40c0,4.2,1.9,6.8,'
        '4.6,7.4c3.2,0.6,6.2-1.4,6.9-4.6c0.1-0.4,0.1-0.8,0.1-1.2V24.1c0-3.2-2.6-5.9-5.8-5.9'
        'C24,18.2,23.9,18.2,23.9,18.2z', '#E37400')]


# 2026-11-22 추가 4종 — 공개 배포된 공식 벡터 경로(24×24 viewBox)
#   Notion     simple-icons `notion.svg` · 정육면체 페이지 윤곽 + 안쪽 N
NOTION_D = ('M4.459 4.208c.746.606 1.026.56 2.428.466l13.215-.793c.28 0 .047-.28-.046-.326'
            'L17.86 1.968c-.42-.326-.981-.7-2.055-.607L3.01 2.295c-.466.046-.56.28-.374.466z'
            'm.793 3.08v13.904c0 .747.373 1.027 1.214.98l14.523-.84c.841-.046.935-.56.935-1.167'
            'V6.354c0-.606-.233-.933-.748-.887l-15.177.887c-.56.047-.747.327-.747.933z'
            'm14.337.745c.093.42 0 .84-.42.888l-.7.14v10.264c-.608.327-1.168.514-1.635.514'
            '-.748 0-.935-.234-1.495-.933l-4.577-7.186v6.952L12.21 19s0 .84-1.168.84l-3.222.186'
            'c-.093-.186 0-.653.327-.746l.84-.233V9.854L7.822 9.76c-.094-.42.14-1.026.793-1.073'
            'l3.456-.233 4.764 7.279v-6.44l-1.215-.139c-.093-.514.28-.887.747-.933z'
            'M1.936 1.035l13.31-.98c1.634-.14 2.055-.047 3.082.7l4.249 2.986c.7.513.934.653.934 1.213'
            'v16.378c0 1.026-.373 1.634-1.68 1.726l-15.458.934c-.98.047-1.448-.093-1.962-.747'
            'l-3.129-4.06c-.56-.747-.793-1.306-.793-1.96V2.667c0-.839.374-1.54 1.447-1.632z')
#   Kling      lobehub `kling.svg` · 안쪽 타원을 감싸는 두 개의 맞물린 띠
KLING_D = ('M5.493 21.234c-1.112-1.451-1.109-4.263-.081-7.459l-4.557-2.63a1.683 1.683 0 0'
           '1-.85-1.304 1.505 1.505 0 01.08-.622 13.18 13.18 0 011.037-2.255c3.476-6.02 '
           '10.916-8.23 16.619-4.938.46.266.82.67 1.081 1.184.785 1.545.685 4.096-.234 6.954'
           'l4.557 2.631c.339.196.596.492.736.832a1.53 1.53 0 01.034 1.093 13.146 13.146 0 0'
           '1-1.037 2.255c-3.476 6.02-10.916 8.23-16.619 4.938a2.6 2.6 0 01-.766-.68z'
           'm11.096-6.615c-2.073 3.591-5.808 5.316-8.343 3.852-1.267-.731-1.994-2.122-2.145-3.778'
           '-.095-1.035.036-2.173.4-3.32.217-.684.517-1.37.902-2.039l.008-.014c2.073-3.59 '
           '5.808-5.315 8.343-3.852.633.366 1.13.895 1.49 1.54.986 1.772.922 4.415-.285 6.914'
           '-.111.23-.232.457-.362.683l-.008.014z')
#   ElevenLabs simple-icons `elevenlabs.svg` · 세로 막대 두 개
ELEVEN_D = 'M4.6035 0v24h4.9317V0zm9.8613 0v24h4.9317V0z'
INK_HEX = '#18181B'


def python_icon():
    """두 뱀이 꼬리를 감은 마크 — 눈은 비워 뚫는다."""
    img = _canvas()
    s, ox, oy = _svg(img, (0.21, -0.077, 110, 110), [(PY_D1, PY_BLUE), (PY_D2, PY_YELL)])

    def eyes(d):
        for cx, cy in ((40.273, 13.205), (70.148, 96.641)):
            r = 4.813 * s
            d.ellipse([_u(ox + cx * s - r), _u(oy + cy * s - r),
                       _u(ox + cx * s + r), _u(oy + cy * s + r)], fill=255)

    _punch(img, eyes)
    return _finish(img)


def sql_icon():
    """데이터베이스 원기둥 — 위 타원 밝게, 몸통 진하게, 두 줄 곡선."""
    img = _canvas()
    d = ImageDraw.Draw(img)
    body, top = (74, 123, 167, 255), (116, 163, 198, 255)
    d.rectangle([_u(20), _u(24), _u(80), _u(72)], fill=body)
    d.pieslice([_u(20), _u(58), _u(80), _u(86)], 0, 180, fill=body)
    d.ellipse([_u(20), _u(12), _u(80), _u(40)], fill=top)
    for y in (46, 62):
        d.arc([_u(20), _u(y - 10), _u(80), _u(y + 10)], 0, 180,
              fill=PAPER, width=int(_u(2.6)))
    d.ellipse([_u(20), _u(12), _u(80), _u(40)], outline=body, width=int(_u(2.2)))
    return _finish(img)


def ga4_icon():
    """GA4 — 원·중간 막대·긴 막대가 오른쪽으로 올라간다.

    2026-11-22 2차 지시로 2쪽 목록에서 빠졌다(자격으로는 남기고 툴 아이콘만 교체).
    다시 쓰려면 `ICONS`에 ('GA4', ga4_icon)을 넣으면 된다 — 이 함수는 그대로 둔다.
    """
    img = _canvas()
    _svg(img, (0, 0, 48, 48), GA4)
    return _finish(img)


def figma_icon():
    """Figma — 2×3 격자의 다섯 조각."""
    img = _canvas()
    _svg(img, (0, 0, 200, 300), FIG)
    return _finish(img)


def mcp_icon():
    """MCP — ±38°로 맞물린 두 고리(가운데를 비워 겹침을 보인다)."""
    img = _canvas()
    for angle in (38, -38):
        ring = _canvas()
        ImageDraw.Draw(ring).ellipse([_u(9), _u(34), _u(91), _u(66)],
                                     outline=INK, width=int(_u(8)))
        img.alpha_composite(ring.rotate(angle, resample=Image.BICUBIC,
                                       center=(U / 2, U / 2)))
    _punch(img, lambda d: d.ellipse([_u(45), _u(45), _u(55), _u(55)], fill=255))
    return _finish(img)


def codex_icon():
    """Codex — 여섯 고리 매듭. 꽃잎 여섯 장을 60°씩 돌려 겹치고 가운데를 뚫는다."""
    img = _canvas()
    for k in range(6):
        petal = _canvas()
        _rr(ImageDraw.Draw(petal), (29, 3, 71, 72), 21, INK)
        img.alpha_composite(petal.rotate(60 * k, resample=Image.BICUBIC,
                                         center=(U / 2, U / 2)))
    _punch(img, lambda d: _hex(d, 50, 50, 24, 255))
    return _finish(img)


def capcut_icon():
    """CapCut — 검은 둥근 사각형 위 흰 재생·컷 글리프."""
    img = _canvas()
    d = ImageDraw.Draw(img)
    _rr(d, (8, 8, 92, 92), 24, INK)
    d.polygon([(_u(34), _u(33)), (_u(34), _u(67)), (_u(62), _u(50))], fill=WHITE)
    _rr(d, (66, 40, 74, 60), 4, WHITE)
    return _finish(img)


def _svg_mark(d, color=INK_HEX, fill_frac=0.84):
    """24×24 viewBox의 단일 path를 pymupdf로 렌더해 100단위 캔버스 가운데에 놓는다.

    `fill-rule=evenodd`를 함께 주어야 Notion의 안쪽 N·Kling의 타원 같은 구멍이
    비워진다(PIL 폴리곤 채움으로는 모든 하위 경로가 메워진다). 글자의 실제 외곽에
    맞추려고 알파 bbox로 잘라 낸 뒤 `fill_frac`만큼만 차지하게 맞춘다.
    """
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
           f'width="{U}" height="{U}"><path fill-rule="evenodd" clip-rule="evenodd" '
           f'style="fill:{color}" d="{d}"/></svg>')
    doc = pymupdf.open(stream=svg.encode('utf-8'), filetype='svg')
    pix = doc[0].get_pixmap(alpha=True)
    im = Image.frombytes('RGBA', (pix.width, pix.height), pix.samples)
    box = im.split()[3].getbbox()
    if box:
        im = im.crop(box)
    side = U * fill_frac
    k = side / max(im.width, im.height)
    im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    canvas = _canvas()
    canvas.alpha_composite(im, (int((U - im.width) / 2), int((U - im.height) / 2)))
    return _finish(canvas)


def notion_icon():
    """Notion — 정육면체 페이지 윤곽과 안쪽 N(3D 블록 느낌의 공식 마크)."""
    return _svg_mark(NOTION_D, fill_frac=0.86)


def kling_icon():
    """Kling — 안쪽 타원을 감싸는 두 개의 맞물린 띠(단선 굵기의 공식 마크).

    면이 꽉 찬 마크라 같은 84%에서는 다른 아이콘보다 무겁게 보여 80%로 줄였다.
    """
    return _svg_mark(KLING_D, fill_frac=0.80)


def elevenlabs_icon():
    """ElevenLabs — 세로 막대 두 개 `||`."""
    return _svg_mark(ELEVEN_D, fill_frac=0.88)


def higgsfield_icon():
    """Higgsfield — 공식 앱 아이콘에서 검은 리본 심볼만 뽑아 잉크색으로 그린다.

    `logos/higgsfield_icon.png`(512², lime #D1FE17 바탕 + 검은 리본)의 R 채널을
    알파로 바꿔 바탕을 지우고, 리본만 페이지의 잉크색으로 얹는다. 라임 타일을
    그대로 쓰면 무채색 지면에서 혼자 튀어 다른 9개와 무게가 맞지 않는다.
    """
    src = Image.open(LOGO / 'higgsfield_icon.png').convert('RGBA')
    mask = src.split()[0].point(lambda v: max(0, min(255, int((209 - v) * 255 / 189))))
    # 공식 아이콘의 둥근 모서리에는 타일 가장자리 그림자가 센 알파로 남는다.
    # 심볼은 가운데만 쓰므로 6% 테두리를 지워 네 귀퉁이 얼룩을 없앤다.
    inset = round(src.width * 0.06)
    core = Image.new('L', src.size, 0)
    core.paste(mask.crop((inset, inset, src.width - inset, src.height - inset)),
               (inset, inset))
    mask = core
    ink = Image.new('RGBA', src.size, INK)
    ink.putalpha(mask)
    box = mask.getbbox()
    if box:
        ink = ink.crop(box)
    side = U * 0.92
    k = side / max(ink.width, ink.height)
    ink = ink.resize((max(1, round(ink.width * k)), max(1, round(ink.height * k))),
                     Image.LANCZOS)
    canvas = _canvas()
    canvas.alpha_composite(ink, (int((U - ink.width) / 2), int((U - ink.height) / 2)))
    return _finish(canvas)


ICONS = (
    ('Python', python_icon),
    ('SQL', sql_icon),
    ('Notion', notion_icon),
    ('Figma', figma_icon),
    ('MCP', mcp_icon),
    ('Codex', codex_icon),
    ('CapCut', capcut_icon),
    ('Higgsfield', higgsfield_icon),
    ('Kling', kling_icon),
    ('ElevenLabs', elevenlabs_icon),
)


def build_all():
    """아이콘 PNG 10장을 만들고 {이름: 경로}를 돌려준다."""
    OUT.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, fn in ICONS:
        path = OUT / f'{name.lower()}.png'
        fn().save(path)
        paths[name] = path
    return paths


def sheet(scale=2):
    """검수용 — 아이콘 열 개를 큰 그림 한 장에 모은다."""
    paths = build_all()
    w = SIZE * scale
    sheet_img = Image.new('RGBA', (w * len(ICONS), w), PAPER)
    for i, (name, _) in enumerate(ICONS):
        icon = Image.open(paths[name]).convert('RGBA').resize((w, w), Image.LANCZOS)
        sheet_img.alpha_composite(icon, (i * w, 0))
    out = OUT / 'sheet.png'
    sheet_img.convert('RGB').save(out)
    return out


if __name__ == '__main__':
    if '--sheet' in sys.argv:
        print(sheet())
    else:
        for k, v in build_all().items():
            print(k, v)
