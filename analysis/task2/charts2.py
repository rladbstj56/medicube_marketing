# -*- coding: utf-8 -*-
"""Task 2 보고서 SVG 차트 8종. 값은 work/task2/num2.json 에서만 읽는다.

색은 메디큐브 톤(시그니처 레드 + 차콜·슬레이트)만 쓴다. 초록 계열은 쓰지 않는다.
"""
import json, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import matplotlib.patheffects as pe

OUT = 'work/task2/fig'
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({
    'font.family': 'Noto Sans CJK KR', 'axes.unicode_minus': False, 'svg.fonttype': 'path',
    'figure.dpi': 100, 'savefig.bbox': 'tight', 'savefig.pad_inches': 0.03,
})
# 메디큐브 팔레트 — brand=시그니처 레드, slate=차콜·슬레이트 보조
C = dict(ink='#1F2937', brand='#D92B3A', brand_d='#9B1B27', brand_l='#F08A95', tint='#FDE2E4',
         slate='#64748B', slate_d='#334155', gray='#8B95A3', gray_l='#CBD5E1',
         grid='#ECECEF', deep='#1F2937', note='#4B5563')
TXT = '#4B5563'      # 축·주석 기본 글자색 (차콜 그레이)
MM = 1 / 25.4
FS_TICK, FS_LEG, FS_ANN = 7.0, 6.8, 6.6
N = json.load(open('work/task2/num2.json'))


def fig(w, h):
    return plt.figure(figsize=(w * MM, h * MM))


def style(ax, grid=True, xgrid=False):
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color('#CBD5E1'); ax.spines[s].set_linewidth(0.7)
    ax.tick_params(colors=TXT, labelsize=FS_TICK, length=2.5, width=0.7, pad=2.5)
    if grid:
        ax.grid(True, axis='y', color=C['grid'], lw=0.7, zorder=0); ax.set_axisbelow(True)
    if xgrid:
        ax.grid(True, axis='x', color=C['grid'], lw=0.7, zorder=0); ax.set_axisbelow(True)


def save(f, name):
    f.savefig(f'{OUT}/{name}.svg', format='svg', transparent=True)
    plt.close(f)


# ── f1 검색−클릭 간격 (브랜드 × 세그먼트)
def f1():
    br = ['메디큐브', '에스트라', '메디힐', '토리든', '넘버즈인']
    segs = [('전체', 'brand_all', C['brand_d']), ('2030', 'brand_2030', C['brand']), ('5060', 'brand_5060', C['brand_l'])]
    f = fig(168, 58); ax = f.add_subplot(111)
    h = 0.26
    for j, (lab, key, col) in enumerate(segs):
        vals = [N['share'][key][b]['gap'] for b in br]
        ys = [i + (j - 1) * h for i in range(len(br))]
        ax.barh(ys, vals, height=h * 0.9, color=col, label=lab, zorder=3)
        for y, v in zip(ys, vals):
            ax.text(v + (0.6 if v >= 0 else -0.6), y, f'{v:+.1f}', va='center',
                    ha='left' if v >= 0 else 'right', fontsize=5.9, color=TXT)
    ax.axvline(0, color=C['gray'], lw=0.8)
    ax.set_yticks(range(len(br))); ax.set_yticklabels(br, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel('데이터랩 브랜드 검색 비중 − 쇼핑인사이트 스킨케어 클릭 비중 (p.p.)', fontsize=6.4, color=TXT)
    ax.set_xlim(-44, 44)
    style(ax, xgrid=True, grid=False)
    ax.legend(frameon=False, fontsize=FS_LEG, loc='lower right', ncol=3, handlelength=1.0, columnspacing=1.2)
    save(f, 'f1_gap')


# ── f2 2030 스킨케어 클릭 비중
def f2():
    br = ['메디큐브', '에스트라', '메디힐', '토리든', '넘버즈인']
    f = fig(84, 52); ax = f.add_subplot(111)
    vals = [N['share']['shop_2030'][b]['recent'] for b in br]
    cols = [C['brand'] if b == '메디큐브' else C['gray_l'] for b in br]
    bars = ax.bar(br, vals, color=cols, width=0.62, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.2, f'{v:.1f}%', ha='center', fontsize=6.8,
                color=C['brand'] if v == max(vals) else TXT,
                fontweight='bold' if v == min(vals) or v == max(vals) else 'normal')
    ax.set_ylim(0, 54)
    style(ax)
    ax.text(0.5, -0.22, '메디큐브 4위 9.3%  ·  1위 토리든 46.3%의 5.0분의 1', transform=ax.transAxes,
            ha='center', fontsize=6.2, color=C['brand_d'])
    save(f, 'f2_click2030')


# ── f3 미니 지수 54주
def f3():
    d = N['series']['line_dates']; allv = N['series']['mini_idx']; v30 = N['series']['mini_idx_2030']
    f = fig(168, 27); ax = f.add_subplot(111)
    ax.plot(range(len(d)), allv, color=C['brand'], lw=1.3, label='전체', zorder=3)
    ax.plot(range(len(d)), v30, color=C['slate'], lw=1.1, ls=(0, (4, 2)), label='여성 2030', zorder=3)
    ax.fill_between(range(len(d)), allv, color=C['tint'], alpha=0.55, zorder=1)
    pi = allv.index(max(allv))
    ax.plot([pi], [allv[pi]], 'o', ms=4, mfc='white', mec=C['brand_d'], mew=1.0, zorder=4)
    ax.annotate(f'연중 최고 {allv[pi]:.1f}\n({d[pi]})', xy=(pi, allv[pi]), xytext=(pi + 3.0, allv[pi] + 1.0),
                fontsize=6.3, color=C['brand_d'], va='center',
                arrowprops=dict(arrowstyle='-', lw=0.6, color=C['gray']))
    ax.annotate(f'마지막 주 {allv[-1]:.1f}', xy=(len(d) - 1, allv[-1]), xytext=(len(d) - 16, 7.0),
                fontsize=6.3, color=C['brand_d'],
                arrowprops=dict(arrowstyle='->', lw=0.6, color=C['brand_d']))
    ticks = [i for i in range(0, len(d), 6)]
    ax.set_xticks(ticks); ax.set_xticklabels([d[i][2:4] + '.' + d[i][5:7] for i in ticks], fontsize=6.0)
    ax.set_ylim(0, 22)
    style(ax)
    ax.legend(frameon=False, fontsize=FS_LEG, loc='upper right', ncol=2, handlelength=1.4)
    save(f, 'f3_mini')


# ── f4 라인 안 미니 비중 3세그먼트 + 프로 대비
def f4():
    segs = [('전체', 'all'), ('2030', '2030'), ('5060', '5060')]
    f = fig(84, 32); ax = f.add_subplot(111)
    vals = [N['line']['부스터 프로 미니'][k]['share_recent'] for _, k in segs]
    bars = ax.bar([s for s, _ in segs], vals, color=[C['gray_l'], C['brand'], C['slate']], width=0.55, zorder=3)
    for b, v, (s, k) in zip(bars, vals, segs):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.10, f'{v:.1f}%', ha='center', fontsize=7,
                color=C['deep'], fontweight='bold')
    ax.set_ylim(0, 4.0)
    style(ax)
    save(f, 'f4_minishare')


# ── f5 5060 vs 2030 브랜드 검색 WoW (이벤트 7주)
def f5():
    keys = list(N['events'].keys())
    lab = ['12/29', '2/16', '3/2', '5/4', '6/29', '8/3', '11/2']
    v50 = [N['events'][k]['brand_5060_wow'] for k in keys]
    v30 = [N['events'][k]['brand_2030_wow'] for k in keys]
    f = fig(168, 48); ax = f.add_subplot(111)
    x = range(len(keys)); w = 0.36
    ax.bar([i - w / 2 for i in x], v50, width=w, color=C['brand'], label='5060', zorder=3)
    ax.bar([i + w / 2 for i in x], v30, width=w, color=C['slate'], label='2030', zorder=3)
    for i, (a, b) in enumerate(zip(v50, v30)):
        ax.text(i - w / 2, a + (0.9 if a >= 0 else -2.6), f'{a:+.1f}', ha='center', fontsize=6.0,
                color=C['brand_d'], va='bottom' if a >= 0 else 'top')
        ax.text(i + w / 2, b + (0.9 if b >= 0 else -2.6), f'{b:+.1f}', ha='center', fontsize=6.0,
                color=C['slate_d'], va='bottom' if b >= 0 else 'top')
    ax.axhline(0, color=C['gray'], lw=0.8)
    ax.set_xticks(list(x)); ax.set_xticklabels(lab, fontsize=6.8)
    ax.set_ylim(-16, 42)
    style(ax)
    ax.legend(frameon=False, fontsize=FS_LEG, loc='upper left', ncol=2, handlelength=1.2)
    save(f, 'f5_gift')


# ── f6 5060 디바이스 비중 54주 (에이지알·프라엘·마미케어)
def f6():
    d = N['series']['dev5060_dates']
    a = N['series']['dev5060_ageal']; p = N['series']['dev5060_prael']; m = N['series']['dev5060_mommy']
    f = fig(168, 28); ax = f.add_subplot(111)
    ax.plot(range(len(d)), m, color=C['slate'], lw=1.0, label='마미케어', zorder=3)
    ax.plot(range(len(d)), a, color=C['brand'], lw=1.4, label='메디큐브 에이지알', zorder=4)
    ax.plot(range(len(d)), p, color=C['gray'], lw=1.0, ls=(0, (3, 2)), label='LG 프라엘', zorder=3)
    for dt, num in [('2026-05-04', '①'), ('2026-11-02', '②')]:
        i = d.index(dt)
        ax.plot([i], [a[i]], 'o', ms=4.6, mfc='white', mec=C['brand_d'], mew=1.2, zorder=5)
        ax.text(i, a[i] + 1.4, num, fontsize=7.0, color=C['brand_d'], ha='center', va='bottom', zorder=6)
    ticks = [i for i in range(0, len(d), 6)]
    ax.set_xticks(ticks); ax.set_xticklabels([d[i][2:4] + '.' + d[i][5:7] for i in ticks], fontsize=6.0)
    ax.set_ylim(0, 40)
    style(ax)
    ax.legend(frameon=False, fontsize=FS_LEG, loc='upper left', ncol=3, handlelength=1.4, columnspacing=1.4)
    save(f, 'f6_dev5060')


# ── f7 라인 구성 2030 vs 5060
def f7():
    lines = ['부스터 프로', '부스터 글로우', 'PDRN 앰플', '제로모공패드', '부스터 프로 미니']
    lab = ['부스터 프로', '부스터 글로우', 'PDRN 앰플', '제로모공패드', '미니']
    f = fig(168, 20); ax = f.add_subplot(111)
    x = range(len(lines)); w = 0.36
    v30 = [N['line'][k]['2030']['share_recent'] for k in lines]
    v50 = [N['line'][k]['5060']['share_recent'] for k in lines]
    ax.bar([i - w / 2 for i in x], v30, width=w, color=C['slate'], label='여성 2030', zorder=3)
    ax.bar([i + w / 2 for i in x], v50, width=w, color=C['brand'], label='여성 5060', zorder=3)
    for i, (a, b) in enumerate(zip(v30, v50)):
        ax.text(i - w / 2, a + 0.7, f'{a:.1f}', ha='center', fontsize=6.2, color=C['slate_d'])
        ax.text(i + w / 2, b + 0.7, f'{b:.1f}', ha='center', fontsize=6.2, color=C['brand_d'])
    ax.set_xticks(list(x)); ax.set_xticklabels(lab, fontsize=6.8)
    ax.set_ylim(0, 58)
    style(ax)
    ax.legend(fontsize=5.8, loc='upper right', ncol=2, handlelength=1.0, columnspacing=1.0, framealpha=0.92, edgecolor='#E4E4E7')
    save(f, 'f7_line')


# ── f8 시즌 캘린더
def f8():
    f = fig(168, 40); ax = f.add_subplot(111)
    ax.set_xlim(0, 12); ax.set_ylim(0, 4)
    ax.axis('off')
    ax.plot([0.3, 11.7], [2.0, 2.0], color='#E4E4E7', lw=1.4, solid_capstyle='round', zorder=1)
    for m in range(1, 13):
        ax.plot([m - 0.5], [2.0], '|', ms=5, color='#CBD5E1', zorder=2)
        ax.text(m - 0.5, 1.72, f'{m}월', ha='center', fontsize=6.0, color=C['gray'])
    ev = [
        (3.05, '올영 세일\n3/1~3/7', 0.55, C['slate']),
        (5.10, '글로우 선출시 5/1\n어버이날 5/8', 1.05, C['brand_d']),
        (5.30, 'GS샵 X2\n홈쇼핑 5/9', -0.55, C['slate_d']),
        (8.15, '11주년 대감사제\n8/3~8/24', 0.55, C['brand']),
        (11.10, '블프 11/1~11/7\n(5060 디바이스 비중 최고)', 1.05, C['brand_d']),
    ]
    for x, txt, dy, col in ev:
        ax.plot([x], [2.0], 'o', ms=5, mfc='white', mec=col, mew=1.4, zorder=4)
        y = 2.0 + dy
        ax.plot([x, x], [2.0, y], color=col, lw=0.6, zorder=2)
        ax.text(x, y + (0.18 if dy > 0 else -0.18), txt, ha='center', va='bottom' if dy > 0 else 'top',
                fontsize=6.1, color=col, linespacing=1.35)
    save(f, 'f8_calendar')


for fn in (f1, f2, f3, f4, f5, f6, f7, f8):
    fn()
print('ok', sorted(os.listdir(OUT)))
