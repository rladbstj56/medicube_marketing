# -*- coding: utf-8 -*-
"""현행 MD를 수정하지 않고 보고서 PDF 여덟 편을 생성한다."""

import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import unquote

from markdown_it import MarkdownIt
from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
REPORTS = [
    ROOT / 'reports/메디큐브_국내_타깃가설_마케팅전략.md',
    ROOT / 'reports/메디큐브_글로우_리뷰분석_2030전략연결.md',
    ROOT / 'reports/메디큐브_GS샵_X2_2027_5월_프로모션기획서.md',
    ROOT / 'reports/메디큐브_GS샵_X2_2027_5월_정적스토리보드.md',
    ROOT / 'reports/메디큐브_GS샵_X2_리뷰분석.md',
    ROOT / 'reports/메디큐브_국내_트렌드_분석보고서.md',
    ROOT / 'reports/메디큐브_글로벌_트렌드_분석보고서.md',
    ROOT / 'reports/메디큐브_국내_피크주_광고_이벤트_대조분석.md',
]
FIGURES = {
    '1-1': 'f1_gap', '3-1': 'f2_click2030', '3-2': 'f3_mini',
    '3-3': 'f4_minishare', '4-1': 'f6_dev5060', '4-3': 'f10_gap5060',
    '4-4': 'f11_skin5060', '4-5': 'f7_line', '7-1': 'f8_calendar',
}


def lenient_strong(source):
    """`**…**` 표기를 `<strong>…</strong>`로 바꿔 준다.

    CommonMark는 닫는 `**`가 문장부호 뒤·한글 조사 앞에 오면(예: `**46.1%**로`,
    `**+12.1p.p.**입니다`) 강조로 읽지 않아 별표가 본문에 그대로 남는다. 원문이
    쓰는 표기를 그대로 살리기 위해 인라인 코드 안은 건드리지 않고 치환한다.
    """
    spans = []

    def keep(match):
        spans.append(match.group(0))
        return f'\x00{len(spans) - 1}\x00'

    lines = []
    in_fence = False
    for line in source.split('\n'):
        if line.lstrip().startswith(('```', '~~~')):
            in_fence = not in_fence
            lines.append(line)
            continue
        if in_fence:
            lines.append(line)
            continue
        line = re.sub(r'`[^`\n]*`', keep, line)
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        lines.append(line)
    text = '\n'.join(lines)
    return re.sub(r'\x00(\d+)\x00', lambda m: spans[int(m.group(1))], text)


def render_markdown(path):
    """MD 경로를 받아 HTML·표시 본문·도표·번호 목록을 반환한다.

    표와 인라인 코드를 파싱하고, 본 보고서의 그림 캡션에 기존 SVG를 연결한다.
    표시 본문은 링크 주소와 서식 기호를 제외해 PDF 추출문과 대조할 기준이다.
    """
    parser = MarkdownIt('commonmark', {'html': True}).enable('table')
    source = path.read_text(encoding='utf-8')
    tokens = parser.parse(lenient_strong(source))
    texts = []
    ordered_markers = []
    for index, token in enumerate(tokens):
        if token.type == 'ordered_list_open':
            items = 0
            for following in tokens[index + 1:]:
                if following.type == 'ordered_list_close' and following.level == token.level:
                    break
                if following.type == 'list_item_open' and following.level == token.level + 1:
                    items += 1
            start = token.attrGet('start') or 1
            ordered_markers.append(''.join(f'{n}.' for n in range(int(start), int(start) + items)))
        if token.type == 'inline':
            texts.append(''.join(
                child.content if child.type in ('text', 'code_inline') else '\n'
                if child.type in ('softbreak', 'hardbreak') else ''
                for child in token.children or []
            ))
        elif token.type in ('fence', 'code_block'):
            texts.append(token.content)
    body = parser.renderer.render(tokens, parser.options, {})
    # MD에 직접 넣은 도표(`![...](../analysis/task2/fig/..)`)는 문단 대신 figure로 감싸
    # 캡션과 함께 한 덩어리로 유지하고, 페이지 경계에서 그림만 잘리지 않게 한다.
    # fig 경로가 아닌 다른 이미지(디자인 시안 등)의 기존 동작은 그대로 둔다.
    body = re.sub(r'<p>\s*(<img [^>]*analysis/task2/fig/[^>]*>)\s*(?=<)',
                  r'<figure>\1</figure><p>', body)
    # 표지 제목은 대시 앞에서 줄을 바꿔 한글 단어가 중간에서 끊기는 것을 막는다.
    # 글자는 그대로이고 줄바꿈만 넣으므로 본문 대조에는 영향이 없다.
    body = re.sub(r'<h1>(.*?)</h1>',
                  lambda m: '<h1>' + m.group(1).replace(' — ', ' —<br>', 1) + '</h1>',
                  body, count=1, flags=re.S)
    figures = []
    if path == REPORTS[0]:
        for number, filename in FIGURES.items():
            figure = HERE / 'fig' / f'{filename}.svg'
            caption = re.compile(r'(<p><em>그림 ' + re.escape(number) + r'\.)')
            assert caption.search(body), f'그림 캡션 없음: {number}'
            body = caption.sub(
                '<figure><img src="' + figure.as_uri() + '" alt=""></figure>\\1', body
            )
            figures.append(str(figure.relative_to(ROOT)))
    for match in list(re.finditer(r'href="([^"#:]+)\.md(#[^"]*)?"', body)):
        target = path.parent / unquote(html.unescape(match.group(1) + '.pdf'))
        if target.exists():
            body = body.replace(match.group(0),
                                'href="' + match.group(1) + '.pdf' + (match.group(2) or '') + '"')
    css = (HERE / 'pdf.css').read_text(encoding='utf-8')
    # 폰트는 저장소에 동봉한 파일을 절대 file URI로 지정해, 빌드 위치나 OS 기본
    # 폰트 유무와 무관하게 같은 굵기로 임베드되게 한다.
    css = css.replace('__FONTS__', (HERE / 'fonts').as_uri())
    title = source.splitlines()[0].lstrip('# ')
    document = ('<!doctype html><html lang="ko"><head><meta charset="utf-8">'
                f'<title>{html.escape(title)}</title><style>{css}</style></head>'
                f'<body>{body}</body></html>')
    return document, '\n'.join(texts), figures, ordered_markers


def build_pdf(path):
    """MD 경로를 받아 PDF를 저장하고 해시·본문·페이지 수 기록을 반환한다.

    HTML 중간 파일과 동일 입력 해시를 남겨 이전 MD로 만든 PDF를 식별한다.
    """
    document, text, figures, ordered_markers = render_markdown(path)
    output = path.with_suffix('.pdf')
    temp = ROOT / 'tmp/pdfs'
    temp.mkdir(parents=True, exist_ok=True)
    (temp / (path.stem + '.html')).write_text(document, encoding='utf-8')
    rendered = HTML(string=document, base_url=str(path.parent)).render()
    rendered.write_pdf(output)
    layout_text = '\n'.join(
        box.text for page in rendered.pages for box in page._page_box.descendants()
        if hasattr(box, 'text') and box.position_y * .75 >= 42
        and (box.position_y + box.height) * .75 <= page.height * .75 - 38
    )
    return {
        'source': str(path.relative_to(ROOT)), 'pdf': str(output.relative_to(ROOT)),
        'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'pdf_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'pages': len(rendered.pages), 'expected_text': text,
        'layout_text': layout_text, 'figures': figures,
        'ordered_list_markers': ordered_markers,
    }


if __name__ == '__main__':
    results = [build_pdf(path) for path in REPORTS]
    (HERE / 'pdf_build_manifest.json').write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    print(json.dumps([{k: v for k, v in row.items() if k not in ('expected_text', 'layout_text')}
                      for row in results], ensure_ascii=False, indent=2))
