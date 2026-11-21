# -*- coding: utf-8 -*-
"""14쪽 두괄식 포트폴리오 PDF·MD 생성기.

구성안(`reports/메디큐브_콘텐츠마케팅_포트폴리오_구성안.md` v1.2)의 페이지별 설계를
한 곳(PAGES)에 적고, 같은 데이터에서 PDF와 MD를 함께 만든다. 두 파일이 서로
어긋날 수 없게 하려는 것이며, 값은 모두 저장소 현행 문서에서 그대로 옮겼다.

이 환경에는 WeasyPrint가 쓰는 libpango가 없어 기존 `build2.py` 경로를 쓸 수 없다.
그래서 저장소에 동봉한 Noto Sans KR 두 굵기와 reportlab으로 직접 조판한다.
쪽수는 각 쪽 블록의 높이를 미리 재서 넘칠 때 빌드를 멈추므로 정확히 14쪽이 된다.
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

RED = HexColor('#D92B3A')
DEEP = HexColor('#9B1B27')
INK = HexColor('#1F2937')
MUTED = HexColor('#64748B')
HAIR = HexColor('#E5E7EB')
TINT = HexColor('#FCF4F5')
SOFT = HexColor('#F6F3F3')
PINKLINE = HexColor('#EFE0E2')
WHITE = HexColor('#FFFFFF')
CREAM = HexColor('#FAF8F7')

FONT, BOLD = 'NotoKR', 'NotoKR-Bold'
pdfmetrics.registerFont(TTFont(FONT, str(HERE / 'fonts/NotoSansKR-Regular.ttf')))
pdfmetrics.registerFont(TTFont(BOLD, str(HERE / 'fonts/NotoSansKR-Bold.ttf')))
pdfmetrics.registerFontFamily(FONT, normal=FONT, bold=BOLD, italic=FONT, boldItalic=BOLD)

PAGE_W, PAGE_H = A4
M = 44.0                      # 좌우 여백
CW = PAGE_W - 2 * M           # 본문 폭
GAP = 9.0                     # 블록 사이 기본 간격
BODY_BOTTOM = 52.0            # 본문 하한
TOTAL_PAGES = 14

ST = {
    'body': ParagraphStyle('body', fontName=FONT, fontSize=8.5, leading=13.0,
                           textColor=INK, wordWrap=None),
    'lead': ParagraphStyle('lead', fontName=FONT, fontSize=9.2, leading=14.4,
                           textColor=INK, wordWrap=None),
    'h3': ParagraphStyle('h3', fontName=BOLD, fontSize=9.8, leading=13.4,
                         textColor=INK, wordWrap=None),
    'deck': ParagraphStyle('deck', fontName=FONT, fontSize=8.6, leading=13.2,
                           textColor=MUTED, wordWrap=None),
    'note': ParagraphStyle('note', fontName=FONT, fontSize=7.0, leading=10.4,
                           textColor=MUTED, wordWrap=None),
    'cell': ParagraphStyle('cell', fontName=FONT, fontSize=7.1, leading=10.6,
                           textColor=INK, wordWrap=None),
    'cellb': ParagraphStyle('cellb', fontName=BOLD, fontSize=7.1, leading=10.6,
                            textColor=DEEP, wordWrap=None),
    'caption': ParagraphStyle('caption', fontName=FONT, fontSize=6.6, leading=9.4,
                              textColor=MUTED, wordWrap=None),
    'cardtitle': ParagraphStyle('cardtitle', fontName=BOLD, fontSize=8.8, leading=12.4,
                                textColor=INK, wordWrap=None),
    'cardline': ParagraphStyle('cardline', fontName=FONT, fontSize=7.7, leading=11.6,
                               textColor=INK, wordWrap=None),
    'concl': ParagraphStyle('concl', fontName=BOLD, fontSize=10.6, leading=17.0,
                            textColor=WHITE, wordWrap=None),
    'quote': ParagraphStyle('quote', fontName=FONT, fontSize=8.6, leading=13.6,
                            textColor=INK, wordWrap=None),
    'status': ParagraphStyle('status', fontName=BOLD, fontSize=7.4, leading=10.8,
                             textColor=DEEP, wordWrap=None),
    'kpi_v': ParagraphStyle('kpi_v', fontName=BOLD, fontSize=14.5, leading=17,
                            textColor=RED, wordWrap=None),
    'kpi_l': ParagraphStyle('kpi_l', fontName=FONT, fontSize=6.6, leading=9.4,
                            textColor=MUTED, wordWrap=None),
    'step_t': ParagraphStyle('step_t', fontName=BOLD, fontSize=7.6, leading=10.6,
                             textColor=WHITE, wordWrap=None),
    'step_b': ParagraphStyle('step_b', fontName=FONT, fontSize=7.0, leading=10.0,
                             textColor=WHITE, wordWrap=None),
    'step_t2': ParagraphStyle('step_t2', fontName=BOLD, fontSize=7.6, leading=10.6,
                              textColor=DEEP, wordWrap=None),
    'step_b2': ParagraphStyle('step_b2', fontName=FONT, fontSize=7.0, leading=10.0,
                              textColor=INK, wordWrap=None),
}

LABELS = ('관측', '해석', '실행 제안', '제작물', '예정', '일부 제작', '내부 검토용',
          '보완 예정', '미집행', '없는 자료', '미확인', '승인 전 콘셉트')


def md(text):
    """본문 표기를 Paragraph 마크업으로 바꾼다.

    `**…**`는 굵게, 라벨 대괄호는 메디큐브 레드로 표시한다. 꺾쇠·앰퍼샌드는 먼저
    이스케이프해 태그로 읽히지 않게 한다.
    """
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = re.sub(r'`([^`]+)`', r'<font color="#475569">\1</font>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    for label in LABELS:
        text = text.replace(f'[{label}]', f'<font color="#D92B3A">[{label}]</font>')
    return text


def P(text, style='body'):
    return Paragraph(md(text), ST[style])


def px(text):
    """표 셀용 문단."""
    return Paragraph(md(text), ST['cell'])


# ── 블록 ────────────────────────────────────────────────────────────────────


class Fig(Flowable):
    """이미지 + 캡션 한 덩어리."""

    def __init__(self, path, width, caption=None, caption_style='caption'):
        super().__init__()
        self.path = str(path)
        self.target_w = width
        self.caption = Paragraph(md(caption), ST[caption_style]) if caption else None
        with PILImage.open(self.path) as im:
            self.ratio = im.width / im.height

    def wrap(self, aw, ah):
        self.img_w = min(self.target_w, aw)
        self.img_h = self.img_w / self.ratio
        self.cap_h = 0
        if self.caption:
            _, self.cap_h = self.caption.wrap(self.img_w, 200)
            self.cap_h += 3
        self.width, self.height = self.img_w, self.img_h + self.cap_h
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.drawImage(self.path, 0, self.cap_h, self.img_w, self.img_h,
                    preserveAspectRatio=True, anchor='c', mask='auto')
        if self.caption:
            self.caption.drawOn(c, 0, 0)


class FigRow(Flowable):
    """높이를 맞춘 이미지 여러 장을 한 줄로 놓는다."""

    def __init__(self, items, height, gap=9, total_width=CW):
        super().__init__()
        self.items = items
        self.h = height
        self.gap = gap
        self.total = total_width

    def wrap(self, aw, ah):
        self.sizes = []
        raw = []
        for path, cap in self.items:
            with PILImage.open(str(path)) as im:
                raw.append((path, cap, im.width / im.height))
        widths = [self.h * r for _, _, r in raw]
        scale = min(1.0, (self.total - self.gap * (len(raw) - 1)) / sum(widths))
        self.width, self.height = sum(w * scale for w in widths) + self.gap * (len(raw) - 1), self.h
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
        x = 0
        for (path, _cap, w, h), (par, ch, _) in zip(self.sizes, self.caps):
            c.drawImage(str(path), x, self.cap_h + 4, w, h,
                        preserveAspectRatio=True, anchor='c', mask='auto')
            if par:
                par.drawOn(c, x, self.cap_h + 4 - ch)
            x += w + self.gap


class VideoSlot(Flowable):
    """합본 전 영상 링크 자리. 점선 상자로 두고 완성처럼 보이지 않게 한다."""

    def __init__(self, title, body, height=42, rows=None):
        super().__init__()
        self.title = Paragraph(md(title), ST['cardtitle'])
        self.body = Paragraph(md(body), ST['note'])
        self.rows = [Paragraph(md(r), ST['note']) for r in (rows or [])]
        self.h = height

    def wrap(self, aw, ah):
        self.width = aw
        self.inner = aw - 70
        self.th = self.title.wrap(self.inner, 60)[1]
        self.bh = self.body.wrap(self.inner, 80)[1]
        self.rh = [r.wrap(self.inner, 40)[1] for r in self.rows]
        self.foot = Paragraph('초안 길이 29.8초 · 세로 1080×1920 · 내레이션·자막·CTA 포함 · 광고 집행 전 검수용',
                              ST['caption'])
        self.fh = self.foot.wrap(self.width - 36, 40)[1]
        need = self.th + self.bh + sum(self.rh) + 8 * (len(self.rh) + 2) + self.fh + 40
        self.height = max(self.h, need)
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        c.setStrokeColor(RED)
        c.setLineWidth(0.8)
        c.setDash(3, 2.4)
        c.roundRect(0.5, 0.5, self.width - 1, self.height - 1, 3.5, stroke=1, fill=0)
        c.setDash()
        cy = self.height - 32
        c.setFillColor(TINT)
        c.circle(32, cy, 15, stroke=0, fill=1)
        c.setFillColor(RED)
        path = c.beginPath()
        path.moveTo(27.5, cy + 7)
        path.lineTo(27.5, cy - 7)
        path.lineTo(38.5, cy)
        path.close()
        c.drawPath(path, stroke=0, fill=1)
        c.restoreState()

        top = self.height - 18
        self.title.drawOn(c, 56, top - self.th)
        y = top - self.th - 6
        self.body.drawOn(c, 56, y - self.bh)
        y -= self.bh + 4
        for row, rh in zip(self.rows, self.rh):
            y -= 12
            c.saveState()
            c.setFillColor(RED)
            c.circle(58, y + 2.6, 1.5, stroke=0, fill=1)
            c.restoreState()
            row.drawOn(c, 66, y - rh + 3)
            y -= rh
        c.saveState()
        c.setStrokeColor(PINKLINE)
        c.setLineWidth(0.5)
        c.setDash(2, 2)
        c.line(18, 40, self.width - 18, 40)
        c.restoreState()
        self.foot.drawOn(c, 18, 16)


class Placeholder(Flowable):
    """아직 없는 소재 자리. 점선과 안내 문구만 두고 완성처럼 보이지 않게 한다."""

    def __init__(self, title, sub, height, width):
        super().__init__()
        self.title = Paragraph(md(title), ST['status'])
        self.sub = Paragraph(md(sub), ST['note'])
        self.h, self.w = height, width

    def wrap(self, aw, ah):
        self.width = min(self.w, aw)
        self.height = self.h
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        c.setStrokeColor(PINKLINE)
        c.setLineWidth(0.9)
        c.setDash(3, 2.4)
        c.rect(0.5, 0.5, self.width - 1, self.height - 1, stroke=1, fill=0)
        c.setDash()
        tw = self.title.wrap(self.width - 16, 40)[1]
        sw = self.sub.wrap(self.width - 16, 40)[1]
        total = tw + sw + 4
        top = (self.height + total) / 2
        self.title.drawOn(c, 8, top - tw)
        self.sub.drawOn(c, 8, top - tw - sw - 4)
        c.restoreState()


def fig(path, width=CW, caption=None):
    return ('fig', str(path), width, caption)


def figrow(items, height):
    return ('figrow', items, height)


def table(header, rows, widths, align_top=True):
    return ('table', header, rows, widths)


def box(kind, title, lines):
    return ('box', kind, title, lines)


def steps(items, inverse_last=False):
    return ('steps', items, inverse_last)


def kpi(items):
    return ('kpi', items)


# ── flowable 조립 ───────────────────────────────────────────────────────────


def as_flowables(entry, width=CW):
    """블록 정의 하나를 flowable 목록으로 바꾼다. width는 칸 폭."""
    kind = entry[0]
    if kind == 'p':
        return [P(entry[1], entry[2] if len(entry) > 2 else 'body')]
    if kind == 'note':
        return [P(entry[1], 'note')]
    if kind == 'status':
        return [status_bar(entry[1], width)]
    if kind == 'h3':
        return [h3_block(entry[1])]
    if kind == 'ul':
        return [Paragraph(f'<font color="#D92B3A">▪</font>&nbsp;&nbsp;{md(i)}', ST['body'])
                for i in entry[1]]
    if kind == 'ol':
        return [Paragraph(f'<font color="#D92B3A"><b>{n}</b></font>&nbsp;&nbsp;{md(i)}', ST['body'])
                for n, i in enumerate(entry[1], 1)]
    if kind == 'table':
        return [make_table(entry[1], entry[2], entry[3], width)]
    if kind == 'box':
        return [make_box(entry[1], entry[2], entry[3], width)]
    if kind == 'fig':
        return [Fig(entry[1], min(entry[2], width), entry[3])]
    if kind == 'figrow':
        return [FigRow(entry[1], entry[2], total_width=width)]
    if kind == 'video':
        return [VideoSlot(entry[1], entry[2])]
    if kind == 'vslot':
        return [VideoSlot(entry[1], entry[2], entry[3], entry[4] if len(entry) > 4 else None)]
    if kind == 'big':
        return [Paragraph(md(entry[1]), ParagraphStyle(
            'big', fontName=BOLD, fontSize=entry[2], leading=entry[2] * 1.3, textColor=INK))]
    if kind == 'toc':
        return [Paragraph(f'<font color="#D92B3A"><b>{no}</b></font>&nbsp;&nbsp;{md(title)}',
                          ParagraphStyle('toc', parent=ST['cell'], fontSize=9.0, leading=17.0))
                for no, title in entry[1]]
    if kind == 'ph':
        return [Placeholder(entry[1], entry[2], entry[3], entry[4])]
    if kind == 'kpi':
        return [make_kpi(entry[1], width)]
    if kind == 'steps':
        return [make_steps(entry[1], entry[2], width)]
    if kind == 'space':
        return [Spacer(entry[1])]
    if kind == 'raw':
        value = entry[1]
        return list(value) if isinstance(value, list) else [value]
    raise ValueError(kind)


class Spacer(Flowable):
    def __init__(self, h):
        super().__init__()
        self.h = h

    def wrap(self, aw, ah):
        return (0, self.h)

    def draw(self):
        pass


class Rule(Flowable):
    """굵은 머리글 아래 짧은 액센트 선."""

    def __init__(self, text, gap=4):
        super().__init__()
        self.par = Paragraph(md(text), ST['h3'])
        self.gap = gap

    def wrap(self, aw, ah):
        self.width = aw
        self.th = self.par.wrap(aw - 14, 100)[1]
        self.height = self.th + self.gap + 3
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(RED)
        c.rect(0, self.height - self.th - 1, 2.6, self.th - 1, stroke=0, fill=1)
        self.par.drawOn(c, 8, self.height - self.th - 1)


def h3_block(text):
    return Rule(text)


def status_bar(text, width=CW):
    par = Paragraph(md(text), ST['status'])
    t = Table([[par]], colWidths=[CW])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), TINT),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEBEFORE', (0, 0), (0, -1), 2.4, RED),
    ]))
    return t


def make_table(header, rows, widths, width=CW):
    col = [width * w for w in widths]
    data = []
    if header:
        data.append([Paragraph(md(h), ST['cellb']) for h in header])
    for row in rows:
        data.append([px(c) for c in row])
    t = Table(data, colWidths=col, repeatRows=1 if header else 0)
    style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, -1), 0.4, HAIR),
        ('LINEABOVE', (0, 0), (-1, 0), 1.1, RED),
    ]
    if header:
        style.append(('BACKGROUND', (0, 0), (-1, 0), TINT))
    t.setStyle(TableStyle(style))
    return t


def make_box(kind, title, lines, width=CW):
    inner = []
    if title:
        style = 'cellb' if kind != 'conclusion' else 'status'
        par = Paragraph(md(title), ST[style] if kind != 'conclusion' else ParagraphStyle(
            'concltitle', parent=ST['status'], textColor=HexColor('#F3C9CD')))
        inner.append(par)
    for line in lines:
        if kind == 'conclusion':
            inner.append(Paragraph(md(line), ST['concl']))
        elif kind == 'warn':
            inner.append(P(line, 'body'))
        else:
            inner.append(P(line, 'quote'))
    t = Table([[inner]], colWidths=[width])
    if kind == 'conclusion':
        bg, line_color, lw = DEEP, DEEP, 0
        pads = (13, 13)
    elif kind == 'warn':
        bg, line_color, lw = HexColor('#FDF3F4'), RED, 2.4
        pads = (9, 9)
    else:
        bg, line_color, lw = TINT, RED, 2.4
        pads = (9, 9)
    style = [
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('LEFTPADDING', (0, 0), (-1, -1), pads[0]),
        ('RIGHTPADDING', (0, 0), (-1, -1), pads[1]),
        ('TOPPADDING', (0, 0), (-1, -1), 12 if kind == 'conclusion' else 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12 if kind == 'conclusion' else 8),
    ]
    if lw:
        style.append(('LINEBEFORE', (0, 0), (0, -1), lw, line_color))
    t.setStyle(TableStyle(style))
    return t


def make_kpi(items, width=CW):
    cells = []
    for value, label in items:
        cells.append([Paragraph(md(value), ST['kpi_v']), Paragraph(md(label), ST['kpi_l'])])
    t = Table([cells], colWidths=[width / len(items)] * len(items))
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('BACKGROUND', (0, 0), (-1, -1), CREAM),
        ('LINEABOVE', (0, 0), (-1, 0), 2.0, RED),
        ('LINEBEFORE', (1, 0), (-1, 0), 0.5, PINKLINE),
    ]))
    return t


def make_steps(items, inverse_last=False, width=CW):
    cells = []
    for i, (label, body) in enumerate(items):
        dark = inverse_last and i == len(items) - 1
        cells.append([
            Paragraph(md(label), ST['step_t'] if dark else ST['step_t2']),
            Paragraph(md(body), ST['step_b'] if dark else ST['step_b2']),
        ])
    t = Table([cells], colWidths=[width / len(items)] * len(items))
    style = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('BACKGROUND', (0, 0), (-1, -1), TINT),
        ('LINEBEFORE', (1, 0), (-1, 0), 2.0, WHITE),
    ]
    if inverse_last:
        style.append(('BACKGROUND', (len(items) - 1, 0), (len(items) - 1, 0), DEEP))
    t.setStyle(TableStyle(style))
    return t


def cards(items, gap=10, width=CW):
    """카드 2~3장을 한 줄로 놓는다."""
    cells = []
    for title, badge, lines, foot in items:
        inner = [Paragraph(md(title), ST['cardtitle'])]
        if badge:
            inner.append(Paragraph(md(badge), ST['status']))
        for line in lines:
            inner.append(P(line, 'cardline'))
        if foot:
            inner.append(Paragraph(md(foot), ST['note']))
        cells.append(inner)
    n = len(items)
    t = Table([cells], colWidths=[(width - gap * (n - 1)) / n] * n, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 9),
        ('RIGHTPADDING', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, -1), CREAM),
        ('LINEABOVE', (0, 0), (-1, 0), 2.0, RED),
        ('LINEBEFORE', (1, 0), (-1, 0), gap, WHITE),
    ]))
    return ('raw', t)


def cols(left, right, ratio=0.5, gap=12):
    """두 칸 레이아웃. 각 칸은 블록 목록."""
    return ('cols', left, right, ratio, gap)


def raw(flowable):
    return ('raw', flowable)


def toc_lines(lines):
    return ('toc', lines)


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

PAGES = [
    {
        'no': 1, 'kicker': 'COVER', 'title': '표지', 'layout': 'cover',
        'deck': None, 'blocks': [],
    },
    {
        'no': 2, 'kicker': 'PROFILE & CAPABILITY', 'title': '프로필 & 핵심 역량',
        'deck': '이력과 자격이 이번 프로젝트에서 어떤 작업으로 이어졌는지 1:1로 적었습니다.',
        'blocks': [
            cols([
                ('ph', '프로필 사진 자리', '[보완 예정] 지원자 확인 후 삽입', 190, 172),
                ('big', '김윤서', 15),
                ('p', '숙명여자대학교 소프트웨어융합전공 · 2025.08 졸업'),
                ('p', '팀스파르타 KDT 데이터 분석가 양성과정 · 2025.12–2026.05'),
                ('p', '**자격** SQLD 2025.04 · ADsP 2025.09 · 빅데이터분석기사 2026.07'),
                ('note', '지원 직무 — 에이피알(APR) [마케팅 특별채용] 국내 콘텐츠 마케팅 신입'),
            ], [
                ('table', ['이력·역량', '이번 프로젝트에서 한 일'], [
                    ['데이터 수집', '네이버 데이터랩·쇼핑인사이트 원자료 13개(데이터랩 9·쇼핑인사이트 4), 구글 트렌드 CSV 13종, 올리브영 Top100 실측, 스니핏 10구간 스크린숏을 직접 확보'],
                    ['검증·재계산', '원자료 재계산 **141항목 불일치 0건**, MD↔PDF **8쌍** 본문 대조, 리뷰 **535건** 전수 코딩'],
                    ['경쟁 대조', '메타 광고 라이브러리 **7개 브랜드** 실측, 경쟁사 원소재 고유·과장 표현 대조(중복 0건)'],
                    ['AI 영상·시안 기획', '30초 콘티 v1.2 설계, **Kling·Higgsfield로 AI 생성한 인물 클립 3개**, **AI TTS 내레이션 7구간**, 홈쇼핑 정적 시안·3면 배치 SVG 제작'],
                    ['문서·조판', '보고서 8편을 같은 CSS로 PDF화하고 MD↔PDF 본문을 대조, 이 포트폴리오도 코드로 조판'],
                ], [0.26, 0.74]),
                ('note', '[AI 제작] 숏폼 인물 클립·내레이션·포스터 연출 컷은 생성형 AI로 만들었고, 8·9·14쪽에 범위를 적었습니다.'),
            ], ratio=0.40),
            ('h3', '이 프로젝트에서 남긴 검증 숫자'),
            ('kpi', [('141', '원자료 재계산 항목 · 불일치 0건'), ('8', '보고서 MD↔PDF 대조 쌍'),
                     ('535', '리뷰 전수 코딩 건수'), ('13', '구글 트렌드 CSV 세트')]),
            box('quote', '이 포트폴리오의 작업 원칙', [
                '**① 확인된 것과 판단한 것을 나눠 쓴다** — [관측]·[해석]·[실행 제안]·[제작물] 라벨을 쪽마다 붙였습니다.',
                '**② 없는 성과는 만들지 않는다** — 매출·ROAS·방송 효과는 판정하지 않고 미판정으로 남겼습니다.',
                '**③ 검증은 다시 돌릴 수 있게** — 원자료 재계산과 MD↔PDF 대조를 저장소 스크립트로 재실행할 수 있습니다.',
            ]),
            ('note', '[보완 예정] 프로필 사진과 최종 이력서 항목은 지원자 확인 후 확정합니다.'),
        ],
    },
    {
        'no': 3, 'kicker': 'CONTENTS & SCOPE', 'title': '목차 + 프로젝트 개요',
        'deck': '조사 순서가 아니라 읽는 순서로 배열했습니다. 4쪽이 결론이고 5쪽부터가 근거입니다.',
        'blocks': [
            ('h3', '목차 — 4~14쪽'),
            cols([toc_lines([(4, '핵심 결론 한눈에 보기'), (5, '국내·글로벌 트렌드 핵심 요약'),
                             (6, '2030·5060 타깃 선정 근거'), (7, '2030 글로우 제품 선정 근거'),
                             (8, '2030 글로우 전략 & 콘티 v1.2'), (9, '2030 글로우 제작물')])],
                 [toc_lines([(10, '5060 GS샵 X2 채널·상품 선정 근거'), (11, '5060 내부 개선 기획안(3면 고도화)'),
                             (12, '5060 2027년 5월 방송 연계 기획'), (13, '5060 홈쇼핑 메인·상세페이지 시안'),
                             (14, '한계, 검증 데이터 & 역할·부록')])]),
            steps([('근거', '5쪽 트렌드\n6쪽 타깃'), ('선택', '7쪽 제품\n10쪽 채널'),
                   ('실행', '8–9쪽 2030\n11–13쪽 5060'), ('한계', '14쪽 미판정\n필요 데이터')]),
            box('quote', '프로젝트 질문',
                ['공개 데이터만으로 메디큐브의 콘텐츠·채널 기회를 어디까지 판단할 수 있고, '
                 '그 판단을 어떤 콘텐츠로 실행할 수 있는가.']),
            ('h3', '자료 범위'),
            ('table', ['자료', '범위'], [
                ['네이버 데이터랩·쇼핑인사이트', '**데이터랩 54주·쇼핑인사이트 52주** · 브랜드 5사·5060 전용 5사·라인·디바이스'],
                ['구글 트렌드', '**CSV 13종** · 미국·영국·일본'],
                ['올리브영 Top100', '실측 1회 · 2026-11-20 04:08 KST 저장'],
                ['스니핏', '**10구간** 스크린숏 **27장**'],
                ['리뷰 535건', '글로우 **232**(공식몰 217·글로우픽 15) + 글로우픽 미니 **82** + GS샵 X2 **221**'],
            ], [0.3, 0.7]),
            ('note', '공식몰 미니 200건은 미니 기존안 검토에만 써서 합산 735건입니다. 535건은 본문에 인용한 모집단입니다.'),
            ('h3', '만드는 순서 — 수집에서 조판까지'),
            steps([('수집', '원자료\n직접 확보'), ('코딩', '리뷰 535건\n전수 코딩'), ('재계산', '141항목\n불일치 대조'),
                   ('검수', '표현·경계\n문구 검토'), ('조판', 'MD↔PDF\n본문 대조')]),
            ('p', '[없는 자료] 매출·주문 로그, 광고 계정, 방문 로그 — 4쪽 경계 문구와 14쪽 한계로 연결했습니다.'),
        ],
    },
    {
        'no': 4, 'kicker': 'EXECUTIVE SUMMARY', 'title': '핵심 결론 한눈에 보기',
        'deck': '이 쪽만 읽어도 무엇을 왜 기획했고, 무엇을 주장하지 않는지 남도록 썼습니다.',
        'blocks': [
            box('conclusion', None, [
                '공개 근거로 **2030 부스터 글로우(숏폼·포스터)** 와 **5060 GS샵 X2(홈쇼핑 시안·내부 개선안)** '
                '두 축을 **조건부**로 기획했습니다.']),
            cards([
                ('01 · 2030 부스터 글로우', '콘텐츠 실험 1순위 · 조건부 채택',
                 ['여성 19–39세·5/1 올리브영 선출시 이후(5/4–11/9) 같은 조건에서 **28주 모두** 미니를 앞섰습니다(상위 3주를 빼도 25주).',
                  '리뷰·공식 정보로 소구 9개를 골라 30초 3샷으로 옮겼습니다.'],
                 '[제작물] Shot 1–3 **AI 생성** 클립·포스터 시안 완료 · 29.8초 조립 초안(비공개) [일부 제작]'),
                ('02 · 5060 GS샵 X2', '방송 연계안 · 조건부 설계',
                 ['GS샵 첫 방송 이력(**2026-05-09**)과 상품평 **221건**이 공개돼 방송 전후 고객 안내물을 설계했습니다.',
                  '**5060 구매 우위 데이터가 아니라**, 안내·개선 프로토타입을 설계하는 **테스트 케이스**입니다.'],
                 '[제작물] 내부 개선 요약 시안 완료 · 고객용 1–2면 비공개 시안(공개 지면 미삽입)'),
            ]),
            figrow([
                ('design/glow_2030_main_poster.png', '2030 숏폼 연계 포스터 시안 — 최종 검수 대기'),
                ('design/gs_x2_2027_static_storyboard.png', '5060 스토리보드 v0.3 화면 1–2 — 고객용 고도화 시안은 비공개(공개 지면 미삽입)'),
            ], 240),
            box('quote', '이 문서에서 "조건부"란', [
                '검증 게이트를 통과할 때만 집행하는 제안입니다. 7쪽 제품 채택, 11·13쪽 5060 시안과 개선안, '
                '12쪽 편성안이 모두 여기에 해당하며, 게이트를 통과하지 못하면 집행하지 않습니다.']),
            steps([('4쪽', '결론'), ('5–6쪽', '근거와 타깃'), ('7–9쪽', '2030 실행'),
                   ('10–13쪽', '5060 실행'), ('14쪽', '한계와 부록')]),
            box('boundary', '미판정 경계', [FIXED_LIMIT]),
        ],
    },
    {
        'no': 5, 'kicker': 'MARKET SIGNALS', 'title': '국내·글로벌 트렌드 핵심 요약',
        'deck': '피크 5주 중 4주는 시장이 함께 오른 주였습니다. 메디큐브만의 상승으로 읽지 않았습니다.',
        'blocks': [
            fig('tmp/portfolio/peakmap.png', CW,
                '그림 1 · 메디큐브 검색 피크 Top 5주(▼)와 경쟁사 급등 시점 — 같은 주 함께 급등은 채운 점, '
                '단독 급등은 빈 점. 붉은 띠는 세일 주 (자료: 네이버 데이터랩 54주)'),
            ('kpi', [('4주', '피크 Top 5 중 경쟁사 동반 상승'), ('8/3', '디바이스 4사 동시 상승 주'),
                     ('35.1%', '영국 온라인 뷰티 내 아마존 UK (2023-04까지 12개월)'),
                     ('25~30%', '일본 온라인 뷰티 내 Qoo10 (2025-03·2026 발표)')]),
            ('p', '[관측] 피크 Top 5주(2026-11-02·08-03·05-04·03-02·06-29) 중 11/02·03/02·05/04·06/29 '
                  '네 주는 경쟁사가 함께 오른 주이고, 8/3만 디바이스 4사가 동시에 움직인 주입니다.'),
            ('p', '[해석] 시장이 함께 오른 주를 메디큐브만의 상승으로 읽지 않았습니다. 5/4 주의 상승은 '
                  '한 해의 한 주에 대한 관찰치이므로 시즌 효과로 확정하지 않습니다.'),
            ('h3', '전략적 시사점 — 왜 디바이스 중심인가'),
            ('ul', [
                '경쟁 4사는 **올리브영 세일가·1+1·어워즈 1위**를 카피 앞머리에 두고 랜딩도 올리브영으로 보냅니다'
                '(메타 광고 라이브러리 **7개 브랜드** 실측 · 스니핏 **10구간 27장**, 2026-11-20).',
                '메디큐브만 **디바이스+자사몰** 축으로 움직입니다.',
                '그래서 콘텐츠를 세일 경쟁이 아니라 **디바이스 사용 상황·제품 이해**로 잡았습니다 — 이 쪽의 판단은 모두 그 실측에 기댑니다.',
            ]),
            ('h3', '글로벌 — 세 방향과 채널 구조'),
            ('p', '미국 1위 유지·영국 상승·일본 하락의 세 방향을 채널 구조와 함께 봤습니다. 영국은 '
                  '뷰티 소비의 45.5%가 온라인(**2025년** 영국 뷰티 시장 기준)이고 그 온라인의 35.1%가 '
                  '아마존 UK(**2023-04까지 12개월** 온라인 뷰티 매출 점유)·틱톡샵 9.8%(**2025년 누계**)이며, 일본은 '
                  '화장품 이커머스 비중이 10% 미만(**2026-04 보도**, E85)이고 그 온라인의 1위가 Qoo10(25~30%, **2025-03 베인·2026 자사 발표**)입니다. '
                  '시점이 다른 값은 합산하지 않았고, 채널 구성이 검색 추세의 원인이라고 단정하지 않았습니다.'),
            ('note', '국내 본문에서는 글로벌을 1~2문장으로만 쓰고, 상세는 글로벌 트렌드 보고서(v1.3)로 넘깁니다.'),
        ],
    },
    {
        'no': 6, 'kicker': 'TARGET SELECTION', 'title': '2030·5060 타깃 선정 근거',
        'deck': '두 타깃을 구매층이 아니라 콘텐츠 기회의 축으로 골랐습니다. 서로 다른 분모의 지표를 퍼널로 빼지 않았습니다.',
        'blocks': [
            ('table', ['구분', '판단 기준', '관측 근거 — 도구·연령·비교군·기간', '경계'], [
                ['**2030**', '검색 관심과 리뷰에서 콘텐츠 질문을 구체화할 수 있는 축 — **콘텐츠 실험 1순위 조건부 채택**',
                 '데이터랩 브랜드 검색 비중 **45.8%**(여성 19–39세·5개 브랜드 안·54주 중 최근 13주·1위) · '
                 '쇼핑인사이트 스킨케어 클릭 **9.3%**(20·30대·스킨케어 5개 브랜드 안·52주 중 최근 13주·4위) · '
                 '글로우픽 리뷰 **82건 중 74건(90.2%)**이 20·30대 표기',
                 '두 지표는 도구·연령 필터·분모가 달라 퍼널로 빼지 않음. **90.2%**는 수집 리뷰 82건 안의 분포이며 전체 고객 연령 비중이 아님'],
                ['**5060**', '**사업상 탐색 타깃** — 공개 근거를 연결할 수 있는 축(구매층 아님)',
                 '데이터랩 기기 검색 **5.6%**(5060 여성·5060 전용 5사 안·54주 중 최근 13주·5위) · '
                 '쇼핑인사이트 이미용가전 클릭 **74.3%**(5060 여성·5060 전용 5개 키워드 안·52주 중 최근 13주·1위) · '
                 '스킨케어 클릭 **6.5%**(5060 여성·5060 전용 5사 안·52주 중 최근 13주·4위, 1년 +5.3p.p.) · '
                 '실장님 인터뷰의 "5060 고객 유입" 과제가 출발점',
                 '도구·키워드·기간이 달라 두 값을 퍼널 두 단계로 읽지 않음. **자사 매출 미확인**·X2 구매 우위 미판정 → 사업상 탐색 타깃으로만 표기'],
            ], [0.08, 0.24, 0.39, 0.29]),
            ('kpi', [('45.8%', '2030 브랜드 검색 비중 · 데이터랩 5사 안'), ('9.3%', '스킨케어 클릭 2030 · 쇼핑인사이트 5사'),
                     ('5.6%', '5060 기기 검색 · 5060 전용 5사 5위'), ('74.3%', '이미용가전 클릭 5060 · 5개 키워드 1위')]),
            fig('tmp/portfolio/search3.png', CW,
                '그림 2 · 메디큐브 브랜드 검색 지수 — 전체·여성 5060·여성 2030, 시작 주 100 '
                '(네이버 데이터랩 54주, 2025-11~2026-11)'),
            ('h3', '선정 기준 3개'),
            ('p', '① 공개 데이터로 **관측이 가능한가** ② 콘텐츠로 **실행할 형식이 있는가** '
                  '③ 확인되지 않은 것을 확인된 것처럼 쓰지 않고 **설계할 수 있는가**.'),
            ('table', ['타깃', '콘텐츠 실행 형식', '판정 상태'], [
                ['2030', '숏폼 30초 · 연계 포스터 (8–9쪽)', '콘텐츠 실험 1순위 **조건부 채택**'],
                ['5060', '홈쇼핑 1–2면 시안 · 내부 개선 기획안 (11·13쪽)', '방송 연계 **조건부 설계**'],
            ], [0.1, 0.52, 0.38]),
            ('note', '모든 비중은 **비교군 안의 몫**입니다 — 데이터랩 2025-11-03–2026-11-09 **54주**, 쇼핑인사이트 '
                     '2025-11-03–2026-10-26 **52주**, 값은 각 계열 **최근 13주 평균**입니다. 5060은 구매층이 아니라 '
                     '**탐색 타깃**이며, 5.6%와 74.3%는 도구·키워드가 달라 직접 비교하지 않습니다.'),
        ],
    },
    {
        'no': 7, 'kicker': 'PRODUCT SELECTION', 'title': '2030 글로우 제품 선정 근거',
        'deck': '미니 기존안을 보류하고 부스터 글로우를 콘텐츠 실험 1순위로 조건부 채택했습니다.',
        'blocks': [
            box('conclusion', None, [
                '매출 주력 여부와 미니 대비 우위는 판정하지 않았습니다. '
                '**콘텐츠로 실험할 1순위**만 정했습니다.']),
            ('kpi', [
                ('28주', '여성 19–39세 같은 조건 · 5/4–11/9 미니 초과'),
                ('25주', '상위 피크 3주 제외 후에도 모두 초과'),
                ('7.5 → 6.9', '28주·25주 합산 지수비 · 최근 13주 9.5'),
                ('−24.6%', '최근 4주(10/19–11/9) 평균 검색 · 판매량 아님'),
            ]),
            ('h3', '근거 1 — 같은 조건 검색 비교'),
            ('p', '여성 19–39세 동일 조회(**2026-05-04–11-09 28주**)에서 글로우는 출시 후 **28주 모두** 미니를 '
                  '앞섰고, 상위 피크 3주를 빼도 **25주 모두** 앞섰습니다. 출시일은 출시 전 4/20 첫 비영값을 쓰지 않고 '
                  '**5/1 올리브영 선출시**에 맞춰 **5/4 주부터** 비교했습니다. 검색 지수이며 **판매량은 확인되지 않았습니다**.'),
            ('h3', '근거 2 — 공식 정보·리뷰 대조로 소구 9개 추리기'),
            ('p', '공식 비교표·FAQ·상세 이미지로 물방울 초음파·**170g**·**5모드**·**12분** 루틴을 확인하고, '
                  '공식몰 키워드 **O01–O12**와 리뷰 주제 **R01–R06**을 대조했습니다.'),
            ('table', ['판정', '소구 후보', '적용', '근거'], [
                ['**채택**', '1·3. 속건조 보습 + 푸석함 물광', 'Shot 1·3', 'O03 + R01(37건)·R03(42건)·R02(24건)'],
                ['**채택**', '2. 탄력 관리', 'Shot 2', '리뷰 건수 집계가 아니라 공식 5모드(**포커스 모드** 포함) 기능 소구 + 30대 직장인 상황 연결 · 리프팅 단정 없음'],
                ['**채택**', '5. 고민별 5가지 모드', 'Shot 3·4', '서로 다른 2030 고민을 한 기기로 묶는 근거(O04·O06)'],
                ['조건부', '7. 매일 12분 홈케어 루틴', 'Shot 2·4', 'O10 + R05 · 시술 대체 표현은 금지선 위반으로 제외'],
                ['제외', '4. 민감 피부 밸런싱·진정', '—', 'R06 중단 사례 · 무자극 단정 금지와 충돌'],
                ['제외', '6. 비싼 피부과 대체 경제성', '—', '시술 대체 표현 금지선과 직접 충돌'],
                ['제외', '8. 임상 결과 신뢰성', '—', '임상 원문·피험자·수치 조건 전수 검수 미완료'],
                ['제외', '9. 저렴한 가격 소구', '—', '리뷰의 가격 부담과 충돌 · 가격은 랜딩에 위임'],
            ], [0.1, 0.31, 0.11, 0.48]),
            ('h3', '근거 3 — 반대 신호 처리'),
            ('p', '미니 리뷰에서 휴대·여행 소구가 **57.5%**(공식몰 미니 리뷰 200건 CSV 태그 중 115건)로 확인돼, 글로우를 "가볍다·간편하다"로 파는 후킹은 '
                  '주 후킹에서 보류했습니다. 검색 하락(여성 19–39세·최근 4주 10/19–11/9 평균 **−24.6%**)도 지우지 않고 함께 적었습니다.'),
            box('quote', '판정을 미룬 것', [
                '**매출 주력 여부 · 미니 대비 우위** — 검색 지수는 판매량이 아니고 두 제품의 판매 자료가 없습니다.',
                '**미니 기존안 폐기** — 미니는 별도 태그 검토 대상으로 남겼고, 추출 기준 적합성은 미확인입니다.' ]),
            ('note', '검색 지수는 **검색 관심도**이며 판매량이 아닙니다. 소구 채택은 메시지 효과 검증이 아닙니다. '
                     '글로우와 X2(10쪽)는 타깃·근거가 달라 같은 축에서 비교하지 않았습니다.'),
        ],
    },
    {
        'no': 8, 'kicker': 'CREATIVE STRATEGY', 'title': '2030 글로우 전략 & 콘티 v1.2',
        'deck': '30초를 고민 1개 → 제품 이유 1개 → 자사몰 비교 랜딩의 세 샷과 CTA로 나눴습니다.',
        'blocks': [
            ('p', '**[왜 숏폼인가]** ① 메타 광고 라이브러리 **7개 브랜드** 실측에서 경쟁사 주력 소재가 동영상·릴스형이고 메디큐브도 동영상+정적 혼합입니다. '
                  '② 지원 직무가 숏폼 제작과 자사몰 연결을 요구합니다. ③ 글로우 5모드·12분 루틴이 아침 강의실·퇴근길·거울 앞 상황 컷에 맞습니다. '
                  'CTR·전환은 **미집행 파일럿 실험 대상**이며, 이 쪽은 소재 설계와 검수까지입니다.'),
            ('h3', '30초 구조'),
            steps([('0–7초', '샷 1 · 아침 속건조'), ('7–14초', '샷 2 · 밤 탄력'),
                   ('14–21초', '샷 3 · 외출 전 피부결'), ('21–30초', 'CTA · 자사몰 비교 랜딩')],
                  inverse_last=True),
            ('h3', '컷별 설계 — 고민 1개와 제품 이유 1개'),
            ('table', ['시간', '상황', '고민 → 훅', '검수 지시'], [
                ['0–7초', '20대 · 강의실 아침', '"기초 바른 지 얼마나 됐다고 속건조가…" → 물방울 초음파',
                 'O02·O03·R01·R04 · 전후 비교·흡수율 % 단정 금지'],
                ['7–14초', '30대 · 퇴근길 거실', '"야근이라 관리할 시간도 없네…" → 집에서 하루 12분',
                 'O06·O10·R05 · "피부과 안 가도" 금지'],
                ['14–21초', '20대 · 화장실 거울', '"뭘 발라도 뜨는 느낌" → 5가지 모드',
                 'O04·O06·R02·R03 · 민감 진정·무자극 금지'],
                ['21–30초', '모션 타이포 CTA', '속건조·탄력·물광 → 5가지 모드 · 하루 12분',
                 'O11 · 가격·할인율 미표기 · 자사몰 비교 랜딩'],
            ], [0.1, 0.19, 0.36, 0.35]),
            ('h3', '샷별 생성 방식과 검수 포인트'),
            ('table', ['샷', '생성 도구', '검수 포인트'], [
                ['샷 1', 'Kling', '표정·제스처만 생성 · 립싱크 없음 · 전후 비교 금지'],
                ['샷 2', 'Higgsfield', '12분 시계 그래픽 · 30초 안에 관리가 끝나는 연출 금지'],
                ['샷 3', 'Kling', '제품 실물 컷은 권한 확인 시만 · 미확인 시 모션 타이포 대체'],
                ['CTA', 'CapCut', '가격·할인율 미표기 · 자사몰 비교 랜딩 연결'],
            ], [0.12, 0.2, 0.68]),
            ('h3', '표현 검수 — 경쟁사 원소재와 대조'),
            ('p', '경쟁사 원소재(B01 메디힐·B02 토리든·B03 톰더글로우)의 고유·과장 표현(1위·1+1·물광 생성기·'
                  '무자극·한정 완판 등)을 **전부 쓰지 않아 중복 0건**으로 통과했습니다. 메디큐브 금지선'
                  '(여배우·전문기관 동일·100% 찐리뷰·전후 비교·시술 대체)도 배제했습니다.'),
            ('h3', 'AI 제작 표기와 난이도 절감'),
            ('p', '**인물 클립 3개(Kling 2·Higgsfield 1)와 7개 구간 내레이션(AI TTS)은 AI로 생성**했습니다 — '
                  '실제 촬영·성우 녹음이 아닙니다. 인물 컷은 표정·제스처만 생성해 립싱크를 피하고, '
                  '마무리는 CapCut 모션 타이포로 처리합니다. 제품 시연과 금지 부위 접촉은 넣지 않았습니다.'),
            box('quote', '마무리 3키워드와 고지', [
                '"속건조 · 탄력 · 물광까지, 5가지 모드로 하루 12분 — 에이지알 부스터 글로우"',
                '하단 고지 — 수분감 있는 젤 크림 등과 함께 · 사용 시간·주기는 공식 가이드 확인. '
                'CTA는 "내 루틴에 맞는 사용법 확인하기"로 자사몰 비교 랜딩에 연결합니다.']),
            ('note', '이 검수는 **메시지 효과 검증이 아니며**, A/B 결과를 만들 수 없습니다.'),
        ],
    },
    {
        'no': 9, 'kicker': 'CREATIVE OUTPUTS', 'title': '2030 글로우 제작물',
        'deck': '포스터 시안과 숏폼 브릿지·엔드카드 4종을 만들었고, 30초 합본은 29.8초 조립 초안까지입니다.',
        'blocks': [
            ('status', '[일부 제작] · Shot 1–3 AI 생성 클립 + 29.8초 조립 초안(비공개) · 최종 시청·음성 검수 대기'),
            cols([
                ('fig', 'design/glow_2030_main_poster.png', 218,
                 '포스터 1080×1350 · 생활 장면 3컷 중 연출 컷 AI 생성 · 제품 실물 이미지 미사용 · 최종 검수 대기'),
            ], [
                ('vslot', '숏폼 29.8초 · 재생 링크와 QR 자리',
                 '[조립 초안 — 비공개 제출용] Shot 1–3 클립을 FFmpeg로 1080×1920·30fps로 이어 붙였고 '
                 'CapCut 최종 편집본은 아닙니다. 음성은 7개 구간 AI TTS, 배경 패드는 자체 제작입니다. '
                 '링크·QR은 최종 시청·음성·권리 검수 뒤 넣습니다.', 216,
                 ['Shot 1 · Kling — 아침 속건조',
                  'Shot 2 · Higgsfield — 밤 탄력',
                  'Shot 3 · Kling — 외출 전 피부결',
                  'CTA · CapCut — 자사몰 비교 랜딩']),
            ], ratio=0.48),
            figrow([
                ('design/glow_2030_bridge_01_bright.png', '브릿지 01 · 3중 주파수 물방울 초음파'),
                ('design/glow_2030_bridge_02_modes_bright.png', '브릿지 02 · 5가지 모드'),
                ('design/glow_2030_bridge_03_time_bright.png', '브릿지 03 · 12분 루틴'),
                ('design/glow_2030_endcard_bright.png', '엔드카드 · 자사몰 CTA'),
            ], 156),
            ('ul', [
                'Shot 1·3은 **Kling**, Shot 2는 **Higgsfield**로 **AI 생성**한 인물 클립입니다(shots/shot1–3.mp4). 7개 구간 내레이션은 **AI TTS**입니다.',
                '브릿지·엔드카드 4종은 2026-11-21 커밋 7372794에서 다듬은 SVG 시안이고, 포스터는 AI 연출 컷을 조합한 시안으로 최종 검수 대기입니다.',
                '제품 사진·TTS가 들어간 조립본과 헬로키티 별도 포스터는 `private_submission/`에만 두었고 이 공개 PDF에는 넣지 않았습니다. 실제 광고 집행·성과는 없습니다.',
            ]),
        ],
    },
    {
        'no': 10, 'kicker': 'CHANNEL & PRODUCT', 'title': '5060 GS샵 X2 채널·상품 선정 근거',
        'deck': '5060의 X2 구매 비중과 홈쇼핑 이용률 통계는 확인되지 않았습니다. 공개 근거를 연결할 수 있는 채널로 GS샵을 먼저 골랐습니다.',
        'blocks': [
            ('h3', '연결된 공개 근거'),
            ('table', ['항목', '내용'], [
                ['첫 방송', '**2026-05-09** · [메디큐브] 부스터프로 시즌2 찬스쇼 단독 런칭 (핑크) · '
                            '상품번호 **1117330943**'],
                ['상품평', '**221건** · 수집 2026-05-10~2026-11-10 · 평점 **4.6**'],
                ['채널 대조', 'CJ온스타일·롯데 — 메디큐브 X2 방송 이력 확인 수준까지'],
            ], [0.18, 0.82]),
            ('h3', '왜 여기인가 — 판정이 아니라 테스트 케이스'),
            ('p', 'GS샵에서 메디큐브 X2 방송 이력이 확인되고 상품·후기·문의가 공개돼 있어 **방송 전후 고객 안내물**을 '
                  '설계할 수 있습니다. **5060의 홈쇼핑 이용률·연령별 주문 통계는 없고**, 리뷰 221건 중 연령 표기는 '
                  '**3건(1.4%)**뿐입니다. 그래서 X2를 5060 구매 우위 데이터가 아니라 **안내·개선 프로토타입을 설계하는 테스트 케이스**로 씁니다.'),
            ('ul', [
                '**방송 이력이 공개돼 있다** — 2026-05-09 첫 방송과 상품번호를 확인할 수 있습니다.',
                '**상품·후기·문의가 공개돼 있다** — 상품평 221건을 전수 코딩할 수 있었습니다.',
                '**방송 전후 안내물을 설계할 형식이 있다** — 고객이 구성·부속·사용법을 확인할 지면이 필요합니다.',
            ]),
            box('warn', '단정하지 않은 것', [
                '221건 중 방송·찬스쇼 언급 **12건(5.4%)**, 연령을 스스로 밝힌 리뷰 **3건(1.4%)** 입니다. '
                '그래서 "5060이 X2를 많이 구매했다"고 쓰지 않습니다.']),
            ('h3', '리뷰 221건 코딩에서 확인된 것 — 비중은 221건 표본 안의 몫'),
            ('table', ['항목', '값'], [
                ['방송·찬스쇼를 구매 계기로 적은 리뷰', '**12건 (5.4%)**'],
                ['연령을 스스로 밝힌 리뷰', '**3건 (1.4%)**'],
                ['선물·대리 구매 맥락', '**22건 (10.0%)**'],
                ['색상 표기', '핑크 **186건(84.2%)** · 화이트 16건(7.2%) · 미상 19건(8.6%)'],
                ['판단 유보 · 체감 없음', '**25건(11.3%)** · **10건(4.5%)**'],
                ['구매 상품명', '**11종**으로 갈림 — 확정 SKU 1개 기준 구성표가 필요한 이유'],
            ], [0.42, 0.58]),
            box('quote', '문장 비교', [
                '**쓰지 않는 문장** — "5060이 X2를 많이 구매했다."',
                f'**쓰는 문장** — "{BOUNDARY_5060}"']),
            ('note', '모든 %는 GS샵 상품평 **221건**(2026-05-10–11-10 수집) 표본 안의 몫이며 발생률·5060 고객 특성으로 해석하지 않습니다. '
                     '221건과 핑크 페이지 구매 표시 848개를 나눠 작성률(약 26%)로 쓰던 문장은 분모 불일치로 폐기했습니다.'),
        ],
    },
    {
        'no': 11, 'kicker': 'INTERNAL PROPOSAL', 'title': '5060 내부 개선 기획안 (3면 고도화)',
        'deck': '리뷰에서 확인된 사용 장벽을 고객 안내·구성·제품 검토 과제로 나눴습니다.',
        'blocks': [
            ('status', '[내부 검토용] — 고객용 광고물 아님'),
            fig('design/gs_x2_internal_improvement_brief.png', CW,
                '내부 개선 검토 요약 지면 시안 — GS샵 상품평 221건(수집 기간 2026-05-10~11-10) 기준'),
            ('table', ['장벽', '언급', '검토 과제'], [
                ['자극·통증', '12건 (5.4%)', '사용감·강도 — 원인 확인 뒤 안전성·사용성 시험'],
                ['무게·크기', '10건 (4.5%)', '무게·그립 — 조작 불편 재현과 설계·원가 검토'],
                ['부속품 부재', '7건 (3.2%)', '설명서·구성품 — 정보 표시와 실제 구성 변경을 분리'],
                ['설명 혼란', '6건 (2.7%)', '설명서·구성품 — 표시 방식 검토'],
                ['버튼 관련', '5건 (2.3%)', '버튼 — 위치·조작 설계 검토'],
            ], [0.2, 0.18, 0.62]),
            ('p', '[내부 검토용] ① 고객 안내로 풀 수 있는 것 ② 구성·설명서로 풀 수 있는 것 ③ **제품 변경 검토가 필요한 것**을 '
                  '나눈 조건부 제안서 요약입니다. 제품 검증 완료·출시 확정·시험 결과를 주장하지 않습니다.'),
            ('note', '리뷰 **221건** 표본 언급 수는 표본 안의 수이며 발생률·5060 고객 특성으로 해석하지 않습니다. '
                     '원인·안전성·원가 검증은 미실시이고, 원문 기획안 전체는 14쪽 깃허브 링크로 넘깁니다.'),
        ],
    },
    {
        'no': 12, 'kicker': '2027 RE-LAUNCH PLAN', 'title': '5060 2027년 5월 방송 연계 기획',
        'deck': '첫 방송 1주년에 맞춘 재방송 연계안입니다. 편성·혜택은 협의 목표일 뿐 확정이 아닙니다.',
        'blocks': [
            ('h3', '제안 시점'),
            ('p', '2026-05-09 첫 방송의 **1주년(2027-05-08–09 전후)** 재방송 연계를 제안합니다. '
                  '**협의 목표일**이며 편성 확정이 아닙니다.'),
            steps([('2026-05-09', 'GS샵 첫 방송\nX2 단독 런칭'),
                   ('2026-11', '상품평 221건\n수집·코딩'),
                   ('2027-05-08–09 전후', '1주년 재방송\n협의 목표일'),
                   ('2027-05 이후', '전용 코드·회차별\n주문 비교')], inverse_last=True),
            ('h3', '조건 — 검증 게이트 3개'),
            ('ol', ['GS샵 **방송 ID·SKU·연령별 순주문·순매출** 확인',
                    'APR 제품 담당의 **개선 가능성·시험·제조 일정** 확인',
                    '방송 **편성·혜택** 협의']),
            ('h3', '고객 안내 3단계 — 스토리보드 v0.3 화면 1·2·4'),
            steps([('방송 전', '구성·사용 조건 확인 (화면 1·2)'),
                   ('방송 중', '체감 차이 중립 안내'),
                   ('방송 후', '정보 재확인 (화면 4)')]),
            ('p', '방송 후 카드에는 "사용감과 체감 시기는 피부 상태·사용 기간에 따라 다릅니다"를 넣었습니다. '
                  '판단 유보 **25건(11.3%)**·체감 없음 **10건(4.5%)**(GS샵 리뷰 221건 표본)이 근거이며 전후 비교·수치를 만들지 않았습니다.'),
            ('h3', '[실행 제안] 측정 설계'),
            ('table', ['측정 항목', '방법', '필요한 자료'], [
                ['방송 회차별 주문', '전용 코드·회차 구분', 'GS샵 주문·SKU·회차 자료'],
                ['디지털 클릭', '랜딩 UTM·클릭 로그', '자사몰·광고 채널 로그'],
                ['안내 이해도', '방송 후 카드 문의 유형', '상담·문의 기록'],
            ], [0.24, 0.36, 0.4]),
            ('h3', '편성 확정 전에 하지 않는 것'),
            ('ul', [
                '2027-05-09를 **확정 방송일로 표기하지 않습니다** — 협의 목표일입니다.',
                '2026년 방송가·증정 구성을 **복제하지 않습니다.**',
                '제품 개선이 **완료된 것처럼 쓰지 않습니다** — 사양·시험·SKU 승인 전에는 고객 문구로 쓰지 않습니다.',
            ]),
            ('note', '디지털 클릭과 TV 전화 주문을 같은 측정값으로 합치지 않습니다. '
                     '2027년 **편성·혜택·매출 목표는 미확정**입니다.'),
        ],
    },
    {
        'no': 13, 'kicker': 'HOME SHOPPING CONCEPT', 'title': '5060 홈쇼핑 메인·상세페이지 시안 (1–2면 고도화)',
        'deck': '기존 3면 시안 중 앞의 1–2면을 실제 광고 페이지 수준으로 올리는 작업입니다.',
        'blocks': [
            ('status', '[승인 전 콘셉트] · 고객용 1–2면 시안은 비공개 제출용으로 제작 완료 · 공개 지면은 스토리보드 배치 시안'),
            fig('design/gs_x2_2027_static_storyboard.png', CW,
                '스토리보드 v0.3 배치 시안 — 화면 1(방송 전 예고 포스터)·2(구성 확인 카드)가 이 쪽의 기준이고, '
                '화면 3은 11쪽 내부 검토용입니다.'),
            cards([
                ('1면 · 방송 전 예고 포스터', '고도화 [제작·비공개]',
                 ['재방송 맥락 → 제품 인지 → 구성 확인 → 일정·랜딩 순서로 읽히게 설계합니다.',
                  '확정 방송일·시각과 승인된 URL만 넣고, 2027-05-09를 확정 방송일로 쓰지 않습니다.'],
                 '제품 이미지는 비공개 시안에서만 채웠고, 공개 PDF에는 넣지 않았습니다.'),
                ('2면 · 방송 구성 확인 카드', '고도화 [제작·비공개]',
                 ['**본품 → 함께 구성 → 보관·부속 → 가격·혜택** 4항목으로 나눕니다.',
                  '확정 SKU 1개 기준 구성표로 고정해 SKU마다 구성이 달라지는 상황을 막습니다.'],
                 '2026년 방송 혜택은 복제하지 않습니다.'),
            ]),
            ('h3', '고도화 기준'),
            ('ul', [
                '고객이 확인할 정보의 순서(구성·사용 조건·주의 문구)를 자체 설계합니다.',
                '공식몰·GS샵 상세페이지의 디자인·문구·상품 사진을 **복사하거나 재편집하지 않습니다**.',
                '확인되지 않은 혜택·수치·랭킹을 넣지 않습니다.',
                '사진 사용 허락이 없으면 제품 이미지 없이 콘셉트 시안으로 둡니다.',
            ]),
            ('note', '**승인 전 콘셉트** — 제품 변경·출시·편성 확정으로 읽히는 문구는 넣지 않습니다. '
                     '3면은 11쪽으로 옮겨 같은 시안을 고객용과 내부용으로 겸용하지 않습니다.'),
        ],
    },
    {
        'no': 14, 'kicker': 'LIMITS & APPENDIX', 'title': '한계, 검증 데이터 & 역할·부록',
        'deck': '주장하지 않은 것을 먼저 적었습니다. 이 쪽의 검증 수치는 저장소에서 다시 실행해 확인할 수 있습니다.',
        'blocks': [
            box('boundary', '미판정 경계', [FIXED_LIMIT,
                                       '[미확인] GS샵 연령별 순주문·제품 개선 일정·2027년 편성 — 10·11·12쪽 판정 유보 사유입니다.']),
            ('h3', '성과 판정에 실제로 필요한 데이터'),
            ('p', 'GS샵 **방송 ID·SKU·연령별 순주문·순매출** / 자사몰·광고 채널의 **방문·전환·광고비** / '
                  '제품 **개선 사양·시험·생산 일정**. 세 가지가 없어 판정을 미뤘습니다.'),
            ('h3', '검증 데이터 — 재현 가능'),
            ('table', ['항목', '결과'], [
                ['원자료 재계산', '**141항목 불일치 0건** (verify2.py --numeric-only)'],
                ['MD↔PDF 본문 대조', '**8쌍** 통과 · 입력·출력 해시 확인 · 빈 쪽 0 (verify_pdf_sync.py)'],
                ['리뷰 코딩', '**535건** 전수 코딩 (글로우 232 · 미니 82 · GS샵 X2 221)'],
                ['GS샵 리뷰 대조', '**221건** 고유 ID·평점 분포 대조'],
            ], [0.28, 0.72]),
            ('h3', '본인 역할·도구 — AI 제작 범위'),
            ('p', '문제 정의·데이터 수집·재계산 검증·리뷰 코딩·경쟁 표현 검수·콘티 설계·'
                  '시안 제작(SVG)·PDF 조판(Python)을 직접 했습니다. **Kling·Higgsfield 영상, AI TTS 내레이션, '
                  '포스터 연출 컷, AI 도구 보조 시안은 AI로 제작·생성**했고, 도구는 생성·렌더링에만 쓰고 판단·검수는 직접 했습니다.'),
            ('note', '[AI 제작] 1·2·8·9쪽에 표기한 숏폼 인물 클립 3개·7개 구간 내레이션·포스터 연출 컷은 생성형 AI 산출물이며, '
                     '실제 촬영·성우 녹음·광고 집행은 없습니다.'),
            ('h3', '부록 — 전체 보고서 8편과 재현 스크립트'),
            ('table', ['보고서', '저장소 경로'], [[a, f'`{b}`'] for a, b in REPORTS], [0.32, 0.68]),
            ('note', '저장소 github.com/rladbstj56/medicube_marketing (비공개) · 검증 스크립트 '
                     'analysis/task2/verify2.py · verify_pdf_sync.py · 리뷰 코딩표 data/reviews/'),
        ],
    },
]

COVER = {
    'kicker': 'CONTENT MARKETING PORTFOLIO · 2026.11',
    'title': ['메디큐브 콘텐츠 마케팅', '리서치 & 전략 포트폴리오'],
    'lead': '공개 데이터로 판단한 두 축',
    'axes': [
        ('01', '2030 부스터 글로우', '숏폼 30초 · 연계 포스터 — 콘텐츠 실험 1순위 조건부 채택'),
        ('02', '5060 GS샵 X2', '홈쇼핑 1–2면 시안 · 내부 개선 기획안 — 방송 연계 조건부 설계'),
    ],
    'meta': [
        ('지원 직무', '에이피알(APR) [마케팅 특별채용] 국내 콘텐츠 마케팅 신입'),
        ('작성자', '김윤서'),
        ('작성 시점', '2026.11'),
        ('문서 버전', 'v0.1 · 1차본 (최종 수정 2026-11-22 02:10 KST)'),
        ('AI 제작', '숏폼 인물 클립·내레이션·포스터 연출 컷 일부 AI 생성 (8·9·14쪽 표기)'),
        ('제출 마감', '2026-11-22 23:59'),
    ],
    'note': '이 문서는 실제 광고·방송을 집행한 성과가 아니라, 공개 근거로 판단하고 소재로 옮긴 과정을 정리한 것입니다. '
            '매출·ROAS·방송 효과는 주장하지 않으며, 모든 판단에는 [관측]·[해석]·[실행 제안]·[제작물] 라벨을 붙였습니다. '
            '숏폼 인물 클립·내레이션·포스터 연출 컷 등 AI로 생성한 소재는 쪽마다 AI 제작 표기를 붙였습니다.',
}


# ── PDF 그리기 ──────────────────────────────────────────────────────────────


def draw_chrome(c, no):
    """모든 쪽 공통 머리글·바닥글."""
    c.setFillColor(DEEP)
    c.setFont(BOLD, 6.3)
    c.drawString(M, PAGE_H - 36, 'MEDICUBE  ·  CONTENT MARKETING PORTFOLIO')
    c.setFillColor(MUTED)
    c.setFont(FONT, 6.3)
    c.drawRightString(PAGE_W - M, PAGE_H - 36, '김윤서 · 2026.11')
    c.setStrokeColor(PINKLINE)
    c.setLineWidth(0.7)
    c.line(M, PAGE_H - 42, PAGE_W - M, PAGE_H - 42)
    c.line(M, 36, PAGE_W - M, 36)
    c.setFont(FONT, 6.2)
    c.setFillColor(MUTED)
    c.drawString(M, 25, '에이피알(APR) [마케팅 특별채용] 국내 콘텐츠 마케팅 신입 지원 · 포트폴리오 (14쪽)')
    c.setFont(BOLD, 7.2)
    c.setFillColor(DEEP)
    c.drawRightString(PAGE_W - M, 25, f'{no:02d} / {TOTAL_PAGES}')


def draw_title_block(c, page):
    """쪽 제목·킥커·설명을 그리고 본문 시작 y를 돌려준다."""
    y = PAGE_H - 70
    c.setFont(BOLD, 6.8)
    c.setFillColor(RED)
    c.drawString(M, y, f'{page["no"]:02d}    {page["kicker"]}')
    y -= 22
    title = Paragraph(md(page['title']), ParagraphStyle(
        'title', fontName=BOLD, fontSize=19, leading=24, textColor=INK, wordWrap=None))
    tw, th = title.wrap(CW, 60)
    title.drawOn(c, M, y - th + 5)
    y -= th + 6
    c.setStrokeColor(RED)
    c.setLineWidth(2.2)
    c.line(M, y, M + 32, y)
    c.setStrokeColor(PINKLINE)
    c.setLineWidth(0.7)
    c.line(M + 38, y, PAGE_W - M, y)
    y -= 15
    if page.get('deck'):
        deck = Paragraph(md(page['deck']), ST['deck'])
        dw, dh = deck.wrap(CW, 80)
        deck.drawOn(c, M, y - dh)
        y -= dh + 4
    return y - 9


def draw_cover(c):
    """표지 — 붉은 면 + 두 축 + 신원 정보."""
    top_h = PAGE_H * 0.60
    c.setFillColor(DEEP)
    c.rect(0, PAGE_H - top_h, PAGE_W, top_h, stroke=0, fill=1)
    c.setFillColor(RED)
    c.rect(0, PAGE_H - top_h, PAGE_W, 5, stroke=0, fill=1)

    x = M + 12
    c.setFillColor(HexColor('#E8B9BE'))
    c.setFont(BOLD, 7.0)
    c.drawString(x, 762, COVER['kicker'])

    c.setFillColor(WHITE)
    c.setFont(BOLD, 30)
    c.drawString(x, 716, COVER['title'][0])
    c.drawString(x, 674, COVER['title'][1])

    c.setStrokeColor(HexColor('#D98A91'))
    c.setLineWidth(0.9)
    c.line(x, 650, x + 64, 650)

    c.setFillColor(HexColor('#F6E3E5'))
    c.setFont(FONT, 10)
    c.drawString(x, 624, COVER['lead'])

    y = 596
    for no, name, desc in COVER['axes']:
        c.setFillColor(HexColor('#E8AEB4'))
        c.setFont(BOLD, 8)
        c.drawString(x, y, no)
        c.setFillColor(WHITE)
        c.setFont(BOLD, 11.5)
        c.drawString(x + 24, y, name)
        c.setFillColor(HexColor('#F2D6D9'))
        c.setFont(FONT, 8)
        c.drawString(x + 24 + c.stringWidth(name, BOLD, 11.5) + 10, y, desc)
        y -= 26

    c.setFillColor(HexColor('#F2D6D9'))
    c.setFont(FONT, 8.2)
    c.drawString(x, 500, '저장소 보고서 8편의 판단을 14쪽으로 압축하고, 그중 제작한 소재만 실었습니다.')

    # 검증 숫자 띠
    c.setStrokeColor(HexColor('#C9737B'))
    c.setLineWidth(0.8)
    c.line(x, 462, PAGE_W - M - 12, 462)
    stats = [('141', '원자료 재계산 항목 · 불일치 0건'), ('535', '리뷰 전수 코딩 건수'),
             ('8', '보고서 MD↔PDF 대조 쌍')]
    for i, (value, label) in enumerate(stats):
        sx = x + i * 162
        c.setFillColor(WHITE)
        c.setFont(BOLD, 15)
        c.drawString(sx, 430, value)
        c.setFillColor(HexColor('#F0C9CE'))
        c.setFont(FONT, 7)
        c.drawString(sx, 414, label)

    # 신원 정보
    y = 318
    for key, value in COVER['meta']:
        c.setFillColor(MUTED)
        c.setFont(BOLD, 6.4)
        c.drawString(M + 12, y, key.upper())
        c.setFillColor(INK)
        c.setFont(FONT, 8.6)
        c.drawString(M + 96, y, value)
        c.setStrokeColor(HAIR)
        c.setLineWidth(0.5)
        c.line(M + 12, y - 9, PAGE_W - M - 12, y - 9)
        y -= 25

    c.setFillColor(MUTED)
    c.setFont(FONT, 7.2)
    c.drawString(M + 12, 162, '읽는 순서   결론(4)  →  근거·타깃(5–6)  →  2030 실행(7–9)  →  5060 실행(10–13)  →  한계·부록(14)')

    note = Paragraph(md(COVER['note']), ST['note'])
    nw, nh = note.wrap(CW - 24, 120)
    note.drawOn(c, M + 12, 62)
    c.setStrokeColor(RED)
    c.setLineWidth(2.2)
    c.line(M + 12, 62 + nh + 10, M + 40, 62 + nh + 10)
    c.setFont(FONT, 6.2)
    c.setFillColor(MUTED)
    c.drawString(M + 12, 30, '메디큐브 콘텐츠 마케팅 포트폴리오 · 김윤서 · 2026.11')
    c.setFont(BOLD, 7.2)
    c.setFillColor(DEEP)
    c.drawRightString(PAGE_W - M - 12, 30, f'01 / {TOTAL_PAGES}')


def flatten(entry):
    kind = entry[0]
    if kind == 'cols':
        return [entry]
    return [entry]


def place(flowables, x, y_top, width, avail, problems, label):
    """flowable을 위에서 아래로 놓고 남은 높이를 돌려준다. 넘치면 기록한다."""
    y = y_top
    for f in flowables:
        w, h = f.wrap(width, avail)
        if y - h < BODY_BOTTOM:
            problems.append((label, round(y - h - BODY_BOTTOM, 1)))
        f.drawOn(draw_canvas, x, y - h)
        y -= h + GAP
    return y


def page_flowables(page, width=CW):
    """블록 정의를 flowable 목록으로 바꾼다(cols는 표로)."""
    out = []
    for entry in page['blocks']:
        if entry[0] == 'cols':
            _, left, right, ratio, gap = entry
            lw = (width - gap) * ratio
            rw = (width - gap) * (1 - ratio)
            lf = [f for e in left for f in as_flowables(e, lw)]
            rf = [f for e in right for f in as_flowables(e, rw)]
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
    c.setKeywords('메디큐브, APR, 콘텐츠 마케팅, 포트폴리오, 부스터 글로우, GS샵 X2')
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
        used = 0
        y = y_top
        for f in flows:
            w, h = f.wrap(CW, avail)
            f.drawOn(c, M, y - h)
            y -= h + GAP
            used += h + GAP
        if y < BODY_BOTTOM:
            problems.append((f'{page["no"]}쪽 {page["title"]}', round(y - BODY_BOTTOM, 1)))
        report.append({'no': page['no'], 'title': page['title'],
                       'used': round(used, 1), 'free': round(y - BODY_BOTTOM, 1),
                       'blocks': len(flows)})
        c.showPage()
    c.save()
    return report, problems


def svg_to_png(svg_path, png_path, dpi=200):
    """도표 SVG를 PNG로 굽는다. reportlab이 SVG를 직접 넣지 못해 한 번 거친다."""
    doc = pymupdf.open(str(svg_path))
    pix = doc[0].get_pixmap(dpi=dpi)
    pix.save(str(png_path))
    return png_path


# ── Markdown ───────────────────────────────────────────────────────────────


def md_table(header, rows, widths=None):
    lines = []
    rows = [[c.replace('\n', ' / ') for c in row] for row in rows]
    head = header if header else [''] * len(rows[0])
    lines.append('| ' + ' | '.join(head) + ' |')
    lines.append('|' + '|'.join(['---'] * len(head)) + '|')
    for row in rows:
        lines.append('| ' + ' | '.join(row) + ' |')
    return '\n'.join(lines)


def entry_to_md(entry):
    kind = entry[0]
    if kind == 'p':
        return entry[1]
    if kind == 'note':
        return f'> {entry[1]}'
    if kind == 'status':
        return f'**{entry[1]}**'
    if kind == 'h3':
        return f'### {entry[1]}'
    if kind == 'ul':
        return '\n'.join(f'- {item}' for item in entry[1])
    if kind == 'ol':
        return '\n'.join(f'{i}. {item}' for i, item in enumerate(entry[1], 1))
    if kind == 'table':
        return md_table(entry[1], entry[2])
    if kind == 'box':
        title, lines = entry[2], entry[3]
        body = []
        if title:
            body.append(f'**{title}**')
            body.append('')
        for line in lines:
            body.append(line)
            body.append('')
        return '\n'.join(('> ' + b).rstrip() for b in body).rstrip()
    if kind == 'fig':
        return f'![{entry[3] or ""}]({relative(entry[1])})'
    if kind == 'figrow':
        return '\n\n'.join(f'![{cap}]({relative(path)})' for path, cap in entry[1])
    if kind == 'video':
        return f'**[{entry[1]}]** — {entry[2]}'
    if kind == 'kpi':
        rows = [[value, label] for value, label in entry[1]]
        return md_table(['숫자', '내용'], rows)
    if kind == 'vslot':
        rows = '\n'.join(f'- {r}' for r in (entry[4] if len(entry) > 4 else []) or [])
        return f'**{entry[1]}** — {entry[2]}' + ('\n\n' + rows if rows else '')
    if kind == 'big':
        return f'**{entry[1]}**'
    if kind == 'toc':
        return '\n'.join(f'- **{no}** {title}' for no, title in entry[1])
    if kind == 'ph':
        return f'{entry[1]} — {entry[2]}'
    if kind == 'steps':
        rows = [[label, body] for label, body in entry[1]]
        return md_table(['구간', '내용'], rows)
    if kind == 'cols':
        _, left, right, ratio, gap = entry
        left_md = '\n\n'.join(entry_to_md(e) if e[0] != 'raw' else raw_to_md(e) for e in left)
        right_md = '\n\n'.join(entry_to_md(e) if e[0] != 'raw' else raw_to_md(e) for e in right)
        return left_md + '\n\n' + right_md
    if kind == 'raw':
        return raw_to_md(entry)
    if kind == 'space':
        return ''
    raise ValueError(kind)


def raw_to_md(entry):
    value = entry[1]
    if isinstance(value, list):
        return '\n'.join('- ' + p.text for p in value)
    return ''


def relative(path):
    text = str(path)
    if text.startswith('tmp/portfolio/'):
        return '../' + text
    if text.startswith(('design/', 'shots/', 'reports/')):
        return '../' + text
    return text


def build_md():
    lines = [
        '# 메디큐브 콘텐츠 마케팅 리서치 & 전략 포트폴리오',
        '',
        '> **14쪽 두괄식 포트폴리오 · v0.1(1차본)** · 최종 수정 2026-11-22 02:10 KST · 김윤서 · 2026.11 · '
        '에이피알(APR) [마케팅 특별채용] 국내 콘텐츠 마케팅 신입 지원 (마감 2026-11-22 23:59)',
        '>',
        '> 이 문서는 `analysis/task2/build_portfolio.py`가 만들었고, 같은 스크립트가 같은 내용으로 '
        '`메디큐브_콘텐츠마케팅_포트폴리오.pdf`(14쪽)를 조판합니다. 수치는 저장소 현행 문서 값을 그대로 옮겼고, '
        '설계 기준은 `메디큐브_콘텐츠마케팅_포트폴리오_구성안.md` v1.2입니다.',
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
            lines.append('# ' + ' '.join(COVER['title']))
            lines.append('')
            lines.append(COVER['lead'])
            lines.append('')
            for no, name, desc in COVER['axes']:
                lines.append(f'- **{no} {name}** — {desc}')
            lines.append('')
            lines.append(md_table(['항목', '내용'], [[k, v] for k, v in COVER['meta']]))
            lines.append('')
            lines.append('> ' + COVER['note'])
            lines.append('')
            lines.append('---')
            lines.append('')
            continue
        lines.append(f'## {page["no"]}쪽 · {page["title"]}')
        lines.append('')
        if page.get('deck'):
            lines.append(f'*{page["deck"]}*')
            lines.append('')
        for entry in page['blocks']:
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
        print(f'{row["no"]:>2}쪽 {row["title"]:<34} 사용 {row["used"]:>6}  여유 {row["free"]:>7}')
    print('페이지', len(report))
    if problems:
        print('!! 넘침:', problems)
        return 1
    print('OK', OUT_PDF.relative_to(ROOT), OUT_MD.relative_to(ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
