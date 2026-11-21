# -*- coding: utf-8 -*-
"""정적 스토리보드 SVG를 PNG(2880×1395)로 다시 렌더링한다.

SVG의 글자 스타일은 축약형 `font:` 대신 개별 속성(font-size·font-weight)으로 쓴다.
일부 SVG 렌더러(WeasyPrint)가 축약형의 크기를 잘못 읽어 글자가 크게 겹치기 때문이다.
"""

from pathlib import Path

from weasyprint import HTML
import pymupdf

ROOT = Path(__file__).resolve().parents[2]
SVG = ROOT / 'design/gs_x2_2027_static_storyboard.svg'
PNG = ROOT / 'design/gs_x2_2027_static_storyboard.png'
TEMP = ROOT / 'tmp/pdfs'
SCALE = 2.0  # PDF 지면 1440pt × 2 = 2880px (1920×930의 1.5배)


def render():
    """SVG를 1920×930px 지면에 맞춰 PDF로 옮긴 뒤 PNG로 래스터화한다."""
    TEMP.mkdir(parents=True, exist_ok=True)
    pdf = TEMP / 'gs_x2_2027_static_storyboard.pdf'
    document = (
        '<!doctype html><html><head><meta charset="utf-8"><style>'
        '@page{size:20in 9.6875in;margin:0}html,body{margin:0;padding:0}'
        'img{display:block;width:1920px;height:930px}'
        f'</style></head><body><img src="{SVG.as_uri()}"></body></html>'
    )
    HTML(string=document, base_url=str(ROOT)).write_pdf(pdf)
    page = pymupdf.open(pdf)[0]
    pix = page.get_pixmap(matrix=pymupdf.Matrix(SCALE, SCALE))
    pix.save(PNG)
    return pix.width, pix.height


if __name__ == '__main__':
    print(PNG.relative_to(ROOT), *render())
