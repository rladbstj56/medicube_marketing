# -*- coding: utf-8 -*-
"""14쪽 포트폴리오 PDF·MD 생성기 — Behance 양식의 이미지 중심 16:9 덱.

2026-11-22 사용자 지시로 전면 재디자인했다. 이전 판(v0.3)은 검증 수치와 방어적
서술이 본문을 차지하는 편집형 보고서였고, 이번 판은 Behance 포트폴리오 세 편
(나현지 브랜딩&마케팅, 김다빈 마케팅, miok Kim PPT 템플릿)을 직접 열어 확인한
양식을 따른다.

- **원컬러 배경**: 딥 차콜 `#18181B` ↔ 웜 오프화이트 `#F8F7F5` 두 면만 쓰고,
  포인트는 메디큐브 크림슨 `#9B1B27` 한 색을 절제해서 쓴다. 붉은 박스·테두리를
  반복하지 않고 헤어라인과 여백으로 나눈다.
- **한 장에 한 메시지**: 큰 한 줄 + 숫자 2~3개 + 이미지. 검증용 수치(141항목·
  535건)와 방법론은 14쪽·깃허브 링크로 보내고, 본문에는 판단과 결과물만 남긴다.
- **디바이스 목업**: `mockups.py`가 만든 스마트폰·태블릿·브라우저 프레임에
  시안을 합성해 '화면 안에 놓인 모습'으로 보여준다.
- **AI 제작·승인 전 콘셉트 고지**는 쪽마다 캡션 한 줄로만 유지한다.

PDF와 MD는 같은 `PAGES` 데이터에서 나온다. 두 파일이 어긋날 수 없게 하려는
것이며, 값은 모두 저장소 현행 문서에서 그대로 옮겼다.
"""

import re
import sys
from pathlib import Path

import pymupdf
from PIL import Image as PILImage
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

import mockups

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT_PDF = ROOT / 'reports/메디큐브_콘텐츠마케팅_포트폴리오.pdf'
OUT_MD = ROOT / 'reports/메디큐브_콘텐츠마케팅_포트폴리오.md'
TMP = ROOT / 'tmp/portfolio'
MOCK = TMP / 'mockups'
PHOTO = ROOT / 'private_submission/assets/profile_yunseo.jpg'   # 증명사진(1·2쪽)

# ── 팔레트 ──────────────────────────────────────────────────────────────────
INK = HexColor('#18181B')          # 딥 차콜
PAPER = HexColor('#F8F7F5')        # 웜 오프화이트
CRIMSON = HexColor('#9B1B27')
CRIMSON_L = HexColor('#C4746C')    # 차콜 위에서 읽히는 크림슨
MUTED = HexColor('#75706A')
MUTED_D = HexColor('#9C968E')
HAIR = HexColor('#DDD7D0')
HAIR_D = HexColor('#35353B')
PANEL = HexColor('#F0EBE4')
PANEL_D = HexColor('#212127')
WHITE = HexColor('#FFFFFF')

FONT, BOLD = 'NotoKR', 'NotoKR-Bold'
pdfmetrics.registerFont(TTFont(FONT, str(HERE / 'fonts/NotoSansKR-Regular.ttf')))
pdfmetrics.registerFont(TTFont(BOLD, str(HERE / 'fonts/NotoSansKR-Bold.ttf')))
pdfmetrics.registerFontFamily(FONT, normal=FONT, bold=BOLD, italic=FONT, boldItalic=BOLD)

PAGE_W, PAGE_H = 960.0, 540.0
M = 44.0
CW = PAGE_W - 2 * M
TOTAL = 14
VERSION = 'v1.0'

# ── 쪽별 내용 ───────────────────────────────────────────────────────────────
# 그리는 값과 MD에 적는 값이 같은 곳에서 나온다.

COVER = {
    'kicker': 'CONTENT MARKETING PORTFOLIO',
    'year': '2026',
    'name': 'KIM YUNSEO',
    'ko': '김윤서',
    'line': '공개 데이터로 판단하고, 콘텐츠로 옮깁니다.',
    'role': '국내 콘텐츠 마케팅 지원 · 에이피알(APR)',
    'badge_role': 'CONTENT MARKETER',
    'contact': ('rladbstj56@gmail.com', '010-9056-0349'),
    'axes': ('01  2030 부스터 글로우', '02  5060 GS샵 X2'),
    'note': 'AI 생성 이미지 일부 포함 · 실제 집행 콘셉트 아님',
}

PROFILE = {
    'kicker': '01 · PROFILE',
    'title': '데이터로 확인하고,\n콘텐츠로 옮깁니다',
    'name': '김윤서',
    'role': 'Content Marketing · Data-driven',
    'tags': ('#데이터검증', '#콘텐츠기획', '#CRM설계'),
    'academic': ('숙명여자대학교 소프트웨어융합전공 · 2025.08 졸업',
                 '팀스파르타 KDT 데이터 분석가 양성과정 · 2025.12–2026.05'),
    'cert': ('빅데이터분석기사 · 2026.07', 'SQLD · 2025.04', 'ADsP · 2025.09', 'TOEIC 925'),
    'skills': (('Python', 4), ('SQL', 4), ('GA4', 2), ('Figma', 3), ('Photoshop', 3), ('CapCut', 3)),
    'strengths': (
        ('01', '데이터 수집·검증', '원자료 13종과 리뷰 원문을 직접 모아 다시 계산합니다.'),
        ('02', '콘텐츠 기획·제작', '고객 고민에서 출발한 30초 콘티와 포스터·CRM 접점.'),
        ('03', 'CRM·퍼널 설계', '이탈 지점과 구매 후 루틴을 메시지로 잇습니다.'),
    ),
    'note': '사진과 이력은 지원자 본인이 제공한 내용입니다.',
}

CONTENTS = {
    'kicker': '02 · CONTENTS',
    'title': 'CONTENTS',
    'sub': '두 프로젝트, 한 가지 방식',
    'rows': (
        ('01', '프로필', '02'),
        ('02', '두 축 한눈에', '04'),
        ('03', 'PROJECT 01 — 2030 부스터 글로우', '05'),
        ('04', 'PROJECT 02 — 5060 GS샵 X2', '09'),
        ('05', 'WORK PROCESS', '13'),
        ('06', '한계 · 부록', '14'),
    ),
    'axes': ('01  2030 부스터 글로우 — 숏폼 · 포스터 · 자사몰 CRM',
             '02  5060 GS샵 X2 — 홈쇼핑 1–2면 · 개선안 · 배송 후 CRM'),
    'note': '읽는 순서 — 결론(04) → 근거 → 실행 → 한계',
}

OVERVIEW = {
    'kicker': '03 · OVERVIEW',
    'title': '두 개의 축, 같은 방식',
    'lead': '공개 데이터로 기회를 확인하고, 콘텐츠로 옮겼습니다. 성과는 주장하지 않고 미판정으로 남겼습니다.',
    'cards': (
        ('01', '2030 부스터 글로우', '콘텐츠 실험 1순위 조건부 채택',
         ('기간', '2026.11'), ('역할', '리뷰 코딩 · 콘티 · 포스터 · CRM'),
         ('산출물', '숏폼 30초 · 포스터 · 엔드카드 · 자사몰 CRM')),
        ('02', '5060 GS샵 X2', '방송 연계 조건부 설계',
         ('기간', '2026.11'), ('역할', '리뷰 코딩 · 채널 설계 · 지면 시안'),
         ('산출물', '홈쇼핑 1–2면 · 내부 개선안 · 배송 후 CRM')),
    ),
    'kpis': (('45.8%', '2030 브랜드 검색 비중 · 데이터랩 5사 안'),
             ('28주', '글로우가 같은 조건에서 미니를 앞선 주'),
             ('221건', 'GS샵 X2 상품평 전수 코딩')),
    'note': '모든 비중은 비교군 안의 몫이며, 검색 지수는 판매량이 아닙니다.',
}

P01 = {
    'kicker': 'PROJECT 01',
    'title': '2030\n부스터 글로우',
    'sub': '숏폼 30초 · 연계 포스터 · 자사몰 CRM',
    'about': (('기간', '2026.11'), ('기여도', '100%'),
              ('역할', '리뷰 코딩 · 콘티 · 시안 · CRM 설계'),
              ('툴', 'Python · SQL · Kling · CapCut · Photoshop'),
              ('목표', '고민 한 문장을 30초로 붙잡고, 자사몰 CRM으로 구매까지 잇기')),
    'caption': '엔드카드 1080×1920 · 메인 포스터 1080×1350 — 실제 제품 사진 사용, 집행 전 시안',
}

P01E = {
    'kicker': 'PROJECT 01 · 근거',
    'title': '고민은 세 문장으로 반복됩니다',
    'lead': '공식몰 리뷰 217건과 글로우픽 15건을 전수 코딩했습니다. 가장 많이 나온 말은 광채·보습·피부결이었습니다.',
    'bars': (('광채 · 물광', 42), ('보습 · 속건조', 37), ('피부결 · 톤', 24)),
    'insights': (('42건', '광채·물광이 최다 코드', '물방울 초음파를 기능 설명이 아니라 결과 언어로 옮겼습니다.'),
                 ('28주', '같은 조건에서 미니 초과', '여성 19–39세 동일 조건 검색에서 출시 후 28주 모두 앞섰습니다.'),
                 ('57.5%', '미니 리뷰의 휴대 태그', '가볍다·간편하다 후킹은 주 후킹에서 뺐습니다.')),
    'shot_title': '샷 1 · 20대 강의실 아침',
    'shot_body': '최다 코드인 광채·물광을 장면으로 옮겼습니다.',
    'note': '검색 지수는 판매량이 아닙니다. 57.5%는 공식몰 미니 리뷰 200건 CSV 태그 중 115건입니다.',
}

P01S = {
    'kicker': 'PROJECT 01 · 전략 & CRM',
    'title': '고민 하나 → 이유 하나 → 비교 랜딩',
    'lead': '30초를 세 샷으로 나누고, 구매 전후 접점을 자사몰 CRM으로 이었습니다.',
    'shots': (('0–7초', '아침 속건조'), ('7–14초', '밤 탄력'), ('14–21초', '외출 전 피부결')),
    'crm': (('온사이트 배너', '비교 랜딩 이탈 · 앱 설치자'),
            ('앱푸시 D+1', '랜딩 방문 · 미구매'),
            ('앱푸시 구매 후 D+7', '구매 고객 · 루틴 정착')),
    'note': '[실행 제안] CRM 발송은 미집행 · [AI 제작] 인물 클립 3개와 내레이션 7구간은 AI 생성',
}

P01O = {
    'kicker': 'PROJECT 01 · OUTPUT',
    'title': '숏폼 3컷에서 포스터·브릿지까지',
    'list': (('01', '숏폼 29.8초 조립 초안', 'AI 클립 3개 + TTS 내레이션'),
             ('02', '메인 포스터 1080×1350', '하루의 세 순간, 다른 피부 고민'),
             ('03', '엔드카드 1080×1920', '제품 사진 + 자사몰 CTA'),
             ('04', '헬로키티 에디션', '별도 기획 포스터 · 판매 CTA 없음'),
             ('05', '브릿지 카드 3종', '초음파 · 5모드 · 12분 루틴')),
    'note': '[AI 제작] 인물 클립·연출 컷 일부는 생성형 AI · 실제 광고 집행과 성과는 없습니다.',
}

P02 = {
    'kicker': 'PROJECT 02',
    'title': '5060\nGS샵 X2',
    'sub': '홈쇼핑 1–2면 시안 · 내부 개선안 · 배송 후 CRM',
    'about': (('기간', '2026.11'), ('기여도', '100%'),
              ('역할', '리뷰 코딩 · 채널 설계 · 지면 시안 · CRM'),
              ('툴', 'Python · SQL · Illustrator · Photoshop'),
              ('목표', '방송 전 예고부터 배송 후 사용까지, 5060이 이해하는 순서로')),
    'caption': '방송 전 예고 포스터와 구성 확인 카드 — 실제 X2 제품 사진 포함, 승인 전 콘셉트',
}

P02E = {
    'kicker': 'PROJECT 02 · 근거',
    'title': '리뷰 221건이 말한 사용 장벽',
    'lead': 'GS샵 상품평 221건을 전수 코딩했습니다. 불편은 제품 성능보다 쓰는 방법에서 나왔습니다.',
    'bars': (('자극 · 통증', 12), ('무게 · 크기', 10), ('부속품 부재', 7), ('설명 혼란', 6), ('버튼', 5)),
    'insights': (('22건', '선물·대리 구매 맥락', '5060이 스스로 고르기보다 대신 사 주는 흐름이 보였습니다.'),
                 ('35건', '판단 유보 · 체감 없음', '기대와 실제가 어긋난 지점을 사용 안내로 메웁니다.'),
                 ('5.4%', '방송을 계기로 적은 리뷰', '방송이 구매 이유로 남으려면 구성 설명이 먼저입니다.')),
    'shot_title': '구성 확인 카드 시안',
    'shot_body': '본품·함께 구성·보관·가격 4항목으로 고정해 SKU마다 달라지는 구성을 막았습니다.',
    'note': '모든 비중은 221건 표본 안의 몫이며, 5060 고객 특성으로 해석하지 않습니다.',
}

P02S = {
    'kicker': 'PROJECT 02 · 개선안 & CRM',
    'title': '고객 안내 · 구성 · 제품 검토로 나눴습니다',
    'lead': '리뷰에서 확인된 장벽을 세 갈래로 나누고, 배송 직후와 2주차 안내를 설계했습니다.',
    'rows': (('자극 · 통증', '12건', '사용감·강도 — 원인 확인 뒤 안전성 검토'),
             ('무게 · 크기', '10건', '그립 — 조작 불편 재현과 설계 검토'),
             ('부속품 · 설명', '13건', '설명서·구성품 — 표시 방식 검토')),
    'messages': (('스냅푸시 · D+0', '큰 글씨 사용법', '손잡이는 아래쪽을 잡으면 버튼이 덜 눌립니다.'),
                 ('알림톡 · D+14', '2주차 체감 안내', '체감 시기와 강도는 피부 상태에 따라 다릅니다.')),
    'note': '[내부 검토용] 고객용 광고물 아님 · 제품 변경·출시·시험 결과는 미확정입니다.',
}

P02O = {
    'kicker': 'PROJECT 02 · OUTPUT',
    'title': '홈쇼핑 1–2면 — 예고와 구성 확인',
    'points': (('1면', '방송 전 예고', '재방송 맥락 → 제품 인지 → 일정·랜딩 순서로 읽히게 설계했습니다.'),
               ('2면', '구성 확인 카드', '본품 → 함께 구성 → 보관·부속 → 가격·혜택 4항목으로 고정했습니다.')),
    'note': '[승인 전 콘셉트] 편성·혜택·제품 변경은 미확정 · 외부 게시하지 않습니다.',
}

PROCESS = {
    'kicker': '05 · WORK PROCESS',
    'title': '어떻게 만들었나',
    'lead': '도구는 생성과 렌더링에만 쓰고, 판단과 검수는 직접 했습니다.',
    'steps': (('01', '수집', '원자료 13종 · 리뷰 원문 · 스니핏 27장을 직접 확보'),
              ('02', '검증', '재계산과 출처 대조, 경쟁사 표현 중복 0건 검수'),
              ('03', '설계', '가설 → 30초 콘티 → CRM 접점 순서로 구조화'),
              ('04', '제작', '포스터·지면 시안·디바이스 목업·이 덱을 코드로 조판')),
    'tools': ('Python', 'SQL', 'GA4', 'Figma', 'Photoshop', 'CapCut', 'Kling'),
    'note': '숫자는 저장소에서 다시 실행해 확인합니다.',
}

LIMITS = {
    'kicker': '06 · LIMITS & APPENDIX',
    'title': '주장하지 않는 것부터 적었습니다',
    'boundary': ('공개 검색·클릭 지표와 수집 가능한 리뷰로 콘텐츠 및 채널 기회를 검토했다. '
                 '고객별 구매, 제품별 순매출, 광고 성과가 없어 타깃의 실제 구매 규모와 '
                 '전략 효과는 판정하지 않았다.'),
    'unknown': ('GS샵 연령별 순주문 · 제품 개선 일정 · 2027년 편성',
                '자사몰 방문·전환 로그와 광고 계정',
                '제품 개선 사양 · 시험 · 생산 일정'),
    'reports': (('국내 타깃·가설 v2.9', 'reports/메디큐브_국내_타깃가설_마케팅전략.md'),
                ('글로우 2030 연결 v2.2', 'reports/메디큐브_글로우_리뷰분석_2030전략연결.md'),
                ('GS샵 X2 리뷰분석 v0.2', 'reports/메디큐브_GS샵_X2_리뷰분석.md'),
                ('X2 프로모션 v0.3', 'reports/메디큐브_GS샵_X2_2027_5월_프로모션기획서.md'),
                ('X2 스토리보드 v0.3', 'reports/메디큐브_GS샵_X2_2027_5월_정적스토리보드.md'),
                ('국내 트렌드 v1.6', 'reports/메디큐브_국내_트렌드_분석보고서.md'),
                ('글로벌 트렌드 v1.3', 'reports/메디큐브_글로벌_트렌드_분석보고서.md'),
                ('피크 주 대조 v1.5', 'reports/메디큐브_국내_피크주_광고_이벤트_대조분석.md')),
    'next': '성과 판정에 필요한 자료는 GS샵 방송 ID·SKU·연령별 순주문·순매출과 자사몰 방문·전환 로그입니다. '
            '이 자료가 오면 두 프로젝트의 판정을 다시 합니다.',
    'note': '[AI 제작] 숏폼 인물 클립 3개·내레이션 7구간·포스터 연출 컷은 생성형 AI 산출물이며 '
            '실제 촬영·광고 집행은 없습니다. 저장소 github.com/rladbstj56/medicube_marketing(비공개)',
}

HEAD = {
    'right': '김윤서 · 2026.11',
}


# ── 그리기 도구 ─────────────────────────────────────────────────────────────
def esc(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


class Deck:
    def __init__(self, path):
        self.c = canvas.Canvas(str(path), pagesize=(PAGE_W, PAGE_H))
        self.c.setTitle('메디큐브 콘텐츠 마케팅 포트폴리오')
        self.c.setAuthor('김윤서')
        self.c.setSubject('에이피알(APR) 국내 콘텐츠 마케팅 지원 포트폴리오')

    # ── 면 ──────────────────────────────────────────────────────────────
    def bg(self, dark=False):
        self.c.setFillColor(INK if dark else PAPER)
        self.c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    def panel(self, x, y, w, h, dark=False, color=None):
        self.c.setFillColor(color or (PANEL_D if dark else PANEL))
        self.c.rect(x, y, w, h, stroke=0, fill=1)

    # ── 글자 ────────────────────────────────────────────────────────────
    def t(self, text, x, y, size=9, color=INK, bold=False, align='l', tracking=0.0):
        f = BOLD if bold else FONT
        c = self.c
        c.setFillColor(color)
        c.setFont(f, size)
        if tracking:
            w = sum(pdfmetrics.stringWidth(ch, f, size) for ch in text) + tracking * (len(text) - 1)
            if align == 'c':
                x -= w / 2
            elif align == 'r':
                x -= w
            for ch in text:
                c.drawString(x, y, ch)
                x += pdfmetrics.stringWidth(ch, f, size) + tracking
            return w
        if align == 'c':
            c.drawCentredString(x, y, text)
        elif align == 'r':
            c.drawRightString(x, y, text)
        else:
            c.drawString(x, y, text)
        return pdfmetrics.stringWidth(text, f, size)

    def para(self, text, x, y_top, w, size=8.6, leading=13.4, color=INK, bold=False, align=0):
        style = ParagraphStyle('p', fontName=BOLD if bold else FONT, fontSize=size,
                               leading=leading, textColor=color, alignment=align,
                               wordWrap='CJK')
        p = Paragraph(esc(text), style)
        _, h = p.wrap(w, 1000)
        p.drawOn(self.c, x, y_top - h)
        return h

    def rule(self, x1, x2, y, dark=False, color=None, width=0.6):
        c = self.c
        c.setStrokeColor(color or (HAIR_D if dark else HAIR))
        c.setLineWidth(width)
        c.line(x1, y, x2, y)

    # ── 이미지 ──────────────────────────────────────────────────────────
    def img(self, path, x, y, h=None, w=None, anchor='l'):
        path = Path(path) if not str(path).startswith('/') else Path(path)
        iw, ih = PILImage.open(path).size
        if h and not w:
            w = h * iw / ih
        elif w and not h:
            h = w * ih / iw
        if anchor == 'c':
            x -= w / 2
        elif anchor == 'r':
            x -= w
        self.c.drawImage(str(path), x, y, w, h, mask='auto')
        return w, h

    def img_cover(self, path, x, y, w, h, valign='c'):
        """비율을 지키며 상자를 꽉 채우고, 남는 부분을 잘라 낸다.

        valign='t'면 위쪽을 기준으로 잘라 머리·얼굴이 잘리지 않게 한다.
        (증명사진처럼 얼굴이 위쪽에 있는 사진에 쓴다.)
        """
        iw, ih = PILImage.open(path).size
        scale = max(w / iw, h / ih)
        dw, dh = iw * scale, ih * scale
        off = {'t': dh - h, 'c': (dh - h) / 2, 'b': 0}.get(valign, (dh - h) / 2)
        c = self.c
        c.saveState()
        p = c.beginPath()
        p.rect(x, y, w, h)
        c.clipPath(p, stroke=0, fill=0)
        c.drawImage(str(path), x - (dw - w) / 2, y - off, dw, dh, mask='auto')
        c.restoreState()

    def dot(self, x, y, r=1.6, color=CRIMSON_L):
        self.c.setFillColor(color)
        self.c.circle(x, y, r, stroke=0, fill=1)

    # ── 머리·꼬리 ───────────────────────────────────────────────────────
    def chrome(self, no, kicker, dark=False, right=None):
        color = CRIMSON_L if dark else CRIMSON
        self.t(kicker, M, 503, 6.4, color, True, tracking=1.7)
        self.t(right or HEAD['right'], PAGE_W - M, 503, 6.2, MUTED_D if dark else MUTED, align='r')
        self.rule(M, PAGE_W - M, 494, dark)
        self.t(f'{no:02d} / {TOTAL}', PAGE_W - M, 28, 6.2, MUTED_D if dark else MUTED, align='r')

    def caption(self, no, text, y=40):
        self.t(text, M, y, 6.1, MUTED_D if no in (1, 3, 8, 12, 14) else MUTED)

    def page_break(self):
        self.c.showPage()


# ── 쪽 그리기 ───────────────────────────────────────────────────────────────

def p01(d):
    d.bg(dark=True)
    c = d.c
    # 사원증 — 목걸이 줄이 위에서 내려온다
    cx, card_w, card_h, card_y = 172.0, 126.0, 170.0, 286.0
    c.setFillColor(HexColor('#2C2C31'))
    c.rect(cx - 10, card_y + card_h, 20, PAGE_H - (card_y + card_h), stroke=0, fill=1)
    c.setFillColor(HexColor('#4A4A50'))
    c.rect(cx - 13, card_y + card_h - 3, 26, 11, stroke=0, fill=1)
    c.setStrokeColor(HexColor('#6E6E74'))
    c.setLineWidth(1.1)
    c.circle(cx, card_y + card_h + 14, 8.5, stroke=1, fill=0)
    # 카드 그림자
    c.setFillColor(HexColor('#0E0E10'))
    c.roundRect(cx - card_w / 2 + 3, card_y - 4, card_w, card_h, 7, stroke=0, fill=1)
    c.setFillColor(HexColor('#F4F1EC'))
    c.roundRect(cx - card_w / 2, card_y, card_w, card_h, 7, stroke=0, fill=1)
    # 증명사진 — 상자를 꽉 채우고 위쪽 기준으로 잘라 머리가 잘리지 않게 한다
    px, py, pw, ph = cx - card_w / 2 + 11, card_y + 55, card_w - 22, 100
    c.setFillColor(HexColor('#E5DFD7'))
    c.rect(px, py, pw, ph, stroke=0, fill=1)
    d.img_cover(PHOTO, px, py, pw, ph, valign='t')
    c.setStrokeColor(HexColor('#D3CCC3'))
    c.setLineWidth(0.5)
    c.rect(px, py, pw, ph, stroke=1, fill=0)
    d.t(COVER['ko'], cx, card_y + 36, 10.5, INK, True, align='c')
    d.t(COVER['badge_role'], cx, card_y + 23, 4.9, MUTED, align='c', tracking=1.1)
    d.t('2026 PORTFOLIO', cx, card_y + 11, 4.6, CRIMSON, True, align='c', tracking=0.9)

    # 오른쪽 텍스트
    x = 320
    d.t(COVER['kicker'], x, 424, 7.0, CRIMSON_L, True, tracking=2.2)
    d.t(COVER['name'], x, 372, 40, WHITE, True, tracking=0.6)
    d.t(COVER['ko'], x + 2, 344, 17, HexColor('#D8D3CB'))
    d.t(COVER['line'], x + 2, 318, 10.4, HexColor('#B5AFA6'))
    d.rule(x, PAGE_W - M, 296, dark=True)
    d.t(COVER['role'], x + 2, 276, 8.0, HexColor('#9C968E'))

    # 연락처 — 오른쪽 아래
    cxp = PAGE_W - M
    d.t('CONTACT', cxp, 176, 6.4, CRIMSON_L, True, align='r', tracking=1.6)
    d.t(COVER['contact'][0], cxp, 156, 9.6, WHITE, align='r')
    d.t(COVER['contact'][1], cxp, 140, 9.6, WHITE, align='r')
    d.rule(M, 360, 142, dark=True)
    d.t(COVER['axes'][0], M, 120, 7.0, HexColor('#B5AFA6'))
    d.t(COVER['axes'][1], M, 104, 7.0, HexColor('#B5AFA6'))
    d.caption(1, COVER['note'], 40)
    d.page_break()


def p02(d):
    d.bg()
    d.chrome(2, PROFILE['kicker'])
    c = d.c

    # 왼쪽 — 증명사진과 이름 (위쪽 기준 크롭으로 얼굴이 잘리지 않게)
    px, py, pw, ph = M, 304, 150, 160
    c.setFillColor(HexColor('#EAE5DE'))
    c.rect(px, py, pw, ph, stroke=0, fill=1)
    d.img_cover(PHOTO, px, py, pw, ph, valign='t')
    c.setStrokeColor(HAIR)
    c.setLineWidth(0.5)
    c.rect(px, py, pw, ph, stroke=1, fill=0)
    d.t(PROFILE['name'], M, 280, 15, INK, True)
    d.t(PROFILE['role'], M, 265, 6.6, MUTED)
    ty = 244
    for tag in PROFILE['tags']:
        tw = pdfmetrics.stringWidth(tag, FONT, 6.0) + 12
        c.setStrokeColor(HAIR)
        c.setLineWidth(0.6)
        c.roundRect(M, ty - 4, tw, 15, 7.5, stroke=1, fill=0)
        d.t(tag, M + 6, ty, 6.0, MUTED)
        ty -= 20

    # 제목
    d.t(PROFILE['title'].replace('\n', ' '), 250, 470, 21, INK, True)

    # 3단 — 학력 / 자격 / 스킬
    cols = ((250, 'ACADEMIC'), (486, 'CERTIFICATE'), (668, 'SKILL & TOOL'))
    top = 434
    for x, label in cols:
        d.t(label, x, top, 6.4, CRIMSON, True, tracking=1.6)
    d.rule(250, 450, top - 8)
    d.rule(486, 646, top - 8)
    d.rule(668, 916, top - 8)

    y = top - 32
    for line in PROFILE['academic']:
        h = d.para(line, 250, y, 184, 7.6, 11.6, INK)
        y -= h + 8
    y = top - 32
    for line in PROFILE['cert']:
        d.t(line, 486, y, 7.6, INK)
        y -= 16
    y = top - 30
    for name, level in PROFILE['skills']:
        d.t(name, 668, y, 7.4, INK)
        for i in range(5):
            c.setFillColor(CRIMSON if i < level else HexColor('#DED8D1'))
            c.rect(786 + i * 12.5, y + 1.5, 8.6, 4.2, stroke=0, fill=1)
        y -= 15.6

    # 핵심 역량 3단
    d.rule(250, PAGE_W - M, 292)
    sx = 250
    for no, title, body in PROFILE['strengths']:
        d.t(no, sx, 270, 7.0, CRIMSON, True, tracking=0.8)
        d.t(title, sx + 18, 270, 8.6, INK, True)
        d.para(body, sx, 256, 208, 7.4, 11.2, MUTED)
        sx += 222

    d.rule(M, PAGE_W - M, 140)
    d.t('숫자는 근거를 남기고, 시안은 끝까지 만듭니다.', M, 104, 13.0, INK, True)
    d.t('이 덱의 모든 판단에는 저장소의 원자료가 붙어 있습니다.', M, 86, 7.6, MUTED)
    d.caption(2, PROFILE['note'], 40)
    d.page_break()


def p03(d):
    d.bg(dark=True)
    d.chrome(3, CONTENTS['kicker'], dark=True)
    d.t(CONTENTS['title'], M, 400, 34, WHITE, True, tracking=1.0)
    d.t(CONTENTS['sub'], M, 372, 8.6, MUTED_D)
    d.rule(M, 300, 356, dark=True)
    y = 320
    for line in CONTENTS['axes']:
        d.t(line, M, y, 7.2, HexColor('#B5AFA6'))
        y -= 15
    d.t('확인된 것과 판단한 것을 나눠 쓰고,', M, 168, 9.6, HexColor('#B5AFA6'))
    d.t('없는 성과는 만들지 않았습니다.', M, 150, 9.6, HexColor('#B5AFA6'))
    d.t(CONTENTS['note'], M, 48, 6.4, MUTED_D)

    top = 452
    for no, title, page in CONTENTS['rows']:
        d.t(no, 368, top - 12, 17, HexColor('#3F3F46'), True)
        d.t(title, 404, top - 10, 10.6, WHITE if no in ('03', '04') else HexColor('#D8D3CB'),
            no in ('03', '04'))
        d.t(page, PAGE_W - M, top - 10, 8.0, CRIMSON_L, True, align='r')
        d.rule(368, PAGE_W - M, top - 22, dark=True)
        top -= 42
    d.page_break()


def p04(d):
    d.bg()
    d.chrome(4, OVERVIEW['kicker'])
    d.t(OVERVIEW['title'], M, 450, 25, INK, True)
    d.para(OVERVIEW['lead'], M, 424, 640, 9.0, 14.2, MUTED)

    for i, (no, title, verdict, *rows) in enumerate(OVERVIEW['cards']):
        x = M + i * 428
        d.rule(x, x + 416, 386, color=INK, width=1.2)
        d.t(no, x, 358, 8.0, CRIMSON, True, tracking=0.8)
        d.t(title, x + 20, 356, 13.4, INK, True)
        d.t(verdict, x, 336, 8.2, CRIMSON)
        y = 312
        for label, value in rows:
            d.t(label, x, y, 6.2, MUTED, tracking=1.0)
            h = d.para(value, x + 44, y + 2.2, 372, 7.6, 11.4, INK)
            y -= max(h + 6, 18)

    d.rule(M, PAGE_W - M, 246)
    x = M
    for value, label in OVERVIEW['kpis']:
        d.t(value, x, 132, 42, INK, True)
        d.para(label, x, 114, 250, 7.4, 10.6, MUTED)
        x += 292
    d.caption(4, OVERVIEW['note'], 40)
    d.page_break()


def _sidebar(d, data, y_top=470):
    d.t(data['kicker'], M, y_top, 6.6, CRIMSON, True, tracking=2.0)
    lines = data['title'].split('\n')
    y = y_top - 26
    for line in lines:
        d.t(line, M, y, 24, INK, True)
        y -= 26
    d.para(data['sub'], M, y + 6, 236, 7.8, 11.6, MUTED)
    y -= 18
    d.t('ABOUT', M, y - 6, 6.2, CRIMSON, True, tracking=1.6)
    y -= 22
    for label, value in data['about']:
        d.t(label, M, y, 6.0, MUTED, tracking=0.8)
        h = d.para(value, M + 40, y + 1.6, 196, 7.2, 10.8, INK)
        y -= max(h + 5, 15)
    return y


def p05(d):
    d.bg()
    d.chrome(5, P01['kicker'] + ' · INTRO')
    _sidebar(d, P01)
    d.panel(320, 58, PAGE_W - M - 320, 404)
    d.img(MOCK / 'tablet_poster.png', 344, 84, h=286)
    d.img(MOCK / 'phone_endcard.png', 636, 70, h=352)
    d.caption(5, P01['caption'], 40)
    d.page_break()


def p06(d):
    d.bg()
    d.chrome(6, P01E['kicker'])
    d.t(P01E['title'], M, 448, 24, INK, True)
    d.para(P01E['lead'], M, 422, 560, 8.8, 13.6, MUTED)

    d.t('공식몰 리뷰 217건 · 코드 상위', M, 372, 6.2, CRIMSON, True, tracking=1.4)
    y = 342
    maxv = max(v for _, v in P01E['bars'])
    for label, value in P01E['bars']:
        d.t(label, M, y, 7.8, INK)
        w = 200 * value / maxv
        d.c.setFillColor(CRIMSON)
        d.c.rect(M + 104, y + 1, w, 7.2, stroke=0, fill=1)
        d.t(f'{value}건', M + 104 + w + 8, y, 7.4, MUTED)
        y -= 28

    # 근거가 콘텐츠가 된 자리
    w, h = d.img(MOCK / 'phone_shot1.png', M, 74, h=178)
    d.t(P01E['shot_title'], M + w + 18, 210, 7.8, INK, True)
    d.para(P01E['shot_body'], M + w + 18, 198, 190, 7.2, 10.8, MUTED)

    x = 420
    for i, (num, head, body) in enumerate(P01E['insights']):
        top = 360 - i * 100
        d.rule(x, PAGE_W - M, top + 20)
        d.t(head, x, top, 8.4, INK, True)
        d.t(num, PAGE_W - M, top - 2, 17, CRIMSON, True, align='r')
        d.para(body, x, top - 8, 400, 7.6, 11.4, MUTED)
    d.caption(6, P01E['note'], 40)
    d.page_break()


def p07(d):
    d.bg()
    d.chrome(7, P01S['kicker'])
    d.t(P01S['title'], M, 452, 22, INK, True)
    d.para(P01S['lead'], M, 426, 520, 8.4, 12.8, MUTED)

    y = 118
    for i, (time, label) in enumerate(P01S['shots']):
        x = M + i * 128
        d.img(MOCK / f'phone_shot{i + 1}.png', x, y + 24, h=222)
        d.t(time, x, y + 10, 6.8, CRIMSON, True, tracking=0.8)
        d.t(label, x + 48, y + 10, 6.8, MUTED)

    phones = (('phone_banner.png', P01S['crm'][0]),
              ('phone_push_d1.png', P01S['crm'][1]),
              ('phone_push_d7.png', P01S['crm'][2]))
    for i, (name, (title, cond)) in enumerate(phones):
        w, h = d.img(MOCK / name, 458 + i * 154, 128, h=268)
        d.t(title, 458 + i * 154 + w / 2, 112, 6.8, INK, True, align='c')
        d.t(cond, 458 + i * 154 + w / 2, 100, 6.0, MUTED, align='c')
    d.caption(7, P01S['note'], 40)
    d.page_break()


def p08(d):
    d.bg(dark=True)
    d.chrome(8, P01O['kicker'], dark=True)
    d.t(P01O['title'], M, 452, 22, WHITE, True)

    x = M
    for name, label in (('phone_shot1.png', '샷 1'), ('phone_shot2.png', '샷 2'),
                        ('phone_shot3.png', '샷 3'), ('phone_endcard.png', '엔드카드')):
        w, h = d.img(MOCK / name, x, 220, h=206)
        d.t(label, x + w / 2, 206, 6.2, MUTED_D, align='c')
        x += 118

    for name, x, h in (('print_poster.png', M, 132), ('print_kitty.png', 157, 132),
                       ('print_bridge1.png', 272, 132), ('print_bridge2.png', 354, 132),
                       ('print_bridge3.png', 436, 132)):
        d.img(MOCK / name, x, 56, h=h)

    ly = 424
    for no, title, sub in P01O['list']:
        d.t(no, 584, ly, 6.6, CRIMSON_L, True)
        d.t(title, 610, ly, 7.8, WHITE)
        d.t(sub, 610, ly - 11, 6.2, MUTED_D)
        d.rule(584, PAGE_W - M, ly - 22, dark=True)
        ly -= 46
    d.caption(8, P01O['note'], 40)
    d.page_break()


def p09(d):
    d.bg()
    d.chrome(9, P02['kicker'] + ' · INTRO')
    _sidebar(d, P02)
    d.panel(320, 58, PAGE_W - M - 320, 404)
    d.img(MOCK / 'print_teaser.png', 344, 100, h=296)
    d.img(MOCK / 'print_details.png', 604, 128, h=240)
    d.caption(9, P02['caption'], 40)
    d.page_break()


def p10(d):
    d.bg()
    d.chrome(10, P02E['kicker'])
    d.t(P02E['title'], M, 448, 24, INK, True)
    d.para(P02E['lead'], M, 422, 560, 8.8, 13.6, MUTED)

    d.t('GS샵 상품평 221건 · 장벽 언급', M, 372, 6.2, CRIMSON, True, tracking=1.4)
    y = 342
    maxv = max(v for _, v in P02E['bars'])
    for label, value in P02E['bars']:
        d.t(label, M, y, 7.6, INK)
        w = 176 * value / maxv
        d.c.setFillColor(CRIMSON)
        d.c.rect(M + 92, y + 1, w, 6.6, stroke=0, fill=1)
        d.t(f'{value}건', M + 92 + w + 8, y, 7.2, MUTED)
        y -= 26

    w, h = d.img(MOCK / 'print_details.png', M, 62, h=150)
    d.t(P02E['shot_title'], M + w + 18, 168, 7.8, INK, True)
    d.para(P02E['shot_body'], M + w + 18, 156, 150, 7.0, 10.4, MUTED)

    x = 420
    for i, (num, head, body) in enumerate(P02E['insights']):
        top = 360 - i * 100
        d.rule(x, PAGE_W - M, top + 20)
        d.t(head, x, top, 8.4, INK, True)
        d.t(num, PAGE_W - M, top - 2, 17, CRIMSON, True, align='r')
        d.para(body, x, top - 8, 400, 7.6, 11.4, MUTED)
    d.caption(10, P02E['note'], 40)
    d.page_break()


def p11(d):
    d.bg()
    d.chrome(11, P02S['kicker'])
    d.t(P02S['title'], M, 448, 21, INK, True)
    d.para(P02S['lead'], M, 422, 560, 8.4, 12.8, MUTED)

    w, h = d.img(MOCK / 'tablet_brief.png', M, 96, w=386)
    d.t('내부 개선 검토 요약 · 3면', M, 78, 6.2, MUTED)

    d.img(MOCK / 'phone_messages.png', 452, 96, h=282)

    x = 614
    y = 366
    for title, sub, body in P02S['messages']:
        d.t(title, x, y, 7.0, CRIMSON, True, tracking=0.6)
        d.t(sub, x, y - 15, 9.0, INK, True)
        hh = d.para(body, x, y - 22, 300, 7.4, 11.2, MUTED)
        y -= 42 + hh
        d.rule(x, PAGE_W - M, y + 14)
        y -= 16

    d.t('장벽 → 검토 과제', x, 196, 6.2, CRIMSON, True, tracking=1.4)
    ry = 176
    for label, count, task in P02S['rows']:
        d.t(label, x, ry, 6.8, INK, True)
        d.t(count, x + 78, ry, 6.8, CRIMSON)
        d.para(task, x + 108, ry + 2, 196, 6.6, 9.8, MUTED)
        ry -= 20
    d.caption(11, P02S['note'], 40)
    d.page_break()


def p12(d):
    d.bg(dark=True)
    d.chrome(12, P02O['kicker'], dark=True)
    d.t(P02O['title'], M, 452, 22, WHITE, True)
    w, h = d.img(MOCK / 'browser_x2_spread.png', M, 78, w=466)
    d.t('웹·태블릿 지면 · 2200×1460', M, 62, 6.0, MUTED_D)

    x = 586
    y = 350
    for no, title, body in P02O['points']:
        d.t(no, x, y, 7.0, CRIMSON_L, True, tracking=0.8)
        d.t(title, x + 34, y, 9.4, WHITE, True)
        hh = d.para(body, x, y - 12, 320, 7.4, 11.0, HexColor('#B5AFA6'))
        d.rule(x, PAGE_W - M, y - hh - 20, dark=True)
        y -= hh + 54
    d.caption(12, P02O['note'], 40)
    d.page_break()


def p13(d):
    d.bg()
    d.chrome(13, PROCESS['kicker'])
    d.t(PROCESS['title'], M, 452, 24, INK, True)
    d.para(PROCESS['lead'], M, 424, 600, 8.6, 13.2, MUTED)

    y = 318
    for i, (no, title, body) in enumerate(PROCESS['steps']):
        x = M + i * 216
        d.rule(x, x + 190, y + 54)
        d.t(no, x, y + 32, 8.0, CRIMSON, True, tracking=0.8)
        d.t(title, x + 22, y + 30, 10.4, INK, True)
        d.para(body, x, y + 16, 190, 7.4, 11.2, MUTED)

    d.rule(M, PAGE_W - M, 250)
    d.t('“확인되지 않은 것은 확인된 것처럼 쓰지 않는다.”', M, 196, 14, INK, True)
    d.t('그래서 14쪽에 미확정을 먼저 적었습니다.', M, 176, 7.8, MUTED)

    d.t('TOOL', M, 160, 6.2, CRIMSON, True, tracking=1.6)
    tx = M + 44
    for tool in PROCESS['tools']:
        tw = pdfmetrics.stringWidth(tool, FONT, 7.4) + 16
        d.c.setStrokeColor(HAIR)
        d.c.setLineWidth(0.6)
        d.c.roundRect(tx, 154, tw, 17, 8.5, stroke=1, fill=0)
        d.t(tool, tx + 8, 160, 7.4, INK)
        tx += tw + 8

    d.rule(M, PAGE_W - M, 132)
    d.t('판단은 직접, 생성은 도구로 — 인물 클립·내레이션·연출 컷은 AI로 만들고 검수는 직접 했습니다.',
        M, 112, 7.8, INK)
    d.caption(13, PROCESS['note'], 40)
    d.page_break()


def p14(d):
    d.bg(dark=True)
    d.chrome(14, LIMITS['kicker'], dark=True)
    d.t(LIMITS['title'], M, 452, 22, WHITE, True)
    d.para(LIMITS['boundary'], M, 424, 520, 8.4, 13.0, HexColor('#B5AFA6'))

    d.t('미확인', M, 336, 6.2, CRIMSON_L, True, tracking=1.6)
    y = 316
    for item in LIMITS['unknown']:
        d.t('—', M, y, 7.4, MUTED_D)
        d.t(item, M + 14, y, 7.4, HexColor('#D8D3CB'))
        y -= 18

    d.para(LIMITS['next'], M, 250, 480, 7.6, 11.4, HexColor('#A8A29A'))
    d.rule(M, 460, 178, dark=True)
    d.t('CONTACT', M, 156, 6.2, CRIMSON_L, True, tracking=1.6)
    d.t(COVER['contact'][0], M, 132, 10.0, WHITE)
    d.t(COVER['contact'][1], M + 168, 132, 10.0, WHITE)

    d.t('APPENDIX — 보고서 8편', 596, 452, 6.2, CRIMSON_L, True, tracking=1.6)
    y = 430
    for title, path in LIMITS['reports']:
        d.t(title, 596, y, 7.4, WHITE)
        d.t(path, 596, y - 9, 5.6, MUTED_D)
        y -= 30
    d.caption(14, LIMITS['note'], 40)
    d.page_break()


PAGE_FUNCS = (p01, p02, p03, p04, p05, p06, p07, p08, p09, p10, p11, p12, p13, p14)


# ── MD ─────────────────────────────────────────────────────────────────────
def write_md():
    L = []
    A = L.append

    A('# 메디큐브 콘텐츠 마케팅 포트폴리오')
    A('')
    A(f'> **14쪽 Behance식 가로형 덱 · {VERSION}** · 최종 수정 2026-11-22 KST · 김윤서 · 2026.11')
    A('> 에이피알(APR) [마케팅 특별채용] 국내 콘텐츠 마케팅 신입 지원 (마감 2026-11-22 23:59)')
    A('>')
    A('> 원컬러 배경(딥 차콜 `#18181B` / 웜 오프화이트 `#F8F7F5`)과 크림슨 한 색으로 조판한')
    A('> 이미지 중심 덱입니다. 검증 수치와 방법론은 14쪽·깃허브 보고서 8편으로 보냈습니다.')
    A('> PDF는 `analysis/task2/build_portfolio.py`가 같은 내용으로 만들며, 쪽 크기는')
    A('> **960×540pt(13.33×7.5in) 16:9**입니다. 디바이스 목업은 `analysis/task2/mockups.py`.')
    A('')
    A('---')
    A('')

    # 1쪽
    A('## 1쪽 · 표지')
    A('')
    A(f"**{COVER['kicker']}** · {COVER['year']}")
    A('')
    A(f"# {COVER['name']} — {COVER['ko']}")
    A('')
    A(COVER['line'])
    A('')
    A(COVER['role'])
    A('')
    A(COVER['axes'][0])
    A('')
    A(COVER['axes'][1])
    A('')
    A(f"CONTACT | {COVER['contact'][0]} | {COVER['contact'][1]}")
    A('')
    A(f"> {COVER['note']}")
    A('')
    A('---')
    A('')

    # 2쪽
    A('## 2쪽 · 프로필')
    A('')
    A(f"# {PROFILE['title'].replace(chr(10), ' ')}")
    A('')
    A(f"{PROFILE['name']} · {PROFILE['role']}")
    A('')
    A(' · '.join(PROFILE['tags']))
    A('')
    for line in PROFILE['academic']:
        A(line)
        A('')
    for line in PROFILE['cert']:
        A(line)
        A('')
    A(' · '.join(name for name, _ in PROFILE['skills']))
    A('')
    for no, title, body in PROFILE['strengths']:
        A(f'{no} · {title} — {body}')
        A('')
    A('숫자는 근거를 남기고, 시안은 끝까지 만듭니다.')
    A('')
    A('이 덱의 모든 판단에는 저장소의 원자료가 붙어 있습니다.')
    A('')
    A('![프로필 사진 · 김윤서](../private_submission/assets/profile_yunseo.jpg)')
    A('')
    A(f"> {PROFILE['note']}")
    A('')
    A('---')
    A('')

    # 3쪽
    A('## 3쪽 · 목차')
    A('')
    A(f"# {CONTENTS['title']} — {CONTENTS['sub']}")
    A('')
    A('| 쪽 | 제목 |')
    A('|---|---|')
    for no, title, page in CONTENTS['rows']:
        A(f'| {page} | {no} · {title} |')
    A('')
    for line in CONTENTS['axes']:
        A(f'- {line}')
    A('')
    A('확인된 것과 판단한 것을 나눠 쓰고,')
    A('')
    A('없는 성과는 만들지 않았습니다.')
    A('')
    A(f"> {CONTENTS['note']}")
    A('')
    A('---')
    A('')

    # 4쪽
    A('## 4쪽 · 두 축 한눈에')
    A('')
    A(f"# {OVERVIEW['title']}")
    A('')
    A(OVERVIEW['lead'])
    A('')
    for no, title, verdict, *rows in OVERVIEW['cards']:
        A(f"**{no} · {title}**")
        A('')
        A(verdict)
        A('')
        for label, value in rows:
            A(f'{label} | {value}')
        A('')
    A('| 숫자 | 내용 |')
    A('|---|---|')
    for value, label in OVERVIEW['kpis']:
        A(f'| {value} | {label} |')
    A('')
    A(f"> {OVERVIEW['note']}")
    A('')
    A('---')
    A('')

    # 5쪽 · 9쪽 — 프로젝트 인트로
    def project_intro(no_page, data):
        A(f'## {no_page}쪽 · {data["kicker"].replace(" · ", " — ")}')
        A('')
        A(f"# {data['title'].replace(chr(10), ' ')}")
        A('')
        A(data['sub'])
        A('')
        A('| 항목 | 내용 |')
        A('|---|---|')
        for label, value in data['about']:
            A(f'| {label} | {value} |')
        A('')
        A(f"> {data['caption']}")
        A('')
        A('---')
        A('')

    project_intro(5, P01)

    # 6쪽
    A('## 6쪽 · PROJECT 01 — 근거')
    A('')
    A(f"# {P01E['title']}")
    A('')
    A(P01E['lead'])
    A('')
    A('| 리뷰 코드 | 건수 |')
    A('|---|---|')
    for label, value in P01E['bars']:
        A(f'| {label} | {value}건 |')
    A('')
    for num, head, body in P01E['insights']:
        A(f'{head} | {num}')
        A('')
        A(body)
        A('')
    A(f"**{P01E['shot_title']}**")
    A('')
    A(P01E['shot_body'])
    A('')
    A(f"> {P01E['note']}")
    A('')
    A('---')
    A('')

    # 7쪽
    A('## 7쪽 · PROJECT 01 — 전략 & CRM')
    A('')
    A(f"# {P01S['title']}")
    A('')
    A(P01S['lead'])
    A('')
    A('| 구간 | 내용 |')
    A('|---|---|')
    for time, label in P01S['shots']:
        A(f'| {time} | {label} |')
    A('')
    A('| 채널 | 발송 조건 |')
    A('|---|---|')
    for title, cond in P01S['crm']:
        A(f'| {title} | {cond} |')
    A('')
    A(f"> {P01S['note']}")
    A('')
    A('---')
    A('')

    # 8쪽
    A('## 8쪽 · PROJECT 01 — 결과물')
    A('')
    A(f"# {P01O['title']}")
    A('')
    for no, title, sub in P01O['list']:
        A(f'| {no} | {title} | {sub} |')
    A('')
    A(f"> {P01O['note']}")
    A('')
    A('---')
    A('')

    project_intro(9, P02)

    # 10쪽
    A('## 10쪽 · PROJECT 02 — 근거')
    A('')
    A(f"# {P02E['title']}")
    A('')
    A(P02E['lead'])
    A('')
    A('| 장벽 | 언급 |')
    A('|---|---|')
    for label, value in P02E['bars']:
        A(f'| {label} | {value}건 |')
    A('')
    for num, head, body in P02E['insights']:
        A(f'{head} | {num}')
        A('')
        A(body)
        A('')
    A(f"**{P02E['shot_title']}**")
    A('')
    A(P02E['shot_body'])
    A('')
    A(f"> {P02E['note']}")
    A('')
    A('---')
    A('')

    # 11쪽
    A('## 11쪽 · PROJECT 02 — 개선안 & CRM')
    A('')
    A(f"# {P02S['title']}")
    A('')
    A(P02S['lead'])
    A('')
    A('| 장벽 | 언급 | 검토 과제 |')
    A('|---|---|---|')
    for label, count, task in P02S['rows']:
        A(f'| {label} | {count} | {task} |')
    A('')
    A('| 채널 | 메시지 | 발송 조건 |')
    A('|---|---|---|')
    for title, head, body in P02S['messages']:
        A(f'| {title} | {head} | {body} |')
    A('')
    A('내부 개선 검토 요약 · 3면')
    A('')
    A(f"> {P02S['note']}")
    A('')
    A('---')
    A('')

    # 12쪽
    A('## 12쪽 · PROJECT 02 — 결과물')
    A('')
    A(f"# {P02O['title']}")
    A('')
    for no, title, body in P02O['points']:
        A(f'| {no} | {title} | {body} |')
    A('')
    A('웹·태블릿 지면 · 2200×1460')
    A('')
    A(f"> {P02O['note']}")
    A('')
    A('---')
    A('')

    # 13쪽
    A('## 13쪽 · 일하는 방식')
    A('')
    A(f"# {PROCESS['title']}")
    A('')
    A(PROCESS['lead'])
    A('')
    for no, title, body in PROCESS['steps']:
        A(f'| {no} | {title} | {body} |')
    A('')
    A('“확인되지 않은 것은 확인된 것처럼 쓰지 않는다.”')
    A('')
    A('그래서 14쪽에 미확정을 먼저 적었습니다.')
    A('')
    A('TOOL | ' + ' | '.join(PROCESS['tools']))
    A('')
    A('판단은 직접, 생성은 도구로 — 인물 클립·내레이션·연출 컷은 AI로 만들고 검수는 직접 했습니다.')
    A('')
    A(f"> {PROCESS['note']}")
    A('')
    A('---')
    A('')

    # 14쪽
    A('## 14쪽 · 한계 · 부록')
    A('')
    A(f"# {LIMITS['title']}")
    A('')
    A('> ' + LIMITS['boundary'])
    A('')
    A('| 미확인 |')
    A('|---|')
    for item in LIMITS['unknown']:
        A(f'| {item} |')
    A('')
    A(LIMITS['next'])
    A('')
    A('| 보고서 | 저장소 경로 |')
    A('|---|---|')
    for title, path in LIMITS['reports']:
        A(f'| {title} | `{path}` |')
    A('')
    A(f"CONTACT | {COVER['contact'][0]} | {COVER['contact'][1]}")
    A('')
    A(f"> {LIMITS['note']}")
    A('')
    return '\n'.join(L)


def main():
    if not MOCK.exists() or not any(MOCK.glob('phone_*.png')):
        mockups.build_all()
    else:
        mockups.build_all()
    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    deck = Deck(OUT_PDF)
    for fn in PAGE_FUNCS:
        fn(deck)
    deck.c.save()
    OUT_MD.write_text(write_md(), encoding='utf-8')

    doc = pymupdf.open(OUT_PDF)
    print(f'{OUT_PDF.name}: {doc.page_count}쪽 · {doc[0].rect.width:.0f}×{doc[0].rect.height:.0f}pt')
    print(f'{OUT_MD.name}: {len(write_md().splitlines())}줄')
    return 0


if __name__ == '__main__':
    sys.exit(main())
