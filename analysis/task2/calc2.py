# -*- coding: utf-8 -*-
"""Task 2 — 타깃·가설 검증용 재계산. 12개 원자료에서 직접 읽어 num2.json에 저장한다.
기존 work/domestic/ 코드와 공유하지 않는 별도 파서(독립 재계산용)."""
import json, os, csv, statistics as st
import openpyxl

BASE = 'downloads/naver-datalab-v2'
FILES = {
    'brand_all':  f'{BASE}/datalab_브랜드검색어_전체.xlsx',
    'brand_2030': f'{BASE}/datalab_브랜드검색어_2030.xlsx',
    'brand_5060': f'{BASE}/datalab_브랜드검색어_5060.xlsx',
    'line_all':   'downloads/datalab_메디큐브 주력 라인 비교.xlsx',
    'line_2030':  'downloads/datalab_메디큐브 주력 라인 비교_여성2030.xlsx',
    'line_5060':  f'{BASE}/datalab_메디큐브 주력 라인 비교_여성5060.xlsx',
    'dev_all':    f'{BASE}/datalab_디바이스실측세트_전체.xlsx',
    'dev_2030':   f'{BASE}/datalab_디바이스실측세트_2030.xlsx',
    'dev_5060':   f'{BASE}/datalab_디바이스실측세트_5060.xlsx',
}
CSVS = {
    'shop_all':  f'{BASE}/쇼핑인사이트_전체.csv',
    'shop_2030': f'{BASE}/쇼핑인사이트_2030.csv',
    'shop_5060': f'{BASE}/쇼핑인사이트_5060.csv',
}


def read_xlsx(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    hi = None
    for i, r in enumerate(rows):
        if r and r[0] == '날짜':
            hi = i; break
    hdr = rows[hi]
    keys, cols = [], {}
    for j in range(0, len(hdr), 2):
        key = hdr[j + 1]
        keys.append(key)
        cols[key] = j
    dates, series = [], {k: [] for k in keys}
    for r in rows[hi + 1:]:
        if not r or not r[0]:
            continue
        dates.append(str(r[0])[:10])
        for k in keys:
            v = r[cols[k] + 1]
            series[k].append(float(str(v).replace(',', '')))
    return {'dates': dates, 'keys': keys, 'series': series}


def read_shop(path):
    rows = list(csv.reader(open(path, encoding='utf-8-sig')))
    hi = None
    for i, r in enumerate(rows):
        if r and r[0] == '날짜':
            hi = i; break
    hdr = rows[hi]
    keys = [h for h in hdr[1:] if h]
    dates, series = [], {k: [] for k in keys}
    for r in rows[hi + 1:]:
        if not r or not r[0]:
            continue
        d = r[0].strip()
        if not d[:4].isdigit():
            continue
        vals = [float(x.replace(',', '') or 0) for x in r[1:1 + len(keys)]]
        if sum(vals) == 0 and d <= '2025-11-02':      # 7일 미만 부분주
            continue
        dates.append(d)
        for k, v in zip(keys, vals):
            series[k].append(v)
    return {'dates': dates, 'keys': keys, 'series': series}


D = {k: read_xlsx(v) for k, v in FILES.items()}
D.update({k: read_shop(v) for k, v in CSVS.items()})


def share(rec, key):
    i = rec['keys'].index(key)
    out = []
    for t in range(len(rec['dates'])):
        s = sum(rec['series'][k][t] for k in rec['keys'])
        out.append(rec['series'][key][t] / s * 100 if s else 0.0)
    return out


def avg(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def window_mean(vals, n=13, first=False):
    return avg(vals[:n] if first else vals[-n:])


def wow(vals, i):
    return (vals[i] / vals[i - 1] - 1) * 100 if i > 0 and vals[i - 1] else None


def idx_of(rec, date):
    return rec['dates'].index(date)


N = {}
BR = ['메디큐브', '에스트라', '메디힐', '토리든', '넘버즈인']
DEV = ['메디큐브 에이지알', '마미케어', '톰더글로우', '쿼드쎄라', 'LG 프라엘']
LINE = ['부스터 프로', '부스터 프로 미니', 'PDRN 앰플', '제로모공패드', '부스터 글로우']

N['meta'] = {
    'brand_weeks': len(D['brand_all']['dates']),
    'shop_weeks': len(D['shop_all']['dates']),
    'brand_range': [D['brand_all']['dates'][0], D['brand_all']['dates'][-1]],
    'shop_range': [D['shop_all']['dates'][0], D['shop_all']['dates'][-1]],
    'keys': {k: D[k]['keys'] for k in D},
}

# ── A. 브랜드 검색·클릭 비중 (최근 13주 / 첫 13주)
N['share'] = {}
for seg in ['all', '2030', '5060']:
    rec = D['brand_' + seg]
    N['share']['brand_' + seg] = {
        k: {'recent': round(window_mean(share(rec, k)), 1),
            'first': round(window_mean(share(rec, k), first=True), 1),
            'last4': round(avg(share(rec, k)[-4:]), 1)}
        for k in BR}
    sh = D['shop_' + seg]
    N['share']['shop_' + seg] = {
        k: {'recent': round(window_mean(share(sh, k)), 1),
            'first': round(window_mean(share(sh, k), first=True), 1),
            'last4': round(avg(share(sh, k)[-4:]), 1)}
        for k in BR}
for seg in ['all', '2030', '5060']:
    for k in BR:
        b = N['share']['brand_' + seg][k]; s = N['share']['shop_' + seg][k]
        b['delta'] = round(b['recent'] - b['first'], 1)
        s['delta'] = round(s['recent'] - s['first'], 1)
        b['gap'] = round(b['recent'] - s['recent'], 1)

# 연령대별 '메디큐브 몫' 배수
N['mini_ratio'] = {
    'click_5060_over_2030': round(N['share']['shop_5060']['메디큐브']['recent'] /
                                 N['share']['shop_2030']['메디큐브']['recent'], 2),
}

# ── B. 주력 라인 (부스터 프로 미니 검증)
N['line'] = {}
for seg in ['all', '2030', '5060']:
    rec = D['line_' + seg]
    for k in LINE:
        sh = share(rec, k)
        v = rec['series'][k]
        N['line'].setdefault(k, {})[seg] = {
            'share_recent': round(window_mean(sh), 1),
            'share_first': round(window_mean(sh, first=True), 1),
            'share_last4': round(avg(sh[-4:]), 1),
            'idx_last': v[-1],
            'idx_first': v[0],
            'idx_peak': max(v), 'idx_peak_date': rec['dates'][v.index(max(v))],
            'idx_min': min(v), 'idx_min_date': rec['dates'][v.index(min(v))],
            'growth_13w': round((window_mean(v) / window_mean(v, first=True) - 1) * 100, 1)
            if window_mean(v, first=True) else None,
            'wow_last': round(wow(v, len(v) - 1), 1) if wow(v, len(v) - 1) is not None else None,
            'chg_4w': round((avg(v[-4:]) / avg(v[-8:-4]) - 1) * 100, 1),
        }
        if k == '부스터 프로 미니':
            sh0 = N['line'][k][seg]
            sh0['share_delta'] = round(sh0['share_recent'] - sh0['share_first'], 1)
            sh0['idx_change_pct'] = round((v[-1] / v[0] - 1) * 100, 1)
# 미니 vs 프로 (같은 파일 안 비중 비율)
for seg in ['all', '2030', '5060']:
    rec = D['line_' + seg]
    m = window_mean(share(rec, '부스터 프로 미니')); p = window_mean(share(rec, '부스터 프로'))
    N['line'].setdefault('_ratio', {})[seg] = {'mini_over_pro': round(m / p, 3)}

# ── C. 디바이스
N['dev'] = {}
for seg in ['all', '2030', '5060']:
    rec = D['dev_' + seg]
    for k in DEV:
        sh = share(rec, k); v = rec['series'][k]
        N['dev'].setdefault(k, {})[seg] = {
            'share_recent': round(window_mean(sh), 1),
            'share_first': round(window_mean(sh, first=True), 1),
            'delta': round(window_mean(sh) - window_mean(sh, first=True), 1),
            'idx_peak': max(v), 'idx_peak_date': rec['dates'][v.index(max(v))],
            'idx_last': v[-1],
            'growth_13w': round((window_mean(v) / window_mean(v, first=True) - 1) * 100, 1),
        }

# ── D. 5060 계절·이벤트 주 (설·가정의 달·연말·블프)
EVENTS = {
    '2025-12-29': '연말(톰더글로우 PRO 런칭 12/28)',
    '2026-02-16': '설날 주(설 2/17)',
    '2026-03-02': '3월 올영세일(3/1~3/7)',
    '2026-05-04': '가정의 달·어버이날(5/8)',
    '2026-06-29': '넾다세일(6/22~7/5)',
    '2026-08-03': '11주년 대감사제(8/3~8/24)',
    '2026-11-02': '올영 블랙프라이데이(11/1~11/7)',
}
N['events'] = {}
for date, label in EVENTS.items():
    row = {'label': label}
    for seg in ['all', '2030', '5060']:
        for axis, key in [('brand', 'brand_' + seg), ('dev', 'dev_' + seg)]:
            rec = D[key]
            if date not in rec['dates']:
                continue
            i = idx_of(rec, date)
            col = '메디큐브' if axis == 'brand' else '메디큐브 에이지알'
            row[f'{axis}_{seg}_wow'] = round(wow(rec['series'][col], i), 1) if wow(rec['series'][col], i) is not None else None
            row[f'{axis}_{seg}_idx'] = rec['series'][col][i]
            row[f'{axis}_{seg}_share'] = round(share(rec, col)[i], 1)
    rec = D['line_5060']
    if date in rec['dates']:
        i = idx_of(rec, date)
        for k in ['부스터 프로', 'PDRN 앰플', '제로모공패드']:
            row[f'line5060_{k}_wow'] = round(wow(rec['series'][k], i), 1) if wow(rec['series'][k], i) is not None else None
            row[f'line5060_{k}_idx'] = rec['series'][k][i]
    N['events'][date] = row

# ── E. 5060 디바이스 — 이벤트 주 4주 평균 vs 그 외
dev5060 = D['dev_5060']
base = share(dev5060, '메디큐브 에이지알')
gift_weeks = [d for d in ['2025-12-29', '2026-02-16', '2026-05-04'] if d in dev5060['dates']]
gi = [idx_of(dev5060, d) for d in gift_weeks]
other = [i for i in range(len(base)) if i not in gi]
N['dev_gift'] = {
    'gift_weeks': gift_weeks,
    'gift_mean_share': round(avg(base[i] for i in gi), 1),
    'other_mean_share': round(avg(base[i] for i in other), 1),
    'brand5060_gift_wow': {d: round(wow(D['brand_5060']['series']['메디큐브'], idx_of(D['brand_5060'], d)), 1) for d in gift_weeks},
}

# ── F. 가격·일일비용 (검증된 가격에서 산출)
PRICE = 99000
N['price'] = {'mini': PRICE, 'per_day_1y': round(PRICE / 365), 'per_day_2y': round(PRICE / 730)}

# ── G. 미니 54주 전체 시계열(차트용, 다운샘플 없이 그대로)
N['series'] = {
    'dates_brand': D['brand_all']['dates'],
    'brand_share_5060': [round(x, 2) for x in share(D['brand_5060'], '메디큐브')],
    'brand_share_2030': [round(x, 2) for x in share(D['brand_2030'], '메디큐브')],
    'click_share_5060': [round(x, 2) for x in share(D['shop_5060'], '메디큐브')],
    'click_share_2030': [round(x, 2) for x in share(D['shop_2030'], '메디큐브')],
    'dates_shop': D['shop_all']['dates'],
    'mini_idx': D['line_all']['series']['부스터 프로 미니'],
    'mini_idx_2030': D['line_2030']['series']['부스터 프로 미니'],
    'mini_idx_5060': D['line_5060']['series']['부스터 프로 미니'],
    'mini_share': [round(x, 2) for x in share(D['line_all'], '부스터 프로 미니')],
    'line_dates': D['line_all']['dates'],
    'dev5060_dates': D['dev_5060']['dates'],
    'dev5060_ageal': [round(x, 2) for x in share(D['dev_5060'], '메디큐브 에이지알')],
    'dev5060_prael': [round(x, 2) for x in share(D['dev_5060'], 'LG 프라엘')],
    'dev5060_mommy': [round(x, 2) for x in share(D['dev_5060'], '마미케어')],
}

os.makedirs('work/task2', exist_ok=True)
json.dump(N, open('work/task2/num2.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: N[k] for k in ['meta', 'mini_ratio']}, ensure_ascii=False)[:800])
print('--- share brand all:', json.dumps(N['share']['brand_all'], ensure_ascii=False))
print('--- share shop 2030:', json.dumps(N['share']['shop_2030'], ensure_ascii=False))
print('--- mini:', json.dumps(N['line']['부스터 프로 미니'], ensure_ascii=False))
print('--- ratio:', json.dumps(N['line']['_ratio'], ensure_ascii=False))
print('--- price:', N['price'])
print('--- dev_gift:', json.dumps(N['dev_gift'], ensure_ascii=False))
for d, r in N['events'].items():
    print(d, json.dumps(r, ensure_ascii=False))
