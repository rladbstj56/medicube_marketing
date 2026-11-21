# -*- coding: utf-8 -*-
"""14쪽 포트폴리오 PDF·MD 생성기 — 에디토리얼/광고 덱 조판.

구성안(`reports/메디큐브_콘텐츠마케팅_포트폴리오_구성안.md` v1.5)의 페이지별 설계를
한 곳(PAGES)에 적고, 같은 데이터에서 PDF와 MD를 함께 만든다. 두 파일이 서로
어긋날 수 없게 하려는 것이며, 값은 모두 저장소 현행 문서에서 그대로 옮겼다.

조판 방향(2026-11-22 사용자 지시):
- 보고서가 아니라 브랜드 캠페인 제안서처럼 — 넉넉한 여백, 큰 한 줄 메시지,
  굵은 숫자 KPI 3개, 0.5pt 헤어라인, 절제된 레드·크림슨·블러시·차콜.
- 회색 박스·표 남발을 줄이고, 4·9·13쪽은 제품 사진 시안이 주인공이 되게 배치.
- 8·12쪽 CRM은 긴 설명 대신 짧은 메시지 카드(온사이트 배너·앱푸시·스냅푸시)로.

이 환경에는 WeasyPrint가 쓰는 libpango가 없어 기존 `build2.py` 경로를 쓸 수 없다.
저장소에 동봉한 Noto Sans KR 두 굵기와 reportlab으로 직접 조판한다. 쪽수는 각 쪽
블록의 높이를 재서 넘칠 때 빌드를 멈추므로 정확히 14쪽이 된다.
"""

import re
import sys
from pathlib import Path

import pymupdf
from PIL import Image as PILImage
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Flowable, Paragraph, Table, TableStyle

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT_PDF = ROOT / 'reports/메디큐브_콘텐츠마케팅_포트폴리오.pdf'
OUT_MD = ROOT / 'reports/메디큐브_콘텐츠마케팅_포트폴리오.md'
TMP = ROOT / 'tmp/portfolio'

# ── 팔레트 ──────────────────────────────────────────────────────────────────
CRIMSON = HexColor('#9B1B27')
RED = HexColor('#D92B3A')
BLUSH = HexColor('#FDF8F9')
INK = HexColor('#1F2937')
MUTE = HexColor('#8A8F98')
HAIR = HexColor('#E6DFE1')
PALE = HexColor('#C9BFC1')
WHITE = HexColor('#FFFFFF')

FONT, BOLD = 'NotoKR', 'NotoKR-Bold'
pdfmetrics.registerFont(TTFont(FONT, str(HERE / 'fonts/NotoSansKR-Regular.ttf')))
pdfmetrics.registerFont(TTFont(BOLD, str(HERE / 'fonts/NotoSansKR-Bold.ttf')))
pdfmetrics.registerFontFamily(FONT, normal=FONT, bold=BOLD, italic=FONT, boldItalic=BOLD)

PAGE_W, PAGE_H = A4
M = 52.0                       # 좌우 여백
CW = PAGE_W - 2 * M            # 본문 폭
GAP = 11.0                     # 블록 사이 기본 간격
BODY_BOTTOM = 58.0             # 본문 하한
TOTAL_PAGES = 14

ST = {
    'body': ParagraphStyle('body', fontName=FONT, fontSize=8.4, leading=13.2,
                           textColor=INK, wordWrap=None),
    'deck': ParagraphStyle('deck', fontName=FONT, fontSize=8.9, leading=13.6,
                           textColor=MUTE, wordWrap=None),
    'note': ParagraphStyle('note', fontName=FONT, fontSize=6.8, leading=10.2,
                           textColor=MUTE, wordWrap=None),
    'th': ParagraphStyle('th', fontName=BOLD, fontSize=6.6, leading=9.8,
                         textColor=CRIMSON, wordWrap=None),
    'td': ParagraphStyle('td', fontName=FONT, fontSize=7.2, leading=10.9,
                         textColor=INK, wordWrap=None),
    'caption': ParagraphStyle('caption', fontName=FONT, fontSize=6.4, leading=9.3,
                              textColor=MUTE, wordWrap=None),
    'h2': ParagraphStyle('h2', fontName=BOLD, fontSize=9.4, leading=13.0,
                         textColor=INK, wordWrap=None),
    'kv': ParagraphStyle('kv', fontName=BOLD, fontSize=25, leading=27,
                         textColor=CRIMSON, wordWrap=None),
    'kv_s': ParagraphStyle('kv_s', fontName=BOLD, fontSize=15, leading=19,
                           textColor=CRIMSON, wordWrap=None),
    'kv_xs': ParagraphStyle('kv_xs', fontName=BOLD, fontSize=11.6, leading=16,
                            textColor=CRIMSON, wordWrap=None),
    'kl': ParagraphStyle('kl', fontName=FONT, fontSize=6.8, leading=10.0,
                         textColor=MUTE, wordWrap=None),
    'tag': ParagraphStyle('tag', fontName=BOLD, fontSize=7.2, leading=10.4,
                          textColor=CRIMSON, wordWrap=None),
    'quote': ParagraphStyle('quote', fontName=FONT, fontSize=8.4, leading=13.2,
                            textColor=INK, wordWrap=None),
    'qlabel': ParagraphStyle('qlabel', fontName=BOLD, fontSize=6.2, leading=9.0,
                              textColor=CRIMSON, wordWrap=None),
    'msgch': ParagraphStyle('msgch', fontName=BOLD, fontSize=5.9, leading=8.6,
                            textColor=CRIMSON, wordWrap=None),
    'msgtitle': ParagraphStyle('msgtitle', fontName=BOLD, fontSize=8.2, leading=11.6,
                               textColor=INK, wordWrap=None),
    'msgbody': ParagraphStyle('msgbody', fontName=FONT, fontSize=7.0, leading=10.4,
                              textColor=INK, wordWrap=None),
    'msgmeta': ParagraphStyle('msgmeta', fontName=FONT, fontSize=6.1, leading=9.0,
                              textColor=MUTE, wordWrap=None),
    'step': ParagraphStyle('step', fontName=BOLD, fontSize=7.6, leading=10.6,
                           textColor=INK, wordWrap=None),
    'stepsub': ParagraphStyle('stepsub', fontName=FONT, fontSize=6.9, leading=10.0,
                              textColor=MUTE, wordWrap=None),
    'arrow': ParagraphStyle('arrow', fontName=FONT, fontSize=9, leading=12,
                            textColor=PALE, alignment=1),
}

LABELS = ('관측', '해석', '실행 제안', '제작물', '예정', '일부 제작', '내부 검토용',
          '보완 예정', '미집행', '없는 자료', '미확인', '승인 전 콘셉트')


def esc(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def md(text):
    """본문 표기를 Paragraph 마크업으로 바꾼다.

    `**…**`는 굵게, 라벨 대괄호는 메디큐브 레드로 표시한다. 꺾쇠·앰퍼샌드는 먼저
    이스케이프해 태그로 읽히지 않게 한다.
    """
    text = esc(text)
    text = re.sub(r'`([^`]+)`', r'<font color="#8A8F98">\1</font>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    for label in LABELS:
        text = text.replace(f'[{label}]', f'<font color="#D92B3A">[{label}]</font>')
    return text


def md_key(text):
    """큰 한 줄 메시지 — 강조는 크림슨으로."""
    text = esc(text)
    return re.sub(r'\*\*(.+?)\*\*', r'<font color="#9B1B27"><b>\1</b></font>', text)


def P(text, style='body'):
    return Paragraph(md(text), ST[style])


# ── 블록 ────────────────────────────────────────────────────────────────────


class Hair(Flowable):
    """0.5pt 헤어라인."""

    def __init__(self, width=CW, color=HAIR, lw=0.5):
        super().__init__()
        self.w, self.color, self.lw = width, color, lw

    def wrap(self, aw, ah):
        self.width = min(self.w, aw)
        self.height = 0.5
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setStrokeColor(self.color)
        c.setLineWidth(self.lw)
        c.line(0, 0.25, self.width, 0.25)


class Spacer(Flowable):
    def __init__(self, h):
        super().__init__()
        self.h = h

    def wrap(self, aw, ah):
        return 0, self.h

    def draw(self):
        pass


class Lead(Flowable):
    """쪽의 한 줄 메시지. 위에 짧은 크림슨 선을 둔다."""

    def __init__(self, text, size=15.0):
        super().__init__()
        self.par = Paragraph(md_key(text), ParagraphStyle(
            'lead', fontName=BOLD, fontSize=size, leading=size * 1.5, textColor=INK))

    def wrap(self, aw, ah):
        self.width = aw
        self.tw, self.th = self.par.wrap(aw, 240)
        self.height = self.th + 13
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(RED)
        c.rect(0, self.height - 2.0, 20, 2.0, stroke=0, fill=1)
        self.par.drawOn(c, 0, 0)


class Head(Flowable):
    """작은 섹션 제목 + 헤어라인."""

    def __init__(self, text):
        super().__init__()
        self.par = Paragraph(md(text), ST['h2'])

    def wrap(self, aw, ah):
        self.width = aw
        self.tw, self.th = self.par.wrap(aw - 10, 80)
        self.height = self.th + 8
        return self.width, self.height

    def draw(self):
        c = self.canv
        self.par.drawOn(c, 0, 8)
        c.setStrokeColor(CRIMSON)
        c.setLineWidth(1.6)
        c.line(0, 1.2, 10, 1.2)
        c.setStrokeColor(HAIR)
        c.setLineWidth(0.5)
        c.line(14, 1.2, self.width, 1.2)


class KPI(Flowable):
    """굵은 숫자 3개 — 위 헤어라인과 열 구분선만."""

    def __init__(self, items, width=CW):
        super().__init__()
        self.items = items
        self.total = width

    def wrap(self, aw, ah):
        self.width = min(self.total, aw)
        self.colw = self.width / len(self.items)
        self.cells = []
        for value, label in self.items:
            size = 'kv' if len(value) <= 5 else ('kv_s' if len(value) <= 9 else 'kv_xs')
            vp = Paragraph(md(value), ST[size])
            lp = Paragraph(md(label), ST['kl'])
            vw, vh = vp.wrap(self.colw - 14, 60)
            lw, lh = lp.wrap(self.colw - 14, 60)
            self.cells.append((vp, lp, vh, lh))
        self.height = 7 + max(c[2] for c in self.cells) + 3 + max(c[3] for c in self.cells) + 6
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setStrokeColor(CRIMSON)
        c.setLineWidth(0.5)
        c.line(0, self.height - 0.25, self.width, self.height - 0.25)
        for i, (vp, lp, vh, lh) in enumerate(self.cells):
            x = i * self.colw
            if i:
                c.setStrokeColor(HAIR)
                c.line(x - 7, 2, x - 7, self.height - 12)
            top = self.height - 7
            vp.drawOn(c, x, top - vh)
            lp.drawOn(c, x, 5)


class Tag(Flowable):
    """한 줄 상태 표기 — 크림슨 사각점 + 작은 글씨."""

    def __init__(self, text):
        super().__init__()
        self.par = Paragraph(md(text), ST['tag'])

    def wrap(self, aw, ah):
        self.width = aw
        self.tw, self.th = self.par.wrap(aw - 12, 40)
        self.height = self.th + 2
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(RED)
        c.rect(0, self.height - 7.2, 3.2, 3.2, stroke=0, fill=1)
        self.par.drawOn(c, 10, 1)


class Quote(Flowable):
    """왼쪽 얇은 크림슨 선 하나로만 구분하는 인용·질문 블록."""

    def __init__(self, text, label=None):
        super().__init__()
        self.par = Paragraph(md(text), ST['quote'])
        self.lab = Paragraph(md(label), ST['qlabel']) if label else None

    def wrap(self, aw, ah):
        self.width = aw
        inner = aw - 14
        self.th = self.par.wrap(inner, 200)[1]
        self.lh = self.lab.wrap(inner, 20)[1] + 3 if self.lab else 0
        self.height = self.th + self.lh + 2
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setStrokeColor(CRIMSON)
        c.setLineWidth(1.1)
        c.line(0, 1, 0, self.height - 1)
        y = self.height - self.lh
        if self.lab:
            self.lab.drawOn(c, 10, y)
        self.par.drawOn(c, 10, 0)


class Fig(Flowable):
    """이미지 + 얇은 캡션."""

    def __init__(self, path, width, caption=None, center=False):
        super().__init__()
        self.path = str(path)
        self.target_w = width
        self.center = center
        self.avail = width
        self.caption = Paragraph(md(caption), ST['caption']) if caption else None
        with PILImage.open(self.path) as im:
            self.ratio = im.width / im.height

    def wrap(self, aw, ah):
        self.avail = aw
        self.img_w = min(self.target_w, aw)
        self.img_h = self.img_w / self.ratio
        self.cap_h = 0
        if self.caption:
            _, self.cap_h = self.caption.wrap(self.img_w, 200)
            self.cap_h += 4
        self.width, self.height = self.img_w, self.img_h + self.cap_h
        return self.width, self.height

    def draw(self):
        c = self.canv
        ox = (self.avail - self.img_w) / 2 if self.center else 0
        c.drawImage(self.path, ox, self.cap_h, self.img_w, self.img_h,
                    preserveAspectRatio=True, anchor='c', mask='auto')
        c.setStrokeColor(HAIR)
        c.setLineWidth(0.4)
        c.rect(ox, self.cap_h, self.img_w, self.img_h, stroke=1, fill=0)
        if self.caption:
            self.caption.drawOn(c, ox, 0)


class FigRow(Flowable):
    """같은 높이로 맞춘 이미지 여러 장."""

    def __init__(self, items, height, gap=10, total_width=CW, center=True):
        super().__init__()
        self.items = items
        self.h = height
        self.gap = gap
        self.total = total_width
        self.center = center
        self.avail = total_width

    def wrap(self, aw, ah):
        self.avail = min(self.total, aw)
        raw = []
        for path, cap in self.items:
            with PILImage.open(str(path)) as im:
                raw.append((path, cap, im.width / im.height))
        widths = [self.h * r for _, _, r in raw]
        scale = min(1.0, (min(self.total, aw) - self.gap * (len(raw) - 1)) / sum(widths))
        self.width = sum(w * scale for w in widths) + self.gap * (len(raw) - 1)
        self.sizes = [(p, c, w * scale, self.h * scale) for (p, c, _), w in zip(raw, widths)]
        self.caps = []
        for _, cap, w, _ in self.sizes:
            par = Paragraph(md(cap), ST['caption']) if cap else None
            ch = par.wrap(w, 100)[1] + 2 if par else 0
            self.caps.append((par, ch, w))
        self.cap_h = max([ch for _, ch, _ in self.caps] or [0])
        self.height = self.h * scale + self.cap_h + (4 if self.cap_h else 0)
        return self.width, self.height

    def draw(self):
        c = self.canv
        x = (self.avail - self.width) / 2 if self.center else 0
        for (path, _cap, w, h), (par, ch, _) in zip(self.sizes, self.caps):
            c.drawImage(str(path), x, self.cap_h + 4, w, h,
                        preserveAspectRatio=True, anchor='c', mask='auto')
            c.setStrokeColor(HAIR)
            c.setLineWidth(0.4)
            c.rect(x, self.cap_h + 4, w, h, stroke=1, fill=0)
            if par:
                par.drawOn(c, x, self.cap_h + 4 - ch)
            x += w + self.gap


class MsgCard(Flowable):
    """앱푸시·온사이트 배너·알림톡 메시지 목업 카드."""

    def __init__(self, channel, title, body, meta):
        super().__init__()
        self.ch = Paragraph(md(channel), ST['msgch'])
        self.tp = Paragraph(md(title), ST['msgtitle'])
        self.bp = Paragraph(md(body), ST['msgbody'])
        self.mp = Paragraph(md(meta), ST['msgmeta'])

    def wrap(self, aw, ah):
        self.width = aw
        inner = aw - 22
        self.chh = self.ch.wrap(inner, 30)[1]
        self.tph = self.tp.wrap(inner, 80)[1]
        self.bph = self.bp.wrap(inner, 100)[1]
        self.mph = self.mp.wrap(inner, 60)[1]
        self.height = 9 + self.chh + 7 + self.tph + 4 + self.bph + 9 + 0.5 + 6 + self.mph + 9
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(BLUSH)
        c.setStrokeColor(HAIR)
        c.setLineWidth(0.5)
        c.roundRect(0.25, 0.25, self.width - 0.5, self.height - 0.5, 4, stroke=1, fill=1)
        inner = 11
        y = self.height - 9
        self.ch.drawOn(c, inner, y - self.chh)
        y -= self.chh + 7
        self.tp.drawOn(c, inner, y - self.tph)
        y -= self.tph + 4
        self.bp.drawOn(c, inner, y - self.bph)
        y -= self.bph + 9
        c.setStrokeColor(HAIR)
        c.setLineWidth(0.4)
        c.line(inner, y, self.width - inner, y)
        y -= 6
        self.mp.drawOn(c, inner, y - self.mph)


class VideoStrip(Flowable):
    """숏폼 재생 링크 자리 — 점선 상자, 완성처럼 보이지 않게."""

    def __init__(self, title, meta):
        super().__init__()
        self.tp = Paragraph(md(title), ST['msgtitle'])
        self.mp = Paragraph(md(meta), ST['note'])

    def wrap(self, aw, ah):
        self.width = aw
        inner = aw - 52
        self.th = self.tp.wrap(inner, 40)[1]
        self.mh = self.mp.wrap(inner, 40)[1]
        self.height = max(40, self.th + self.mh + 18)
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        c.setStrokeColor(RED)
        c.setLineWidth(0.6)
        c.setDash(2.4, 2.2)
        c.roundRect(0.3, 0.3, self.width - 0.6, self.height - 0.6, 3, stroke=1, fill=0)
        c.restoreState()
        cy = self.height / 2
        c.setFillColor(BLUSH)
        c.circle(24, cy, 10, stroke=0, fill=1)
        c.setFillColor(RED)
        path = c.beginPath()
        path.moveTo(21, cy + 4.6)
        path.lineTo(21, cy - 4.6)
        path.lineTo(28, cy)
        path.close()
        c.drawPath(path, stroke=0, fill=1)
        top = self.height - 9
        self.tp.drawOn(c, 44, top - self.th)
        self.mp.drawOn(c, 44, top - self.th - 2 - self.mh)


class PlaceholderBox(Flowable):
    """아직 없는 소재 자리 — 점선과 안내 문구."""

    def __init__(self, title, sub, height, width):
        super().__init__()
        self.tp = Paragraph(md(title), ST['tag'])
        self.sp = Paragraph(md(sub), ST['note'])
        self.h, self.w = height, width

    def wrap(self, aw, ah):
        self.width = min(self.w, aw)
        self.height = self.h
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setStrokeColor(PALE)
        c.setLineWidth(0.6)
        c.setDash(2.6, 2.4)
        c.rect(0.3, 0.3, self.width - 0.6, self.height - 0.6, stroke=1, fill=0)
        c.setDash()
        tw = self.tp.wrap(self.width - 16, 40)[1]
        sw = self.sp.wrap(self.width - 16, 60)[1]
        total = tw + sw + 4
        top = (self.height + total) / 2
        self.tp.drawOn(c, 8, top - tw)
        self.sp.drawOn(c, 8, top - tw - sw - 4)


# ── 블록 생성자 ─────────────────────────────────────────────────────────────


def fig(path, width=CW, caption=None, center=True):
    return ('fig', str(path), width, caption, center)


def figrow(items, height):
    return ('figrow', items, height)


def table(header, rows, widths):
    return ('table', header, rows, widths)


def cols(left, right, ratio=0.5, gap=14):
    return ('cols', left, right, ratio, gap)


def lead(text, size=15.0):
    return ('lead', text, size)


def kpi(items):
    return ('kpi', items)


def steps(items):
    return ('steps', items)


def flow(cards):
    return ('flow', cards)


def video(title, meta):
    return ('video', title, meta)


def tag(text):
    return ('tag', text)


def hair():
    return ('hair',)


def space(h):
    return ('space', h)


# ── flowable 조립 ───────────────────────────────────────────────────────────


def make_table(header, rows, widths, width=CW):
    col = [width * w for w in widths]
    data = []
    if header:
        data.append([Paragraph(md(h), ST['th']) for h in header])
    for row in rows:
        data.append([Paragraph(md(c), ST['td']) for c in row])
    t = Table(data, colWidths=col)
    style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 9),
        ('RIGHTPADDING', (0, 0), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, -1), 0.35, HAIR),
    ]
    if header:
        style += [('LINEABOVE', (0, 0), (-1, 0), 0.5, CRIMSON),
                  ('LINEBELOW', (0, 0), (-1, 0), 0.5, CRIMSON),
                  ('BOTTOMPADDING', (0, 0), (-1, 0), 4)]
    t.setStyle(TableStyle(style))
    t.hAlign = 'LEFT'
    return t


def make_steps(items, width=CW):
    cells = []
    for i, (label, sub) in enumerate(items, 1):
        cells.append([
            Paragraph(f'<font color="#D92B3A"><b>{i:02d}</b></font>&nbsp;&nbsp;'
                      f'{md(label)}', ST['step']),
            Paragraph(md(sub), ST['stepsub']),
        ])
    t = Table([cells], colWidths=[width / len(items)] * len(items))
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, PALE),
        ('LINEBEFORE', (1, 0), (-1, 0), 0.4, HAIR),
    ]))
    t.hAlign = 'LEFT'
    return t


def make_flow(cards, width=CW):
    """메시지 카드 2~3장 + 얇은 화살표 한 줄."""
    n = len(cards)
    arrow_w = 15 if n > 1 else 0
    card_w = (width - arrow_w * (n - 1)) / n
    row = []
    for i, (channel, title, body, meta) in enumerate(cards):
        row.append(MsgCard(channel, title, body, meta))
        if i < n - 1:
            row.append(Paragraph('→', ST['arrow']))
    widths = []
    for cell in row:
        widths.append(card_w if isinstance(cell, MsgCard) else arrow_w)
    t = Table([row], colWidths=widths)
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (1, 0), (1, 0), 'MIDDLE'),
    ]))
    t.hAlign = 'LEFT'
    return ('raw', t)


def as_flowables(entry, width=CW):
    kind = entry[0]
    if kind == 'p':
        return [P(entry[1])]
    if kind == 'note':
        return [P(entry[1], 'note')]
    if kind == 'lead':
        return [Lead(entry[1], entry[2])]
    if kind == 'h2':
        return [Head(entry[1])]
    if kind == 'tag':
        return [Tag(entry[1])]
    if kind == 'ul':
        return [Paragraph(f'<font color="#D92B3A">▪</font>&nbsp;&nbsp;{md(i)}', ST['body'])
                for i in entry[1]]
    if kind == 'hair':
        return [Hair(width)]
    if kind == 'space':
        return [Spacer(entry[1])]
    if kind == 'quote':
        return [Quote(entry[1], entry[2] if len(entry) > 2 else None)]
    if kind == 'table':
        return [make_table(entry[1], entry[2], entry[3], width)]
    if kind == 'kpi':
        return [KPI(entry[1], width)]
    if kind == 'steps':
        return [make_steps(entry[1], width)]
    if kind == 'fig':
        return [Fig(entry[1], min(entry[2], width), entry[3], entry[4] if len(entry) > 4 else True)]
    if kind == 'figrow':
        return [FigRow(entry[1], entry[2], total_width=width)]
    if kind == 'flow':
        t = make_flow(entry[1], width)
        return [t[1]]
    if kind == 'video':
        return [VideoStrip(entry[1], entry[2])]
    if kind == 'ph':
        return [PlaceholderBox(entry[1], entry[2], entry[3], entry[4])]
    if kind == 'raw':
        value = entry[1]
        return list(value) if isinstance(value, list) else [value]
    raise ValueError(kind)


# ── 페이지 정의 ─────────────────────────────────────────────────────────────

REPORTS = [
    ('국내 타깃·가설 v2.9', 'reports/메디큐브_국내_타깃가설_마케팅전략.md'),
    ('글로우 2030 전략 연결 v2.2', 'reports/메디큐브_글로우_리뷰분석_2030전략연결.md'),
    ('GS샵 X2 리뷰 분석 v0.2', 'reports/메디큐브_GS샵_X2_리뷰분석.md'),
    ('X2 2027 프로모션 기획서 v0.3', 'reports/메디큐브_GS샵_X2_2027_5월_프로모션기획서.md'),
    ('X2 2027 정적 스토리보드 v0.3', 'reports/메디큐브_GS샵_X2_2027_5월_정적스토리보드.md'),
    ('국내 트렌드 v1.6', 'reports/메디큐브_국내_트렌드_분석보고서.md'),
    ('글로벌 트렌드 v1.3', 'reports/메디큐브_글로벌_트렌드_분석보고서.md'),
    ('국내 피크 주 대조 v1.5', 'reports/메디큐브_국내_피크주_광고_이벤트_대조분석.md'),
]

FIXED_LIMIT = ('공개 검색·클릭 지표와 수집 가능한 리뷰로 콘텐츠 및 채널 기회를 검토했다. '
               '고객별 구매, 제품별 순매출, 광고 성과가 없어 타깃의 실제 구매 규모와 '
               '전략 효과는 판정하지 않았다.')

BOUNDARY_5060 = '공개 근거를 연결할 수 있어 GS샵 X2 방송 연계안을 먼저 설계했다.'

POSTER = 'design/glow_2030_main_poster.png'
ENDCARD = 'private_submission/2030/glow_endcard_submission.png'
KITTY = 'private_submission/2030/kitty_edition_portfolio_poster.png'
PLACE13 = 'private_submission/5060/x2_page13_placement.png'
BRIEF = 'design/gs_x2_internal_improvement_brief.png'
STORY = 'design/gs_x2_2027_static_storyboard.png'
BRIDGES = [
    ('design/glow_2030_bridge_01_bright.png', '브릿지 01 · 3중 주파수 물방울 초음파'),
    ('design/glow_2030_bridge_02_modes_bright.png', '브릿지 02 · 5가지 모드'),
    ('design/glow_2030_bridge_03_time_bright.png', '브릿지 03 · 12분 루틴'),
]

PAGES = [
    {'no': 1, 'kicker': 'COVER', 'title': '표지', 'layout': 'cover',
     'deck': None, 'blocks': []},

    {'no': 2, 'kicker': 'PROFILE', 'title': '프로필 & 핵심 역량', 'gap': 15,
     'deck': '이력이 이번 프로젝트에서 어떤 작업이 됐는지 한 줄씩 적었습니다.',
     'blocks': [
         cols([
             ('ph', '프로필 사진 자리', '[보완 예정] 지원자 확인 후 삽입', 185, 140),
         ], [
             ('raw', Paragraph(md('김윤서'), ParagraphStyle(
                 'name', fontName=BOLD, fontSize=22, leading=27, textColor=INK))),
             ('p', '숙명여자대학교 소프트웨어융합전공 · 2025.08 졸업'),
             ('p', '팀스파르타 KDT 데이터 분석가 양성과정 · 2025.12–2026.05'),
             ('p', '**자격** SQLD 2025.04 · ADsP 2025.09 · 빅데이터분석기사 2026.07'),
             ('note', '지원 직무 — 에이피알(APR) [마케팅 특별채용] 국내 콘텐츠 마케팅 신입'),
         ], ratio=0.25),
         ('h2', '이력 ↔ 이번 프로젝트에서 한 일'),
         ('table', ['역량', '이번 프로젝트에서 한 일'], [
             ['데이터 수집', '네이버 데이터랩·쇼핑인사이트 원자료 13개, 구글 트렌드 CSV 13종, 올리브영 Top100 실측, 스니핏 10구간 27장을 직접 확보'],
             ['검증·재계산', '원자료 재계산 **141항목 불일치 0건**, MD↔PDF **8쌍** 본문 대조, 리뷰 **535건** 전수 코딩'],
             ['경쟁 대조', '메타 광고 라이브러리 **7개 브랜드** 실측, 경쟁사 원소재 고유·과장 표현 대조(중복 0건)'],
             ['AI 영상·시안', '30초 콘티 v1.2 설계, **AI 인물 클립 3개**, 홈쇼핑 1–2면 시안·3면 배치 SVG 제작'],
             ['문서·조판', '보고서 8편을 같은 CSS로 PDF화하고 MD↔PDF 본문을 대조, 이 포트폴리오도 코드로 조판'],
         ], [0.16, 0.84]),
     ],
     'bottom': [
         lead('데이터로 확인하고, **콘텐츠로 옮겼습니다.**', 14.5),
         ('kpi', [('141', '원자료 재계산 항목 · 불일치 0건'), ('535', '리뷰 전수 코딩 건수'),
                  ('8', '보고서 MD↔PDF 대조 쌍')]),
         ('note', '[AI 제작] 숏폼 인물 클립·내레이션·포스터 연출 컷은 생성형 AI로 만들었고, 범위는 8·9·14쪽에 적었습니다. '
                  '[보완 예정] 프로필 사진과 최종 이력 항목은 지원자 확인 후 확정합니다.'),
     ]},

    {'no': 3, 'kicker': 'CONTENTS & SCOPE', 'title': '목차 + 프로젝트 개요', 'gap': 14,
     'deck': '조사 순서가 아니라 읽는 순서로 배열했습니다. 4쪽이 결론이고 5쪽부터가 근거입니다.',
     'blocks': [
         cols([
             ('table', ['쪽', '제목'], [
                 ['04', '핵심 결론 한눈에 보기'], ['05', '시장 신호 — 국내·글로벌'],
                 ['06', '2030·5060 타깃 선정'], ['07', '2030 글로우 제품 선정'],
                 ['08', '2030 전략·콘티·CRM'], ['09', '2030 제작물'],
             ], [0.16, 0.84]),
         ], [
             ('table', ['쪽', '제목'], [
                 ['10', '5060 채널·상품 선정'], ['11', '5060 내부 개선 기획안'],
                 ['12', '5060 2027 방송 연계·CRM'], ['13', '5060 홈쇼핑 1–2면 시안'],
                 ['14', '한계·검증·부록'],
             ], [0.16, 0.84]),
         ], ratio=0.5),
         ('quote', '공개 데이터만으로 메디큐브의 콘텐츠·채널 기회를 어디까지 판단할 수 있고, '
                   '그 판단을 어떤 콘텐츠로 실행할 수 있는가.', '프로젝트 질문'),
         ('steps', [('근거', '5쪽 트렌드\n6쪽 타깃'), ('선택', '7쪽 제품\n10쪽 채널'),
                    ('실행', '8–9쪽 2030\n11–13쪽 5060'), ('한계', '14쪽 미판정\n필요 데이터')]),
         ('h2', '자료 범위'),
         ('table', ['자료', '범위'], [
             ['네이버 데이터랩·쇼핑인사이트', '**데이터랩 54주·쇼핑인사이트 52주** · 브랜드 5사·5060 전용 5사·라인·디바이스'],
             ['구글 트렌드', '**CSV 13종** · 미국·영국·일본'],
             ['올리브영 Top100', '실측 1회 · 2026-11-20 04:08 KST 저장'],
             ['스니핏', '**10구간** 스크린숏 **27장**'],
             ['리뷰 535건', '글로우 **232**(공식몰 217·글로우픽 15) + 글로우픽 미니 **82** + GS샵 X2 **221**'],
         ], [0.3, 0.7]),
     ],
     'bottom': [
         ('h2', '이 문서의 세 가지 원칙'),
         ('ul', ['**확인된 것과 판단한 것을 나눠 쓴다** — [관측]·[해석]·[실행 제안]·[제작물] 라벨을 쪽마다 붙였습니다.',
                 '**없는 성과는 만들지 않는다** — 매출·ROAS·방송 효과는 판정하지 않고 미판정으로 남겼습니다.',
                 '**검증은 다시 돌릴 수 있게** — 원자료 재계산과 MD↔PDF 대조를 저장소 스크립트로 재실행합니다.']),
         ('note', '공식몰 미니 200건은 미니 기존안 검토에만 써서 합산 735건입니다. 535건이 본문에 인용한 모집단입니다. '
                  '[없는 자료] 매출·주문 로그, 광고 계정, 방문 로그는 4쪽 경계 문구와 14쪽 한계로 연결했습니다.'),
     ]},

    {'no': 4, 'kicker': 'EXECUTIVE SUMMARY', 'title': '핵심 결론 한눈에 보기',
     'deck': '이 쪽만 읽어도 무엇을 왜 기획했고, 무엇을 주장하지 않는지 남도록 썼습니다.',
     'blocks': [
         lead('공개 근거로 **2030 부스터 글로우**와 **5060 GS샵 X2**, 두 축을 **조건부**로 기획했습니다.', 16.0),
         ('kpi', [('28주', '2030 글로우 · 같은 조건에서 미니 초과'),
                  ('221건', 'GS샵 X2 리뷰 전수 코딩'),
                  ('0건', '원자료 재계산 141항목 불일치')]),
         cols([
             ('fig', POSTER, 182, '2030 숏폼 연계 포스터 — 생활 컷은 AI 생성 · 최종 검수 대기'),
         ], [
             ('fig', PLACE13, 284, '5060 홈쇼핑 1–2면 시안 — 실제 X2 제품 사진 포함 · 승인 전 콘셉트'),
         ], ratio=0.40),
         ('table', ['축', '판단', '제작·실행'], [
             ['01 · 2030 부스터 글로우', '콘텐츠 실험 1순위 **조건부 채택** — 여성 19–39세·5/1 선출시 이후 28주 모두 미니 초과',
              '숏폼 30초 · 연계 포스터 · 자사몰 CRM (8–9쪽)'],
             ['02 · 5060 GS샵 X2', '방송 연계 **조건부 설계** — 첫 방송 2026-05-09, 상품평 221건 공개',
              '홈쇼핑 1–2면 · 내부 개선안 · 배송 후 CRM (11–13쪽)'],
         ], [0.22, 0.5, 0.28]),
         ('p', '**[CRM]** 2030은 비교 랜딩 이탈 고객에게 온사이트 배너·앱푸시를, 구매 후에는 루틴 정착 푸시를 붙였습니다. '
               '5060은 배송 직후 사용법과 2주차 체감 안내를 스냅푸시·알림톡으로 설계했습니다.'),
         ('note', '이 문서에서 "조건부"란 검증 게이트를 통과할 때만 집행하는 제안입니다 — 7쪽 제품 채택, 11·13쪽 시안, 12쪽 편성안이 '
                  '모두 해당하며 게이트를 통과하지 못하면 집행하지 않습니다.'),
         ('quote', FIXED_LIMIT, '미판정 경계'),
     ]},

    {'no': 5, 'kicker': 'MARKET SIGNALS', 'title': '시장 신호 — 국내·글로벌', 'gap': 16,
     'deck': '피크 5주 중 4주는 시장이 함께 오른 주였습니다. 메디큐브만의 상승으로 읽지 않았습니다.',
     'blocks': [
         lead('피크 5주 중 **4주**는 경쟁사가 함께 올랐고, **8/3**만 디바이스 4사가 동시에 움직였습니다.', 14.0),
         fig('tmp/portfolio/peakmap.png', CW,
             '그림 1 · 메디큐브 검색 피크 Top 5주(▼)와 경쟁사 급등 시점 — 같은 주 함께 급등은 채운 점, '
             '단독 급등은 빈 점. 붉은 띠는 세일 주 (자료: 네이버 데이터랩 54주)'),
         ('kpi', [('4주', '피크 Top 5 중 경쟁사 동반 상승'), ('8/3', '디바이스 4사 동시 상승 주'),
                  ('35.1%', '영국 온라인 뷰티 내 아마존 UK')]),
         ('p', '[관측] 피크 Top 5주는 2026-11-02·08-03·05-04·03-02·06-29입니다. 11/02·03/02·05/04·06/29 네 주는 '
               '경쟁사가 함께 올랐고, 5/4 주의 상승은 한 해의 한 주 관측치라 시즌 효과로 확정하지 않습니다.'),
         ('p', '[해석] 경쟁 4사는 올리브영 세일가·1+1·어워즈 1위를 카피 앞머리에 두고 랜딩도 올리브영으로 보냅니다'
               '(메타 광고 라이브러리 **7개 브랜드** 실측 · 스니핏 **10구간 27장**). 메디큐브만 **디바이스+자사몰** 축이라, '
               '콘텐츠를 세일 경쟁이 아니라 **디바이스 사용 상황·제품 이해**로 잡았습니다.'),
         ('p', '**글로벌** — 미국 1위 유지·영국 상승·일본 하락. 영국은 온라인 뷰티 45.5%·아마존 UK 35.1%·틱톡샵 9.8%, '
               '일본은 Qoo10 25~30%입니다. 시점이 다른 값은 합산하지 않았고 채널 구성이 검색 추세의 원인이라고 단정하지 않았습니다.'),
     ],
     'bottom': [
         ('note', '상세 근거와 도표는 국내 트렌드 v1.6 · 글로벌 트렌드 v1.3 · 피크 주 대조 v1.5로 넘깁니다. '
                  '영국·일본 채널 비중의 기준 시점은 각각 2023-04까지 12개월·2025년·2025-03이며 서로 합산하지 않았습니다.'),
     ]},

    {'no': 6, 'kicker': 'TARGET SELECTION', 'title': '2030·5060 타깃 선정', 'gap': 15,
     'deck': '두 타깃을 구매층이 아니라 콘텐츠 기회의 축으로 골랐습니다. 서로 다른 분모의 지표를 퍼널로 빼지 않았습니다.',
     'blocks': [
         lead('2030은 **콘텐츠 실험 1순위**, 5060은 **사업상 탐색 타깃**입니다.', 14.0),
         ('table', ['타깃', '관측 근거 — 도구·연령·비교군·기간', '경계'], [
             ['**2030**', '데이터랩 브랜드 검색 비중 **45.8%**(여성 19–39세·5개 브랜드·최근 13주·1위) · '
                         '쇼핑인사이트 스킨케어 클릭 **9.3%**(20·30대·5개 브랜드·4위) · '
                         '글로우픽 리뷰 **82건 중 74건(90.2%)**이 20·30대 표기',
              '두 지표는 도구·연령 필터·분모가 달라 퍼널로 빼지 않음. **90.2%**는 수집 리뷰 안의 분포이며 전체 고객 연령 비중이 아님'],
             ['**5060**', '데이터랩 기기 검색 **5.6%**(5060 여성·5060 전용 5사·5위) · '
                         '쇼핑인사이트 이미용가전 클릭 **74.3%**(5개 키워드·1위) · '
                         '스킨케어 클릭 **6.5%**(4위, 1년 +5.3p.p.)',
              '도구·키워드·기간이 달라 퍼널 두 단계로 읽지 않음. **자사 매출 미확인**·X2 구매 우위 미판정 → 탐색 타깃으로만 표기'],
         ], [0.1, 0.56, 0.34]),
         ('kpi', [('45.8%', '2030 브랜드 검색 비중 · 데이터랩 5사 안'), ('74.3%', '이미용가전 클릭 5060 · 5개 키워드 1위'),
                  ('90.2%', '글로우픽 미니 리뷰 20·30대 표기')]),
         fig('tmp/portfolio/search3.png', CW * 0.86,
             '그림 2 · 메디큐브 브랜드 검색 지수 — 전체·여성 5060·여성 2030, 시작 주 100 (네이버 데이터랩 54주)'),
         ('p', '**선정 기준 3개** — ① 공개 데이터로 관측이 가능한가 ② 콘텐츠로 실행할 형식이 있는가 '
               '③ 확인되지 않은 것을 확인된 것처럼 쓰지 않고 설계할 수 있는가.'),
     ],
     'bottom': [
         ('note', '모든 비중은 **비교군 안의 몫**입니다 — 데이터랩 2025-11-03–2026-11-09 **54주**, 쇼핑인사이트 2025-11-03–2026-10-26 **52주**, '
                  '값은 각 계열 **최근 13주 평균**입니다. 5.6%와 74.3%는 도구·키워드가 달라 직접 비교하지 않습니다.'),
     ]},

    {'no': 7, 'kicker': 'PRODUCT SELECTION', 'title': '2030 글로우 제품 선정', 'gap': 16,
     'deck': '미니 기존안을 보류하고 부스터 글로우를 콘텐츠 실험 1순위로 조건부 채택했습니다.',
     'blocks': [
         lead('매출 주력도, 미니 대비 우위도 판정하지 않았습니다. **콘텐츠로 실험할 1순위**만 정했습니다.', 14.0),
         ('kpi', [('28주', '여성 19–39세 같은 조건 · 5/4–11/9 미니 초과'), ('25주', '상위 피크 3주 제외 후에도 모두 초과'),
                  ('−24.6%', '최근 4주 평균 검색 · 판매량 아님')]),
         ('h2', '근거 1 — 같은 조건 검색 비교'),
         ('p', '여성 19–39세 동일 조회(**2026-05-04–11-09 28주**)에서 글로우는 출시 후 **28주 모두** 미니를 앞섰고, 상위 피크 3주를 빼도 '
               '**25주 모두** 앞섰습니다(합산 지수비 7.5 → 6.9, 최근 13주 9.5). 출시 전 4/20 첫 비영값을 쓰지 않고 **5/1 올리브영 선출시**에 맞춰 '
               '5/4 주부터 비교했습니다. 검색 지수이며 **판매량은 확인되지 않았습니다**.'),
         ('h2', '근거 2 — 공식 정보·리뷰 대조로 소구 9개 추리기'),
         ('table', ['판정', '소구'], [
             ['**채택**', '속건조 보습·물광(Shot 1·3) · 탄력 관리(Shot 2) · 고민별 5가지 모드(Shot 3·4) — 공식 5모드 기능 소구, 리프팅 단정 없음'],
             ['조건부', '매일 12분 홈케어 루틴(Shot 2·4) — 시술 대체 표현은 금지선 위반으로 제외'],
             ['제외', '민감 피부 진정 · 피부과 대체 경제성 · 임상 결과 신뢰성 · 저렴한 가격 소구'],
         ], [0.12, 0.88]),
         ('h2', '근거 3 — 반대 신호 처리'),
         ('p', '미니 리뷰의 휴대·여행 소구가 **57.5%**(공식몰 미니 리뷰 200건 CSV 태그 중 115건)로 확인돼 "가볍다·간편하다" 후킹은 주 후킹에서 보류했습니다. '
               '최근 4주 검색 하락(**−24.6%**)도 지우지 않고 함께 적었습니다.'),
         ('quote', '매출 주력 여부와 미니 대비 우위는 판정하지 않았습니다. 검색 지수는 판매량이 아니고 두 제품의 판매 자료가 없습니다. '
                   '미니 기존안은 폐기가 아니라 별도 태그 검토 대상으로 남겼습니다.', '판정을 미룬 것'),
     ],
     'bottom': [
         ('note', '검색 지수는 **검색 관심도**이며 판매량이 아닙니다. 소구 채택은 메시지 효과 검증이 아니며, 글로우와 X2(10쪽)는 타깃·근거가 달라 같은 축에서 비교하지 않았습니다.'),
     ]},

    {'no': 8, 'kicker': 'CREATIVE STRATEGY · CRM', 'title': '2030 글로우 전략 · 콘티 v1.2 · CRM', 'gap': 14,
     'deck': '30초를 세 샷으로 나누고, 구매 전후 접점을 자사몰 CRM으로 이어 붙였습니다.',
     'blocks': [
         lead('고민 1개 → 제품 이유 1개 → 자사몰 비교 랜딩. 구매 후에는 **하루 12분 루틴** 정착까지.', 13.5),
         ('steps', [('0–7초', '샷 1 · 아침 속건조'), ('7–14초', '샷 2 · 밤 탄력'),
                    ('14–21초', '샷 3 · 외출 전 피부결'), ('21–30초', 'CTA · 자사몰 비교 랜딩')]),
         cols([
             ('figrow', [('shots/pic_shot1_final.png', '샷 1 · 20대 강의실 아침'),
                         ('shots/pic_shot2_final.png', '샷 2 · 30대 퇴근길 거실'),
                         ('shots/pic_shot3_final.png', '샷 3 · 20대 화장실 거울')], 186),
         ], [
             ('h2', '샷별 생성 방식과 검수'),
             ('p', '**샷 1 · Kling** — 속건조 → 물방울 초음파. 전후 비교·흡수율 % 단정 금지'),
             ('p', '**샷 2 · Higgsfield** — 야근 후 하루 12분. "피부과 안 가도" 금지'),
             ('p', '**샷 3 · Kling** — 뜨는 느낌 → 5가지 모드. 민감 진정·무자극 금지'),
             ('p', '**CTA · CapCut** — 가격·할인율 미표기, 자사몰 비교 랜딩 연결'),
         ], ratio=0.64),
         ('h2', '자사몰 CRM — 비교 랜딩 이탈과 구매 후 정착'),
         flow([
             ('온사이트 배너', '내 피부 고민별 5가지 모드 가이드',
              '속건조·탄력·물광 중 내 고민부터. 숏폼에서 보던 모드를 앱에서 이어서 확인합니다.', '비교 랜딩 이탈 · 앱 설치자'),
             ('앱푸시 D+1', '내 피부 고민별 5가지 모드 가이드',
              '보던 모드 가이드, 앱에서 이어 보기. 고민별 5가지 모드를 한 번에 비교합니다.', '랜딩 방문 · 미구매'),
             ('앱푸시 구매 후 D+7', '하루 12분 루틴(젤 크림 병행)',
              '오늘 루틴 한 번만 확인해 보세요. 젤 크림과 함께 쓰는 순서까지 안내합니다.', '구매 고객 · 루틴 정착'),
         ]),
         ('quote', '숏폼은 유입까지만 만듭니다. 이탈 지점에서 다시 부르고, 구매 뒤에는 루틴으로 붙잡는 것이 CRM의 몫입니다.', 'CRM 원칙'),
     ],
     'bottom': [
         ('note', '[AI 제작] 인물 클립 3개(Kling 2·Higgsfield 1)와 7개 구간 내레이션(AI TTS)은 AI로 생성했습니다. '
                  '경쟁사 원소재 대비 표현 중복은 0건이며, 이 검수는 메시지 효과 검증이 아닙니다. '
                  '푸시 발송에는 자사몰 방문·구매 로그가 필요해 [실행 제안]이고 실제 발송·성과는 미집행입니다.'),
     ]},

    {'no': 9, 'kicker': 'CREATIVE OUTPUTS', 'title': '2030 글로우 제작물',
     'deck': '포스터·엔드카드·헬로키티 에디션·브릿지 3종. 실제 제품 사진을 넣은 시안까지 만들었습니다.',
     'blocks': [
         tag('[일부 제작] Shot 1–3 AI 생성 클립 + 29.8초 조립 초안 · 최종 시청·음성 검수 대기'),
         figrow([
             (POSTER, '메인 포스터 1080×1350 — "하루의 세 순간, 다른 피부 고민". 생활 3컷 중 연출 컷은 AI 생성'),
             (ENDCARD, '엔드카드 1080×1920 — 실제 제품 사진과 물방울 초음파 루틴, 자사몰 CTA'),
             (KITTY, '헬로키티 에디션 1080×1350 — 별도 제품 포스터, 판매·가격 CTA 없이 시안으로만'),
         ], 232),
         figrow(BRIDGES, 188),
         video('숏폼 29.8초 · 1080×1920 · 30fps 조립 초안',
               'Shot 1–3 클립을 FFmpeg로 이어 붙였고 CapCut 최종 편집본은 아닙니다. 음성은 7개 구간 AI TTS, '
               '배경 패드는 자체 제작입니다. 재생 링크·QR은 최종 시청·음성·권리 검수 뒤 넣습니다.'),
         ('note', '제품 사진 시안 3종은 저장소 `private_submission/`에 함께 들어 있습니다. 실제 광고 집행·성과는 없고, '
                  '제품 이미지 재사용 허락은 확인되지 않아 외부 게시에는 쓰지 않습니다.'),
     ]},

    {'no': 10, 'kicker': 'CHANNEL & PRODUCT', 'title': '5060 GS샵 X2 채널·상품 선정', 'gap': 16,
     'deck': '5060의 X2 구매 비중과 홈쇼핑 이용률 통계는 확인되지 않았습니다. 공개 근거를 연결할 수 있는 채널로 GS샵을 먼저 골랐습니다.',
     'blocks': [
         lead(BOUNDARY_5060, 14.5),
         ('kpi', [('2026-05-09', 'GS샵 X2 첫 방송 · 단독 런칭'), ('221건', '상품평 수집 · 평점 4.6'),
                  ('10.0%', '선물·대리 구매 맥락 22건')]),
         ('table', ['항목', '내용'], [
             ['첫 방송', '**2026-05-09** · [메디큐브] 부스터프로 시즌2 찬스쇼 단독 런칭 (핑크) · 상품번호 **1117330943**'],
             ['상품평', '**221건** · 수집 2026-05-10~2026-11-10 · 평점 **4.6** · 고유 ID 221건 대조'],
             ['채널 대조', 'CJ온스타일·롯데 — 메디큐브 X2 방송 이력 확인 수준까지'],
         ], [0.16, 0.84]),
         ('h2', '리뷰 221건 코딩에서 확인된 것 — 비중은 221건 표본 안의 몫'),
         ('table', ['항목', '값'], [
             ['선물·대리 구매 맥락', '**22건 (10.0%)**'],
             ['방송·찬스쇼를 구매 계기로 적은 리뷰', '**12건 (5.4%)** · 연령을 스스로 밝힌 리뷰 **3건 (1.4%)**'],
             ['색상 표기', '핑크 **186건(84.2%)** · 화이트 16건(7.2%) · 미상 19건(8.6%)'],
             ['판단 유보 · 체감 없음', '**25건(11.3%)** · **10건(4.5%)** — 합 35건'],
             ['구매 상품명', '**11종**으로 갈림 — 확정 SKU 1개 기준 구성표가 필요한 이유'],
         ], [0.42, 0.58]),
         cols([
             ('quote', '5060이 X2를 많이 구매했다.', '쓰지 않는 문장'),
         ], [
             ('quote', BOUNDARY_5060, '쓰는 문장'),
         ], ratio=0.42),
     ],
     'bottom': [
         ('note', '모든 %는 GS샵 상품평 **221건**(2026-05-10–11-10 수집) 표본 안의 몫이며 발생률·5060 고객 특성으로 해석하지 않습니다. '
                  '221건과 핑크 페이지 구매 표시 848개를 나눠 작성률(약 26%)로 쓰던 문장은 분모 불일치로 폐기했습니다.'),
     ]},

    {'no': 11, 'kicker': 'INTERNAL PROPOSAL', 'title': '5060 내부 개선 기획안 (3면 고도화)',
     'deck': '리뷰에서 확인된 사용 장벽을 고객 안내·구성·제품 검토 과제로 나눴습니다.',
     'blocks': [
         tag('[내부 검토용] — 고객용 광고물 아님'),
         fig(BRIEF, CW, '내부 개선 검토 요약 지면 시안 — GS샵 상품평 221건(수집 기간 2026-05-10~11-10) 기준'),
         ('table', ['장벽', '언급', '검토 과제'], [
             ['자극·통증', '12건 (5.4%)', '사용감·강도 — 원인 확인 뒤 안전성·사용성 시험'],
             ['무게·크기', '10건 (4.5%)', '무게·그립 — 조작 불편 재현과 설계·원가 검토'],
             ['부속품 부재', '7건 (3.2%)', '설명서·구성품 — 정보 표시와 실제 구성 변경을 분리'],
             ['설명 혼란', '6건 (2.7%)', '설명서·구성품 — 표시 방식 검토'],
             ['버튼 관련', '5건 (2.3%)', '버튼 — 위치·조작 설계 검토'],
         ], [0.18, 0.16, 0.66]),
     ],
     'bottom': [
         ('note', '[내부 검토용] 고객 안내로 풀 수 있는 것 · 구성·설명서로 풀 수 있는 것 · **제품 변경 검토가 필요한 것**을 나눈 조건부 제안서 요약입니다. '
                  '제품 검증 완료·출시 확정·시험 결과를 주장하지 않으며, 원인·안전성·원가 검증은 미실시입니다. 원문 기획안 전체는 14쪽 저장소 링크로 넘깁니다.'),
     ]},

    {'no': 12, 'kicker': '2027 RE-LAUNCH · CRM', 'title': '5060 2027년 5월 방송 연계 · CRM', 'gap': 15,
     'deck': '첫 방송 1주년에 맞춘 재방송 연계안입니다. 편성·혜택은 협의 목표일 뿐 확정이 아닙니다.',
     'blocks': [
         lead('재방송은 편성이 아니라 **고객 안내 설계**부터 — 배송 직후 사용법, 2주차 체감 안내.', 13.5),
         ('steps', [('2026-05-09', 'GS샵 첫 방송 · X2 단독 런칭'), ('2026-11', '상품평 221건 수집·코딩'),
                    ('2027-05-08–09 전후', '1주년 재방송 · 협의 목표일'), ('2027-05 이후', '전용 코드·회차별 주문 비교')]),
         ('p', '**검증 게이트 3개** — ① GS샵 방송 ID·SKU·연령별 순주문·순매출 확인 ② APR 제품 담당의 개선 가능성·시험·제조 일정 확인 '
               '③ 방송 편성·혜택 협의. 셋을 통과할 때만 집행합니다.'),
         fig(STORY, CW * 0.94,
             '스토리보드 v0.3 — 방송 전(화면 1·2) → 방송 중 → 방송 후(화면 4) 안내 흐름. 화면 3은 11쪽 내부 검토용입니다.'),
         ('h2', '배송 후 CRM — 스냅푸시·알림톡 2단계'),
         flow([
             ('스냅푸시 · 알림톡 D+0', '큰 글씨 사용법 + 손잡이 아래쪽 그립 팁',
              '손잡이는 아래쪽을 잡으면 버튼이 덜 눌립니다. 사용 전 확인할 3가지를 큰 글씨로 안내합니다.',
              '배송 완료 직후 · 구매 고객'),
             ('알림톡 D+14', '피부 상태별 체감 안내',
              '사용 2주, 체감 시기와 강도는 피부 상태에 따라 다릅니다. 단계별 사용 강도를 안내합니다.',
              '배송 2주차 · 구매 고객'),
         ]),
     ],
     'bottom': [
         ('note', '근거는 GS샵 상품평 221건 표본 — 버튼 **5건(2.3%)** · 설명서 **6건(2.7%)** · 자극 **12건(5.4%)** · '
                  '판단 유보 25건·체감 없음 10건(합 **35건**)입니다. 2027년 편성·혜택·매출 목표는 미확정이고, '
                  '발송에는 GS샵 주문·회차 자료가 필요해 [실행 제안]입니다.'),
     ]},

    {'no': 13, 'kicker': 'HOME SHOPPING CONCEPT', 'title': '5060 홈쇼핑 1–2면 시안', 'gap': 16,
     'deck': '기존 3면 시안 중 앞의 1–2면을 실제 광고 페이지 수준으로 올린 작업입니다.',
     'blocks': [
         tag('[승인 전 콘셉트] — 제품 변경·출시·편성 확정으로 읽히는 문구는 넣지 않았습니다'),
         fig(PLACE13, CW, '1면 방송 전 예고 포스터 · 2면 방송 구성 확인 카드 — 실제 X2 제품 사진 포함'),
         cols([
             ('h2', '1면 · 방송 전 예고'),
             ('p', '재방송 맥락 → 제품 인지 → 구성 확인 → 일정·랜딩 순서로 읽히게 설계했습니다. 확정 방송일·승인된 URL만 넣고, '
                   '2027-05-09를 확정 방송일로 쓰지 않습니다.'),
         ], [
             ('h2', '2면 · 구성 확인 카드'),
             ('p', '**본품 → 함께 구성 → 보관·부속 → 가격·혜택** 4항목으로 나눴습니다. 확정 SKU 1개 기준 구성표로 고정해 '
                   'SKU마다 구성이 달라지는 상황을 막습니다.'),
         ], ratio=0.5),
     ],
     'bottom': [
         ('note', '**승인 전 콘셉트** — 제품 변경·출시·편성 확정으로 읽히는 문구는 넣지 않았습니다. 공식몰·GS샵 상세페이지의 디자인·문구·사진을 '
                  '복사하거나 재편집하지 않았고, 확인되지 않은 혜택·수치·랭킹도 넣지 않았습니다. 시안 파일은 저장소 `private_submission/5060/`에 '
                  '포함되어 있으며, 제품 이미지 재사용 허락은 확인되지 않아 광고 집행·외부 게시에는 쓰지 않습니다.'),
     ]},

    {'no': 14, 'kicker': 'LIMITS & APPENDIX', 'title': '한계, 검증 데이터 & 역할·부록',
     'deck': '주장하지 않은 것을 먼저 적었습니다. 검증 수치는 저장소에서 다시 실행해 확인할 수 있습니다.',
     'blocks': [
         ('quote', FIXED_LIMIT, '미판정 경계'),
         ('p', '**[미확인]** GS샵 연령별 순주문·제품 개선 일정·2027년 편성 — 10·11·12쪽 판정 유보 사유입니다. '
               '성과 판정에 필요한 자료는 GS샵 **방송 ID·SKU·연령별 순주문·순매출**, 자사몰·광고 채널의 **방문·전환·광고비**, '
               '제품 **개선 사양·시험·생산 일정**입니다.'),
         ('kpi', [('141', '원자료 재계산 항목 · 불일치 0건'), ('8', 'MD↔PDF 본문 대조 쌍 · 빈 쪽 0'),
                  ('535', '리뷰 전수 코딩 건수')]),
         ('table', ['검증 항목', '결과'], [
             ['원자료 재계산', '**141항목 불일치 0건** (verify2.py --numeric-only)'],
             ['MD↔PDF 본문 대조', '**8쌍** 통과 · 입력·출력 해시 확인 · 빈 쪽 0 (verify_pdf_sync.py)'],
             ['리뷰 코딩', '**535건** 전수 코딩 (글로우 232 · 미니 82 · GS샵 X2 221)'],
             ['GS샵 리뷰 대조', '**221건** 고유 ID·평점 분포 대조'],
         ], [0.3, 0.7]),
         ('p', '**역할·도구** — 문제 정의·데이터 수집·재계산 검증·리뷰 코딩·경쟁 표현 검수·콘티 설계·시안 제작(SVG)·PDF 조판(Python)을 직접 했습니다. '
               '**Kling·Higgsfield 영상, AI TTS 내레이션, 포스터 연출 컷은 AI로 생성**했고, 도구는 생성·렌더링에만 쓰고 판단·검수는 직접 했습니다.'),
         ('h2', '부록 — 전체 보고서 8편'),
         ('table', ['보고서', '저장소 경로'], [[a, f'`{b}`'] for a, b in REPORTS], [0.35, 0.65]),
     ],
     'bottom': [
         ('note', '[AI 제작] 1·2·8·9쪽에 표기한 숏폼 인물 클립 3개·7개 구간 내레이션·포스터 연출 컷은 생성형 AI 산출물이며, 실제 촬영·성우 녹음·광고 집행은 없습니다. '
                  '저장소 github.com/rladbstj56/medicube_marketing(비공개) · 검증 스크립트 analysis/task2/verify2.py · verify_pdf_sync.py · verify_portfolio.py · 리뷰 코딩표 data/reviews/.'),
     ]},
]

COVER = {
    'kicker': 'CONTENT MARKETING PORTFOLIO',
    'right': '2026.11',
    'title': ['메디큐브 콘텐츠 마케팅', '리서치 & 전략 포트폴리오'],
    'lead': '공개 데이터로 판단한 두 개의 축',
    'line': '저장소 보고서 8편의 판단을 14쪽으로 압축하고, 그중 제작한 소재만 실었습니다.',
    'axes': [
        ('01', '2030 부스터 글로우', '숏폼 30초 · 연계 포스터 · 자사몰 CRM', '콘텐츠 실험 1순위 조건부 채택'),
        ('02', '5060 GS샵 X2', '홈쇼핑 1–2면 시안 · 내부 개선 기획안', '방송 연계 조건부 설계'),
    ],
    'meta': [
        ('지원 직무', '에이피알(APR) [마케팅 특별채용] 국내 콘텐츠 마케팅 신입 · 마감 2026-11-22 23:59'),
        ('작성', '김윤서 · 숙명여자대학교 소프트웨어융합전공 · 2026.11'),
        ('고지', '숏폼 인물 클립·내레이션·포스터 연출 컷 일부는 생성형 AI로 제작(8·9·14쪽 표기). 실제 광고 집행·성과는 없습니다.'),
    ],
    'version': 'v0.2 · 최종 수정 2026-11-22 03:50 KST',
    'band': [(ENDCARD, 0.23), (PLACE13, 0.77)],
}


# ── PDF 그리기 ──────────────────────────────────────────────────────────────


def spaced_text(c, x, y, text, font, size, color, tracking=1.2):
    """자간을 준 작은 킥커. 캔버스 상태를 건드리지 않도록 글자를 하나씩 그린다."""
    c.setFont(font, size)
    c.setFillColor(color)
    cx = x
    for ch in text:
        c.drawString(cx, y, ch)
        cx += c.stringWidth(ch, font, size) + tracking
    return cx


def draw_chrome(c, no):
    """모든 쪽 공통 머리글·바닥글."""
    c.setStrokeColor(HAIR)
    c.setLineWidth(0.5)
    c.line(M, PAGE_H - 40, PAGE_W - M, PAGE_H - 40)
    c.line(M, 42, PAGE_W - M, 42)
    c.setFont(BOLD, 6.0)
    c.setFillColor(CRIMSON)
    c.drawString(M, PAGE_H - 34, 'MEDICUBE  ·  CONTENT MARKETING PORTFOLIO')
    c.setFont(FONT, 6.0)
    c.setFillColor(MUTE)
    c.drawRightString(PAGE_W - M, PAGE_H - 34, '김윤서 · 2026.11')
    c.setFont(FONT, 6.0)
    c.drawString(M, 30, '에이피알(APR) 국내 콘텐츠 마케팅 신입 지원 · 포트폴리오 (14쪽)')
    c.setFont(BOLD, 7.0)
    c.setFillColor(CRIMSON)
    c.drawRightString(PAGE_W - M, 30, f'{no:02d} / {TOTAL_PAGES}')


def draw_title_block(c, page):
    """쪽 제목·킥커·설명을 그리고 본문 시작 y를 돌려준다."""
    spaced_text(c, M, PAGE_H - 58, f'{page["no"]:02d}', BOLD, 6.6, CRIMSON, 0.4)
    spaced_text(c, M + 18, PAGE_H - 58, page['kicker'], BOLD, 6.6, CRIMSON, 1.3)

    title = Paragraph(md(page['title']), ParagraphStyle(
        'title', fontName=BOLD, fontSize=23, leading=29, textColor=INK, wordWrap=None))
    tw, th = title.wrap(CW, 70)
    title.drawOn(c, M, PAGE_H - 74 - th)
    y = PAGE_H - 74 - th - 13
    c.setStrokeColor(HAIR)
    c.setLineWidth(0.5)
    c.line(M, y, PAGE_W - M, y)
    y -= 15
    if page.get('deck'):
        deck = Paragraph(md(page['deck']), ST['deck'])
        dw, dh = deck.wrap(CW * 0.92, 80)
        deck.drawOn(c, M, y - dh)
        y -= dh + 4
    return y - 14


def crop_image(c, path, x, y, w, h):
    """비율을 유지한 채 상자에 꽉 차게 잘라 넣는다(표지 띠)."""
    with PILImage.open(str(path)) as im:
        iw, ih = im.size
    s = max(w / iw, h / ih)
    dw, dh = iw * s, ih * s
    c.saveState()
    p = c.beginPath()
    p.rect(x, y, w, h)
    c.clipPath(p, stroke=0, fill=0)
    c.drawImage(str(path), x + (w - dw) / 2, y + (h - dh) / 2, dw, dh, mask='auto')
    c.restoreState()


def draw_cover(c):
    """표지 — 여백 · 큰 타이틀 · 2축 · 미니멀 메타 · 하단 캠페인 띠."""
    band_h = 300
    c.setFillColor(CRIMSON)
    c.rect(0, PAGE_H - 4, PAGE_W, 4, stroke=0, fill=1)

    spaced_text(c, M, PAGE_H - 62, COVER['kicker'], BOLD, 7.0, CRIMSON, 1.6)
    c.setFont(FONT, 7.6)
    c.setFillColor(MUTE)
    c.drawRightString(PAGE_W - M, PAGE_H - 62, COVER['version'])

    c.setFillColor(INK)
    c.setFont(BOLD, 31)
    c.drawString(M, PAGE_H - 138, COVER['title'][0])
    c.setFillColor(CRIMSON)
    c.drawString(M, PAGE_H - 182, COVER['title'][1])

    c.setStrokeColor(HAIR)
    c.setLineWidth(0.5)
    c.line(M, PAGE_H - 208, PAGE_W - M, PAGE_H - 208)

    c.setFillColor(MUTE)
    c.setFont(FONT, 10.5)
    c.drawString(M, PAGE_H - 238, COVER['lead'])

    y = PAGE_H - 288
    for no, name, mak, status in COVER['axes']:
        c.setFillColor(RED)
        c.setFont(BOLD, 8.2)
        c.drawString(M, y, no)
        c.setFillColor(INK)
        c.setFont(BOLD, 14.5)
        c.drawString(M + 26, y - 1, name)
        c.setFillColor(MUTE)
        c.setFont(FONT, 7.8)
        c.drawString(M + 26 + c.stringWidth(name, BOLD, 14.5) + 12, y, mak)
        c.setFillColor(CRIMSON)
        c.setFont(FONT, 7.4)
        c.drawString(M + 26, y - 15, status)
        y -= 46

    c.setFillColor(MUTE)
    c.setFont(FONT, 8.2)
    c.drawString(M, band_h + 154, COVER['line'])

    y = band_h + 118
    meta_style = ParagraphStyle('meta', fontName=FONT, fontSize=8.0, leading=12.0,
                                textColor=INK)
    for key, value in COVER['meta']:
        par = Paragraph(md(value), meta_style)
        pw, ph = par.wrap(CW - 70, 60)
        c.setFillColor(PALE)
        c.setFont(BOLD, 6.2)
        c.drawString(M, y - 1, key.upper())
        par.drawOn(c, M + 70, y - ph + 7)
        y -= max(ph + 12, 22)

    c.setStrokeColor(HAIR)
    c.setLineWidth(0.5)
    c.line(0, band_h + 4, PAGE_W, band_h + 4)
    gap = 8
    x = 0
    for i, (path, frac) in enumerate(COVER['band']):
        w = (PAGE_W - gap * (len(COVER['band']) - 1)) * frac
        crop_image(c, ROOT / path, x, 0, w, band_h)
        x += w + gap


def build_pdf():
    global draw_canvas
    TMP.mkdir(parents=True, exist_ok=True)
    svg_to_png(HERE / 'fig/peak/f3_peakmap.svg', TMP / 'peakmap.png', dpi=200)
    svg_to_png(HERE / 'fig/domestic/c01_search3.svg', TMP / 'search3.png', dpi=210)

    report = []
    problems = []
    c = canvas.Canvas(str(OUT_PDF), pagesize=A4)
    draw_canvas = c
    c.setTitle('메디큐브 콘텐츠 마케팅 리서치 & 전략 포트폴리오')
    c.setAuthor('김윤서')
    c.setSubject('에이피알(APR) [마케팅 특별채용] 국내 콘텐츠 마케팅 신입 지원 포트폴리오 (14쪽)')
    c.setKeywords('메디큐브, APR, 콘텐츠 마케팅, 포트폴리오, 부스터 글로우, GS샵 X2, CRM')
    c.setCreator('analysis/task2/build_portfolio.py')

    for page in PAGES:
        key = f'page-{page["no"]:02d}'
        c.bookmarkPage(key)
        c.addOutlineEntry(f'{page["no"]}. {page["title"]}', key, level=0)
        if page.get('layout') == 'cover':
            draw_cover(c)
            report.append({'no': page['no'], 'title': page['title'], 'used': 0, 'free': 0})
            c.showPage()
            continue
        draw_chrome(c, page['no'])
        y_top = draw_title_block(c, page)
        avail = y_top - BODY_BOTTOM
        flows = page_flowables(page)
        gap = page.get('gap', GAP)
        used = 0
        y = y_top
        for f in flows:
            w, h = f.wrap(CW, avail)
            f.drawOn(c, M, y - h)
            y -= h + gap
            used += h + gap
        # 바닥에 고정하는 꼬리 블록 — 남는 여백을 메모가 받치게 한다.
        bottom_flows = []
        for e in page.get('bottom', []):
            bottom_flows.extend(as_flowables(e, CW))
        stack = 0
        if bottom_flows:
            heights = [f.wrap(CW, 120)[1] for f in bottom_flows]
            stack = sum(heights) + 8 * (len(bottom_flows) - 1)
            by = BODY_BOTTOM
            for f, h in zip(reversed(bottom_flows), reversed(heights)):
                f.drawOn(c, M, by)
                by += h + 8
            if y < BODY_BOTTOM + stack + 6:
                problems.append((f'{page["no"]}쪽 꼬리 블록 겹침', round(y - BODY_BOTTOM - stack, 1)))
        if y < BODY_BOTTOM:
            problems.append((f'{page["no"]}쪽 {page["title"]}', round(y - BODY_BOTTOM, 1)))
        free = y - BODY_BOTTOM - stack
        report.append({'no': page['no'], 'title': page['title'],
                       'used': round(y_top - BODY_BOTTOM - free, 1), 'free': round(free, 1),
                       'blocks': len(flows) + len(bottom_flows)})
        c.showPage()
    c.save()
    return report, problems


def svg_to_png(svg_path, png_path, dpi=200):
    """도표 SVG를 PNG로 굽는다. reportlab이 SVG를 직접 넣지 못해 한 번 거친다."""
    doc = pymupdf.open(str(svg_path))
    pix = doc[0].get_pixmap(dpi=dpi)
    pix.save(str(png_path))
    return png_path


def stack_cell(entries, width):
    """cols 한 칸 — 블록 사이에 8pt 숨을 넣는다."""
    out = []
    for i, e in enumerate(entries):
        if i:
            out.append(Spacer(8))
        if e[0] == 'fig' and len(e) > 4:
            e = ('fig', e[1], e[2], e[3], False)
        out.extend(as_flowables(e, width))
    return out


def page_flowables(page, width=CW):
    """블록 정의를 flowable 목록으로 바꾼다(cols는 표로)."""
    out = []
    for entry in page['blocks']:
        if entry[0] == 'cols':
            _, left, right, ratio, gap = entry
            lw = (width - gap) * ratio
            rw = (width - gap) * (1 - ratio)
            lf = stack_cell(left, lw)
            rf = stack_cell(right, rw)
            t = Table([[lf, rf]], colWidths=[lw, rw])
            t.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (0, 0), 0),
                ('RIGHTPADDING', (0, 0), (0, 0), gap / 2),
                ('LEFTPADDING', (1, 0), (1, 0), gap / 2),
                ('RIGHTPADDING', (1, 0), (1, 0), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            t.hAlign = 'LEFT'
            out.append(t)
        elif entry[0] == 'raw':
            value = entry[1]
            if isinstance(value, list):
                out.extend(value)
            else:
                out.append(value)
        else:
            out.extend(as_flowables(entry, width))
    return out


# ── Markdown ────────────────────────────────────────────────────────────────


def md_table(header, rows):
    rows = [[c.replace('\n', ' / ') for c in row] for row in rows]
    head = header if header else [''] * len(rows[0])
    lines = ['| ' + ' | '.join(head) + ' |', '|' + '|'.join(['---'] * len(head)) + '|']
    for row in rows:
        lines.append('| ' + ' | '.join(row) + ' |')
    return '\n'.join(lines)


def entry_to_md(entry):
    kind = entry[0]
    if kind == 'p':
        return entry[1]
    if kind == 'note':
        return f'> {entry[1]}'
    if kind == 'lead':
        return f'**{entry[1]}**'
    if kind == 'h2':
        return f'### {entry[1]}'
    if kind == 'tag':
        return f'**{entry[1]}**'
    if kind == 'ul':
        return '\n'.join(f'- {i}' for i in entry[1])
    if kind == 'quote':
        label = f'**{entry[2]}** — ' if len(entry) > 2 and entry[2] else ''
        return f'> {label}{entry[1]}'
    if kind == 'table':
        return md_table(entry[1], entry[2])
    if kind == 'kpi':
        return md_table(['숫자', '내용'], [[v, l] for v, l in entry[1]])
    if kind == 'steps':
        return md_table(['구간', '내용'], [[a, b] for a, b in entry[1]])
    if kind == 'flow':
        return md_table(['채널', '메시지', '발송 조건'],
                        [[c[0], f'{c[1]} — {c[2]}', c[3]] for c in entry[1]])
    if kind == 'fig':
        return f'![{entry[3] or ""}]({relative(entry[1])})'
    if kind == 'figrow':
        return '\n\n'.join(f'![{cap}]({relative(path)})' for path, cap in entry[1])
    if kind == 'video':
        return f'**{entry[1]}** — {entry[2]}'
    if kind == 'ph':
        return f'{entry[1]} — {entry[2]}'
    if kind == 'cols':
        _, left, right, ratio, gap = entry
        left_md = '\n\n'.join(entry_to_md(e) for e in left if e[0] not in ('hair', 'space'))
        right_md = '\n\n'.join(entry_to_md(e) for e in right if e[0] not in ('hair', 'space'))
        return left_md + '\n\n' + right_md
    if kind in ('hair', 'space'):
        return ''
    if kind == 'raw':
        return ''
    raise ValueError(kind)


def relative(path):
    text = str(path)
    if text.startswith(('tmp/portfolio/', 'design/', 'shots/', 'reports/', 'private_submission/')):
        return '../' + text
    return text


def build_md():
    lines = [
        '# 메디큐브 콘텐츠 마케팅 리서치 & 전략 포트폴리오',
        '',
        '> **14쪽 에디토리얼 포트폴리오 · v0.2** · 최종 수정 2026-11-22 03:50 KST · 김윤서 · 2026.11 · '
        '에이피알(APR) [마케팅 특별채용] 국내 콘텐츠 마케팅 신입 지원 (마감 2026-11-22 23:59)',
        '>',
        '> 이 문서는 `analysis/task2/build_portfolio.py`가 만들었고, 같은 스크립트가 같은 내용으로 '
        '`메디큐브_콘텐츠마케팅_포트폴리오.pdf`(14쪽)를 조판합니다. 수치는 저장소 현행 문서 값을 그대로 옮겼고, '
        '설계 기준은 `메디큐브_콘텐츠마케팅_포트폴리오_구성안.md` v1.5입니다.',
        '',
        f'> **고정 문구(4·14쪽)** — *"{FIXED_LIMIT}"*',
        '',
        '---',
        '',
    ]
    for page in PAGES:
        if page.get('layout') == 'cover':
            lines.append('## 1쪽 · 표지')
            lines.append('')
            lines.append(f'**{COVER["kicker"]}**')
            lines.append('')
            lines.append(COVER['version'])
            lines.append('')
            lines.append('# ' + ' '.join(COVER['title']))
            lines.append('')
            lines.append(COVER['lead'])
            lines.append('')
            lines.append(md_table(['구분', '축', '제작·실행', '판정'],
                                  [[no, name, mak, status] for no, name, mak, status in COVER['axes']]))
            lines.append('')
            lines.append(COVER['line'])
            lines.append('')
            for key, value in COVER['meta']:
                lines.append(f'- {key} — {value}')
            lines.append('')
            for path, _frac in COVER['band']:
                lines.append(f'![표지 소재]({relative(path)})')
            lines.append('')
            lines.append('---')
            lines.append('')
            continue
        lines.append(f'## {page["no"]}쪽 · {page["title"]}')
        lines.append('')
        if page.get('deck'):
            lines.append(f'*{page["deck"]}*')
            lines.append('')
        for entry in page['blocks'] + page.get('bottom', []):
            block = entry_to_md(entry)
            if block:
                lines.append(block)
                lines.append('')
        lines.append('---')
        lines.append('')
    OUT_MD.write_text('\n'.join(lines), encoding='utf-8')


def main():
    report, problems = build_pdf()
    build_md()
    for row in report:
        print(f'{row["no"]:>2}쪽 {row["title"]:<32} 사용 {row["used"]:>6}  여유 {row["free"]:>7}')
    print('페이지', len(report))
    if problems:
        print('!! 넘침:', problems)
        return 1
    print('OK', OUT_PDF.relative_to(ROOT), OUT_MD.relative_to(ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
