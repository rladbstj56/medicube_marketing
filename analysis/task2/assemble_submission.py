#!/usr/bin/env python3
"""private_submission 시안 파일을 최신 Photoshop MCP 미리보기에서 다시 만든다.

- 2030 엔드카드 : glow_ps_mcp_preview.jpg            -> glow_endcard_submission.png (1080x1920)
- 헬로키티 포스터: kitty_header_mcp_preview.jpg        -> kitty_edition_portfolio_poster.png (1080x1350)
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

CANVAS_W, CANVAS_H = 2200, 1460
PANEL_W, PANEL_H = 1020, 1275
LEFT_X, RIGHT_X, TOP_Y = 60, 1120, 95
BG = (255, 250, 248)


def to_png(src: Path, dst: Path, size: tuple[int, int]) -> None:
    im = Image.open(src).convert('RGB')
    if im.size != size:
        raise SystemExit(f'{src.name}: 크기가 {im.size}, 기대값 {size}')
    im.save(dst, format='PNG')
    print(f'{dst.relative_to(ROOT)} <- {src.relative_to(ROOT)} {im.size}')


def build_placement() -> None:
    canvas = Image.new('RGB', (CANVAS_W, CANVAS_H), BG)
    for src, x in [
        (SUB / '5060/x2_teaser_mcp_preview.jpg', LEFT_X),
        (SUB / '5060/x2_details_submission.png', RIGHT_X),
    ]:
        im = Image.open(src).convert('RGB').resize((PANEL_W, PANEL_H), Image.BICUBIC)
        canvas.paste(im, (x, TOP_Y))
        print(f'  panel {src.relative_to(ROOT)} -> ({x},{TOP_Y}) {PANEL_W}x{PANEL_H}')
    out = SUB / '5060/x2_page13_placement.png'
    canvas.save(out, format='PNG')
    print(f'{out.relative_to(ROOT)} {canvas.size}')


if __name__ == '__main__':
    to_png(SUB / '2030/glow_ps_mcp_preview.jpg', SUB / '2030/glow_endcard_submission.png', (1080, 1920))
    to_png(SUB / '2030/kitty_header_mcp_preview.jpg', SUB / '2030/kitty_edition_portfolio_poster.png', (1080, 1350))
    build_placement()
