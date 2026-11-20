# -*- coding: utf-8 -*-
"""v1.2 확장 계산 — 5060 전용 3파일을 읽어 num2.json 에 덧붙인다.

추가 원자료(사용자 2026-11-20 15:14 #pickle 업로드)
  ① datalab_디바이스경쟁사_5060.xlsx   데이터랩 통검 · 여성 50~60+ · 54주 · 5개 기기 브랜드
  ② 쇼핑인사이트_5060_이미용가전.csv   쇼핑인사이트 디지털/가전>이미용가전 · 여성 50대·60대이상 · 52주
  ③ 쇼핑인사이트_5060_스킨케어.csv     쇼핑인사이트 화장품/미용>스킨케어 · 여성 50대·60대이상 · 52주

기존 키는 건드리지 않고 N['v12'] 아래에만 쓴다(2030·브랜드·라인 계산은 v1.1과 동일해야 함).
"""
import json, csv, statistics as st
import openpyxl

BASE = 'downloads/naver-datalab-v2'
F_NEW_DEV = f'{BASE}/datalab_디바이스경쟁사_5060.xlsx'
F_NEW_SDEV = f'{BASE}/쇼핑인사이트_5060_이미용가전.csv'
F_NEW_SSKIN = f'{BASE}/쇼핑인사이트_5060_스킨케어.csv'
F_OLD_DEV = f'{BASE}/datalab_디바이스실측세트_5060.xlsx'


def read_xlsx(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    hi = next(i for i, r in enumerate(rows) if r and r[0] == '날짜')
    hdr = rows[hi]
    keys, cols = [], {}
    for j in range(0, len(hdr), 2):
        keys.append(hdr[j + 1]); cols[hdr[j + 1]] = j
    dates, series = [], {k: [] for k in keys}
    for r in rows[hi + 1:]:
        if not r or not r[0]:
            continue
        dates.append(str(r[0])[:10])
        for k in keys:
            series[k].append(float(str(r[cols[k] + 1]).replace(',', '')))
    return {'dates': dates, 'keys': keys, 'series': series}


def read_shop(path):
    rows = list(csv.reader(open(path, encoding='utf-8-sig')))
    hi = next(i for i, r in enumerate(rows) if r and r[0] == '날짜')
    keys = [h for h in rows[hi][1:] if h]
    dates, series = [], {k: [] for k in keys}
    for r in rows[hi + 1:]:
        if not r or not r[0]:
            continue
        d = r[0].strip()
        if not d[:4].isdigit():
            continue
        vals = [float(x.replace(',', '') or 0) for x in r[1:1 + len(keys)]]
        if sum(vals) == 0 and d <= '2025-11-02':     # 7일 미만 부분주
            continue
        dates.append(d)
        for k, v in zip(keys, vals):
            series[k].append(v)
    return {'dates': dates, 'keys': keys, 'series': series}


def share(rec, key, keys=None):
    keys = keys or rec['keys']
    out = []
    for t in range(len(rec['dates'])):
        tot = sum(rec['series'][k][t] for k in keys)
        out.append(rec['series'][key][t] / tot * 100 if tot else 0.0)
    return out


def avg(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def wm(v, n=13, first=False):
    return avg(v[:n] if first else v[-n:])


def wow(v, i):
    return (v[i] / v[i - 1] - 1) * 100 if i > 0 and v[i - 1] else None


DEV = read_xlsx(F_NEW_DEV)
SDEV = read_shop(F_NEW_SDEV)
SSKIN = read_shop(F_NEW_SSKIN)
OLD = read_xlsx(F_OLD_DEV)

N = json.load(open('work/task2/num2.json'))
V = {}
V['meta'] = {
    'dev5060_keywords': DEV['keys'], 'dev5060_weeks': len(DEV['dates']),
    'dev5060_range': [DEV['dates'][0], DEV['dates'][-1]],
    'imgapp_keywords': SDEV['keys'], 'imgapp_weeks': len(SDEV['dates']),
    'skin5060_keywords': SSKIN['keys'], 'skin5060_weeks': len(SSKIN['dates']),
    'shop_range': [SDEV['dates'][0], SDEV['dates'][-1]],
}


def block(rec, key):
    sh = share(rec, key)
    v = rec['series'][key]
    d = {'recent': round(wm(sh), 1), 'first': round(wm(sh, first=True), 1),
         'last4': round(avg(sh[-4:]), 1), 'delta': round(wm(sh) - wm(sh, first=True), 1),
         'now': round(sh[-1], 1),
         'peak': round(max(sh), 1), 'peak_date': rec['dates'][sh.index(max(sh))],
         'peak_raw': max(v), 'raw_last': v[-1],
         'raw_growth_13w': round((wm(v) / wm(v, first=True) - 1) * 100, 1) if wm(v, first=True) else None}
    return d


V['dev5060'] = {k: block(DEV, k) for k in DEV['keys']}
V['skin5060'] = {k: block(SSKIN, k) for k in SSKIN['keys']}
V['imgapp5060'] = {k: block(SDEV, k) for k in SDEV['keys']}

# 이미용가전: 클릭이 실제로 잡히는 키워드만 남긴 2자 구도(메디큐브 vs 듀얼소닉)
LIVE = [k for k in SDEV['keys'] if max(SDEV['series'][k]) >= 50]
V['imgapp_live'] = {'keys': LIVE,
                    'live_max': {k: max(SDEV['series'][k]) for k in SDEV['keys']},
                    'zero_keys': [k for k in SDEV['keys'] if max(SDEV['series'][k]) == 0]}
sh2 = share(SDEV, '메디큐브', keys=LIVE)
V['imgapp2'] = {'recent': round(wm(sh2), 1), 'first': round(wm(sh2, first=True), 1),
                'delta': round(wm(sh2) - wm(sh2, first=True), 1), 'last4': round(avg(sh2[-4:]), 1),
                'peak': round(max(sh2), 1), 'peak_date': SDEV['dates'][sh2.index(max(sh2))]}

# 검색(통검) vs 클릭(이미용가전) — 같은 5060 안에서의 낙차
V['gap5060'] = {
    'search': V['dev5060']['메디큐브 에이지알']['recent'],
    'click': V['imgapp5060']['메디큐브']['recent'],
    'gap': round(V['imgapp5060']['메디큐브']['recent'] - V['dev5060']['메디큐브 에이지알']['recent'], 1),
}

# 비교군을 바꾼 결과(기존 5사 vs 5060 전용 5사)
V['setcmp'] = {}
for lab, rec in [('old', OLD), ('new', DEV)]:
    V['setcmp'][lab] = {k: block(rec, k) for k in rec['keys']}

# 두 파일의 정합성 — 겹치는 키워드의 시계열 비율이 일정한가
V['consistency'] = {}
for k in set(OLD['keys']) & set(DEV['keys']):
    r = [OLD['series'][k][i] / DEV['series'][k][i] for i in range(len(DEV['dates'])) if DEV['series'][k][i]]
    V['consistency'][k] = {'ratio_min': round(min(r), 2), 'ratio_max': round(max(r), 2),
                           'ratio_mean': round(avg(r), 2),
                           'proportional': bool(max(r) - min(r) < 0.02)}

# 이벤트 주 — 새 3파일 안에서의 전주 대비·비중
EV_DATES = ['2025-12-29', '2026-02-16', '2026-03-02', '2026-05-04', '2026-06-29',
            '2026-08-03', '2026-09-07', '2026-11-02']
V['events'] = {}
for d in EV_DATES:
    row = {}
    if d in DEV['dates']:
        i = DEV['dates'].index(d)
        row['dev_wow'] = round(wow(DEV['series']['메디큐브 에이지알'], i), 1)
        row['dev_share'] = round(share(DEV, '메디큐브 에이지알')[i], 1)
        row['dev_top'] = max(((round(share(DEV, k)[i], 1), k) for k in DEV['keys']))
    if d in SDEV['dates']:
        i = SDEV['dates'].index(d)
        row['click_wow'] = round(wow(SDEV['series']['메디큐브'], i), 1)
        row['click_share'] = round(share(SDEV, '메디큐브')[i], 1)
    if d in SSKIN['dates']:
        i = SSKIN['dates'].index(d)
        row['skin_medicube_share'] = round(share(SSKIN, '메디큐브')[i], 1)
        row['skin_sulwhasoo_share'] = round(share(SSKIN, '설화수')[i], 1)
        row['skin_sulwhasoo_raw'] = SSKIN['series']['설화수'][i]
    V['events'][d] = row

# 스킨케어 5060 — 9월 초 정점 주의 확인(설화수 raw 연중 최고)
sh_sul = share(SSKIN, '설화수')
V['sulwhasoo_peak'] = {'raw_max': max(SSKIN['series']['설화수']),
                       'raw_max_date': SSKIN['dates'][SSKIN['series']['설화수'].index(max(SSKIN['series']['설화수']))],
                       'share_at_peak': round(sh_sul[SSKIN['series']['설화수'].index(max(SSKIN['series']['설화수']))], 1),
                       'share_top': round(max(sh_sul), 1)}
# 메디큐브 5060 스킨케어 클릭 최근 4주 순위
V['skin5060_last4_rank'] = sorted(((V['skin5060'][k]['last4'], k) for k in SSKIN['keys']), reverse=True)
V['imgapp_last4_rank'] = sorted(((V['imgapp5060'][k]['last4'], k) for k in SDEV['keys']), reverse=True)

# 차트용 시계열
V['series'] = {
    'dev_dates': DEV['dates'],
    **{f'dev_{k}': [round(x, 2) for x in share(DEV, k)] for k in DEV['keys']},
    'img_dates': SDEV['dates'],
    **{f'img_{k}': [round(x, 2) for x in share(SDEV, k)] for k in SDEV['keys']},
    'skin_dates': SSKIN['dates'],
    **{f'skin_{k}': [round(x, 2) for x in share(SSKIN, k)] for k in SSKIN['keys']},
}
V['dev_sum'] = {}
tot = [sum(DEV['series'][k][t] for k in DEV['keys']) for t in range(len(DEV['dates']))]
V['dev_sum'] = {'first': round(tot[0], 1), 'last': round(tot[-1], 1),
                'peak': round(max(tot), 1), 'peak_date': DEV['dates'][tot.index(max(tot))],
                'chg_pct': round((tot[-1] / tot[0] - 1) * 100, 1),
                'min': round(min(tot), 1), 'min_date': DEV['dates'][tot.index(min(tot))]}

_i = SDEV['dates'].index('2026-05-04')
V['imgapp_5_4'] = {'raw': SDEV['series']['메디큐브'][_i], 'prev_raw': SDEV['series']['메디큐브'][_i - 1],
                   'wow_raw': round((SDEV['series']['메디큐브'][_i] / SDEV['series']['메디큐브'][_i - 1] - 1) * 100, 1),
                   'share': round(share(SDEV, '메디큐브')[_i], 1)}

# 값 개수(원자료 대장용)
V['value_count'] = {'dev5060': len(DEV['dates']) * len(DEV['keys']),
                    'imgapp': len(SDEV['dates']) * len(SDEV['keys']),
                    'skin5060': len(SSKIN['dates']) * len(SSKIN['keys'])}
V['value_count']['total_new'] = sum(V['value_count'].values())

N['v12'] = V
json.dump(N, open('work/task2/num2.json', 'w'), ensure_ascii=False, indent=1)

print(json.dumps({k: V[k] for k in ('meta', 'gap5060', 'imgapp2', 'imgapp_live', 'sulwhasoo_peak',
                                    'value_count', 'skin5060_last4_rank', 'imgapp_last4_rank',
                                    'consistency')}, ensure_ascii=False, indent=1))
print('--- dev5060'); [print(' ', k, v) for k, v in V['dev5060'].items()]
print('--- skin5060'); [print(' ', k, v) for k, v in V['skin5060'].items()]
print('--- imgapp'); [print(' ', k, v) for k, v in V['imgapp5060'].items()]
print('--- events'); [print(' ', k, v) for k, v in V['events'].items()]
