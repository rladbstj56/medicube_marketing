# -*- coding: utf-8 -*-
"""글로벌 트렌드 보고서 도표 16종 — 메디큐브 레드 팔레트.

work/gt/charts.py의 값 계산·레이블을 그대로 두고 색만 메디큐브 톤으로 바꾼 판이다.
값은 analysis/task2/chartdata/gt.json(원자료 CSV 13종에서 재계산된 중간 산출물)에서만 읽고,
결과는 analysis/task2/fig/global/ 에 SVG로 쓴다. 글자는 모두 path로 굽기 때문에
PDF·PPT 어디에 넣어도 한글·일본어 폰트가 깨지지 않는다.
"""
import json, os, statistics as st
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.ticker import MultipleLocator, FuncFormatter
import matplotlib.patheffects as pe
from matplotlib.ticker import NullFormatter

HERE = Path(__file__).resolve().parent
for _p in (HERE / 'fonts').glob('*.ttf'):
    fm.fontManager.addfont(str(_p))

OUT = str(HERE / 'fig' / 'global')
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    'font.family': ['Noto Sans CJK KR', 'Noto Sans KR', 'AppleGothic', 'Malgun Gothic'],
    'axes.unicode_minus': False, 'svg.fonttype': 'path',
    'figure.dpi': 100, 'savefig.bbox': 'tight', 'savefig.pad_inches': 0.03,
})
# 메디큐브 팔레트 — brand=시그니처 레드, 나머지는 차콜·슬레이트 계단(경쟁사·배경)
C = dict(ink='#1F2937', green='#D92B3A', green_d='#9B1B27', green_l='#F08A95', mint='#FDE2E4',
         red='#9B1B27', amber='#64748B', blue='#334155', gray='#8B95A3', gray_l='#CBD5E1',
         grid='#ECECEF', navy='#1F2937', sand='#E4636F', purple='#94A3B8')
MM = 1 / 25.4
FS_TICK, FS_LEG, FS_ANN, FS_END = 7.2, 7.2, 7.0, 7.4

G = json.load(open(HERE / 'chartdata' / 'gt.json'))
S = G['sets']


def save(f, name):
    """SVG는 보고서용으로 남기고, 눈으로 볼 PNG 미리보기는 gitignore된 tmp/에만 쓴다."""
    f.savefig(f'{OUT}/{name}.svg')
    prev = HERE / 'tmp' / 'figpng'
    prev.mkdir(parents=True, exist_ok=True)
    f.savefig(prev / f'{name}.png', dpi=170)
    plt.close(f)


def fig(w, h):
    return plt.figure(figsize=(w * MM, h * MM))


def style(ax, ymax=None, ymajor=None, grid=True):
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color('#CBD5E1'); ax.spines[s].set_linewidth(0.7)
    ax.tick_params(colors='#4B5563', labelsize=FS_TICK, length=2.5, width=0.7, pad=2.5)
    if grid:
        ax.yaxis.grid(True, color=C['grid'], lw=0.7, zorder=0); ax.set_axisbelow(True)
    if ymax is not None:
        ax.set_ylim(0, ymax)
    if ymajor is not None:
        ax.yaxis.set_major_locator(MultipleLocator(ymajor))


def mticks(ax, dates, every=6):
    ticks, labels, seen = [], [], set()
    for i, d in enumerate(dates):
        ym = d[:7]
        if ym not in seen and (i % every == 0 or i == len(dates) - 1):
            seen.add(ym); ticks.append(i); labels.append(f"{d[2:4]}.{int(d[5:7])}")
    ax.set_xticks(ticks); ax.set_xticklabels(labels, fontsize=FS_TICK)


def qticks(ax, dates):
    ax.set_xticks([0, 13, 26, 39, 52])
    ax.set_xticklabels([f"{dates[i][2:4]}.{int(dates[i][5:7])}" for i in (0, 13, 26, 39, 52)], fontsize=FS_TICK)


def bold(ax, x, y, s, color, fs=FS_END, ha='left', va='center'):
    t = ax.text(x, y, s, color=color, fontsize=fs, ha=ha, va=va, zorder=6)
    t.set_path_effects([pe.withStroke(linewidth=0.3, foreground=color)])


def note(ax, xy, xytext, s, color, ha='left', va='center', fs=FS_ANN):
    ax.annotate(s, xy=xy, xytext=xytext, color=color, fontsize=fs, ha=ha, va=va, zorder=7,
                bbox=dict(boxstyle='round,pad=0.22', fc='white', ec='none', alpha=0.9),
                arrowprops=dict(arrowstyle='-', color=color, lw=0.7, shrinkA=1, shrinkB=3))


# ─────────────────────────── ① 미국 4개 브랜드 주별 추세
def c1_us_lines():
    d = S['A_time']; dates = d['dates']
    order = ['medicube', 'Anua', 'COSRX', 'BIODANCE', 'Dr.Althea']
    col = {'medicube': C['green'], 'Anua': C['blue'], 'COSRX': C['amber'], 'BIODANCE': C['purple'], 'Dr.Althea': C['gray_l']}
    lw = {'medicube': 2.0, 'Anua': 1.5, 'COSRX': 1.4, 'BIODANCE': 1.3, 'Dr.Althea': 1.0}
    f = fig(178, 80); ax = f.add_axes([0.075, 0.135, 0.845, 0.79])
    x = list(range(len(dates)))
    for k in order:
        v = d['series'][k]
        ax.plot(x, v, color=col[k], lw=lw[k], marker='o', ms=2.6 if k == 'medicube' else 1.9,
                mfc='white', mec=col[k], mew=0.8, zorder=4 if k == 'medicube' else 2, label=k, markevery=(0, 2))
    style(ax, ymax=124, ymajor=20)
    ax.set_xlim(-1.2, len(dates) + 8)
    mticks(ax, dates, 6)
    ax.legend(loc='upper left', ncol=5, frameon=False, fontsize=FS_LEG, handlelength=1.6,
              columnspacing=1.4, bbox_to_anchor=(0.0, 1.10))
    # 주석: 4/12 카테고리 동반, 11/15 브랜드 단독
    i4 = dates.index('2026-04-12'); i11 = dates.index('2026-11-15')
    ax.axvspan(i4 - 0.5, i4 + 0.5, color=C['sand'], alpha=0.35, zorder=0)
    ax.axvspan(i11 - 0.5, i11 + 0.5, color=C['mint'], alpha=0.55, zorder=0)
    note(ax, (i4, 89), (i4 - 15.0, 100.5), '4/12 카테고리 동반 상승 (5개 중 4개 동시 최고)', C['amber'], ha='left')
    note(ax, (i11, 100), (i11 - 15.5, 110), '11/15 메디큐브만 100 (경쟁 3개는 8~37)', C['green'])
    bold(ax, len(dates) + 0.8, 100, '100', C['green'])
    bold(ax, len(dates) + 0.8, d['series']['Anua'][-1], '37', C['blue'])
    bold(ax, len(dates) + 0.8, d['series']['COSRX'][-1] + 2.2, '11', C['amber'])
    bold(ax, len(dates) + 0.8, d['series']['BIODANCE'][-1] - 3.0, '9', C['purple'])
    ax.set_ylabel('');
    save(f, 'c1_us_lines')


# ─────────────────────────── ② 미국 점유율(5개 검색어 합계 대비) 100% 누적
def c2_us_share():
    d = S['A_time']; dates = d['dates']
    ser = d['series']; keys = d['keys']
    tot = [sum(ser[k][i] for k in keys) for i in range(len(dates))]
    order = ['medicube', 'Anua', 'COSRX', 'BIODANCE', 'Dr.Althea']
    col = {'medicube': C['green'], 'Anua': C['blue'], 'COSRX': C['amber'], 'BIODANCE': C['purple'], 'Dr.Althea': C['gray_l']}
    f = fig(90, 64); ax = f.add_axes([0.13, 0.16, 0.84, 0.74])
    x = list(range(len(dates)))
    base = [0] * len(dates)
    for k in order:
        v = [ser[k][i] / tot[i] * 100 for i in x]
        ax.fill_between(x, base, [a + b for a, b in zip(base, v)], color=col[k], lw=0, alpha=0.95 if k == 'medicube' else 0.85)
        base = [a + b for a, b in zip(base, v)]
    style(ax, ymax=100, grid=False)
    ax.set_yticks([0, 50, 100]); ax.set_yticklabels(['0%', '50%', '100%'])
    ax.set_xlim(0, len(dates) - 1); qticks(ax, dates)
    bold(ax, len(dates) * 0.30, 30, '메디큐브', '#FFFFFF', fs=7.6)
    bold(ax, len(dates) * 0.72, 82, '31.8%', '#FFFFFF', fs=7.2)
    ax.text(len(dates) * 0.72, 74, 'Anua', color='#FFFFFF', fontsize=6.4, ha='center', va='center')
    save(f, 'c2_us_share')


# ─────────────────────────── ③ 미국 메디큐브 ÷ Anua 배수
def c3_us_gap():
    d = S['A_time']; dates = d['dates']
    r = [d['series']['medicube'][i] / d['series']['Anua'][i] for i in range(len(dates))]
    f = fig(90, 64); ax = f.add_axes([0.145, 0.16, 0.83, 0.74])
    x = list(range(len(dates)))
    ax.plot(x, r, color=C['green'], lw=1.9, zorder=4)
    ax.fill_between(x, 1, r, color=C['mint'], alpha=0.5, lw=0)
    ax.axhline(1, color=C['gray'], lw=0.8, ls=(0, (4, 3)))
    style(ax, ymax=3.3, ymajor=0.5, grid=True)
    ax.set_yticks([1, 1.5, 2, 2.5, 3]); ax.set_yticklabels(['1.0배', '1.5', '2.0', '2.5', '3.0'])
    ax.set_xlim(-0.8, len(dates) - 0.2); qticks(ax, dates)
    imin = r.index(min(r))
    bold(ax, imin + 1.4, 1.06, f'최소 {min(r):.2f}배', C['red'], fs=6.4)
    bold(ax, len(dates) - 1.2, r[-1] + 0.16, f'{r[-1]:.2f}배', C['green'], fs=7.2, ha='right')
    bold(ax, 4.0, 1.04, f'첫 주 {r[1]:.2f}배', C['green'], fs=6.4)
    save(f, 'c3_us_gap')


# ─────────────────────────── ④ 미국 51개 주 — 메디큐브 점유율 분포
def c4_us_geo():
    A = G['geo']['A_geo']
    rows = sorted(A['rows'], key=lambda r: -(r['medicube_share'] or 0))
    f = fig(178, 70); ax = f.add_axes([0.055, 0.13, 0.92, 0.76])
    n = len(rows); x = list(range(n))
    vals = [r['medicube_share'] for r in rows]
    mean = st.mean(vals)
    ax.bar(x, vals, width=0.74, color=[C['green'] if v >= mean else C['green_l'] for v in vals], lw=0)
    ax.axhline(mean, color=C['red'], lw=0.8, ls=(0, (4, 3)))
    style(ax, ymax=86, ymajor=20, grid=True)
    ax.set_yticks([40, 50, 60, 70]); ax.set_yticklabels(['40%', '50%', '60%', '70%'])
    ax.set_xticks([]); ax.tick_params(axis='x', length=0)
    ax.set_xlim(-0.8, n + 0.6)
    ax.text(n * 0.60, mean + 2.4, f'51개 주 평균 {mean:.1f}%', color=C['red'], fontsize=6.8,
            bbox=dict(boxstyle='round,pad=0.16', fc='white', ec='none', alpha=0.9), zorder=7)
    note(ax, (0, vals[0] - 2), (7.0, 80), f'{rows[0]["region"]} {vals[0]:.1f}%', C['green'])
    note(ax, (n - 1, vals[-1] - 2), (n - 14, 50), f'{rows[-1]["region"]} {vals[-1]:.1f}%', C['green_l'])
    save(f, 'c4_us_geo')


# ─────────────────────────── ⑤ 미국 제품·성분 — 메디큐브=100 환산
def c5_us_products():
    d = S['B_time']; dates = d['dates']
    base = d['series']['medicube']
    order = [('pdrn', C['green'], 1.9), ('collagen night wrapping mask', C['purple'], 1.3),
             ('medicube toner pads', C['blue'], 1.3), ('medicube booster pro', C['amber'], 1.3)]
    lab = {'pdrn': 'pdrn(성분)', 'collagen night wrapping mask': 'collagen night wrapping mask',
           'medicube toner pads': 'medicube toner pads', 'medicube booster pro': 'medicube booster pro'}
    f = fig(178, 84); ax = f.add_axes([0.07, 0.135, 0.85, 0.76])
    x = list(range(len(dates)))
    for k, c, w in order:
        v = [d['series'][k][i] / base[i] * 100 for i in x]
        ax.plot(x, v, color=c, lw=w, zorder=4 if k == 'pdrn' else 2, label=f'{lab[k]}', marker='o', ms=1.8,
                mfc='white', mec=c, mew=0.7, markevery=(0, 3))
    ax.axhline(100, color=C['ink'], lw=1.0, ls=(0, (5, 3)))
    style(ax, ymax=118, ymajor=20)
    ax.set_yticks([0, 20, 40, 60, 80, 100]); ax.set_yticklabels(['0', '20', '40', '60', '80', '100'])
    ax.set_xlim(-0.5, len(dates) + 6); mticks(ax, dates, 6)
    ax.legend(loc='upper left', ncol=5, frameon=False, fontsize=FS_LEG, handlelength=1.5,
              columnspacing=1.3, bbox_to_anchor=(0.0, 1.10))
    bold(ax, len(dates) + 0.6, 104, 'medicube=100', C['green'], fs=6.6)
    p = [d['series']['pdrn'][i] / base[i] * 100 for i in x]
    bold(ax, len(dates) + 0.6, p[-1], f'{p[-1]:.0f}', C['green'], fs=7.2)
    i = dates.index('2026-11-15')
    note(ax, (i - 3, p[-4]), (i - 20, p[-4] - 16), '성분 검색이 브랜드 자체 검색의 절반 가까이', C['green'])
    save(f, 'c5_us_products')


# ─────────────────────────── ⑥ 부스터 프로 — 헤드텀 감소 vs 하위 검색어 상승
def c6_booster():
    d = S['B_time']; dates = d['dates']
    mc = d['series']['medicube']; bp = d['series']['medicube booster pro']
    r = [bp[i] / mc[i] * 100 for i in range(len(dates))]
    f = fig(90, 56); ax = f.add_axes([0.15, 0.18, 0.82, 0.70])
    x = list(range(len(dates)))
    ax.plot(x, r, color=C['amber'], lw=1.7)
    ax.fill_between(x, 0, r, color=C['sand'], alpha=0.55, lw=0)
    style(ax, ymax=6, ymajor=2)
    ax.set_yticks([0, 2, 4, 6]); ax.set_yticklabels(['0', '2', '4', '6'])
    ax.set_xlim(0, len(dates) - 1); mticks(ax, dates, 15)
    note(ax, (1, r[1]), (6, 4.7), f'첫 주 {r[1]:.1f}%', C['amber'])
    note(ax, (len(dates) - 1, r[-1]), (len(dates) - 12, 0.55), f'최근 {r[-1]:.1f}%', C['red'])
    save(f, 'c6_booster')


# ─────────────────────────── ⑦ 영국 5개 브랜드
def c7_uk_lines():
    d = S['C_time']; dates = d['dates']
    order = ['medicube', 'beauty of joseon', 'BIODANCE', 'COSRX', 'celimax']
    col = {'medicube': C['green'], 'beauty of joseon': C['amber'], 'BIODANCE': C['purple'], 'COSRX': C['blue'], 'celimax': C['gray']}
    lw = {'medicube': 2.0, 'beauty of joseon': 1.4, 'BIODANCE': 1.3, 'COSRX': 1.3, 'celimax': 1.3}
    f = fig(178, 88); ax = f.add_axes([0.075, 0.13, 0.845, 0.79])
    x = list(range(len(dates)))
    for k in order:
        ax.plot(x, d['series'][k], color=col[k], lw=lw[k], marker='o', ms=2.5 if k == 'medicube' else 1.8,
                mfc='white', mec=col[k], mew=0.8, zorder=4 if k == 'medicube' else 2, label=k, markevery=(0, 2))
    style(ax, ymax=112, ymajor=20)
    ax.set_xlim(-1.2, len(dates) + 7); mticks(ax, dates, 6)
    ax.legend(loc='upper left', ncol=5, frameon=False, fontsize=FS_LEG, handlelength=1.6,
              columnspacing=1.4, bbox_to_anchor=(0.0, 1.09))
    i10 = dates.index('2026-10-04')
    ax.axvspan(i10 - 0.5, i10 + 0.5, color=C['sand'], alpha=0.4, zorder=0)
    note(ax, (i10, 100), (i10 - 26, 92), '10/4 프라임 빅딜데이즈 주 (영국 100, 미국 76)', C['amber'])
    ends = sorted(([(d['series'][k][-1], c) for k, c in (('beauty of joseon', C['amber']), ('BIODANCE', C['purple']), ('COSRX', C['blue']), ('celimax', C['gray']))]))
    y = None
    for v, c in ends:
        yy = v if y is None else max(v, y + 4.4)
        bold(ax, len(dates) + 0.5, yy, f'{v:g}', c, fs=6.4)
        y = yy
    bold(ax, len(dates) + 0.5, 97, '97', C['green'])
    save(f, 'c7_uk_lines')


# ─────────────────────────── ⑧ 영국 점유율
def c8_uk_share():
    d = S['C_time']; dates = d['dates']; ser = d['series']; keys = d['keys']
    tot = [sum(ser[k][i] for k in keys) for i in range(len(dates))]
    order = ['medicube', 'beauty of joseon', 'BIODANCE', 'COSRX', 'celimax']
    col = {'medicube': C['green'], 'beauty of joseon': C['amber'], 'BIODANCE': C['purple'], 'COSRX': C['blue'], 'celimax': C['gray']}
    f = fig(178, 54); ax = f.add_axes([0.075, 0.19, 0.90, 0.66])
    x = list(range(len(dates))); base = [0] * len(dates)
    for k in order:
        v = [ser[k][i] / tot[i] * 100 for i in x]
        ax.fill_between(x, base, [a + b for a, b in zip(base, v)], color=col[k], lw=0,
                        alpha=0.95 if k == 'medicube' else 0.85)
        base = [a + b for a, b in zip(base, v)]
    style(ax, ymax=100, grid=False)
    ax.set_yticks([0, 50, 100]); ax.set_yticklabels(['0%', '50%', '100%'])
    ax.set_xlim(0, len(dates) - 1); mticks(ax, dates, 6)
    bold(ax, len(dates) * 0.24, 26, '메디큐브', '#FFFFFF', fs=8.0)
    bold(ax, len(dates) * 0.55, 74, '조선미녀 14.8%', '#FFFFFF', fs=6.8)
    save(f, 'c8_uk_share')


# ─────────────────────────── ⑨ 일본 5개 브랜드
def c9_jp_lines():
    d = S['J_time']; dates = d['dates']
    order = ['アヌア', 'メディキューブ', 'トリデン', 'ティルティル', 'Biodance']
    col = {'アヌア': C['blue'], 'メディキューブ': C['green'], 'トリデン': C['amber'], 'ティルティル': C['purple'], 'Biodance': C['gray_l']}
    lab = {'アヌア': 'アヌア(Anua)', 'メディキューブ': 'メディキューブ(medicube)', 'トリデン': 'トリデン(Torriden)',
           'ティルティル': 'ティルティル(TIRTIR)', 'Biodance': 'Biodance(라틴 표기)'}
    lw = {'アヌア': 1.8, 'メディキューブ': 2.0, 'トリデン': 1.3, 'ティルティル': 1.3, 'Biodance': 0.9}
    f = fig(178, 88); ax = f.add_axes([0.075, 0.13, 0.855, 0.79])
    x = list(range(len(dates)))
    for k in order:
        ax.plot(x, d['series'][k], color=col[k], lw=lw[k], marker='o', ms=2.4 if k == 'メディキューブ' else 1.7,
                mfc='white', mec=col[k], mew=0.8, zorder=4 if k == 'メディキューブ' else 2, label=lab[k], markevery=(0, 2))
    style(ax, ymax=124, ymajor=20)
    ax.set_xlim(-1.2, len(dates) + 12); mticks(ax, dates, 6)
    ax.legend(loc='upper left', ncol=5, frameon=False, fontsize=FS_LEG, handlelength=1.6,
              columnspacing=1.3, bbox_to_anchor=(0.0, 1.09))
    i8 = dates.index('2026-08-30')
    note(ax, (i8, 100), (i8 - 21, 108), '8/30 アヌア 100 — 메디큐브도 64로 동반 급등', C['blue'])
    bold(ax, len(dates) + 0.4, d['series']['アヌア'][-1], '75', C['blue'])
    bold(ax, len(dates) + 0.4, 43, '43', C['green'])
    bold(ax, len(dates) + 0.4, 17, '17', C['amber'])
    bold(ax, len(dates) + 0.4, 7, '7', C['purple'])
    save(f, 'c9_jp_lines')


# ─────────────────────────── ⑩ 일본 점유율
def c10_jp_share():
    d = S['J_time']; dates = d['dates']; ser = d['series']; keys = d['keys']
    tot = [sum(ser[k][i] for k in keys) for i in range(len(dates))]
    order = ['アヌア', 'メディキューブ', 'トリデン', 'ティルティル', 'Biodance']
    col = {'アヌア': C['blue'], 'メディキューブ': C['green'], 'トリデン': C['amber'], 'ティルティル': C['purple'], 'Biodance': C['gray_l']}
    f = fig(178, 50); ax = f.add_axes([0.075, 0.20, 0.90, 0.64])
    x = list(range(len(dates))); base = [0] * len(dates)
    for k in order:
        v = [ser[k][i] / tot[i] * 100 for i in x]
        ax.fill_between(x, base, [a + b for a, b in zip(base, v)], color=col[k], lw=0,
                        alpha=0.95 if k in ('アヌア', 'メディキューブ') else 0.85)
        base = [a + b for a, b in zip(base, v)]
    style(ax, ymax=100, grid=False)
    ax.set_yticks([0, 50, 100]); ax.set_yticklabels(['0%', '50%', '100%'])
    ax.set_xlim(0, len(dates) - 1); mticks(ax, dates, 6)
    bold(ax, len(dates) * 0.20, 22, 'アヌア 50.3%', '#FFFFFF', fs=7.4)
    bold(ax, len(dates) * 0.72, 90, 'メディキューブ 30.6%', '#FFFFFF', fs=7.2)
    save(f, 'c10_jp_share')


# ─────────────────────────── ⑪ 3국 비교 — 메디큐브=100 상대지수
def c11_anchor():
    A_, C_, J_ = S['A_time'], S['C_time'], S['J_time']

    def idx(d, k):
        return st.mean(d['series'][k]) / st.mean(d['series'][d['keys'][0]]) * 100
    groups = [('미국 (A세트)', A_, ['Anua', 'BIODANCE', 'COSRX', 'Dr.Althea']),
              ('영국 (C세트)', C_, ['beauty of joseon', 'BIODANCE', 'COSRX', 'celimax']),
              ('일본 (J세트)', J_, ['アヌア', 'トリデン', 'ティルティル', 'Biodance'])]
    groups = [(g[0], g[1], sorted(g[2], key=lambda k: -idx(g[1], k))) for g in groups]
    f = fig(178, 70); ax = f.add_axes([0.07, 0.20, 0.90, 0.66])
    xs = [0, 1, 2]; bw = 0.20
    rankcol = [C['blue'], C['amber'], C['purple'], C['gray_l']]
    for gi, (gname, d, ks) in enumerate(groups):
        for i, k in enumerate(ks):
            v = idx(d, k)
            x = xs[gi] + (i - 1.5) * bw
            ax.bar(x, v, width=bw * 0.88, color=rankcol[i], lw=0)
            lab = f'{v:.1f}' if v < 10 else f'{v:.0f}'
            bold(ax, x, v + 3.4, lab, rankcol[i], fs=6.2, ha='center')
    ax.axhline(100, color=C['green'], lw=1.0, ls=(0, (5, 3)))
    style(ax, ymax=190, ymajor=50, grid=True)
    ax.set_yticks([0, 50, 100, 150]); ax.set_yticklabels(['0', '50', '100', '150'])
    ax.set_xticks(xs); ax.set_xticklabels([g[0] for g in groups], fontsize=8.2)
    ax.tick_params(axis='x', length=0, pad=4)
    ax.text(2.44, 105, 'medicube = 100', color=C['green'], fontsize=6.6, ha='right', va='center', zorder=7,
            bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='none', alpha=0.9))
    bold(ax, 2.0, 176, '일본만 경쟁자가 153 — 메디큐브가 2위', C['blue'], fs=7.2, ha='right')
    for i, lab in enumerate(['1위 경쟁 브랜드', '2위', '3위', '4위']):
        ax.barh([], [], color=rankcol[i], label=lab)
    ax.legend(loc='upper left', frameon=False, fontsize=6.4, ncol=4, handlelength=0.9,
              handletextpad=0.35, columnspacing=1.1, bbox_to_anchor=(0.0, 1.10))
    save(f, 'c11_anchor')


# ─────────────────────────── ⑫ 유럽 주요국 (F세트 지역별)
def c12_europe():
    F = G['geo']['F_geo']
    rows = {r['region']: r['medicube_share'] for r in F['rows']}
    EU9 = ['영국', '네덜란드', '스페인', '폴란드', '벨기에', '스위스', '이탈리아', '프랑스', '독일']
    extras = ['리투아니아', '아일랜드', '덴마크', '스웨덴', '포르투갈', '체코', '그리스', '오스트리아', '노르웨이', '핀란드', '헝가리', '루마니아']
    f = fig(178, 60); ax = f.add_axes([0.055, 0.26, 0.93, 0.64])
    labels, vals, cols = [], [], []
    for k in EU9:
        labels.append(k); vals.append(rows[k]); cols.append(C['green'] if k == '영국' else C['green_l'])
    for k in extras:
        labels.append(k); vals.append(rows[k]); cols.append(C['gray_l'])
    x = list(range(len(labels)))
    ax.bar(x, vals, width=0.7, color=cols, lw=0)
    for i, v in enumerate(vals):
        ax.text(i, v + 1.1, f'{v:g}', fontsize=6.0, ha='center', color='#334155')
    style(ax, ymax=76, ymajor=20)
    ax.set_yticks([0, 20, 40, 60]); ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=6.6)
    ax.tick_params(axis='x', length=0)
    ax.axvspan(-0.5, len(EU9) - 0.5, color='#F8F9FB', zorder=0)
    bold(ax, 0.0, 70, '유럽 주요국 9개국(확정 정의)', C['green'], fs=6.8)
    bold(ax, len(EU9) + 0.1, 70, '같은 CSV의 다른 유럽 국가(비교용)', C['gray'], fs=6.8)
    save(f, 'c12_europe')


# ─────────────────────────── ⑬ 일본 47개 도도부현 분포
def c13_jp_geo():
    J = G['geo']['J_geo']
    rows = sorted(J['rows'], key=lambda r: -(r['medicube_share'] or 0))
    f = fig(178, 56); ax = f.add_axes([0.05, 0.20, 0.93, 0.68])
    n = len(rows); x = list(range(n))
    mc = [r['medicube_share'] for r in rows]
    an = [r['v']['アヌア'] for r in rows]
    ax.scatter(x, an, s=9, color=C['blue'], zorder=3)
    ax.scatter(x, mc, s=9, color=C['green'], zorder=3)
    style(ax, ymax=70, ymajor=20, grid=True); ax.set_ylim(19, 64)
    ax.set_yticks([30, 40, 50, 60]); ax.set_yticklabels(['30%', '40%', '50%', '60%'])
    ax.set_xticks([]); ax.tick_params(axis='x', length=0)
    ax.set_xlim(-1, n)
    ax.scatter([], [], s=12, color=C['blue'], label='アヌア(Anua) 점유')
    ax.scatter([], [], s=12, color=C['green'], label='メディキューブ 점유')
    ax.legend(loc='lower right', frameon=False, fontsize=6.6, ncol=2, handletextpad=0.4, columnspacing=1.4,
              bbox_to_anchor=(1.0, 1.0))
    bold(ax, -0.6, 22.0, f'47개 도도부현 전수 · 메디큐브 {min(mc):.0f}~{max(mc):.0f}% (평균 {st.mean(mc):.1f}%) · 아누아 평균 {st.mean(an):.1f}%', C['gray'], fs=6.4)
    save(f, 'c13_jp_geo')


# ─────────────────────────── ⑭ 관련 검색어 급상승 (미국 vs 영국)
def c14_rising():
    A = G['rel']['A_rel']; Cc = G['rel']['C_rel']
    def pctmap(rel):
        return {x['q']: x['pct'] for x in rel['rising'] if x['pct']}
    am, cm = pctmap(A), pctmap(Cc)
    am['medicube shampoo and conditioner'] = am.get('medicube shampoo and conditioner reviews')
    keys = [('medicube deodorant', '데오도란트'), ('medicube kojic acid body wash', '코직애씨드 바디워시'),
            ('medicube pdrn stick', 'PDRN 스틱'), ('medicube drying lotion', '드라잉 로션'),
            ('medicube body peel', '바디 필'), ('medicube peel shot', '필 샷'),
            ('medicube hyaluronic ceramide jelly cream', '히알루론 세라마이드 젤리크림'),
            ('medicube shampoo and conditioner', '샴푸·컨디셔너')]
    f = fig(178, 72); ax = f.add_axes([0.245, 0.16, 0.735, 0.72])
    ys = list(range(len(keys)))[::-1]
    for y, (k, lab) in zip(ys, keys):
        a, c = am.get(k), cm.get(k)
        if a is not None and c is not None:
            ax.plot([a, c], [y, y], color=C['gray_l'], lw=1.6, zorder=1, solid_capstyle='round')
        if a is not None:
            ax.scatter([a], [y], s=26, color=C['green'], zorder=3)
            ax.text(a * 1.08, y, f'+{a:,.0f}%', fontsize=6.2, va='center', color=C['green'])
        if c is not None:
            ax.scatter([c], [y], s=26, color=C['amber'], zorder=3)
            if a is None:
                ax.text(c * 1.08, y, f'+{c:,.0f}%', fontsize=6.2, va='center', color=C['amber'])
    ax.set_xscale('log')
    ax.set_xlim(300, 6500)
    ax.set_xticks([300, 500, 1000, 2000, 4000, 6000])
    ax.set_xticklabels(['+300%', '+500%', '+1,000%', '+2,000%', '+4,000%', '+6,000%'], fontsize=6.4)
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_yticks(ys); ax.set_yticklabels([lab for _, lab in keys], fontsize=7.0)
    ax.set_ylim(-0.8, len(keys) - 0.2)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color('#CBD5E1'); ax.spines['bottom'].set_linewidth(0.7)
    ax.xaxis.grid(True, color=C['grid'], lw=0.7); ax.set_axisbelow(True)
    ax.tick_params(axis='y', length=0)
    ax.scatter([], [], s=26, color=C['green'], label='미국(A세트)')
    ax.scatter([], [], s=26, color=C['amber'], label='영국(C세트)')
    ax.legend(loc='upper left', frameon=False, fontsize=6.6, ncol=2, handletextpad=0.2, columnspacing=1.2,
              bbox_to_anchor=(0.0, 1.10))
    save(f, 'c14_rising')


# ─────────────────────────── ⑮ 미국 스파이크 3개의 구성
def c15_spike():
    d = S['A_time']; dates = d['dates']; ser = d['series']
    weeks = ['2026-04-12', '2026-06-21', '2026-11-15']
    order = ['medicube', 'Anua', 'COSRX', 'BIODANCE', 'Dr.Althea']
    col = {'medicube': C['green'], 'Anua': C['blue'], 'COSRX': C['amber'], 'BIODANCE': C['purple'], 'Dr.Althea': C['gray_l']}
    f = fig(90, 60); ax = f.add_axes([0.12, 0.18, 0.86, 0.68])
    xs = list(range(len(weeks)))
    bottom = [0] * len(weeks)
    for k in order:
        vals = [ser[k][dates.index(w)] for w in weeks]
        ax.bar(xs, vals, bottom=bottom, width=0.6, color=col[k], lw=0, label=k)
        bottom = [a + b for a, b in zip(bottom, vals)]
    style(ax, ymax=215, ymajor=50)
    ax.set_yticks([0, 50, 100, 150, 200])
    ax.set_xticks(xs); ax.set_xticklabels(['4/12', '6/21', '11/15'], fontsize=7.4)
    ax.tick_params(axis='x', length=0)
    shares = []
    for w in weeks:
        i = dates.index(w)
        tot = sum(ser[k][i] for k in order)
        shares.append(ser['medicube'][i] / tot * 100)
        ax.text(xs[weeks.index(w)], bottom[weeks.index(w)] + 4, f'메디큐브 {shares[-1]:.1f}%', fontsize=6.6,
                ha='center', color=C['ink'])
    ax.legend(loc='upper left', frameon=False, fontsize=6.0, ncol=2, handlelength=0.9, columnspacing=0.9,
              handletextpad=0.3, bbox_to_anchor=(0.0, 1.16))
    ax.set_title('5개 검색어 합계(0~100 눈금 합)', fontsize=6.6, color='#6B7280', pad=3)
    save(f, 'c4_spike')





# ─────────────────────────── ⑯ 일본 관련 검색어 TOP — 기기 검색어가 2·3위
def c16_jp_rel():
    top = G['rel']['J_rel']['top'][:12]
    f = fig(178, 62); ax = f.add_axes([0.26, 0.16, 0.70, 0.74])
    ys = list(range(len(top)))[::-1]
    top = [(x['q'], x['v']) for x in top]
    for y, (q, v) in zip(ys, top):
        dev = ('美顔' in q) or ('ブースター' in q)
        ax.barh(y, float(v), height=0.62, color=C['green'] if dev else C['gray_l'], lw=0)
        ax.text(float(v) + 1.6, y, f'{float(v):g}', fontsize=6.2, va='center', color='#334155')
    ax.set_yticks(ys); ax.set_yticklabels([q for q, _ in top], fontsize=6.8)
    ax.set_xlim(0, 118); ax.set_xticks([0, 50, 100])
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color('#CBD5E1'); ax.spines['bottom'].set_linewidth(0.7)
    ax.xaxis.grid(True, color=C['grid'], lw=0.7); ax.set_axisbelow(True)
    ax.tick_params(axis='y', length=0, pad=2)
    ax.set_ylim(-0.7, len(top) - 0.3)
    ax.barh([], [], color=C['green'], label='미용기기 관련')
    ax.barh([], [], color=C['gray_l'], label='스킨케어·기타')
    ax.legend(loc='lower right', frameon=False, fontsize=6.2, handlelength=0.9, ncol=2,
              bbox_to_anchor=(1.0, 0.0), columnspacing=1.2)
    save(f, 'c16_jp_rel')

# 도표 1~16 전수 (도표 4 '세 봉우리 구성'은 c15_spike → c4_spike.svg)
FIGURES = (c1_us_lines, c2_us_share, c3_us_gap, c15_spike, c4_us_geo, c5_us_products, c6_booster,
           c7_uk_lines, c8_uk_share, c9_jp_lines, c10_jp_share, c13_jp_geo, c16_jp_rel,
           c11_anchor, c12_europe, c14_rising)

if __name__ == '__main__':
    for fn in FIGURES:
        fn()
        print('ok', fn.__name__)
