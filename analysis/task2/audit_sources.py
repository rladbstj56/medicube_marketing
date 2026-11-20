"""Task 2 공개 원자료의 분모·영값·리뷰 태그를 독립 재계산한다."""

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLICK = ROOT / "data/naver-datalab-v2/쇼핑인사이트_5060_이미용가전.csv"
MALL = ROOT / "data/reviews/medicube_mall_mini_reviews_2026-11-20.csv"
GLOW = ROOT / "data/reviews/glowpick_mini_reviews_2026-11-20.csv"
OUT = ROOT / "analysis/task2/source_audit.json"


def load_click(path):
    """쇼핑 CSV를 읽어 머리글, 52개 완전주, 제외된 부분주를 반환한다."""
    with path.open(encoding="utf-8-sig", newline="") as f:
        lines = list(csv.reader(f))
    header_idx = next(i for i, row in enumerate(lines) if row and row[0] == "날짜")
    keywords = lines[header_idx][1:]
    weeks = []
    excluded = []
    for row in lines[header_idx + 1 :]:
        if len(row) != len(keywords) + 1 or not row[0].startswith("20"):
            continue
        values = {key: float(value.replace(",", "")) for key, value in zip(keywords, row[1:])}
        if row[0] < "2025-11-03" and sum(values.values()) == 0:
            excluded.append(row[0])
            continue
        weeks.append({"date": row[0], **values})
    return {"category": lines[2][0], "filters": lines[4:7], "keywords": keywords, "weeks": weeks, "excluded_partial_week": excluded}


def audit_click(record):
    """주별 비중의 최근 13주 평균과 영값·비교군 민감도를 반환한다."""
    weeks = record["weeks"]
    keys = record["keywords"]
    last = weeks[-13:]
    weekly_share = [row["메디큐브"] / sum(row[key] for key in keys) * 100 for row in last]
    two_share = [row["메디큐브"] / (row["메디큐브"] + row["듀얼소닉"]) * 100 for row in last]
    return {
        "category": record["category"],
        "filters": record["filters"],
        "keywords": keys,
        "excluded_partial_week": record["excluded_partial_week"],
        "complete_weeks": len(weeks),
        "date_range": [weeks[0]["date"], weeks[-1]["date"]],
        "zero_weeks": {key: sum(row[key] == 0 for row in weeks) for key in keys},
        "positive_weeks": {key: sum(row[key] > 0 for row in weeks) for key in keys},
        "max_index": {key: max(row[key] for row in weeks) for key in keys},
        "recent13": {
            "date_range": [last[0]["date"], last[-1]["date"]],
            "mean_weekly_share_all5_pct": round(sum(weekly_share) / len(weekly_share), 3),
            "ratio_of_index_sums_all5_pct": round(sum(row["메디큐브"] for row in last) / sum(sum(row[key] for key in keys) for row in last) * 100, 3),
            "mean_weekly_share_top2_pct": round(sum(two_share) / len(two_share), 3),
        },
    }


def audit_reviews(mall_path, glow_path):
    """리뷰 행 기준 태그·기간과 작성자 중복을 계산해 반환한다."""
    with mall_path.open(encoding="utf-8-sig", newline="") as f:
        mall = list(csv.DictReader(f))
    with glow_path.open(encoding="utf-8-sig", newline="") as f:
        glow = list(csv.DictReader(f))
    tags = Counter(tag.strip() for row in mall for tag in row["coded_axes"].split("|") if tag.strip())
    twenties_thirties = [row for row in glow if 20 <= int(row["age"]) < 40]
    authors = {row["author"] for row in glow}
    age_authors = {row["author"] for row in twenties_thirties}
    return {
        "mall": {
            "rows": len(mall),
            "unique_ids": len({row["id"] for row in mall}),
            "date_range": [min(row["create_date"][:10] for row in mall), max(row["create_date"][:10] for row in mall)],
            "tag_counts": dict(tags),
            "tag_count_denominator": "수집된 리뷰 200행; 태그 문맥 검증 전",
        },
        "glowpick": {
            "rows": len(glow),
            "age_20_39_review_rows": len(twenties_thirties),
            "age_20_39_review_row_share_pct": round(len(twenties_thirties) / len(glow) * 100, 1),
            "unique_authors_by_name": len(authors),
            "age_20_39_unique_authors_by_name": len(age_authors),
            "age_20_39_unique_author_share_pct": round(len(age_authors) / len(authors) * 100, 1),
            "review_level_theme_columns_present": any("code" in key or "axis" in key for key in glow[0]),
        },
    }


result = {"click": audit_click(load_click(CLICK)), "reviews": audit_reviews(MALL, GLOW)}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(OUT.relative_to(ROOT))
