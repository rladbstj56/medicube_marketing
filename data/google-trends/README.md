# 구글 트렌드 CSV 13종 — 메디큐브 3개국 비교(A·B·C·J) + 전 세계(F)

2026-11-20 01:12·02:0x(KST)에 Google Trends에서 **직접 내려받은 원자료**입니다. 가공하지 않고 그대로 두었습니다.

## 공통 조회 조건

| 항목 | 값 |
|---|---|
| 카테고리 | `미용 & 건강` (`cat=44`, Beauty & Fitness) |
| 기간 | 지난 12개월 (2025-11-16 ~ 2026-11-15, 주간 53구간) |
| 검색 유형 | 웹 검색 |
| 검색어 수 | 한 요청에 5개 이하(0~100 눈금 공유) |
| 언어 | UI 한국어, 검색어는 **현지 표기**(일본은 メディキューブ 등) |

- CSV에는 조회 조건 메타데이터가 한 줄(`카테고리: 미용 & 건강`)만 있습니다. 지역·기간·검색유형은 **열 이름**(`medicube: (미국)`, `メディキューブ: (일본)`)과 설계 문서(`research/메디큐브_글로벌_리서치_사전근거_및_트렌드설계.md` 3.3·C-6)로 확인했습니다.

## 파일 목록 (13종)

| 파일 | 세트 | 지역 | 카드 | 검색어 | 행 | sha256(앞 16) |
|---|---|---|---|---|---|---|
| `geoMap_A세트.csv` | A 미국 브랜드 | US | 지역별 | medicube·BIODANCE·Anua·Dr.Althea·COSRX | 51개 주 | `a61450543075a955…` |
| `multiTimeline_A세트.csv` | A 미국 브랜드 | US | 시계열 | 같음 | 53주 | `f2fc4ed26807e3d6…` |
| `relatedQueries_A세트.csv` | A 미국 브랜드 | US | 관련 검색어 | medicube | TOP 25·RISING 25 | `272acfb660f514af…` |
| `multiTimeline_B세트.csv` | B 미국 제품·성분 | US | 시계열 | medicube·toner pads·pdrn·collagen night wrapping mask·booster pro | 53주 | `a0d669380f9f9b3b…` |
| `relatedQueries_B세트.csv` | B 미국 제품·성분 | US | 관련 검색어 | medicube booster pro | TOP 25·RISING 18 | `05903004d5469cf4…` |
| `geoMap_C세트.csv` | C 영국 | GB | 지역별 | medicube·BIODANCE·COSRX·beauty of joseon·celimax | 4개 지역 | `d1deff3f456ddd14…` |
| `multiTimeline_C세트.csv` | C 영국 | GB | 시계열 | 같음 | 53주 | `74a088d5f6c7be75…` |
| `relatedQueries_C세트.csv` | C 영국 | GB | 관련 검색어 | medicube | TOP 25·RISING 25 | `4f49353220276768…` |
| `geoMap_J세트.csv` | J 일본 | JP | 지역별 | メディキューブ·ティルティル·Biodance·トリデン·アヌア | 47개 도도부현 | `50fe1165abf39149…` |
| `multiTimeline_J세트.csv` | J 일본 | JP | 시계열 | 같음 | 53주 | `de059a8085687937…` |
| `relatedQueries_J세트.csv` | J 일본 | JP | 관련 검색어 | メディキューブ | TOP 25·RISING 18 | `e093c8d04d9bc49d…` |
| `relatedQueries_J세트(1).csv` | J 일본 | JP | (같은 파일 두 번째 사본) | — | 같음 | `e093c8d04d9bc49d…` |
| `trends_geomap_medicube.csv` | F 전 세계 | WORLD | 지역별 | medicube 단독 | 75개 지역 | `500e5f96df1c66d6…` |
| `trends_multitimeline_medicube.csv` | F 전 세계 | WORLD | 시계열 | medicube 단독 | 53주 | `4e851a2f7da0e9ad…` |

- `relatedQueries_J세트.csv`와 `relatedQueries_J세트(1).csv`는 **바이트·해시가 동일**합니다(Google이 TOP·RISING을 한 파일에 담아 내려줌). 계산에는 한 번만 썼습니다.
- F세트 2종(전 세계)은 01:12 수령분으로, 파일명만 `trends_*`입니다(같은 원자료).

## 값의 성격

- **단일 검색어 `geoMap`(F)**: 그 나라 전체 구글 검색 중 `medicube`가 차지한 비율이고 최고 지역이 100입니다. 절대 검색량이 아니므로 소국이 위로 올라옵니다(캄보디아 100·리투아니아 56·**영국 54**·독일 14).
- **다중 검색어 `geoMap`(A·C·J)**: 그 지역의 **5개 검색어 합계 중 비중(%)** 입니다. 행 합계가 100.0~100.5%로 확인됩니다.
- **`multiTimeline`**: 요청 안의 최고점이 100인 상대 지수입니다. 세트 간 절대 비교는 불가능하고, 세트 안 배수·비중으로만 읽습니다.
- **`relatedQueries`**: TOP은 0~100 상대값, RISING은 증가율(%) 또는 `급등`(Breakout, 임계 이상 — % 아님).
- **`isPartial` 열이 없습니다**: 13개 파일 모두. 마지막 주(2026-11-15)의 집계 완결 여부는 파일만으로 알 수 없어, 성장률은 13주 평균 기준으로 계산했습니다.

## 재현

```bash
python3 - <<'EOF'
import csv, statistics as st
rows = list(csv.reader(open('multiTimeline_A세트.csv', encoding='utf-8-sig')))
hdr = rows[2]; data = [r for r in rows[3:] if r and r[0]]
mc = [float(r[1]) for r in data]; an = [float(r[3]) for r in data]
print(len(mc), round(st.mean(mc), 2), round(st.mean(mc[-13:]) / st.mean(mc[:13]) * 100 - 100, 1))
print('medicube/Anua 최근 4주', round(st.mean([mc[i] / an[i] for i in range(len(mc) - 4, len(mc))]), 2))
EOF
```

- 해석·한계·판정은 `reports/메디큐브_글로벌_트렌드_분석보고서.md`(29쪽)와 `research/메디큐브_글로벌_리서치_사전근거_및_트렌드설계.md`(C-4~C-8)에 있습니다.
