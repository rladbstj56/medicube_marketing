# -*- coding: utf-8 -*-
"""피크주 대조 보고서 그림 4종 — 메디큐브 레드 팔레트.

work/stage3/charts.py의 값 계산·레이블을 그대로 두고 색만 메디큐브 톤으로 바꾼 판이다.
값은 analysis/task2/chartdata/nums3.json(네이버 데이터랩 원자료에서 재계산된 중간 산출물)에서만
읽고, 결과는 analysis/task2/fig/peak/ 에 SVG로 쓴다. 글자는 모두 path로 굽는다.
"""
import json, os
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import numpy as np
from matplotlib.patches import Rectangle, Patch

HERE = Path(__file__).resolve().parent
for _p in (HERE / 'fonts').glob('*.ttf'):
    fm.fontManager.addfont(str(_p))

OUT = str(HERE / 'fig' / 'peak')
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({'font.family': ['Noto Sans CJK KR', 'Noto Sans KR', 'AppleGothic', 'Malgun Gothic'],
                     'axes.unicode_minus': False, 'svg.fonttype': 'path',
                     'figure.dpi': 100, 'savefig.bbox': 'tight', 'savefig.pad_inches': 0.03})
# 메디큐브 팔레트 — brand=시그니처 레드, 나머지는 차콜·슬레이트 계단(경쟁사·배경)
C=dict(ink='#1F2937',green='#D92B3A',green_d='#9B1B27',green_l='#F08A95',mint='#FDE2E4',
       red='#9B1B27',amber='#64748B',blue='#334155',gray='#8B95A3',gray_l='#CBD5E1',
       grid='#ECECEF',purple='#94A3B8',rose='#E4636F',teal='#CBD5E1')
N=json.load(open(HERE / 'chartdata' / 'nums3.json'))
MM=1/25.4
FS=6.8
BR=['메디큐브','에스트라','메디힐','토리든','넘버즈인']
COL={'메디큐브':C['green'],'에스트라':C['blue'],'메디힐':C['amber'],'토리든':C['purple'],'넘버즈인':C['teal'],
     '마미케어':C['blue'],'톰더글로우':C['amber'],'쿼드쎄라':C['purple'],'LG 프라엘':C['gray']}
SALE={'2025-12-01':'12월 세일','2026-03-02':'3월 세일','2026-06-01':'6월 세일','2026-08-31':'9월 세일','2026-11-02':'블프'}
def fig(w,h): return plt.figure(figsize=(w*MM,h*MM))
def save(f,name):
    """SVG는 보고서용으로 남기고, 눈으로 볼 PNG 미리보기는 gitignore된 tmp/에만 쓴다."""
    f.savefig(f'{OUT}/{name}.svg')
    prev = HERE / 'tmp' / 'figpng'
    prev.mkdir(parents=True, exist_ok=True)
    f.savefig(prev / f'{name}.png', dpi=170)
    plt.close(f)
def dates(): return N['weeks']

def f1():
    D=N['weeks']; n=len(D)
    M=np.full((len(BR),n),np.nan)
    for i,b in enumerate(BR):
        w=N['series'][f'brand_all|{b}']['wow']
        for j in range(n):
            if w[j] is not None: M[i,j]=w[j]
    f=fig(176,52); ax=f.add_subplot(111)
    cmap=matplotlib.colors.LinearSegmentedColormap.from_list('r',[C['blue'],'#F5F6F8',C['green']])
    M2=np.clip(M,-60,60)
    im=ax.imshow(M2,aspect='auto',cmap=cmap,vmin=-60,vmax=60,interpolation='nearest')
    for j,dt in enumerate(D):
        if dt in SALE:
            ax.add_patch(Rectangle((j-0.5,-0.5),1,len(BR),fill=False,ec=C['red'],lw=0.9,ls=(0,(2,1.2))))
    for j,dt in enumerate(['2026-11-02','2026-08-03','2026-05-04','2026-03-02','2026-06-29']):
        if dt in D:
            jj=D.index(dt); ax.plot(jj,0,'o',mfc='none',mec=C['ink'],ms=3.4,mew=0.8)
    ax.set_yticks(range(len(BR))); ax.set_yticklabels(BR,fontsize=FS)
    idx=[j for j in range(n) if j%4==0]
    ax.set_xticks(idx); ax.set_xticklabels([D[j][2:] for j in idx],fontsize=FS-0.4,rotation=0)
    ax.tick_params(length=0)
    for s in ax.spines.values(): s.set_color(C['gray_l'])
    cb=f.colorbar(im,ax=ax,pad=0.006,fraction=0.014)
    cb.ax.tick_params(labelsize=FS-0.8,length=0)
    ax.set_xlabel('전주 대비 상승률(%), 오른쪽 막대 = −60~+60에서 자름 · 점선 빨강 = 올리브영 정기 세일 주 · ○ = 메디큐브 피크 주 Top5',fontsize=FS-0.3,labelpad=2)
    save(f,'f1_heatmap')

def f2():
    D=N['weeks']; f=fig(176,56); ax=f.add_subplot(111)
    for dt in SALE:
        if dt in D:
            j=D.index(dt); ax.axvspan(j-0.5,j+0.5,color=C['red'],alpha=0.07,lw=0)
    s=N['series']['brand_all|메디큐브']
    ax.plot(range(len(D)),s['val'],color=C['green'],lw=1.5,zorder=3)
    for name,dt,txt,dy in [('X2','2026-03-23','부스터프로 X2\n출시 3/23',-26),('GL','2026-05-04','부스터글로우\n올영 5/1',22)]:
        if dt in D:
            j=D.index(dt); v=s['val'][j]
            ax.annotate(txt,(j,v),xytext=(j,v+dy),fontsize=FS-1,ha='center',color=C['ink'],
                        arrowprops=dict(arrowstyle='-',color=C['gray'],lw=0.6))
    for dt in SALE:
        if dt in D:
            j=D.index(dt); ax.text(j,103,SALE[dt],fontsize=FS-1.4,ha='center',color=C['red'])
    ax.set_ylim(0,110); ax.set_xlim(-0.5,len(D)-0.5)
    idx=[j for j in range(len(D)) if j%4==0]
    ax.set_xticks(idx); ax.set_xticklabels([D[j][2:] for j in idx],fontsize=FS-0.5)
    ax.set_ylabel('메디큐브 브랜드 검색 지수(파일 내 100 정규화)',fontsize=FS-0.4)
    for s_ in ('top','right'): ax.spines[s_].set_visible(False)
    ax.grid(axis='y',color=C['grid'],lw=0.5); ax.tick_params(length=0,labelsize=FS-0.5)
    save(f,'f2_timeline')

def f3():
    D=N['weeks']; f=fig(176,70); ax=f.add_subplot(111)
    for dt in SALE:
        if dt in D:
            j=D.index(dt); ax.axvspan(j-0.5,j+0.5,color=C['red'],alpha=0.06,lw=0)
    rows=['메디큐브']+BR[1:]+['마미케어','톰더글로우','쿼드쎄라','LG 프라엘']
    lab=[]
    for i,b in enumerate(rows):
        if b=='메디큐브':
            for dt in ['2026-11-02','2026-08-03','2026-05-04','2026-03-02','2026-06-29']:
                j=D.index(dt)
                ax.plot(j,i,marker='v',ms=4.6,mfc=C['green'],mec=C['green'],ls='',zorder=4)
                ax.annotate(dt[5:].replace('-','/'),(j,i),xytext=(0,7),textcoords='offset points',
                            fontsize=FS-1.6,ha='center',color=C['green'])
            continue
        items=N['sk'].get(b) if b in N['sk'] else N['dv'].get(b)
        for k,it in enumerate(items):
            if it['week'] not in D: continue
            j=D.index(it['week'])
            mx=max([x[1] for x in it['c20']],default=0)
            co = N['med_top5'].get(it['week']) is not None
            col=COL.get(b,C['gray'])
            ax.scatter(j,i,s=14+it['score']*3.2,facecolor=col if co else 'white',edgecolor=col,lw=1.0,zorder=3,alpha=0.95)
            ax.annotate(it['week'][5:].replace('-','/'),(j,i),xytext=(0,8),textcoords='offset points',
                        fontsize=FS-1.3,ha='center',color=C['ink'] if co else C['gray'])
    ax.set_yticks(range(len(rows))); ax.set_yticklabels(rows,fontsize=FS)
    ax.set_ylim(len(rows)-0.3,-1.1); ax.set_xlim(-0.5,len(D)-0.5)
    idx=[j for j in range(len(D)) if j%4==0]
    ax.set_xticks(idx); ax.set_xticklabels([D[j][2:] for j in idx],fontsize=FS-0.5)
    ax.grid(axis='y',color=C['grid'],lw=0.5); ax.tick_params(length=0)
    for s_ in ('top','right'): ax.spines[s_].set_visible(False)
    ax.legend(handles=[plt.Line2D([],[],marker='v',ls='',mfc=C['green'],mec=C['green'],ms=4.6,label='메디큐브 피크 주 Top5'),
                       plt.Line2D([],[],marker='o',ls='',mfc=C['green'],mec=C['green'],ms=5,label='같은 주에 함께 급등'),
                       plt.Line2D([],[],marker='o',ls='',mfc='white',mec=C['gray'],ms=5,label='단독 급등')],
              fontsize=FS-1.6,frameon=False,loc='lower center',bbox_to_anchor=(0.5,1.01),ncol=3,handletextpad=0.3,columnspacing=1.6)
    save(f,'f3_peakmap')

def f4():
    D=N['weeks']; ev=[('2025-12-01','12월 올영세일'),('2026-03-02','3월 올영세일'),('2026-06-01','6월 올영세일'),
                      ('2026-08-31','9월 올영세일'),('2026-11-02','올영 블랙프라이데이')]
    f=fig(176,50); ax=f.add_subplot(111)
    w=0.15; x=np.arange(len(ev))
    for i,b in enumerate(BR):
        vals=[]
        for dt,_ in ev:
            r=N['events'][dt]['brand'].get(b,{})
            v=r.get('brand_all')
            vals.append(np.nan if v is None else v)
        ax.bar(x+(i-2)*w,vals,w*0.92,label=b,color=COL[b],alpha=0.92)
    ax.axhline(0,color=C['ink'],lw=0.7)
    ax.set_xticks(x); ax.set_xticklabels([f'{a}\n{b}' for a,b in ev],fontsize=FS-0.6)
    ax.set_ylabel('브랜드 검색(전체) 전주 대비 %',fontsize=FS-0.4)
    ax.set_ylim(-52,44)
    ax.legend(fontsize=FS-0.8,frameon=False,ncol=5,loc='lower center',bbox_to_anchor=(0.5,1.0))
    for s_ in ('top','right'): ax.spines[s_].set_visible(False)
    ax.grid(axis='y',color=C['grid'],lw=0.5); ax.tick_params(length=0,labelsize=FS-0.5)
    save(f,'f4_saleweeks')

def f5():
    brands=['메디큐브','에스트라','메디힐','토리든','넘버즈인','마미케어']
    val=[650,59,210,66,100,710]
    f=fig(176,40); ax=f.add_subplot(111)
    y=np.arange(len(brands))
    col=[C['green'],C['blue'],C['amber'],C['purple'],C['gray_l'],C['gray']]
    ax.barh(y,val,color=col,height=0.62)
    for i,v in enumerate(val):
        if v: ax.text(v+12,i,f'{v}건',va='center',fontsize=FS-0.4,color=C['ink'])
    ax.set_yticks(y); ax.set_yticklabels(brands,fontsize=FS-0.8); ax.invert_yaxis()
    ax.set_xlim(0,800); ax.set_xlabel('키워드 일치 활성 광고 수(건, 2026-11-20 04:4x KST)',fontsize=FS-0.6)
    for s_ in ('top','right'): ax.spines[s_].set_visible(False)
    ax.tick_params(length=0,labelsize=FS-0.6)
    save(f,'f5_ads')

# 복원 대상 4종 (그림 3-1·4-1·4-2·7-1). f2 타임라인은 현행 보고서에 캡션이 없어 뺐다.
FIGURES = (f1, f3, f4, f5)

if __name__ == '__main__':
    for _fn in FIGURES:
        _fn()
        print('ok', _fn.__name__)
