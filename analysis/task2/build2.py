# -*- coding: utf-8 -*-
"""Task 2 보고서 빌드: 블록 → (MD · HTML) → PDF. 두 산출물이 같은 블록에서 나온다."""
import sys, os
sys.path.insert(0, 'work/domestic')
sys.path.insert(0, 'work/task2')
import render
import doc1, doc2, doc3, doc4, doc5
from weasyprint import HTML

OUT_MD = 'downloads/메디큐브_국내_타깃가설_마케팅전략_2026-11-20.md'
OUT_PDF = 'downloads/메디큐브_국내_타깃가설_마케팅전략_2026-11-20.pdf'
FIG = 'work/task2/fig'

CSS = open('work/task2/style.css', encoding='utf-8').read()

WIDTHS = {
    '표 0-1': ['28mm', '60mm', '40mm', '50mm'],
    '표 0-2': ['22mm', '156mm'],
    '표 0-3': ['40mm', '46mm', '56mm', '36mm'],
    '표 1-1': ['70mm', '36mm', '36mm', '36mm'],
    '표 2-1': ['22mm', '78mm', '78mm'],
    '표 2-2': ['20mm', '88mm', '70mm'],
    '표 2-3': ['36mm', '64mm', '78mm'],
    '표 2-4': ['36mm', '64mm', '78mm'],
    '표 3-1': ['70mm', '36mm', '36mm', '36mm'],
    '표 3-2': ['26mm', '56mm', '52mm', '44mm'],
    '표 3-3': ['50mm', '68mm', '38mm'],
    '표 3-4': ['16mm', '76mm', '62mm', '24mm'],
    '표 4-1': ['46mm', '28mm', '28mm', '28mm', '32mm'],
    '표 4-2': ['68mm', '44mm', '30mm', '30mm'],
    '표 4-3': ['22mm', '38mm', '38mm', '34mm', '46mm'],
    '표 4-4': ['16mm', '68mm', '68mm', '24mm'],
    '표 5-1': ['26mm', '74mm', '78mm'],
    '표 6-1': ['28mm', '16mm', '48mm', '50mm', '30mm'],
    '표 6-2': ['30mm', '60mm', '64mm', '22mm'],
    '표 6-3': ['16mm', '38mm', '38mm', '56mm', '24mm'],
    '표 6-4': ['44mm', '38mm', '50mm', '50mm'],
    '표 7-1': ['28mm', '16mm', '48mm', '50mm', '30mm'],
    '표 7-2': ['26mm', '54mm', '36mm', '60mm'],
    '표 7-3': ['20mm', '70mm', '36mm', '50mm'],
    '표 8-1': ['18mm', '50mm', '56mm', '54mm'],
    '표 8-2': ['16mm', '30mm', '50mm', '32mm', '46mm'],
    '표 8-3': ['24mm', '76mm', '76mm'],
    '표 9-1': ['26mm', '64mm', '50mm', '26mm'],
    '표 9-2': ['32mm', '20mm', '72mm', '48mm'],
    '표 10-1': ['7mm', '56mm', '111mm'],
    '표 A-1': ['60mm', '60mm', '13mm', '15mm'],
    '표 A-2': ['30mm', '104mm', '38mm'],
    '표 A-3': ['24mm', '24mm', '24mm', '24mm', '24mm', '24mm', '24mm'],
    '표 A-4': ['50mm', '24mm', '24mm', '24mm'],
    '표 A-5': ['110mm', '62mm'],
    '표 A-6': ['12mm', '60mm', '78mm', '13mm'],
    '표 A-7': ['12mm', '60mm', '78mm', '13mm'],
    '표 A-8': ['34mm', '94mm', '48mm'],
}


NUMERIC = ('표 1-1', '표 3-1', '표 3-3', '표 4-1', '표 4-2', '표 A-3', '표 A-4')


def patch_block(blk):
    if blk[0] == 'table':
        cap = blk[1] or ''
        for k in sorted(WIDTHS, key=len, reverse=True):
            if cap.startswith(k):
                opts = dict(blk[4]) if len(blk) > 4 else {}
                opts['widths'] = WIDTHS[k]
                opts['align'] = ('l' + 'r' * (len(blk[2]) - 1)) if cap.startswith(NUMERIC) else 'l' * len(blk[2])
                return (blk[0], blk[1], blk[2], blk[3], opts)
    if blk[0] == 'two':
        return (blk[0], [patch_block(x) for x in blk[1]], [patch_block(x) for x in blk[2]])
    return blk


PAGES = []
for mod in (doc1, doc2, doc3, doc4, doc5):
    for pg in mod.PAGES:
        pg['blocks'] = [patch_block(b) for b in pg['blocks']]
        PAGES.append(pg)

META = dict(doc1.META)
META['meta'] = {
    '작성일': '2026-11-20(금)',
    '작성': '김윤서 · 픽클 정리',
    '데이터': '네이버 데이터랩 9개 + 쇼핑인사이트 3개 = 12개 원자료(3,210값) · 54주 · 전체/2030/5060',
    '실측': 'Snipit 27장·10구간 · 메타 광고 라이브러리(2026-11-20 04:4x KR) · Apify 71건 · 올리브영 Top100(11-20 04:08 사용자 저장)',
    '범위': '국내 집중 2축(2026-11-20 14:17 사용자 확정) · 글로벌은 시간이 남을 때 추가',
    '검증': '.md↔.pdf 수치 토큰 대조 · 원자료 독립 재계산 · 전 페이지 이미지 200dpi 검수',
}

html = render.to_html(PAGES, META, CSS, fig_dir=FIG)
open('work/task2/report.html', 'w').write(html)
md = render.to_md(PAGES, META)
open(OUT_MD, 'w').write(md)
HTML(string=html, base_url=os.getcwd()).write_pdf(OUT_PDF)
print('pages', len(PAGES), 'md_chars', len(md), 'pdf_bytes', os.path.getsize(OUT_PDF))
