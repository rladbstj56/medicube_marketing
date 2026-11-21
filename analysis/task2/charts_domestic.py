# -*- coding: utf-8 -*-
"""국내 트렌드 보고서 도표 8종 — 메디큐브 레드 팔레트.

work/domestic/charts.py의 값 계산·레이블을 그대로 두고 색만 메디큐브 톤으로 바꾼 판이다.
값은 analysis/task2/chartdata/dom.json·nums.json(원자료에서 재계산된 중간 산출물)에서만 읽고,
결과는 analysis/task2/fig/domestic/ 에 SVG로 쓴다. 글자는 모두 path로 굽기 때문에
PDF·PPT 어디에 넣어도 한글 폰트가 깨지지 않는다(폰트는 미리보기용으로만 쓰인다).
"""
import json, os, statistics as st
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.ticker import MultipleLocator
import matplotlib.patheffects as pe

HERE = Path(__file__).resolve().parent
for _p in (HERE / 'fonts').glob('*.ttf'):
    fm.fontManager.addfont(str(_p))

OUT = str(HERE / 'fig' / 'domestic')
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    'font.family': ['Noto Sans CJK KR', 'Noto Sans KR', 'AppleGothic', 'Malgun Gothic'],
    'axes.unicode_minus': False, 'svg.fonttype': 'path',
    'figure.dpi': 100, 'savefig.bbox': 'tight', 'savefig.pad_inches': 0.03,
})
# 메디큐브 팔레트 — brand=시그니처 레드, 나머지는 차콜·슬레이트 계단(경쟁사·배경)
C = dict(ink='#1F2937', green='#D92B3A', green_d='#9B1B27', green_l='#F08A95', mint='#FDE2E4',
         red='#9B1B27', amber='#64748B', blue='#334155', gray='#8B95A3', gray_l='#CBD5E1',
         grid='#ECECEF', navy='#1F2937', sand='#E4636F', purple='#94A3B8', rose='#E4636F')
MM = 1 / 25.4
FS_TICK, FS_LEG, FS_ANN, FS_END = 7.2, 7.0, 6.9, 7.4

D = json.load(open(HERE / 'chartdata' / 'dom.json'))
N = json.load(open(HERE / 'chartdata' / 'nums.json'))
X, S = D['xlsx'], D['csv']
DATES = X['brand_all']['dates']
SDATES = S['shop_all']['dates']
BR = ['메디큐브', '에스트라', '메디힐', '토리든', '넘버즈인']
DEV = ['메디큐브 에이지알', '마미케어', '톰더글로우', '쿼드쎄라', 'LG 프라엘']
LINE = ['부스터 프로', '부스터 프로 미니', 'PDRN 앰플', '제로모공패드', '부스터 글로우']
COL = {'메디큐브': C['green'], '에스트라': C['blue'], '메디힐': C['amber'], '토리든': C['purple'],
       '넘버즈인': C['gray_l'],
       '메디큐브 에이지알': C['green'], '마미케어': C['blue'], '톰더글로우': C['amber'],
       '쿼드쎄라': C['purple'], 'LG 프라엘': C['gray_l'],
       '부스터 프로': C['green'], '부스터 프로 미니': C['amber'], 'PDRN 앰플': C['blue'],
       '제로모공패드': C['purple'], '부스터 글로우': C['rose']}
LBL = {'메디큐브': '메디큐브', '에스트라': '에스트라', '메디힐': '메디힐', '토리든': '토리든',
       '넘버즈인': '넘버즈인', '메디큐브 에이지알': '에이지알', '마미케어': '마미케어',
       '톰더글로우': '톰더글로우', '쿼드쎄라': '쿼드쎄라', 'LG 프라엘': '프라엘',
       '부스터 프로': '부스터 프로', '부스터 프로 미니': '미니', 'PDRN 앰플': 'PDRN 앰플',
       '제로모공패드': '제로모공패드', '부스터 글로우': '부스터 글로우'}


def mean(v):
    return sum(v) / len(v)


def share(rec, k):
    ks = rec['keys']
    n = len(rec['dates'])
    return [rec['series'][k][i] / sum(rec['series'][j][i] for j in ks) * 100 for i in range(n)]


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


def mticks(ax, dates, step=2):
    """월이 바뀌는 첫 주만 눈금으로 쓰고, step개월 간격으로 솎는다."""
    seen = {}
    for i, d in enumerate(dates):
        seen.setdefault(d[:7], i)
    items = list(seen.items())
    ticks, labels = [], []
    for j, (m, i) in enumerate(items):
        if j % step == 0:
            ticks.append(i); labels.append(f"{m[2:4]}.{int(m[5:7])}")
    ax.set_xticks(ticks); ax.set_xticklabels(labels, fontsize=FS_TICK)


def bold(ax, x, y, s, color, fs=FS_END, ha='left', va='center'):
    t = ax.text(x, y, s, color=color, fontsize=fs, ha=ha, va=va, zorder=6)
    t.set_path_effects([pe.withStroke(linewidth=0.3, foreground=color)])


def note(ax, xy, xytext, s, color, ha='left', va='center', fs=FS_ANN):
    ax.annotate(s, xy=xy, xytext=xytext, color=color, fontsize=fs, ha=ha, va=va, zorder=7,
                bbox=dict(boxstyle='round,pad=0.22', fc='white', ec='none', alpha=0.88),
                arrowprops=dict(arrowstyle='-', color=color, lw=0.7, shrinkA=1, shrinkB=3))


def save(f, name):
    """SVG는 보고서용으로 남기고, 눈으로 볼 PNG 미리보기는 gitignore된 tmp/에만 쓴다."""
    f.savefig(f'{OUT}/{name}.svg')
    prev = HERE / 'tmp' / 'figpng'
    prev.mkdir(parents=True, exist_ok=True)
    f.savefig(prev / f'{name}.png', dpi=170)
    plt.close(f)


# ── c01 검색 3축: 메디큐브 지수 (전체·2030·5060)
def c01():
    f = fig(178, 74); ax = f.add_axes([0.075, 0.16, 0.845, 0.72])
    x = list(range(len(DATES)))
    for k, c, lw in (('brand_all', C['green'], 2.0), ('brand_5060', C['blue'], 1.4),
                     ('brand_2030', C['amber'], 1.4)):
        ax.plot(x, X[k]['series']['메디큐브'], color=c, lw=lw,
                marker='o', ms=2.4 if k == 'brand_all' else 1.7, mfc='white', mec=c, mew=0.8,
                label={'brand_all': '전체', 'brand_5060': '여성 5060', 'brand_2030': '여성 2030'}[k],
                markevery=(0, 3), zorder=4 if k == 'brand_all' else 2)
    style(ax, ymax=112, ymajor=20)
    ax.set_xlim(-1.2, len(x) + 0.8); mticks(ax, DATES, 2)
    ax.legend(loc='upper right', ncol=3, frameon=False, fontsize=FS_LEG, handlelength=1.6,
              columnspacing=1.6, bbox_to_anchor=(1.0, 1.09))
    i_low = DATES.index('2026-07-13'); i_nov = DATES.index('2026-11-02')
    ax.axvspan(i_nov - 0.5, i_nov + 0.5, color=C['mint'], alpha=0.55, zorder=0)
    note(ax, (i_low, 40.5), (i_low - 12, 16), '7/13 저점 40.5', C['gray'])
    bold(ax, i_nov - 0.6, 65, '11/2 52.8', C['green'], fs=6.9)
    bold(ax, 2.2, 103, '시작 주 100', C['green'], fs=6.8)
    ax.set_ylabel(''); save(f, 'c01_search3')


# ── c02 검색 비중 스택(전체)
def c02():
    f = fig(178, 66); ax = f.add_axes([0.055, 0.17, 0.86, 0.70])
    rec = X['brand_all']; x = list(range(len(DATES)))
    base = [0] * len(x)
    import matplotlib.patches as mpatches
    handles = []
    for k in ['메디큐브', '에스트라', '메디힐', '토리든', '넘버즈인']:
        v = share(rec, k)
        ax.fill_between(x, base, [a + b for a, b in zip(base, v)], color=COL[k],
                        lw=0, alpha=1.0)
        base = [a + b for a, b in zip(base, v)]
        handles.append(mpatches.Patch(color=COL[k], label=k))
    style(ax, ymax=100, grid=False)
    ax.set_yticks([0, 25, 50, 75, 100]); ax.set_yticklabels(['0', '25', '50', '75', '100%'])
    ax.set_xlim(0, len(x) - 1); mticks(ax, DATES, 2)
    ax.axvline(DATES.index('2026-04-20'), color='#FFFFFF', lw=0.8, ls=(0, (2, 2)))
    bold(ax, 20, 27.3, '메디큐브', '#FFFFFF', fs=8.6)
    ax.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, -0.09), ncol=5,
              frameon=False, fontsize=6.8, handlelength=1.1, columnspacing=1.8, handletextpad=0.4)
    save(f, 'c02_search_stack')


# ── c03 검색 비중 2030 vs 5060 (최근 13주 평균)
def c03():
    f = fig(90, 62); ax = f.add_axes([0.14, 0.19, 0.83, 0.70])
    ks = ['메디큐브', '에스트라', '메디힐', '토리든', '넘버즈인']
    y = list(range(len(ks)))[::-1]
    a = [mean(share(X['brand_2030'], k)[-13:]) for k in ks]
    b = [mean(share(X['brand_5060'], k)[-13:]) for k in ks]
    h = 0.34
    ax.barh([i + h / 2 for i in y], a, height=h, color=C['amber'], label='여성 2030')
    ax.barh([i - h / 2 for i in y], b, height=h, color=C['green'], label='여성 5060')
    for i, (va, vb) in enumerate(zip(a, b)):
        ax.text(va + 0.9, y[i] + h / 2 + 0.04, f'{va:.1f}', va='bottom', fontsize=6.2, color=C['ink'])
        ax.text(vb + 0.9, y[i] - h / 2 - 0.04, f'{vb:.1f}', va='top', fontsize=6.2, color=C['ink'])
    ax.set_yticks(y); ax.set_yticklabels(ks, fontsize=FS_TICK)
    style(ax, ymax=None)
    ax.set_xlim(0, 58); ax.xaxis.grid(True, color=C['grid'], lw=0.7); ax.set_axisbelow(True)
    ax.tick_params(axis='x', labelsize=FS_TICK, colors='#4B5563', length=2.5, width=0.7, pad=2.5)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False, fontsize=6.6, loc='lower right', handlelength=1.2)
    ax.tick_params(axis='y', length=0)
    save(f, 'c03_search_age')


# ── c04 클릭 지수 라인 (전체 3개 브랜드)
def c04():
    f = fig(178, 62); ax = f.add_axes([0.07, 0.17, 0.85, 0.72])
    x = list(range(len(SDATES)))
    for k, c, lw in (('토리든', C['purple'], 1.5), ('에스트라', C['blue'], 1.5), ('메디큐브', C['green'], 2.1)):
        ax.plot(x, S['shop_all']['series'][k], color=c, lw=lw, marker='o', ms=2.2 if k == '메디큐브' else 1.6,
                mfc='white', mec=c, mew=0.8, label=k, markevery=(0, 3), zorder=4 if k == '메디큐브' else 2)
    style(ax, ymax=112, ymajor=25)
    ax.set_xlim(-1, len(x) + 0.5); mticks(ax, SDATES, 2)
    ax.legend(loc='upper right', ncol=3, frameon=False, fontsize=FS_LEG, handlelength=1.6, bbox_to_anchor=(1.0, 1.10))
    i = S['shop_all']['series']['메디큐브'].index(38)
    bold(ax, i + 1.2, 44, '3/2 38', C['green'])
    bold(ax, 2.0, 14, '시작 5', C['green'])
    save(f, 'c04_click_lines')


# ── c05 검색 vs 클릭 비중 덤벨 (전체, 최근 13주)
def c05():
    f = fig(90, 62); ax = f.add_axes([0.15, 0.19, 0.82, 0.68])
    ks = ['메디큐브', '에스트라', '메디힐', '토리든', '넘버즈인']
    y = list(range(len(ks)))[::-1]
    sep = [mean(share(X['brand_all'], k)[-13:]) for k in ks]
    clk = [mean(share(S['shop_all'], k)[-13:]) for k in ks]
    for i in range(len(ks)):
        ax.plot([clk[i], sep[i]], [y[i], y[i]], color='#CBD5E1', lw=1.4, zorder=1, solid_capstyle='round')
    ax.scatter(clk, y, s=26, color=C['blue'], zorder=3, label='쇼핑 클릭 비중')
    ax.scatter(sep, y, s=26, color=C['green'], zorder=3, label='브랜드 검색 비중')
    for i in range(len(ks)):
        ax.text(max(sep[i], clk[i]) + 1.6, y[i], f'{sep[i] - clk[i]:+.1f}pp', va='center',
                fontsize=6.5, color=C['ink'])
    ax.set_yticks(y); ax.set_yticklabels(ks, fontsize=FS_TICK)
    ax.set_xlim(0, 62); ax.xaxis.grid(True, color=C['grid'], lw=0.7); ax.set_axisbelow(True)
    ax.tick_params(axis='x', labelsize=FS_TICK, colors='#4B5563', length=2.5, width=0.7, pad=2.5)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.legend(frameon=False, fontsize=6.4, loc='lower right', handletextpad=0.4, borderpad=0.2)
    save(f, 'c05_gap_dumbbell')


# ── c06 클릭 비중 2030 vs 5060
def c06():
    f = fig(90, 62); ax = f.add_axes([0.14, 0.19, 0.83, 0.70])
    ks = ['메디큐브', '에스트라', '메디힐', '토리든', '넘버즈인']
    y = list(range(len(ks)))[::-1]
    a = [mean(share(S['shop_2030'], k)[-13:]) for k in ks]
    b = [mean(share(S['shop_5060'], k)[-13:]) for k in ks]
    h = 0.34
    ax.barh([i + h / 2 for i in y], a, height=h, color=C['amber'], label='여성 2030')
    ax.barh([i - h / 2 for i in y], b, height=h, color=C['green'], label='여성 5060')
    for i, (va, vb) in enumerate(zip(a, b)):
        ax.text(va + 0.9, y[i] + h / 2 + 0.04, f'{va:.1f}', va='bottom', fontsize=6.2, color=C['ink'])
        ax.text(vb + 0.9, y[i] - h / 2 - 0.04, f'{vb:.1f}', va='top', fontsize=6.2, color=C['ink'])
    ax.set_yticks(y); ax.set_yticklabels(ks, fontsize=FS_TICK)
    ax.set_xlim(0, 62); ax.xaxis.grid(True, color=C['grid'], lw=0.7); ax.set_axisbelow(True)
    ax.tick_params(axis='x', labelsize=FS_TICK, colors='#4B5563', length=2.5, width=0.7, pad=2.5)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.legend(frameon=False, fontsize=6.6, loc='lower right', handlelength=1.2)
    save(f, 'c06_click_age')


# ── c07 주력 라인 5개 지수(전체)
def c07():
    f = fig(178, 72); ax = f.add_axes([0.07, 0.17, 0.85, 0.72])
    x = list(range(len(DATES)))
    for k in ['부스터 프로', 'PDRN 앰플', '부스터 글로우', '제로모공패드', '부스터 프로 미니']:
        ax.plot(x, X['line_all']['series'][k], color=COL[k], lw=2.0 if k == '부스터 프로' else 1.4,
                marker='o', ms=2.2 if k == '부스터 프로' else 1.5, mfc='white', mec=COL[k], mew=0.7,
                label=LBL[k], markevery=(0, 3), zorder=4 if k == '부스터 프로' else 2)
    style(ax, ymax=112, ymajor=20)
    ax.set_xlim(-1, len(x) + 3.5); mticks(ax, DATES, 2)
    ax.legend(loc='upper right', ncol=3, frameon=False, fontsize=6.8, handlelength=1.5,
              columnspacing=1.3, bbox_to_anchor=(1.0, 1.11))
    ig = DATES.index('2026-04-20')
    ax.axvline(ig, color=C['rose'], lw=0.8, ls=(0, (3, 2)))
    bold(ax, ig + 0.6, 107, '4/20 부스터 글로우 첫 값', C['rose'], fs=6.6)
    i = DATES.index('2026-03-16')
    bold(ax, i - 9.4, 104, '부스터 프로 100 (3/16)', C['green'], fs=6.9)
    i = DATES.index('2026-03-02')
    ax.scatter([i], [75.9], s=18, facecolor='white', edgecolor=C['blue'], lw=0.9, zorder=7)
    i = DATES.index('2026-06-29')
    ax.scatter([i], [35.0], s=18, facecolor='white', edgecolor=C['rose'], lw=0.9, zorder=7)
    save(f, 'c07_line_lines')


# ── c08 라인 비중 2030 vs 5060
def c08():
    f = fig(90, 62); ax = f.add_axes([0.19, 0.19, 0.78, 0.70])
    ks = ['부스터 프로', '부스터 글로우', 'PDRN 앰플', '제로모공패드', '부스터 프로 미니']
    y = list(range(len(ks)))[::-1]
    a = [mean(share(X['line_2030'], k)[-13:]) for k in ks]
    b = [mean(share(X['line_5060'], k)[-13:]) for k in ks]
    h = 0.34
    ax.barh([i + h / 2 for i in y], a, height=h, color=C['amber'], label='여성 2030')
    ax.barh([i - h / 2 for i in y], b, height=h, color=C['green'], label='여성 5060')
    for i, (va, vb) in enumerate(zip(a, b)):
        ax.text(va + 0.7, y[i] + h / 2 + 0.04, f'{va:.1f}', va='bottom', fontsize=6.2, color=C['ink'])
        ax.text(vb + 0.7, y[i] - h / 2 - 0.04, f'{vb:.1f}', va='top', fontsize=6.2, color=C['ink'])
    ax.set_yticks(y); ax.set_yticklabels([LBL[k] for k in ks], fontsize=FS_TICK)
    ax.set_xlim(0, 56); ax.xaxis.grid(True, color=C['grid'], lw=0.7); ax.set_axisbelow(True)
    ax.tick_params(axis='x', labelsize=FS_TICK, colors='#4B5563', length=2.5, width=0.7, pad=2.5)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.legend(frameon=False, fontsize=6.5, loc='lower right', handlelength=1.2)
    save(f, 'c08_line_age')


# ── c09 디바이스 5개 지수(전체)
def c09():
    f = fig(178, 70); ax = f.add_axes([0.07, 0.17, 0.85, 0.72])
    x = list(range(len(DATES)))
    for k in ['마미케어', '메디큐브 에이지알', '톰더글로우', '쿼드쎄라', 'LG 프라엘']:
        ax.plot(x, X['device_all']['series'][k], color=COL[k], lw=2.0 if k == '마미케어' else 1.4,
                marker='o', ms=2.2 if k == '마미케어' else 1.5, mfc='white', mec=COL[k], mew=0.7,
                label=LBL[k], markevery=(0, 3), zorder=4 if k == '마미케어' else 2)
    style(ax, ymax=112, ymajor=20)
    ax.set_xlim(-1, len(x) + 0.8); mticks(ax, DATES, 2)
    ax.legend(loc='upper right', ncol=5, frameon=False, fontsize=6.6, handlelength=1.4,
              columnspacing=1.1, bbox_to_anchor=(1.0, 1.11))
    i = DATES.index('2026-02-16'); j = DATES.index('2025-12-29')
    ax.scatter([i], [100.0], s=26, facecolor='white', edgecolor=C['blue'], lw=1.0, zorder=7)
    ax.scatter([j], [94.6], s=26, facecolor='white', edgecolor=C['amber'], lw=1.0, zorder=7)
    save(f, 'c09_device_lines')


# ── c10 디바이스 비중 2030 vs 5060
def c10():
    f = fig(90, 62); ax = f.add_axes([0.19, 0.19, 0.78, 0.70])
    ks = ['마미케어', '메디큐브 에이지알', '톰더글로우', '쿼드쎄라', 'LG 프라엘']
    y = list(range(len(ks)))[::-1]
    a = [mean(share(X['device_2030'], k)[-13:]) for k in ks]
    b = [mean(share(X['device_5060'], k)[-13:]) for k in ks]
    h = 0.34
    ax.barh([i + h / 2 for i in y], a, height=h, color=C['amber'], label='여성 2030')
    ax.barh([i - h / 2 for i in y], b, height=h, color=C['green'], label='여성 5060')
    for i, (va, vb) in enumerate(zip(a, b)):
        ax.text(va + 0.7, y[i] + h / 2 + 0.04, f'{va:.1f}', va='bottom', fontsize=6.2, color=C['ink'])
        ax.text(vb + 0.7, y[i] - h / 2 - 0.04, f'{vb:.1f}', va='top', fontsize=6.2, color=C['ink'])
    ax.set_yticks(y); ax.set_yticklabels([LBL[k] for k in ks], fontsize=FS_TICK)
    ax.set_xlim(0, 44); ax.xaxis.grid(True, color=C['grid'], lw=0.7); ax.set_axisbelow(True)
    ax.tick_params(axis='x', labelsize=FS_TICK, colors='#4B5563', length=2.5, width=0.7, pad=2.5)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.legend(frameon=False, fontsize=6.5, loc='lower right', handlelength=1.2)
    save(f, 'c10_device_age')


# ── c11 피크 주 타임라인 (상: 검색 지수 / 하: 클릭 지수 + 상위 5주 마커)
def c11():
    f = fig(178, 84)
    ax = f.add_axes([0.07, 0.55, 0.86, 0.37])
    x = list(range(len(DATES)))
    ax.plot(x, X['brand_all']['series']['메디큐브'], color=C['green'], lw=1.8, marker='o', ms=2.0,
            mfc='white', mec=C['green'], mew=0.7, markevery=(0, 3), zorder=3)
    style(ax, ymax=112, ymajor=25)
    ax.set_xlim(-1, len(x) + 0.8); mticks(ax, DATES, 2)
    ax.text(-0.6, 118, '브랜드 검색 지수(전체) — 메디큐브', fontsize=7.2, color=C['ink'])
    tops = ['2026-03-02', '2026-05-04', '2026-06-29', '2026-08-03', '2026-11-02']
    for d in tops:
        i = DATES.index(d); v = X['brand_all']['series']['메디큐브'][i]
        ax.scatter([i], [v], s=42, facecolor='white', edgecolor=C['red'], lw=1.0, zorder=6)
    for d, dy, dyx in (('2026-03-02', 12, -3), ('2026-05-04', 16, -4), ('2026-06-29', 16, -3),
                       ('2026-08-03', 14, -3), ('2026-11-02', 16, -5)):
        i = DATES.index(d); v = X['brand_all']['series']['메디큐브'][i]
        ax.annotate(d[5:].replace('-', '/'), xy=(i, v), xytext=(i + dyx, min(108, v + dy)),
                    fontsize=6.4, color=C['red'], ha='center',
                    arrowprops=dict(arrowstyle='-', color=C['red'], lw=0.6, shrinkB=4))
    ax2 = f.add_axes([0.07, 0.11, 0.86, 0.30])
    xs = list(range(len(SDATES)))
    ax2.plot(xs, S['shop_all']['series']['메디큐브'], color=C['blue'], lw=1.8, marker='o', ms=2.0,
             mfc='white', mec=C['blue'], mew=0.7, markevery=(0, 3), zorder=3)
    style(ax2, ymax=48, ymajor=10)
    ax2.set_xlim(-1, len(xs) + 0.8); mticks(ax2, SDATES, 2)
    ax2.text(-0.6, 50, '쇼핑 클릭 지수(전체) — 메디큐브 (52주)', fontsize=7.2, color=C['ink'])
    for d in ('2026-01-12', '2026-02-23', '2026-03-02', '2026-09-28', '2026-10-26'):
        if d in SDATES:
            i = SDATES.index(d); v = S['shop_all']['series']['메디큐브'][i]
            ax2.scatter([i], [v], s=26, facecolor='none', edgecolor=C['red'], lw=0.9, zorder=5)
    save(f, 'c11_peak_timeline')


# ── c12 검색·클릭 격차(브랜드별, 3세그먼트)
def c12():
    f = fig(178, 62); ax = f.add_axes([0.07, 0.24, 0.86, 0.62])
    ks = ['메디큐브', '에스트라', '메디힐', '토리든', '넘버즈인']
    segs = [('all', '전체'), ('2030', '여성 2030'), ('5060', '여성 5060')]
    w = 0.26
    for j, (seg, lab) in enumerate(segs):
        vals = [N['X'][seg][k]['diff_pp'] for k in ks]
        xs = [i + (j - 1) * w for i in range(len(ks))]
        ax.bar(xs, vals, width=w * 0.92,
               color=[C['ink'], C['amber'], C['green']][j], label=lab,
               zorder=3)
        for xx, vv in zip(xs, vals):
            ax.text(xx, vv + (2.0 if vv >= 0 else -4.0), f'{vv:+.1f}', ha='center', fontsize=5.9,
                    color=C['ink'])
    ax.axhline(0, color='#94A3B8', lw=0.7)
    ax.set_xticks(range(len(ks))); ax.set_xticklabels(ks, fontsize=FS_TICK)
    ax.set_ylim(-48, 48); ax.yaxis.set_major_locator(MultipleLocator(20))
    ax.yaxis.grid(True, color=C['grid'], lw=0.7); ax.set_axisbelow(True)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.legend(frameon=False, fontsize=6.6, ncol=3, loc='upper right', handlelength=1.2,
              bbox_to_anchor=(1.0, 1.14))
    save(f, 'c12_gap_bars')


# 기초 리포트 3부작 도표 복원분 8종 (그림 2-1·2-3·3-1·5-1·5-2·6-1·6-2·7-1)
RESTORED = (c02, c01, c04, c07, c08, c09, c10, c11)

if __name__ == '__main__':
    for fn in RESTORED:
        fn()
        print('done', fn.__name__)
