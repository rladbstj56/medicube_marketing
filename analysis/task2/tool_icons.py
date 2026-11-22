# -*- coding: utf-8 -*-
"""2쪽 Skill & Tool — 일곱 툴의 아이콘을 PIL로 그린다.

2026-11-22 사용자 지시로 스킬 레벨 막대를 없애고 툴 아이콘만 남겼다. 아이콘은
작은 크기(약 34pt)로 들어가므로, 100×100 단위 좌표계에 5배 슈퍼샘플(800px)로
그린 뒤 160px로 줄여 가장자리를 매끄럽게 만든다.

- Python · Figma · GA4  각 사가 공개한 로고 도형의 좌표를 그대로 옮겨 채운다
                       (`_svg` — 경로를 0.15단위 폴리곤으로 편 뒤 색을 입힌다).
- SQL                  적층 원기둥(데이터베이스) — 단일 공식 마크가 없어 직접 그린다.
- MCP                  맞물린 두 고리(프로토콜·연결)
- Codex                여섯 고리 매듭(OpenAI 마크 계열의 육각 고리)
- CapCut               검은 둥근 사각형 위 흰 재생·컷 표시

`python3 tool_icons.py --sheet`로 큰 아이콘 한 장에 모아 눈으로 확인한다.
"""

import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'tmp/portfolio/icons'

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
    """GA4 — 원·중간 막대·긴 막대가 오른쪽으로 올라간다."""
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


ICONS = (
    ('Python', python_icon),
    ('SQL', sql_icon),
    ('GA4', ga4_icon),
    ('Figma', figma_icon),
    ('MCP', mcp_icon),
    ('Codex', codex_icon),
    ('CapCut', capcut_icon),
)


def build_all():
    """아이콘 PNG 7장을 만들고 {이름: 경로}를 돌려준다."""
    OUT.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, fn in ICONS:
        path = OUT / f'{name.lower()}.png'
        fn().save(path)
        paths[name] = path
    return paths


def sheet(scale=2):
    """검수용 — 아이콘 7개를 큰 그림 한 장에 모은다."""
    paths = build_all()
    w = SIZE * scale
    sheet_img = Image.new('RGBA', (w * 7, w), PAPER)
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
