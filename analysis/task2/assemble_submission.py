#!/usr/bin/env python3
"""5060 1-2면 합본 시안을 다시 만든다.

- 5060 1-2면 합본: x2_teaser_mcp_preview.jpg + x2_details_submission.png
                                                    -> x2_page13_placement.png (2200x1460)

1-2면 합본 배치는 이전 합본(f9131f0)과 같은 값이다.
캔버스 2200x1460, 배경 (255,250,248), 각 면 1020x1275, 좌 (60,95) / 우 (1120,95), BICUBIC.
2면 x2_details_submission.png는 (1) 본품 아이콘 통일본이 아직 없어 현행 파일을 그대로 쓴다.

실행: python3 analysis/task2/assemble_submission.py
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SUB = ROOT / 'private_submission'
ARCHIVE = SUB / '5060/archive'

CANVAS_W, CANVAS_H = 2200, 1460
PANEL_W, PANEL_H = 1020, 1275
LEFT_X, RIGHT_X, TOP_Y = 60, 1120, 95
BG = (255, 250, 248)


def build_placement() -> None:
    canvas = Image.new('RGB', (CANVAS_W, CANVAS_H), BG)
    for src, x in [
        (ARCHIVE / 'x2_teaser_mcp_preview.jpg', LEFT_X),
        (ARCHIVE / 'x2_details_submission.png', RIGHT_X),
    ]:
        im = Image.open(src).convert('RGB').resize((PANEL_W, PANEL_H), Image.BICUBIC)
        canvas.paste(im, (x, TOP_Y))
        print(f'  panel {src.relative_to(ROOT)} -> ({x},{TOP_Y}) {PANEL_W}x{PANEL_H}')
    out = ARCHIVE / 'x2_page13_placement.png'
    canvas.save(out, format='PNG')
    print(f'{out.relative_to(ROOT)} {canvas.size}')


if __name__ == '__main__':
    build_placement()
