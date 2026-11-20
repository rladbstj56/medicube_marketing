"""수동 코딩을 원문과 결합하고 출처별 기술 통계를 재생성한다."""

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'data/reviews'


def load_reviews():
    """입력 없음. 저장된 두 CSV를 읽어 (출처, 식별키)별 원문 행을 반환한다.

    공식몰 리뷰 ID와 글로우픽 내부 식별키를 구분해 출처 간 오결합을 방지한다.
    """
    records = {}
    for source in ('medicube_mall', 'glowpick'):
        with (OUTPUT / f'{source}_glow_reviews_2026-11-20.csv').open(
            encoding='utf-8-sig', newline=''
        ) as stream:
            for row in csv.DictReader(stream):
                key = row['review_id'] if source == 'medicube_mall' else row['record_key']
                assert (source, key) not in records, f'중복 키: {source}/{key}'
                records[source, key] = row
    return records


def build_outputs(records, annotations):
    """원문 사전과 수동 판정 목록을 받아 코딩 CSV·출처별 집계 JSON을 저장한다.

    반환값은 집계 사전이다. 원문과 판정의 키·근거를 전수 대조한 후에만 저장한다.
    키워드 분류는 수행하지 않으며, 복수 코드는 리뷰당 코드별 한 번씩 센다.
    제품 제공 명시 5건 제외 및 대표 상품번호 한정 집계를 별도로 생성한다.
    """
    coded = []
    seen = set()
    for item in annotations:
        key = item['source'], item['record_key']
        assert key not in seen, f'판정 중복: {key}'
        seen.add(key)
        row = records[key]
        title = row.get('review_title', '')
        evidence = (title + '\n' if title else '') + row['review_comment']
        assert item['evidence'] == evidence, f'원문 변경: {key}'
        assert len(item['codes']) == len(set(item['codes'])), f'코드 중복: {key}'
        coded.append({
            'source': key[0], 'record_key': key[1],
            'source_review_id': row['review_id'],
            'product_id': row.get('product_id', '190848'),
            'date_displayed': row.get('create_date', row.get('date_displayed', '')),
            'displayed_age': row.get('displayed_age', ''),
            'provision_disclosure': row.get('provision_disclosure', '미확인'),
            'review_status': item['review_status'],
            'codes': ' | '.join(item['codes']), 'evidence': evidence,
            'review_notes': ' | '.join(item.get('review_notes', [])),
            'source_url': row['source_url'], 'collected_at': row['collected_at'],
        })
    assert seen == set(records), '판정 누락 또는 원문에 없는 판정'
    groups = {
        'mall_all': [x for x in coded if x['source'] == 'medicube_mall'],
        'mall_without_disclosed_provision': [
            x for x in coded if x['source'] == 'medicube_mall'
            and x['provision_disclosure'] != '제품 제공 명시'
        ],
        'mall_product_2795': [
            x for x in coded if x['source'] == 'medicube_mall' and x['product_id'] == '2795'
        ],
        'glowpick_all': [x for x in coded if x['source'] == 'glowpick'],
    }
    summary = {}
    for name, rows in groups.items():
        counts = Counter(code for row in rows for code in row['codes'].split(' | ') if code)
        summary[name] = {
            'denominator': len(rows), 'code_counts': dict(sorted(counts.items())),
            'review_status': dict(Counter(x['review_status'] for x in rows)),
        }
    with (OUTPUT / 'glow_reviews_coded_2026-11-20.csv').open(
        'w', encoding='utf-8-sig', newline=''
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=list(coded[0]))
        writer.writeheader()
        writer.writerows(coded)
    (ROOT / 'analysis/task2/glow_review_summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    return summary


if __name__ == '__main__':
    decisions = json.loads(
        (ROOT / 'analysis/task2/glow_review_annotations.json').read_text(encoding='utf-8')
    )
    result = build_outputs(load_reviews(), decisions['annotations'])
    print(json.dumps(result, ensure_ascii=False, indent=2))
