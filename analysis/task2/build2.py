# -*- coding: utf-8 -*-
"""현행 MD를 수정하지 않고 보고서 PDF 두 편을 생성한다."""

import hashlib
import html
import json
import re
from pathlib import Path

from markdown_it import MarkdownIt
from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
REPORTS = [
    ROOT / 'reports/메디큐브_국내_타깃가설_마케팅전략.md',
    ROOT / 'reports/메디큐브_글로우_리뷰분석_2030전략연결.md',
]
FIGURES = {
    '1-1': 'f1_gap', '3-1': 'f2_click2030', '3-2': 'f3_mini',
    '3-3': 'f4_minishare', '4-1': 'f6_dev5060', '4-3': 'f10_gap5060',
    '4-4': 'f11_skin5060', '4-5': 'f7_line', '7-1': 'f8_calendar',
}


def render_markdown(path):
    """MD 경로를 받아 HTML·표시 본문·도표·번호 목록을 반환한다.

    표와 인라인 코드를 파싱하고, 본 보고서의 그림 캡션에 기존 SVG를 연결한다.
    표시 본문은 링크 주소와 서식 기호를 제외해 PDF 추출문과 대조할 기준이다.
    """
    parser = MarkdownIt('commonmark', {'html': False}).enable('table')
    source = path.read_text(encoding='utf-8')
    tokens = parser.parse(source)
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
    body = re.sub(r'href="([^"#:]+)\.md(#[^"]*)?"', r'href="\1.pdf\2"', body)
    css = (HERE / 'pdf.css').read_text(encoding='utf-8')
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
