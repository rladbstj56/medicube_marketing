# -*- coding: utf-8 -*-
"""14쪽 포트폴리오 PDF·MD 검증 — 16:9 가로형 덱 규격.

① 쪽수 = 14, 쪽 크기 = 960×540pt(13.33×7.5in, 16:9 피피티 슬라이드)
② MD 본문 문장이 해당 쪽 PDF에 실제로 있는지(공백 제거 후 대조)
③ 고정 문구·5060 경계 문장이 원문 그대로인지
④ 글꼴이 모든 글자를 가지고 있는지(두부 글자 방지)
⑤ 인용한 모든 숫자가 저장소 현행 문서·스크립트에 있는지
⑥ 여백을 넘어간 글자·겹친 글자·빈 쪽·이미지 누락이 없는지
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
PAGE_W, PAGE_H = 960.0, 540.0   # 16:9 슬라이드 규격
M = 44.0                         # 좌우 여백(조판과 같은 값)
TOL = 2.5

FIXED = ('공개 검색·클릭 지표와 수집 가능한 리뷰로 콘텐츠 및 채널 기회를 검토했다. '
         '고객별 구매, 제품별 순매출, 광고 성과가 없어 타깃의 실제 구매 규모와 '
         '전략 효과는 판정하지 않았다.')
BOUNDARY = '공개 근거를 연결할 수 있어 GS샵 X2 방송 연계안을 먼저 설계했다.'

# 성과·효과를 주장하는 문장이 들어가면 안 된다.
# 인용 형태('쓰지 않는 문장')로만 나와야 하는 문장과, 아예 없어야 하는 문장을 나눈다.
QUOTED_ONLY = ['5060이 X2를 많이 구매했다']
FORBIDDEN = ['매출이 늘었다', 'ROAS 1', '구매 전환', '효과가 검증되었다',
             '개선이 완료되었다', '매출 상승을 확인']


def norm(text):
    text = unicodedata.normalize('NFKC', text)
    return re.sub(r'\s+', '', text)


def md_pages():
    """MD를 쪽 단위로 나눠 (쪽번호, 본문) 목록을 만든다."""
    source = MD.read_text(encoding='utf-8')
    parts = re.split(r'^## (\d+)쪽 · .*$', source, flags=re.M)
    pages = {}
    for i in range(1, len(parts), 2):
        pages[int(parts[i])] = parts[i + 1]
    return pages


TAG = re.compile(r'<[^>]+>')
MD_MARK = re.compile(r'(\*\*|`|^#+\s*|^>\s*|^\d+\.\s*|^[-*]\s*|\*)')


def plain(text):
    """MD 표기·HTML 태그를 지워 PDF 추출문과 비교할 수 있게 한다."""
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = TAG.sub('', text)
    text = MD_MARK.sub('', text)
    return text.strip()


def fragments(line):
    """한 줄을 PDF에서 따로 찾을 수 있는 조각들로 나눈다."""
    line = plain(line)
    parts = re.split(r'\||  | — |: ', line)
    return [p.strip(' .') for p in parts if len(p.strip(' .')) >= 2]


def content_lines(body):
    """목차용 머리표·표 구분선을 뺀 실제 본문 조각만 남긴다."""
    out = []
    for line in body.splitlines():
        line = line.strip()
        if not line or set(line) <= set('-|'):
            continue
        if line.startswith('!['):
            continue
        if line.startswith('|'):
            for cell in line.strip('|').split('|'):
                cell = cell.strip()
                if cell and set(cell) > set('-'):
                    out.extend(fragments(cell))
            continue
        out.extend(fragments(line))
    return out


def check_text_matches(doc, pages):
    """MD 문장이 같은 쪽 PDF 본문에 있는지 확인한다."""
    problems = []
    stats = []
    for no, body in pages.items():
        if no > len(doc):
            problems.append(f'{no}쪽 없음')
            continue
        actual = norm(doc[no - 1].get_text())
        lines = content_lines(body)
        missing = [line for line in lines if norm(line) and norm(line) not in actual]
        stats.append({'page': no, 'lines': len(lines), 'missing': len(missing)})
        for line in missing:
            problems.append(f'{no}쪽 누락: {line[:70]}')
    return problems, stats


def check_fixed(doc):
    problems = []
    for no in (4, 14):
        text = norm(doc[no - 1].get_text())
        if norm(FIXED) not in text:
            problems.append(f'{no}쪽 고정 한계 문구 불일치')
    if norm(BOUNDARY) not in norm(doc[9].get_text()):
        problems.append('10쪽 5060 경계 문장 누락')
    for word in QUOTED_ONLY:
        for i, page in enumerate(doc, 1):
            text = page.get_text()
            if word in text and '쓰지 않는 문장' not in text:
                problems.append(f'{i}쪽 인용 없는 단정: {word}')
    for word in FORBIDDEN:
        for i, page in enumerate(doc, 1):
            if word in page.get_text():
                problems.append(f'{i}쪽 금지 표현: {word}')
    return problems


def check_glyphs(pages):
    """본문에 쓴 모든 글자가 임베드 글꼴에 있는지 확인한다(빈 네모 방지)."""
    problems = []
    body = MD.read_text(encoding='utf-8')
    used = {ch for ch in body if not ch.isspace()}
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
    """포트폴리오의 모든 숫자 토큰이 저장소 현행 문서에 있는지 확인한다."""
    corpus_files = [p for p in (ROOT / 'reports').glob('*.md')
                    if '포트폴리오' not in p.name]
    corpus_files += [ROOT / 'README.md', ROOT / 'worklog.md']
    corpus_files += list((HERE).glob('*.py')) + list((HERE).glob('*.json'))
    corpus = ''
    for path in corpus_files:
        corpus += path.read_text(encoding='utf-8', errors='ignore') + '\n'
    corpus = corpus.replace(',', '')
    tokens = set()
    for body in pages.values():
        for token in re.findall(r'\d+(?:[.,]\d+)*', body):
            tokens.add(token.replace(',', ''))
    missing = sorted(t for t in tokens if t not in corpus)
    return missing


def check_page_size(doc):
    """쪽 크기가 16:9 슬라이드 규격인지 확인한다."""
    problems = []
    for i, page in enumerate(doc, 1):
        w, h = page.rect.width, page.rect.height
        if abs(w - PAGE_W) > 0.6 or abs(h - PAGE_H) > 0.6:
            problems.append(f'{i}쪽 크기 {w:.1f}×{h:.1f} (16:9 {PAGE_W:.0f}×{PAGE_H:.0f} 아님)')
    return problems


def check_overlap(doc, ratio=0.4):
    """다른 글자와 40% 넘게 겹친 글자가 없는지 확인한다(겹침 0건)."""
    problems = []
    for i, page in enumerate(doc, 1):
        spans = []
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                for span in line['spans']:
                    text = span['text'].strip()
                    if len(text) >= 1:
                        spans.append((pymupdf.Rect(span['bbox']), text))
        for a in range(len(spans)):
            ra, ta = spans[a]
            for b in range(a + 1, len(spans)):
                rb, tb = spans[b]
                inter = ra & rb
                if inter.is_empty:
                    continue
                share = (inter.width * inter.height) / max(
                    1.0, min(ra.width * ra.height, rb.width * rb.height))
                if share > ratio:
                    problems.append(f'{i}쪽 글자 겹침 {share:.0%}: {ta[:18]} / {tb[:18]}')
    return problems


def check_layout(doc):
    problems = []
    for i, page in enumerate(doc, 1):
        if not norm(page.get_text()).strip():
            problems.append(f'{i}쪽 빈 쪽')
            continue
        data = page.get_text('dict')
        for block in data['blocks']:
            for line in block.get('lines', []):
                for span in line['spans']:
                    x0, x1 = span['bbox'][0], span['bbox'][2]
                    if x0 < M - TOL or x1 > page.rect.width - M + TOL:
                        problems.append(
                            f'{i}쪽 여백 침범 x={x0:.1f}~{x1:.1f}: {span["text"][:40]}')
    images = {i: len(doc[i - 1].get_images(full=True)) for i in range(1, len(doc) + 1)}
    for no in (4, 9, 11, 13):
        if images[no] < 1:
            problems.append(f'{no}쪽 이미지 없음')
    return problems, images


def main():
    doc = pymupdf.open(PDF)
    pages = md_pages()
    problems = []
    if doc.page_count != 14:
        problems.append(f'쪽수 {doc.page_count} (14 아님)')
    if len(pages) != 14:
        problems.append(f'MD 쪽 구획 {len(pages)}개 (14 아님)')

    text_problems, stats = check_text_matches(doc, pages)
    problems += text_problems
    problems += check_fixed(doc)
    problems += check_glyphs(pages)
    numbers = check_numbers(pages)
    problems += check_page_size(doc)
    problems += check_overlap(doc)
    layout_problems, images = check_layout(doc)
    problems += layout_problems

    print('쪽수', doc.page_count, '| MD 쪽 구획', len(pages))
    for row in stats:
        print(f'  {row["page"]:>2}쪽 문장 {row["lines"]:>3}개 · 누락 {row["missing"]}')
    print('쪽별 이미지', images)
    if numbers:
        print('문서에 없는 숫자:', numbers)
    if problems:
        print('\n실패', len(problems), '건')
        for p in problems[:40]:
            print(' -', p)
        return 1
    print('\n통과 — 쪽수·16:9 크기·본문·고정 문구·글리프·숫자 출처·여백·겹침·이미지 확인')
    return 0


if __name__ == '__main__':
    sys.exit(main())
