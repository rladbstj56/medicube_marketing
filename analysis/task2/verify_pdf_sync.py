"""MD 입력 해시·렌더 본문·PDF 추출문을 대조한다. 숫자 일치만으로 완료하지 않는다."""

import difflib
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from collections import Counter

import fitz

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def normalize(text):
    """문자열을 받아 줄바꿈·글머리표 차이를 제거한 표시 본문을 반환한다.

    숫자와 문장부호는 보존하며 글꼴이 만든 합자만 NFKC로 통일한다.
    """
    text = unicodedata.normalize('NFKC', text)
    return re.sub(r'\s+', '', text).replace('•', '').replace('\u00ad', '')


def verify_record(record):
    """빌드 기록 한 건을 받아 입력·출력 해시와 본문 일치 결과를 반환한다.

    머리말·쪽번호를 제외한 PDF 본문을 추출한다. 반복 표제·목록 번호의 삽입과
    원문 누락을 구분하고 실제 배치 본문과는 전체 문자열을 대조한다.
    """
    source = ROOT / record['source']
    pdf = ROOT / record['pdf']
    document = fitz.open(pdf)
    page_text = [page.get_text(clip=fitz.Rect(0, 42, page.rect.width, page.rect.height - 38))
                 for page in document]
    actual = normalize('\n'.join(page_text))
    expected = normalize(record['expected_text'])
    layout = normalize(record['layout_text'])
    layout_differences = [
        (kind, layout[a:b], actual[c:d])
        for kind, a, b, c, d in difflib.SequenceMatcher(
            None, layout, actual, autojunk=False
        ).get_opcodes() if kind != 'equal'
    ]
    inserted_markers = Counter(
        marker for kind, old, value in layout_differences if kind == 'insert'
        for marker in re.findall(r'\d+\.', value)
    )
    expected_markers = Counter(
        marker for group in record['ordered_list_markers']
        for marker in re.findall(r'\d+\.', group)
    )
    list_markers_only = (
        all(kind == 'insert' for kind, _, _ in layout_differences)
        and all(re.fullmatch(r'(?:\d+\.)+', value) for kind, _, value in layout_differences)
        and inserted_markers == expected_markers
    )
    differences = [
        {'kind': kind, 'source': expected[a:b][:120], 'pdf': actual[c:d][:120]}
        for kind, a, b, c, d in difflib.SequenceMatcher(
            None, expected, actual, autojunk=False
        ).get_opcodes() if kind not in ('equal', 'insert')
    ]
    result = {
        'source': record['source'], 'pdf': record['pdf'], 'pages': len(document),
        'source_hash_matches': hashlib.sha256(source.read_bytes()).hexdigest() == record['source_sha256'],
        'pdf_hash_matches': hashlib.sha256(pdf.read_bytes()).hexdigest() == record['pdf_sha256'],
        'layout_text_matches': actual == layout or list_markers_only,
        'generated_list_markers_accounted_for': list(inserted_markers.elements()),
        'source_omissions_or_replacements': differences,
        'empty_body_pages': [i + 1 for i, text in enumerate(page_text) if not text.strip()],
        'expected_chars': len(expected), 'pdf_chars': len(actual),
    }
    result['passed'] = (result['source_hash_matches'] and result['pdf_hash_matches']
                        and result['layout_text_matches'] and not differences
                        and not result['empty_body_pages'])
    return result


if __name__ == '__main__':
    records = json.loads((HERE / 'pdf_build_manifest.json').read_text(encoding='utf-8'))
    results = [verify_record(record) for record in records]
    (HERE / 'pdf_sync_verification.json').write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))
    raise SystemExit(0 if all(row['passed'] for row in results) else 1)
