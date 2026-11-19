# 구글 트렌드 F세트 — 메디큐브 지역별 관심도·12개월 시계열

2026-11-20 01:12(KST)에 Google Trends에서 **직접 내려받은 원자료**입니다. 가공하지 않고 그대로 두었습니다.

## 조회 조건

| 항목 | 값 |
|---|---|
| 검색어 | `medicube` (**검색어**, 주제 아님) |
| 카테고리 | `미용 & 건강` (`cat=44`, Beauty & Fitness) |
| 지역 | 전 세계 |
| 기간 | 지난 12개월 (2025-11-16 ~ 2026-11-15, 주간 53구간) |
| 검색 유형 | 웹 검색 |
| 기타 | 검색량이 적은 지역 포함(추정 — 캄보디아·세인트헬레나 등 저검색량 지역이 포함됨) |

- CSV에는 조회 조건 메타데이터가 없습니다. 위 조건은 내려받은 화면(2026-11-20 01:10 캡처)과 대화 기록으로 확인한 값입니다.

## 파일

| 파일 | 원래 구글 파일명 | 카드 | 행 | 크기 | sha256 |
|---|---|---|---|---|---|
| `trends_geomap_medicube.csv` | `지역별관심도_메디큐브.csv` | `geoMap.csv` (지역별 관심도) | 75개 지역 | 1,285 B | `500e5f96df1c66d6b6ceb4a5e7d4451a1914b8dbdef905d22bf4388fd18bf918` |
| `trends_multitimeline_medicube.csv` | `multitimeline_메디큐브.csv` | `multiTimeline.csv` (시간 흐름) | 53주 | 866 B | `4e851a2f7da0e9ad293b7ee8a305f9e132229bbbac3d0b0c2e9116827f700848` |

- 열 구성: 두 파일 모두 `Region`/`Time` + `medicube` 두 열뿐입니다. `isPartial` 열이 없어 마지막 주의 집계 완결 여부는 파일만으로 알 수 없습니다.

## 값의 성격

- **지역별 값은 그 나라 전체 구글 검색 중 `medicube`가 차지한 비율**이고, 가장 높은 지역이 100입니다. 절대 검색량이 아닙니다.
- 그래서 작은 시장이 위로 올라옵니다 — 캄보디아 100 · 아랍에미리트 65 · 파라과이 60 · 리투아니아 56 · **영국 54** · 슬로바키아 54 …
- **유럽 주요국 순위**: 영국 54 > 네덜란드 35 > 스페인 25 = 폴란드 25 > 벨기에 24 > 스위스 23 > 이탈리아 18 > 프랑스 16 > 독일 14
- **시계열**은 전 세계 기준입니다(지역 고정 아님). 최저 31(2025-11-16) → 최고 100(2026-11-15), 평균 57.6, 앞 13주 평균 38.9 → 뒤 13주 평균 79.9(**+105.3%**).

## 재현

```bash
python3 - <<'EOF'
import csv, statistics
rows = list(csv.DictReader(open('trends_geomap_medicube.csv', encoding='utf-8-sig')))
d = {r['Region']: int(r['medicube']) for r in rows}
print(len(d), d['영국'], d['독일'], round(d['영국']/d['독일'], 2))

tl = [(r['Time'], int(r['medicube'])) for r in csv.DictReader(open('trends_multitimeline_medicube.csv', encoding='utf-8-sig'))]
v = [x for _, x in tl]
print(len(v), v[0], v[-1], round(statistics.mean(v), 1),
      round(statistics.mean(v[:13]), 1), round(statistics.mean(v[-13:]), 1))
EOF
```

- 계산·해석·한계는 `research/메디큐브_글로벌_리서치_사전근거_및_트렌드설계.md`의 **00-C → C-4**에 있습니다.
- 이 조회는 `medicube` 단독이라 **경쟁사 대비 성과는 알 수 없습니다.** 경쟁사 비교는 국가를 고정한 A(미국)·C(영국) 세트로 채웁니다(같은 문서 C-6).
