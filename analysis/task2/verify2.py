# -*- coding: utf-8 -*-
"""Task 2 검증.
① 원자료 독립 재계산 — openpyxl을 쓰지 않고 xlsx(zip+XML)·csv를 직접 읽어 본문 인용값을 다시 계산해 num2.json과 대조
② .md ↔ .pdf 숫자 토큰 다중집합 대조
③ 페이지 렌더 결과(빈 쪽·텍스트 길이) 점검용 요약
"""
import json, re, csv, sys, zipfile, statistics as st
from xml.etree import ElementTree as ET

BASE = 'data/naver-datalab-v2'
XLSX = {
    'brand_all': f'{BASE}/datalab_브랜드검색어_전체.xlsx',
    'brand_2030': f'{BASE}/datalab_브랜드검색어_2030.xlsx',
    'line_all': 'data/naver-datalab/datalab_메디큐브 주력 라인 비교.xlsx',
    'line_2030': 'data/naver-datalab/datalab_메디큐브 주력 라인 비교_여성2030.xlsx',
    'line_5060': f'{BASE}/datalab_메디큐브 주력 라인 비교_여성5060.xlsx',
    'dev_all': f'{BASE}/datalab_디바이스실측세트_전체.xlsx',
    'dev_2030': f'{BASE}/datalab_디바이스실측세트_2030.xlsx',
    'dev_5060': f'{BASE}/datalab_디바이스실측세트_5060.xlsx',
    'devc_5060': f'{BASE}/datalab_디바이스경쟁사_5060.xlsx',
}
SHOP = {
    'shop_all': f'{BASE}/쇼핑인사이트_전체.csv',
    'shop_2030': f'{BASE}/쇼핑인사이트_2030.csv',
    'imgapp_5060': f'{BASE}/쇼핑인사이트_5060_이미용가전.csv',
    'skin_5060': f'{BASE}/쇼핑인사이트_5060_스킨케어.csv',
}
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def xlsx_cells(path):
    """zip + XML 직독. 반환: {행번호: {열번호: 값}} (열 1=날짜, 2=값, 3=날짜 …)"""
    z = zipfile.ZipFile(path)
    shared = []
    if 'xl/sharedStrings.xml' in z.namelist():
        root = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in root.findall('m:si', NS):
            shared.append(''.join(t.text or '' for t in si.iter(
                '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')))
    sheet = [n for n in z.namelist() if n.startswith('xl/worksheets/sheet')][0]
    root = ET.fromstring(z.read(sheet))
    out = {}
    for row in root.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
        r = int(row.get('r'))
        cells = {}
        for c in row:
            ref = c.get('r')
            col = 0
            for ch in ref:
                if ch.isalpha():
                    col = col * 26 + (ord(ch.upper()) - 64)
                else:
                    break
            v = c.find('m:v', NS)
            if v is None:
                continue
            txt = v.text
            if c.get('t') == 's':
                txt = shared[int(txt)]
            cells[col] = txt
        out[r] = cells
    return out


def load_xlsx(path):
    rows = xlsx_cells(path)
    hdr_row = None
    for r, cells in rows.items():
        if cells.get(1) == '날짜':
            hdr_row = r; break
    dates, series, k = [], {}, 1
    while (hdr_row and rows[hdr_row].get(k + 1)):
        key = rows[hdr_row][k + 1]
        series[key] = []
        k += 2
    for r in sorted(rows):
        if r <= hdr_row:
            continue
        cells = rows[r]
        d = cells.get(1)
        if not d:
            continue
        dates.append(d[:10])
        k = 1
        for key in series:
            series[key].append(float(cells.get(k + 1, 0)))
            k += 2
    return {'dates': dates, 'keys': list(series), 'series': series}


def load_shop(path):
    rows = [r for r in csv.reader(open(path, encoding='utf-8-sig'))]
    hi = next(i for i, r in enumerate(rows) if r and r[0] == '날짜')
    keys = [x for x in rows[hi][1:] if x]
    dates, series = [], {k: [] for k in keys}
    for r in rows[hi + 1:]:
        if not r or not r[0][:4].isdigit():
            continue
        d = r[0].strip()
        vals = [float((x or '0').replace(',', '')) for x in r[1:1 + len(keys)]]
        if sum(vals) == 0 and d <= '2025-11-02':
            continue
        dates.append(d)
        for k, v in zip(keys, vals):
            series[k].append(v)
    return {'dates': dates, 'keys': keys, 'series': series}


D = {k: load_xlsx(v) for k, v in XLSX.items()}
D.update({k: load_shop(v) for k, v in SHOP.items()})


def shares(rec, key):
    i = rec['keys'].index(key)
    out = []
    for t in range(len(rec['dates'])):
        tot = sum(rec['series'][k][t] for k in rec['keys'])
        out.append(rec['series'][key][t] / tot * 100 if tot else 0.0)
    return out


def m(xs):
    xs = list(xs)
    return sum(xs) / len(xs)


def wow(rec, key, date):
    i = rec['dates'].index(date)
    prev = rec['series'][key][i - 1]
    return (rec['series'][key][i] / prev - 1) * 100 if prev else None


BR = ['메디큐브', '에스트라', '메디힐', '토리든', '넘버즈인']
DEV = ['메디큐브 에이지알', '마미케어', '톰더글로우', '쿼드쎄라', 'LG 프라엘']
LINE = ['부스터 프로', '부스터 프로 미니', 'PDRN 앰플', '제로모공패드', '부스터 글로우']

checks = []


def ck(label, got, want, tol=0.06):
    ok = got is not None and abs(got - want) <= tol
    checks.append([label, round(got, 2) if got is not None else None, want, ok])


N = json.load(open('analysis/task2/num2.json'))
EV = N['events']

# 브랜드 검색·클릭 비중 (최근 13주)
for seg in ('all', '2030'):
    for b in BR:
        ck(f'검색 {seg} {b}', m(shares(D['brand_' + seg], b)[-13:]), N['share']['brand_' + seg][b]['recent'])
        ck(f'클릭 {seg} {b}', m(shares(D['shop_' + seg], b)[-13:]), N['share']['shop_' + seg][b]['recent'])
# 라인·디바이스 비중
for seg in ('all', '2030', '5060'):
    for k in LINE:
        ck(f'라인 {seg} {k}', m(shares(D['line_' + seg], k)[-13:]), N['line'][k][seg]['share_recent'])
    for k in DEV:
        ck(f'디바이스 {seg} {k}', m(shares(D['dev_' + seg], k)[-13:]), N['dev'][k][seg]['share_recent'])
# 1년 전 비중(첫 13주) — 미니
for seg in ('all', '2030', '5060'):
    ck(f'미니 1년전 비중 {seg}', m(shares(D['line_' + seg], '부스터 프로 미니')[:13]),
       N['line']['부스터 프로 미니'][seg]['share_first'])
# 이벤트 주 WoW
WOW = [
    ('2026-05-04', 'brand_5060', '메디큐브', 'brand_5060_wow'),
    ('2026-05-04', 'brand_2030', '메디큐브', 'brand_2030_wow'),
    ('2026-05-04', 'brand_all', '메디큐브', 'brand_all_wow'),
    ('2026-05-04', 'dev_5060', '메디큐브 에이지알', 'dev_5060_wow'),
    ('2026-05-04', 'dev_2030', '메디큐브 에이지알', 'dev_2030_wow'),
    ('2026-05-04', 'line_5060', '부스터 프로', 'line5060_부스터 프로_wow'),
    ('2026-05-04', 'line_5060', '제로모공패드', 'line5060_제로모공패드_wow'),
    ('2026-02-16', 'brand_5060', '메디큐브', 'brand_5060_wow'),
    ('2026-02-16', 'line_5060', 'PDRN 앰플', 'line5060_PDRN 앰플_wow'),
    ('2026-02-16', 'dev_5060', '메디큐브 에이지알', 'dev_5060_wow'),
    ('2025-12-29', 'brand_5060', '메디큐브', 'brand_5060_wow'),
    ('2025-12-29', 'dev_5060', '메디큐브 에이지알', 'dev_5060_wow'),
    ('2026-11-02', 'brand_5060', '메디큐브', 'brand_5060_wow'),
    ('2026-11-02', 'brand_2030', '메디큐브', 'brand_2030_wow'),
    ('2026-11-02', 'dev_5060', '메디큐브 에이지알', 'dev_5060_wow'),
    ('2026-11-02', 'line_5060', 'PDRN 앰플', 'line5060_PDRN 앰플_wow'),
    ('2026-08-03', 'brand_5060', '메디큐브', 'brand_5060_wow'),
    ('2026-08-03', 'dev_5060', '메디큐브 에이지알', 'dev_5060_wow'),
    ('2026-08-03', 'line_5060', '제로모공패드', 'line5060_제로모공패드_wow'),
    ('2026-03-02', 'brand_5060', '메디큐브', 'brand_5060_wow'),
    ('2026-06-29', 'brand_5060', '메디큐브', 'brand_5060_wow'),
]
for date, rec, col, key in WOW:
    if rec == 'brand_5060':
        continue
    ck(f'{date} {rec} {col} WoW', wow(D[rec], col, date), EV[date][key])
# 클릭 WoW(표 4-3에 직접 적은 값)
ck('2026-03-02 shop_2030 클릭 WoW', wow(D['shop_2030'], '메디큐브', '2026-03-02'), 312.5)
# 이벤트 주 비중
for date, rec, col, key in [('2026-05-04', 'brand_5060', '메디큐브', 'brand_5060_share'),
                            ('2026-05-04', 'brand_2030', '메디큐브', 'brand_2030_share'),
                            ('2026-02-16', 'brand_5060', '메디큐브', 'brand_5060_share')]:
    if rec == 'brand_5060':
        continue
    i = D[rec]['dates'].index(date)
    ck(f'{date} {rec} 비중', shares(D[rec], col)[i], EV[date][key])
for date, want in [('2026-11-02', 24.3), ('2026-05-04', 21.2)]:
    dts = N['series']['dev5060_dates']
    ck(f'{date} dev_5060 에이지알 비중', shares(D['dev_5060'], '메디큐브 에이지알')[dts.index(date)],
       N['series']['dev5060_ageal'][dts.index(date)])
# 미니 지수·성장
for seg in ('all', '2030', '5060'):
    base = N['line']['부스터 프로 미니'][seg]
    v = D['line_' + seg]['series']['부스터 프로 미니']
    ck(f'미니 {seg} 첫값', v[0], base['idx_first'])
    ck(f'미니 {seg} 마지막값', v[-1], base['idx_last'])
    ck(f'미니 {seg} 13주 성장', (m(v[-13:]) / m(v[:13]) - 1) * 100, base['growth_13w'])
    ck(f'미니 {seg} 최근4주 대비', (m(v[-4:]) / m(v[-8:-4]) - 1) * 100, base['chg_4w'])
# 하루 비용
ck('하루 비용 1년', 99000 / 365, 271, tol=0.5)
ck('하루 비용 2년', 99000 / 730, 136, tol=0.5)

# ── v1.2: 5060 전용 3파일 독립 재계산
V = N['v12']
DEVC = ['메디큐브 에이지알', '듀얼소닉', '마데카 프라임', 'LG 프라엘', '마미케어']
for k in DEVC:
    b = V['dev5060'][k]
    ck(f'v12 기기검색 {k} 최근13주', m(shares(D['devc_5060'], k)[-13:]), b['recent'])
    ck(f'v12 기기검색 {k} 첫13주', m(shares(D['devc_5060'], k)[:13]), b['first'])
    ck(f'v12 기기검색 {k} 최고비중', max(shares(D['devc_5060'], k)), b['peak'])
    values = shares(D['devc_5060'], k)
    peak_date = D['devc_5060']['dates'][values.index(max(values))]
    checks.append([f'v12 기기검색 {k} 비중 최고주', peak_date, b['peak_date'], peak_date == b['peak_date']])
for k in ['메디큐브', '듀얼소닉', '센텔리안24', '프라엘', '마미케어']:
    ck(f'v12 이미용가전 {k} 최근13주', m(shares(D['imgapp_5060'], k)[-13:]), V['imgapp5060'][k]['recent'])
    ck(f'v12 이미용가전 {k} 첫13주', m(shares(D['imgapp_5060'], k)[:13]), V['imgapp5060'][k]['first'])
for k in ['메디큐브', '센텔리안24', 'AHC', '달바', '설화수']:
    ck(f'v12 스킨케어 {k} 최근13주', m(shares(D['skin_5060'], k)[-13:]), V['skin5060'][k]['recent'])
    ck(f'v12 스킨케어 {k} 첫13주', m(shares(D['skin_5060'], k)[:13]), V['skin5060'][k]['first'])
# 2자 구도
LIVE = [k for k in D['imgapp_5060']['keys'] if max(D['imgapp_5060']['series'][k]) >= 50]
s2 = shares(D['imgapp_5060'], '메디큐브')
tot2 = [sum(D['imgapp_5060']['series'][k][t] for k in LIVE) for t in range(len(D['imgapp_5060']['dates']))]
r2 = [D['imgapp_5060']['series']['메디큐브'][t] / tot2[t] * 100 for t in range(len(tot2))]
ck('v12 2자 구도 최근13주', m(r2[-13:]), V['imgapp2']['recent'])
ck('v12 2자 구도 첫13주', m(r2[:13]), V['imgapp2']['first'])
# 5개 키워드 합계
tot = [sum(D['devc_5060']['series'][k][t] for k in D['devc_5060']['keys']) for t in range(len(D['devc_5060']['dates']))]
ck('v12 기기검색 합계 첫주', tot[0], V['dev_sum']['first'])
ck('v12 기기검색 합계 마지막주', tot[-1], V['dev_sum']['last'])
# 5/4 이미용가전 클릭 WoW (원지수)
i = D['imgapp_5060']['dates'].index('2026-05-04')
ck('v12 5/4 이미용가전 클릭 WoW', (D['imgapp_5060']['series']['메디큐브'][i] / D['imgapp_5060']['series']['메디큐브'][i-1] - 1) * 100, 78.9)
# 이벤트: 새 파일 기기 검색 WoW
for d, want in [('2026-05-04', -2.5), ('2026-08-03', 47.6), ('2026-09-07', 34.2), ('2026-11-02', 46.6)]:
    ck(f'v12 {d} 기기검색 WoW', wow(D['devc_5060'], '메디큐브 에이지알', d), want)
# 설화수 원지수 최고
ck('v12 설화수 원지수 최고', max(D['skin_5060']['series']['설화수']), V['sulwhasoo_peak']['raw_max'])
# 비교군 교체 값(기존 파일)
for k in ['메디큐브 에이지알', '마미케어', '톰더글로우', '쿼드쎄라', 'LG 프라엘']:
    ck(f'v12 비교군(기존) {k}', m(shares(D['dev_5060'], k)[-13:]), V['setcmp']['old'][k]['recent'])
# 값 개수
ck('현행 13파일 값 개수', sum(len(values) for rec in D.values() for values in rec['series'].values()), 3470, tol=0)

fail = [c for c in checks if not c[3]]
res = {'recompute_total': len(checks), 'recompute_fail': len(fail), 'fails': fail[:20],
       'excluded_archive': ['datalab_브랜드검색어_5060.xlsx', '쇼핑인사이트_5060.csv'],
       'scope': '현행 13파일 수치 대조. 디바이스 구 비교군은 비교군 변경 검증용으로만 포함. 전략·효과 검증 아님.'}

if '--numeric-only' in sys.argv:
    json.dump(res, open('analysis/task2/verify2_numeric.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    sys.exit(1 if fail else 0)

# 현행 MD→PDF 빌드 기록으로 본문을 대조한다.
from verify_pdf_sync import verify_record

records = json.load(open('analysis/task2/pdf_build_manifest.json', encoding='utf-8'))
res['pdf_sync'] = [verify_record(record) for record in records]
json.dump(res, open('analysis/task2/verify2.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
sys.exit(1 if fail or not all(row['passed'] for row in res['pdf_sync']) else 0)
