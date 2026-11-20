"""여성 19–39세 동일 요청의 제품명 검색 지수를 비교한다."""

import csv
import hashlib
import json
from pathlib import Path
from statistics import mean, median

import openpyxl

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'data/naver-datalab/datalab_메디큐브 주력 라인 비교_여성2030.xlsx'


def load_series(path):
    """XLSX 경로를 받아 메타데이터 사전과 날짜·제품별 지수 행 목록을 반환한다.

    같은 조회 요청의 값을 그대로 보존하며 다른 요청의 지수와 결합하지 않는다.
    """
    workbook = openpyxl.load_workbook(path, data_only=True)
    values = list(workbook.active.values)
    header_index = next(i for i, row in enumerate(values) if row[0] == '날짜')
    metadata = {row[0]: row[1] for row in values[:header_index] if row[0]}
    header = values[header_index]
    rows = []
    for row in values[header_index + 1:]:
        if row[0]:
            rows.append({'date': str(row[0])[:10], **{
                header[j + 1]: float(row[j + 1]) for j in range(0, len(header), 2)
            }})
    workbook.close()
    return metadata, rows


def summarize(rows):
    """동일 기간 행 목록을 받아 주 수·범위·글로우 대 미니 지수 비교를 반환한다.

    기간 합의 비율과 주별 비율 중앙값을 구분한다. 검색량·매출 비율은 계산하지 않는다.
    """
    glow = [row['부스터 글로우'] for row in rows]
    mini = [row['부스터 프로 미니'] for row in rows]
    assert all(value > 0 for value in mini)
    return {
        'weeks': len(rows), 'date_range': [rows[0]['date'], rows[-1]['date']],
        'glow_mean_index': mean(glow), 'mini_mean_index': mean(mini),
        'sum_index_ratio_glow_to_mini': sum(glow) / sum(mini),
        'median_weekly_ratio': median(g / m for g, m in zip(glow, mini)),
        'glow_above_mini_weeks': sum(g > m for g, m in zip(glow, mini)),
    }


if __name__ == '__main__':
    meta, rows = load_series(SOURCE)
    # 선출시 주의 부분 노출을 피하고 첫 완전주부터 양쪽을 같은 기간으로 비교한다.
    postlaunch = [row for row in rows if row['date'] >= '2026-05-04']
    top3 = sorted(postlaunch, key=lambda row: row['부스터 글로우'], reverse=True)[:3]
    excluded = {row['date'] for row in top3}
    last4, previous4 = rows[-4:], rows[-8:-4]
    result = {
        'source': str(SOURCE.relative_to(ROOT)),
        'sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'metadata': meta,
        'keyword_definition_verified_at': '2026-11-20',
        'keyword_groups_from_source_result_page': {
            '부스터 프로': ['부스터프로', '부스터프로', '부스터프로x2'],
            '부스터 프로 미니': ['부스터프로미니', '부스터프로미니', '부스터미니'],
            '부스터 글로우': ['부스터글로우', '메디큐브부스터글로우'],
        },
        'postlaunch': summarize(postlaunch),
        'after_first_four_weeks': summarize(postlaunch[4:]),
        'excluding_top3_glow_weeks': summarize([
            row for row in postlaunch if row['date'] not in excluded
        ]),
        'excluded_top3_dates': sorted(excluded),
        'recent13': summarize(rows[-13:]), 'recent4': summarize(last4),
        'latest_week': rows[-1],
        'change_last4_vs_previous4': {
            key: (mean(row[key] for row in last4) /
                  mean(row[key] for row in previous4) - 1) * 100
            for key in ('부스터 글로우', '부스터 프로 미니', '부스터 프로')
        },
        'change_window_dates': {
            'last4': [last4[0]['date'], last4[-1]['date']],
            'previous4': [previous4[0]['date'], previous4[-1]['date']],
        },
        'limitations': [
            '원본 결과 페이지에서 프로에 X2 포함 확인. 미니 플러스는 명시적으로 포함되지 않음. 부분 문자열 매칭 여부까지 확인한 것은 아님.',
            '첫 4주·상위 3주 제외는 탐색적 민감도 점검이며 행사 인과 분리가 아님.',
            '조회 연령은 여성 19–39세. 시장 전체·남성·매출 효과로 일반화하지 않음.',
        ],
    }
    (ROOT / 'analysis/task2/glow_search_comparison.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    with (ROOT / 'data/reviews/glow_search_weekly_2030.csv').open(
        'w', encoding='utf-8-sig', newline=''
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(result, ensure_ascii=False, indent=2))
