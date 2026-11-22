# -*- coding: utf-8 -*-
"""13쪽 포트폴리오 PDF·MD 검증 — Behance식 이미지 중심 덱 규격.

① 쪽수 13 · 쪽 크기 960×540pt(16:9)
② MD 본문 조각이 같은 쪽 PDF에 실제로 있는지(공백 무시 대조)
③ AI 제작·승인 전 콘셉트 고지가 정해진 쪽에 있는지
④ 두 글꼴이 MD의 모든 글자를 가지고 있는지(두부 글자 방지)
⑤ 인용한 숫자가 저장소 현행 문서·스크립트에 있는지
⑥ 여백 침범·글자 겹침·빈 쪽·이미지 누락이 없는지
⑦ 미판정 경계 문구가 14쪽에 그대로 있는지, 금지 표현이 없는지

이전 판은 '고정 장문 보고서 문구'를 4·14쪽에 강제했다. 이번 양식은 검증 수치를
14쪽 부록으로 보냈으므로, 문구 검사는 **미판정 경계 한 문장**과 **고지 라벨**로
좁히고 나머지는 조판 규격과 본문 일치로 본다.
"""

import re
import sys
import unicodedata
from pathlib import Path

import pymupdf
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PDF = ROOT / 'reports/메디큐브_콘텐츠마케팅_포트폴리오.pdf'
MD = ROOT / 'reports/메디큐브_콘텐츠마케팅_포트폴리오.md'
PAGE_W, PAGE_H = 960.0, 540.0
M = 44.0
TOL = 2.5
TOP_LIMIT = PAGE_H - 24
BOTTOM_LIMIT = 18

BOUNDARY = ('공개 검색·클릭 지표와 수집 가능한 리뷰로 콘텐츠 및 채널 기회를 검토했다. '
            '고객별 구매, 제품별 순매출, 광고 성과가 없어 타깃의 실제 구매 규모와 '
            '전략 효과는 판정하지 않았다.')

# 고지·라벨이 반드시 있어야 하는 쪽
NOTICES = {
    6: ['[실행 제안]', '[AI 제작]'],
    7: ['[AI 제작]'],
    10: ['[내부 검토용]'],
    11: ['[승인 전 콘셉트]'],
    13: ['[AI 제작]', '미확인'],
}

# 이미지가 있어야 하는 쪽(표지·목차는 활자와 도형만 쓴다)
IMAGE_PAGES = (4, 5, 6, 7, 8, 9, 10, 11)

FORBIDDEN = ['매출이 늘었다', 'ROAS 1', '구매 전환', '효과가 검증되었다',
             '개선이 완료되었다', '매출 상승을 확인']


def norm(text):
    text = unicodedata.normalize('NFKC', text)
    return re.sub(r'\s+', '', text)


def md_pages():
    source = MD.read_text(encoding='utf-8')
    parts = re.split(r'^## (\d+)쪽 · .*$', source, flags=re.M)
    return {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}


def fragments(body):
    """MD 한 줄을 PDF에서 따로 찾을 수 있는 조각들로 나눈다.

    표 머리행(`| 항목 | 내용 |` 다음이 구분선)은 PDF에 그리지 않으므로 건너뛴다.
    """
    out = []
    lines = body.splitlines()
    for idx, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith('!['):
            continue
        if set(line) <= set('-| '):
            continue
        nxt = lines[idx + 1].strip() if idx + 1 < len(lines) else ''
        is_header = line.startswith('|') and set(nxt) <= set('-| ') and nxt.startswith('|')
        if is_header:
            continue
        if line.startswith('>'):
            line = line.lstrip('>').strip()
        line = re.sub(r'^#{1,6}\s*', '', line)
        line = re.sub(r'^[-*]\s+', '', line)
        cells = [c.strip() for c in line.strip('|').split('|')] if line.startswith('|') else [line]
        for cell in cells:
            cell = cell.replace('**', '').replace('`', '')
            for frag in re.split(r' — | · | \| | {2,}', cell):
                frag = frag.strip(' .,;')
                if len(frag) >= 2 and not set(frag) <= set('-'):
                    out.append(frag)
    return out


def check_text(doc, pages):
    problems, stats = [], []
    for no, body in pages.items():
        if no > len(doc):
            problems.append(f'{no}쪽 없음')
            continue
        actual = norm(doc[no - 1].get_text())
        frags = fragments(body)
        missing = [f for f in frags if norm(f) not in actual]
        stats.append({'page': no, 'fragments': len(frags), 'missing': len(missing)})
        for f in missing:
            problems.append(f'{no}쪽 누락: {f[:60]}')
    return problems, stats


def check_notices(doc):
    problems = []
    if norm(BOUNDARY) not in norm(doc[12].get_text()):
        problems.append('13쪽 미판정 경계 문구 불일치')
    for no, labels in NOTICES.items():
        text = doc[no - 1].get_text()
        for label in labels:
            if label not in text:
                problems.append(f'{no}쪽 고지 누락: {label}')
    for word in FORBIDDEN:
        for i, page in enumerate(doc, 1):
            if word in page.get_text():
                problems.append(f'{i}쪽 금지 표현: {word}')
    return problems


def check_glyphs():
    problems = []
    used = {ch for ch in MD.read_text(encoding='utf-8') if not ch.isspace()}
    for name in ('NotoSansKR-Regular.ttf', 'NotoSansKR-Bold.ttf'):
        font = TTFont(str(HERE / 'fonts' / name))
        cmap = set()
        for table in font['cmap'].tables:
            cmap |= set(table.cmap)
        missing = sorted(ch for ch in used if ord(ch) not in cmap)
        if missing:
            problems.append(f'{name} 글리프 없음: {"".join(missing)}')
    return problems


def check_numbers(pages):
    corpus_files = [p for p in (ROOT / 'reports').glob('*.md') if '포트폴리오' not in p.name]
    corpus_files += [ROOT / 'README.md', ROOT / 'worklog.md']
    corpus_files += list(HERE.glob('*.py')) + list(HERE.glob('*.json'))
    corpus = ''
    for path in corpus_files:
        corpus += path.read_text(encoding='utf-8', errors='ignore') + '\n'
    corpus = corpus.replace(',', '')
    tokens = set()
    for body in pages.values():
        for token in re.findall(r'\d+(?:[.,]\d+)*', body):
            tokens.add(token.replace(',', ''))
    return sorted(t for t in tokens if t not in corpus)


def check_size(doc):
    problems = []
    for i, page in enumerate(doc, 1):
        w, h = page.rect.width, page.rect.height
        if abs(w - PAGE_W) > 0.6 or abs(h - PAGE_H) > 0.6:
            problems.append(f'{i}쪽 크기 {w:.1f}×{h:.1f} (960×540 아님)')
    return problems


def check_layout(doc):
    problems = []
    for i, page in enumerate(doc, 1):
        if not norm(page.get_text()).strip():
            problems.append(f'{i}쪽 빈 쪽')
            continue
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                for span in line['spans']:
                    x0, y0, x1, y1 = span['bbox']
                    if x0 < M - TOL or x1 > page.rect.width - M + TOL:
                        problems.append(f'{i}쪽 여백 침범 x={x0:.1f}~{x1:.1f}: {span["text"][:36]}')
                    if y1 > TOP_LIMIT or y0 < BOTTOM_LIMIT:
                        problems.append(f'{i}쪽 상하 침범 y={y0:.1f}~{y1:.1f}: {span["text"][:36]}')
    images = {i: len(doc[i - 1].get_images(full=True)) for i in range(1, len(doc) + 1)}
    for no in IMAGE_PAGES:
        if images[no] < 1:
            problems.append(f'{no}쪽 이미지 없음')
    return problems, images


def check_overlap(doc, ratio=0.4):
    problems = []
    for i, page in enumerate(doc, 1):
        spans = []
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                for span in line['spans']:
                    if span['text'].strip():
                        spans.append((pymupdf.Rect(span['bbox']), span['text']))
        for a in range(len(spans)):
            ra, ta = spans[a]
            for b in range(a + 1, len(spans)):
                rb, tb = spans[b]
                inter = ra & rb
                if inter.is_empty:
                    continue
                share = (inter.width * inter.height) / max(1.0, min(ra.width * ra.height, rb.width * rb.height))
                if share > ratio:
                    problems.append(f'{i}쪽 글자 겹침 {share:.0%}: {ta[:16]} / {tb[:16]}')
    return problems


def main():
    doc = pymupdf.open(PDF)
    pages = md_pages()
    problems = []
    if doc.page_count != 13:
        problems.append(f'쪽수 {doc.page_count} (13 아님)')
    if len(pages) != 13:
        problems.append(f'MD 쪽 구획 {len(pages)}개 (13 아님)')

    text_problems, stats = check_text(doc, pages)
    problems += text_problems
    problems += check_notices(doc)
    problems += check_glyphs()
    problems += check_size(doc)
    problems += check_overlap(doc)
    layout, images = check_layout(doc)
    problems += layout
    numbers = check_numbers(pages)
    if numbers:
        problems.append('문서에 없는 숫자: ' + ', '.join(numbers))

    print('쪽수', doc.page_count, '| MD 쪽 구획', len(pages))
    for row in stats:
        print(f'  {row["page"]:>2}쪽 조각 {row["fragments"]:>3}개 · 누락 {row["missing"]}')
    print('쪽별 이미지', images)
    if problems:
        print(f'\n실패 {len(problems)}건')
        for p in problems[:40]:
            print(' -', p)
        return 1
    print('\n통과 — 13쪽·16:9·MD↔PDF·고지·글리프·숫자 출처·여백·겹침·이미지 확인')
    return 0


if __name__ == '__main__':
    sys.exit(main())
