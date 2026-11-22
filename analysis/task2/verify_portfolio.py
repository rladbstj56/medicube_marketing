# -*- coding: utf-8 -*-
"""14쪽 포트폴리오 PDF·MD 검증 — Behance식 이미지 중심 덱 규격.

① 쪽수 14 · 쪽 크기 960×540pt(16:9)
② MD 본문 조각이 같은 쪽 PDF에 실제로 있는지(공백 무시 대조)
③ AI 제작·승인 전 콘셉트 고지가 정해진 쪽에 있는지
④ 두 글꼴이 MD의 모든 글자를 가지고 있는지(두부 글자 방지)
⑤ 인용한 숫자가 저장소 현행 문서·스크립트에 있는지
⑥ 여백 침범·글자 겹침·빈 쪽·이미지 누락이 없는지
⑦ 미판정 경계 문구가 14쪽에 그대로 있는지, 금지 표현이 없는지
⑧ 2026-11-22 2·4차 일괄 수정 항목의 문구가 그대로 있는지(REQUIRED) ·
   `사후 CRM`·`5.6%`·`LIMITS & APPENDIX`처럼 걷어낸 표현이 남아 있지 않은지(RETIRED)
⑨ 7·8·12쪽 인쇄물 설명이 **각 이미지 가로 폭의 중심**에 놓였는지(CENTERED_PAGES)

5차 판(17개 항목)은 2쪽 고지·공식 툴 로고 6종, 4~12쪽 하단 문구(AI 활용 고지),
4쪽 목표·9쪽 ABOUT 4행, 10쪽 제목·글자 크기, 11쪽 소제목, 13쪽 듀얼 트랙(검증 게이트
삭제·툴 6칩·5060 홍보물 2종 썸네일), 14쪽 `CLOSING` 단독 면, 3쪽 `05 CLOSING`을
확인한다.
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

# 2026-11-22 4차 지시(4번)로 14쪽의 경계 문단은 **한 줄 고지**로 바뀌었다. 이전 판의
# `미확인` 목록과 미판정 문단은 14쪽에서 걷어냈다.
BOUNDARY = ('[알림] 본 덱의 수치는 공개 자료 기반이며, 집행 전 시안은 실제 성과·편성과 무관합니다.')

# 대괄호 라벨로 남는 고지는 14쪽 두 줄뿐이다. 4~12쪽은 2026-11-22 5차 지시로 대괄호 없이
# `AI를 활용하여 …` 문장 안에 녹였으므로, 그 문장은 아래 REQUIRED에서 쪽별로 확인한다.
NOTICES = {
    14: ['[알림]', '[AI 제작]'],
}

# 이미지가 있어야 하는 쪽(표지·목차·일하는 방식·부록은 활자와 도형만 쓴다)
IMAGE_PAGES = (4, 5, 6, 7, 8, 9, 10, 11, 12)

FORBIDDEN = ['매출이 늘었다', 'ROAS 1', '구매 전환', '효과가 검증되었다',
             '개선이 완료되었다', '매출 상승을 확인']

# 2026-11-22 5차 지시(17개 항목)의 문구가 지면에 실제로 남아 있는지 쪽별로 확인한다.
# 값은 build_portfolio.py의 데이터와 같은 문자열이어야 한다(한쪽만 고치면 여기서 걸린다).
REQUIRED = {
    1: ['2030 타깃 부스터 글로우 마케팅', '5060 타깃 부스터 프로 X2 마케팅'],
    2: ['2026.07 취득', '2025.04 취득', '2025.09 취득', '925점',
        'Python', 'SQL', 'Notion', 'Figma', 'MCP',
        'Codex', 'CapCut', 'Higgsfield', 'Kling', 'ElevenLabs'],
    3: ['PROFILE', 'CLOSING',
        '리뷰 수집 · 숏폼 콘티 · 시안 · CRM 설계',
        '리뷰 수집 · 채널 선정 · 홍보물 제작',
        '숏폼 콘티 · 브릿지 카드 · 포스터 2종 · 자사몰 앱 CRM',
        'GS샵 1주년 홍보물 2종(방송 홍보 · 모드 가이드) · 사용 장벽 리뷰 분석'],
    4: ['생활 속 피부 고민 공감에서 데일리 루틴 · 앱 리텐션까지 연결',
        '해당 이미지는 AI를 활용하여 생성함',
        'Python · Photoshop MCP · Kling · Higgsfield · Codex · Pickle',
        '리뷰 수집 · 숏폼 콘티 · 시안 · CRM 설계'],
    5: ['장면별 숏폼 연출은 시안임. 해당 숏폼 이미지는 AI를 활용하여 생성함.'],
    6: ['앱 화면은 기획 시안. 실제 앱 반영 및 발송 기록은 없음. 화면 목업 이미지는 AI를 활용하여 제작'],
    7: ['포스터 연출 컷은 생성형 AI를 활용하여 제작. 실제 광고 집행과 성과는 없음.'],
    8: ['엔드카드와 브릿지 카드 3종', '엔드카드·브릿지 카드 4종',
        '화면 목업 및 연출 컷은 생성형 AI를 활용하여 제작. 실제 광고 집행과 성과는 없음. 숏폼 원본은 편집 미완성'],
    9: ['Python · Photoshop MCP · Codex · Pickle', '리뷰 수집 · 채널 선정 · 홍보물 제작',
        '해당 방송 홍보물은 AI를 활용하여 생성함. 실제 편성, 구성, 가격, 혜택 미확정'],
    10: ['첫 론칭 주의 검색 급등을 1주년 재방송으로 잇다',
         '01 · 근거 — 5060 검색·클릭 52주 추이', '검색 지수 · 부스터 프로',
         '클릭 지수 · 메디큐브', '100.0', '52주 최고', '38 → 68',
         '5/4 주 동시 급등 · 5/9 GS샵 첫 론칭',
         '02 · 1주년 방송 연계 계획', '5060 검색 직전주 대비 27.3% 상승',
         '리뷰 221건 사용 장벽 파악', '2027.05.09', '1주년 방송 연계 제안',
         '불편 해소 홍보물 2종',
         '해당 방송 계획은 제안이며 편성, 구성, 가격, 혜택 미확정. 52주 추이는 검색과 클릭 지수일 뿐, 매출과 성과와는 상관없음'],
    11: ['5060은 \'성능\'이 아니라 \'사용법\'에서 막힙니다',
         'GS샵 상품평 221건 전수 코딩하여 데이터 수집',
         '① 방송 홍보', '6단계 강도 · 1단계부터 시작', '자극 · 버튼 우려 완화',
         '② 모드 가이드', '6가지 모드 한눈 정리', '설명 혼란 해소',
         '해당 홍보물은 AI를 활용하여 생성함.'],
    12: ['GS샵 방송 홍보', '6가지 모드 한눈에', '2027.05.09 19:00 편성 제안',
         '방송 편성, 구성, 가격, 혜택 미확정. 해당 홍보물은 AI를 활용하여 생성함.'],
    13: ['원자료 수집', '& 전수 검증', '데이터랩 · 리뷰 438건', '원자료 대조',
         '2030 · AQUA · 4~8쪽', '타깃 인사이트', '광채 · 보습 · 결',
         '숏폼 콘티 · 브릿지', '포스터 2종 · 앱 CRM',
         '5060 · PLUM · 9~12쪽', '5/9 GS샵 론칭 피크', '실사용 불편 키워드 도출',
         '1주년 GS샵 재방송', '홍보물 2종',
         'Python', 'Photoshop', 'Higgsfield', 'Kling', 'Codex', 'Pickle'],
    14: ['CLOSING', 'KIM YOONSEO · 김윤서', '감사합니다',
         '공개 데이터로 판단하고, 콘텐츠로 옮기겠습니다.',
         'rladbstj56@gmail.com', '010-9056-0349', 'https://github.com/rladbstj56',
         '[알림] 본 덱의 수치는 공개 자료 기반이며, 집행 전 시안은 실제 성과·편성과 무관합니다.'],
}

# 걷어낸 표현 — 다시 들어오면 실패한다. 5차 지시로 걷어낸 대괄호 고지·장문 안내,
# 4쪽 이전 목표 문장, 11쪽 이전 소제목, 13쪽 검증 게이트, 14쪽 APPENDIX가 대상이다.
RETIRED = ['루틴 카드', 'VOC 기반 UX/패키지', 'GTX', '22건', '35건', '5.4%',
           '사후 CRM', 'phone_x2_crm', 'D+0', 'D+14', '방송 예고',
           '메인 포스터는 하루의 세 순간을 담았습니다',
           '5.6%', '74.3%', 'LIMITS & APPENDIX', '+89.9%', '+30.2%', '+22.7%',
           '02 · 판단', '부스터 글로우 라인', '미확인',
           '그래서 14쪽에 미확정을 먼저 적었습니다', '확인되지 않은 것은 확인된 것처럼 쓰지 않는다',
           # ── 5차 지시(1·3~16번)로 걷어낸 문구
           '사진과 이력은 지원자 본인이 제공한 내용입니다',
           '모든 건수는', '장면별 고민 · 케어 표현은 집행 전 시안입니다',
           '[실행 제안]', '[승인 전 콘셉트]',
           '고민 한 문장을 30초로 붙잡고',
           '방송 전 예고부터 배송 후 사용까지',
           'GS샵 상품평 221건을 전수 코딩했습니다',
           '도구는 생성과 렌더링에만 쓰고', '숫자는 저장소에서 다시 실행해 확인합니다',
           '검증 게이트', '141항목 재계산', '리뷰 221건 장벽',
           'APPENDIX', '조사·분석 보고서 아카이브',
           '국내 타깃·가설 v2.9', '피크 주 대조 v1.5',
           'CLOSING & APPENDIX', '표지의 두 축']

# 쪽 하나에서만 걷어낸 문구 — 표지(1쪽)에는 그대로 남아 있으므로 전역 검사로는 못 잡는다.
PAGE_RETIRED = {
    9: ['목표'],
    13: ['검증 게이트', '141항목'],
    14: ['2030 타깃 부스터 글로우 마케팅', '5060 타깃 부스터 프로 X2 마케팅',
         '국내 콘텐츠 마케팅 지원'],
}

# 설명을 이미지 가로 폭 중앙에 맞춘 쪽 — 이미지 아래 두 줄(연번+이름, 규격·설명)의
# 중심이 이미지 중심에서 3pt 안에 있어야 한다.
CENTERED_PAGES = (7, 8, 12)
CENTER_TOL = 3.0


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
    if norm(BOUNDARY) not in norm(doc[13].get_text()):
        problems.append('14쪽 미판정 경계 문구 불일치')
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


def check_required(doc):
    problems = []
    for no, strings in REQUIRED.items():
        text = norm(doc[no - 1].get_text())
        for value in strings:
            if norm(value) not in text:
                problems.append(f'{no}쪽 필수 문구 없음: {value[:44]}')
    return problems


def check_retired(doc):
    problems = []
    for word in RETIRED:
        for i, page in enumerate(doc, 1):
            if word in page.get_text():
                problems.append(f'{i}쪽 걷어낸 표현 남음: {word}')
    return problems


def check_page_retired(doc):
    """쪽 하나에서만 걷어낸 문구가 그 쪽에 되살아나지 않았는지 본다(2026-11-22 5차 지시)."""
    problems = []
    for no, words in PAGE_RETIRED.items():
        text = norm(doc[no - 1].get_text())
        for word in words:
            if norm(word) in text:
                problems.append(f'{no}쪽 걷어낸 표현 남음: {word}')
    return problems


def check_centered(doc):
    """인쇄물 설명이 각 이미지의 가로 중심에 놓였는지 본다.

    이미지 아래 두 줄(연번+이름 · 규격·설명)을 각각 한 줄씩 보고, 줄의 가로 중심과
    이미지 중심의 차이를 잰다. 2026-11-22 지시 5·6·9번이 좌측 정렬로 되돌아가면
    줄의 중심이 반 줄 폭만큼(수십 pt) 어긋나 바로 걸린다.
    """
    problems = []
    for no in CENTERED_PAGES:
        page = doc[no - 1]
        spans = [pymupdf.Rect(s['bbox']) for b in page.get_text('dict')['blocks']
                 for line in b.get('lines', []) for s in line['spans'] if s['text'].strip()]
        images = [pymupdf.Rect(info['bbox']) for info in page.get_image_info()
                  if info['bbox'][2] - info['bbox'][0] > 120]
        if len(images) < 2:
            problems.append(f'{no}쪽 인쇄물 이미지 {len(images)}장 (2장 이상이어야 정렬 확인)')
            continue
        for img in images:
            # pymupdf 좌표는 위가 0이므로 '이미지 아래'는 y0가 img.y1보다 큰 구간이다.
            # 가로는 이미지 폭 ±40pt 안에 든 줄만 그 이미지의 설명으로 본다.
            near = [r for r in spans
                    if r.y0 >= img.y1 - 0.5 and r.y1 <= img.y1 + 42
                    and img.x0 - 40 <= (r.x0 + r.x1) / 2 <= img.x1 + 40]
            lines = []
            for rect in sorted(near, key=lambda r: (round(r.y0), r.x0)):
                if lines and abs(lines[-1][0].y0 - rect.y0) < 3:
                    lines[-1].append(rect)
                else:
                    lines.append([rect])
            if len(lines) != 2:
                problems.append(f'{no}쪽 이미지 아래 설명 {len(lines)}줄 (2줄 필요)')
                continue
            cx = (img.x0 + img.x1) / 2
            for group in lines:
                left, right = min(r.x0 for r in group), max(r.x1 for r in group)
                gap = abs((left + right) / 2 - cx)
                if gap > CENTER_TOL:
                    problems.append(f'{no}쪽 설명 중심 {gap:.1f}pt 어긋남 '
                                    f'(이미지 중심 {cx:.1f} · 줄 중심 {(left + right) / 2:.1f})')
    return problems


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
    if doc.page_count != 14:
        problems.append(f'쪽수 {doc.page_count} (14 아님)')
    if len(pages) != 14:
        problems.append(f'MD 쪽 구획 {len(pages)}개 (14 아님)')

    text_problems, stats = check_text(doc, pages)
    problems += text_problems
    problems += check_notices(doc)
    problems += check_required(doc)
    problems += check_retired(doc)
    problems += check_page_retired(doc)
    problems += check_centered(doc)
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
    print('\n통과 — 14쪽·16:9·MD↔PDF·고지·필수/걷어낸 문구·이미지 중심 정렬·글리프·숫자 출처·여백·겹침·이미지 확인')
    return 0


if __name__ == '__main__':
    sys.exit(main())
