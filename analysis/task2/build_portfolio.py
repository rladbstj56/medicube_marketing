# -*- coding: utf-8 -*-
"""13쪽 포트폴리오 PDF·MD 생성기 — Behance 양식의 이미지 중심 16:9 덱.

2026-11-22 사용자 지시로 전면 재디자인했다. 이전 판(v0.3)은 검증 수치와 방어적
서술이 본문을 차지하는 편집형 보고서였고, 이번 판은 Behance 포트폴리오 세 편
(나현지 브랜딩&마케팅, 김다빈 마케팅, miok Kim PPT 템플릿)을 직접 열어 확인한
양식을 따른다.

- **원컬러 배경**: 딥 차콜 `#18181B` ↔ 웜 오프화이트 `#F8F7F5` 두 면만 쓰고,
  포인트는 메디큐브 크림슨 `#9B1B27` 한 색을 절제해서 쓴다. 붉은 박스·테두리를
  반복하지 않고 헤어라인과 여백으로 나눈다.
- **한 장에 한 메시지**: 큰 한 줄 + 숫자 2~3개 + 이미지. 검증용 수치(141항목·
  535건)와 방법론은 13쪽·깃허브 링크로 보내고, 본문에는 판단과 결과물만 남긴다.
- **디바이스 목업**: `mockups.py`가 만든 스마트폰·태블릿·브라우저 프레임에
  시안을 합성해 '화면 안에 놓인 모습'으로 보여준다.
- **AI 제작·승인 전 콘셉트 고지**는 쪽마다 캡션 한 줄로만 유지한다.

PDF와 MD는 같은 `PAGES` 데이터에서 나온다. 두 파일이 어긋날 수 없게 하려는
것이며, 값은 모두 저장소 현행 문서에서 그대로 옮겼다.
"""

import math
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
import tool_icons

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

# ── 2030 파트(4~7쪽) 아쿠아 팔레트 ─────────────────────────────────────────
# `private_submission/2030/glow_main_photo_water_harmonized_v3.png`의 맑은 물빛에서
# 뽑은 색만 쓴다. 표지·프로필·5060·부록 쪽은 위의 차콜/오프화이트/크림슨을 그대로 쓴다.
AQ_BG = HexColor('#F3F9FB')        # 아이스 아쿠아 화이트(밝은 장 배경)
AQ_PANEL = HexColor('#E2F0F5')     # 연한 미스트 아쿠아(쇼케이스 패널)
AQ_INK = HexColor('#12262E')       # 딥 슬레이트 네이비(본문 잉크)
AQ_MUTED = HexColor('#5C7883')     # 물빛 회색(보조 글자)
AQ_MUTED_D = HexColor('#8FA8B2')   # 어두운 면 위 보조 글자
AQ_HAIR = HexColor('#CFE3EA')      # 밝은 면 헤어라인
AQ_TEAL = HexColor('#165B72')      # 딥 워터 틸(밝은 면 포인트)
AQ_TEAL_L = HexColor('#6EC4DB')    # 아쿠아 틸(어두운 면 포인트)
AQ_DARK = HexColor('#0E1E26')      # 딥 오션(7쪽 배경)
AQ_HAIR_D = HexColor('#22353F')
AQ_SOFT_D = HexColor('#B9CDD6')    # 어두운 면 본문
KEYVIS = ROOT / 'private_submission/2030/glow_main_photo_water_harmonized_v3.png'

FONT, BOLD = 'NotoKR', 'NotoKR-Bold'
pdfmetrics.registerFont(TTFont(FONT, str(HERE / 'fonts/NotoSansKR-Regular.ttf')))
pdfmetrics.registerFont(TTFont(BOLD, str(HERE / 'fonts/NotoSansKR-Bold.ttf')))
pdfmetrics.registerFontFamily(FONT, normal=FONT, bold=BOLD, italic=FONT, boldItalic=BOLD)

PAGE_W, PAGE_H = 960.0, 540.0
M = 44.0
CW = PAGE_W - 2 * M
TOTAL = 13
VERSION = 'v1.4'

# ── 쪽별 내용 ───────────────────────────────────────────────────────────────
# 그리는 값과 MD에 적는 값이 같은 곳에서 나온다.

COVER = {
    'kicker': 'CONTENT MARKETING PORTFOLIO',
    'year': '2026',
    'name': 'KIM YOONSEO',
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
    'name': '김윤서',
    'role': 'Content Marketing · Data-driven',
    'tags': ('#데이터검증', '#콘텐츠기획', '#CRM설계'),
    'contacts': (('Email', 'rladbstj56@gmail.com'),
                 ('GitHub', 'https://github.com/rladbstj56')),
    'links': {'Email': 'mailto:rladbstj56@gmail.com',
              'GitHub': 'https://github.com/rladbstj56'},
    'education': (('숙명여자대학교 소프트웨어융합전공', '2020.03 - 2025.08'),
                  ('Brandenburg University of Technology (교환학생)', '2023.09 - 2024.08'),
                  ('팀스파르타 KDT 데이터 분석가 양성과정', '2025.12 - 2026.05')),
    'cert': (('빅데이터분석기사', '2026.07'), ('SQLD', '2025.04'),
             ('ADsP', '2025.09'), ('TOEIC', '925')),
    'tools': ('Python', 'SQL', 'GA4', 'Figma', 'MCP', 'Codex', 'CapCut'),
    'note': '사진과 이력은 지원자 본인이 제공한 내용입니다.',
}

CONTENTS = {
    'kicker': 'CONTENTS',
    'title': 'CONTENTS',
    'rows': (
        ('01', '프로필', '02', ()),
        ('02', 'PROJECT 01 — 2030 타깃 · 부스터 글로우 유입·전환 캠페인', '04',
         (('기간', '2026.11'),
          ('역할', '리뷰 코딩 · 콘티 · 포스터 · CRM'),
          ('산출물', '숏폼(릴스·쇼츠) · 키비주얼 포스터 · 자사몰 CRM(온사이트 배너·앱푸시)'))),
        ('03', 'PROJECT 02 — 5060 타깃 · GS샵 X2 홈쇼핑 연계 캠페인', '08',
         (('기간', '2026.11'),
          ('역할', '리뷰 코딩 · 채널 설계 · 지면 시안'),
          ('산출물', '홈쇼핑 티저·상세 랜딩 시안 · VOC 기반 UX/패키지 개선안 · 사후 CRM(알림톡·스냅푸시)'))),
        ('04', 'WORK PROCESS', '12', ()),
        ('05', '한계 · 부록', '13', ()),
    ),
}

P01 = {
    'kicker': 'PROJECT 01',
    'title': '2030을 타깃으로 한\n부스터 글로우\n마케팅 전략',
    'sub': '숏폼 30초 · 연계 포스터 · 자사몰 CRM',
    'about': (('기간', '2026.11'), ('기여도', '100%'),
              ('역할', '리뷰 코딩 · 콘티 · 시안 · CRM 설계'),
              ('툴', 'Python · SQL · Kling · CapCut · Photoshop'),
              ('목표', '고민 한 문장을 30초로 붙잡고, 자사몰 CRM으로 구매까지 잇기')),
    'caption': '아쿠아 키비주얼 1080×1920 · 엔드카드 1080×1920 — 실제 제품 사진 사용, 집행 전 시안',
}

P01E = {
    'kicker': 'PROJECT 01 · 근거',
    'title': '고민은 세 문장으로 반복됩니다',
    'lead': '공식몰 리뷰 217건과 글로우픽 15건을 전수 코딩했습니다. 가장 많이 나온 말은 광채·보습·피부결이었고, 그 세 갈래가 30초의 세 장면이 되었습니다.',
    'bars': (('광채 · 물광', 42), ('보습 · 속건조', 37), ('피부결 · 톤', 24)),
    'shots': (('샷 1', '20대 강의실 아침', '아침 기초 후 속건조 · 광채 부족',
               '물방울 초음파 광채 케어'),
              ('샷 2', '야근 후 퇴근길', '시간 없고 탄력은 처짐',
               '5가지 모드 · 12분 데일리 루틴'),
              ('샷 3', '외출 전 화장대', '피부결 들뜸 · 화장 밀림',
               '메이크업 전 부스트 · 글로우 케어')),
    'note': '모든 건수는 공식몰 리뷰 217건·글로우픽 15건 표본 안의 몫입니다. 장면별 고민·케어 표현은 집행 전 시안입니다.',
}

P01S = {
    'kicker': 'PROJECT 01 · CRM STRATEGY',
    'title': '디바이스가 고객의 매일 루틴이\n되도록 설계한 디지털 클리닉\n앱 CRM 전략',
    'lead': '이미 쓰고 있는 메디큐브 디지털 클리닉(AGE-R) 앱을 루틴 관리 중심으로 확장했습니다.|알림이 오는 시간이 곧 디바이스를 켜는 시간이 됩니다.',
    'points': (('①', '루틴 · 알림 시간 설정',
                '매일 밤 10:30, 주 5회. 내 피부 고민 모드(물광)를 고르면 그 모드에 맞춰 루틴 단계가 바뀝니다.'),
               ('②', '설정 시간 데일리 푸시',
                '"윤서님, 오늘 밤 10:30 글로우 12분 루틴 시간이에요" — 앱을 열지 않아도 12분이 시작됩니다.'),
               ('③', '루틴 달성 트래커 · 리포트',
                '주 5일 달성, 연속 12일, 모드별 사용 횟수를 쌓아 디바이스 사용을 습관으로 남깁니다.')),
    'flow': '온사이트 배너 → D+1 모드 안내 → 매일 10:30 루틴 알림 → 주간 리포트',
    'note': '[실행 제안] 앱 화면은 기획 시안 · 실제 앱 반영·발송 기록은 없습니다 · [AI 제작] 화면 목업 이미지는 생성형 AI 제작',
}

P01O = {
    'kicker': 'PROJECT 01 · OUTPUT',
    'title': '포스터에서 루틴 카드까지, 7종',
    'lead': '인쇄 규격으로 마감한 포스터 2종, 엔드카드와 키비주얼, 루틴 카드 3종입니다. 화면용과 인쇄용을 같은 키비주얼에서 뽑았습니다.',
    'items': (('01', '메인 포스터', '1080×1350', 'print_poster.png', '하루의 세 순간'),
              ('02', '헬로키티 에디션', '1080×1350', 'print_kitty.png', '별도 기획 · 판매 CTA 없음'),
              ('03', '엔드카드 v3', '1080×1920', 'print_endcard.png', '제품 사진 + 자사몰 CTA'),
              ('04', '아쿠아 키비주얼', '1080×1920', 'print_keyvisual.png', '물빛 제품 사진'),
              ('05', '브릿지 01', '1080×1920', 'print_bridge1.png', '초음파 1–3–10MHz'),
              ('06', '브릿지 02', '1080×1920', 'print_bridge2.png', '5가지 모드'),
              ('07', '브릿지 03', '1080×1920', 'print_bridge3.png', '약 12분 데일리 루틴')),
    'note': '[AI 제작] 포스터 연출 컷은 생성형 AI · 실제 광고 집행과 성과는 없습니다 · 숏폼 완본은 편집 진행 중(보류 가능)',
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
    'kicker': '04 · WORK PROCESS',
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
    'kicker': '05 · LIMITS & APPENDIX',
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


def cover_fade(path, name, w, h, fade_w, color, valign='c', scale=2.6):
    """이미지를 상자 비율로 꽉 채워 자르고, 왼쪽 가장자리를 color로 녹인 PNG를 만든다.

    보고서 캔버스 위에 얇은 사각형을 쌓는 방식은 계단이 보이므로, 픽셀 단위 알파
    마스크를 PIL로 만들어 한 장의 이미지로 그린다.
    """
    rgb = (int(color.red * 255), int(color.green * 255), int(color.blue * 255))
    im = PILImage.open(path).convert('RGB')
    iw, ih = im.size
    s = max(w / iw, h / ih)
    im = im.resize((max(1, int(iw * s * scale)), max(1, int(ih * s * scale))), PILImage.LANCZOS)
    W, H = int(w * scale), int(h * scale)
    left = (im.width - W) // 2
    off = {'t': im.height - H, 'c': (im.height - H) // 2, 'b': 0}[valign]
    im = im.crop((left, off, left + W, off + H))
    mask = PILImage.new('L', (W, H), 255)
    fw = max(1, min(W, int(fade_w * scale)))
    ramp = PILImage.new('L', (fw, 1))
    ramp.putdata([int(255 * x / fw) for x in range(fw)])
    mask.paste(ramp.resize((fw, H), PILImage.NEAREST), (0, 0))
    base = PILImage.new('RGB', (W, H), rgb)
    base.paste(im, (0, 0), mask)
    out = TMP / 'fade' / f'{name}.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    base.save(out, optimize=True)
    return out


class Deck:
    def __init__(self, path):
        self.c = canvas.Canvas(str(path), pagesize=(PAGE_W, PAGE_H))
        self.c.setTitle('메디큐브 콘텐츠 마케팅 포트폴리오')
        self.c.setAuthor('김윤서')
        self.c.setSubject('에이피알(APR) 국내 콘텐츠 마케팅 지원 포트폴리오')

    # ── 면 ──────────────────────────────────────────────────────────────
    def bg(self, dark=False, color=None):
        self.c.setFillColor(color or (INK if dark else PAPER))
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
    def chrome(self, no, kicker, dark=False, right=None, accent=None, label=None, hair=None):
        color = accent or (CRIMSON_L if dark else CRIMSON)
        self.t(kicker, M, 503, 6.4, color, True, tracking=1.7)
        self.t(right or HEAD['right'], PAGE_W - M, 503, 6.2,
               label or (MUTED_D if dark else MUTED), align='r')
        self.rule(M, PAGE_W - M, 494, dark, color=hair)
        self.t(f'{no:02d} / {TOTAL}', PAGE_W - M, 28, 6.2,
               label or (MUTED_D if dark else MUTED), align='r')

    def caption(self, no, text, y=40, color=None):
        self.t(text, M, y, 6.1, color or (MUTED_D if no in (1, 3, 7, 11, 13) else MUTED))

    def page_break(self):
        self.c.showPage()


# ── 쪽 그리기 ───────────────────────────────────────────────────────────────

def p01(d):
    d.bg(dark=True)
    c = d.c
    # 사원증 — 증명사진 세로 비율(689:886)만큼 카드를 길게 잡아 사진 전체를 넣는다
    cx, card_w = 172.0, 126.0
    pad, below = 11.0, 55.0          # pad: 사진 상자 여백 · below: 사진 아래 이름·직함 자리
    iw, ih = PILImage.open(PHOTO).size
    pw = card_w - pad * 2
    ph = pw * ih / iw                # 104 × 133.7 — 사진을 자르지 않는 높이
    card_h = below + ph + pad
    card_y = 370.0 - card_h / 2
    c.setFillColor(HexColor('#2C2C31'))
    c.rect(cx - 10, card_y + card_h - 6, 20, PAGE_H - (card_y + card_h - 6), stroke=0, fill=1)
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
    # 증명사진 — 세로 비율 그대로 그려 어깨까지 잘리지 않는다
    px, py = cx - card_w / 2 + pad, card_y + below
    c.setFillColor(HexColor('#E5DFD7'))
    c.rect(px, py, pw, ph, stroke=0, fill=1)
    d.img(PHOTO, px, py, w=pw)
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
    """2쪽 프로필 — 왼쪽 증명사진·이름, 오른쪽 2×2 네 섹션.

    2026-11-22 사용자 지시 4차: 오른쪽 3단을 걷어내고 슬랙에 올린 레퍼런스
    (`downloads/slack_profile_ref.png`)처럼 **Contacts · Education ·
    Certificate · Skill & Tool** 네 칸을 2×2로 두었다. 섹션 제목 위에 레퍼런스와
    같은 작은 기호(●·■·*·■)를 붙이고, Skill & Tool은 레벨 막대 대신 툴 아이콘
    7개(4+3)와 작은 영문명만 둔다. 왼쪽 사진은 158×203pt 원본 비율 그대로이고
    두 영역의 위끝을 468pt에서 맞춰 한 줄로 읽히게 했다.
    """
    d.bg()
    d.chrome(2, PROFILE['kicker'])
    c = d.c
    TOP = 468.0                     # 두 영역의 위끝

    # ── 왼쪽 — 증명사진·이름·역할·태그 (세로 비율 그대로, 잘림 없음) ────
    pw = 158.0
    iw, ih = PILImage.open(PHOTO).size
    ph = pw * ih / iw               # 158 × 203 — 689:886 비율
    py = TOP - ph
    c.setFillColor(HexColor('#EAE5DE'))
    c.rect(M, py, pw, ph, stroke=0, fill=1)
    d.img(PHOTO, M, py, w=pw)
    c.setStrokeColor(HAIR)
    c.setLineWidth(0.5)
    c.rect(M, py, pw, ph, stroke=1, fill=0)

    d.t(PROFILE['name'], M, py - 32, 19, INK, True)
    d.t(PROFILE['role'], M, py - 50, 8.6, MUTED)
    tag_h, tag_step = 18.0, 27.0
    ty = py - 74                    # 첫 태그 상자 위끝
    for tag in PROFILE['tags']:
        tw = pdfmetrics.stringWidth(tag, FONT, 7.2) + 15
        c.setStrokeColor(HAIR)
        c.setLineWidth(0.6)
        c.roundRect(M, ty - tag_h, tw, tag_h, tag_h / 2, stroke=1, fill=0)
        d.t(tag, M + 7.5, ty - tag_h + 5.2, 7.2, MUTED)
        ty -= tag_step

    # ── 오른쪽 — 2×2 네 섹션 ─────────────────────────────────────────
    X1, COL, GAP = 250.0, 310.0, 46.0
    X2 = X1 + COL + GAP             # 606
    ROW1, ROW2 = TOP, TOP - 176.0   # 468 / 292
    TITLE, ROW_H = 16.5, 22.0
    ROW_SZ, DATE_SZ, VALUE_X = 9.6, 8.6, 70.0

    def mark(x, y, kind):
        mx, my = x + 3.6, y - 4.2
        c.setFillColor(CRIMSON)
        if kind == 'circle':
            c.circle(mx, my, 3.0, stroke=0, fill=1)
        elif kind == 'square':
            c.rect(mx - 2.7, my - 2.7, 5.4, 5.4, stroke=0, fill=1)
        else:                        # 네 갈래 별
            p = c.beginPath()
            for k in range(8):
                r = 4.7 if k % 2 == 0 else 1.7
                a = math.radians(90 * k)
                px, py_ = mx + r * math.cos(a), my + r * math.sin(a)
                p.moveTo(px, py_) if k == 0 else p.lineTo(px, py_)
            p.close()
            c.drawPath(p, stroke=0, fill=1)

    def head(x, y, label, kind):
        mark(x, y, kind)
        d.t(label, x, y - 24, TITLE, INK, True)
        d.rule(x, x + COL, y - 33)

    # 1) 좌상단 — Contacts (●)
    head(X1, ROW1, 'Contacts', 'circle')
    for i, (label, value) in enumerate(PROFILE['contacts']):
        y = ROW1 - 51 - i * ROW_H
        d.t(label, X1, y, 8.4, MUTED, True)
        w = d.t(value, X1 + VALUE_X, y, ROW_SZ, INK)
        c.linkURL(PROFILE['links'][label],
                  (X1 + VALUE_X, y - 2.6, X1 + VALUE_X + w, y + 9.6),
                  relative=0, thickness=0)

    # 2) 우상단 — Education (■)
    head(X2, ROW1, 'Education', 'square')
    for i, (name, period) in enumerate(PROFILE['education']):
        y = ROW1 - 51 - i * ROW_H
        d.t(name, X2, y, ROW_SZ, INK)
        d.t(period, X2 + COL, y, DATE_SZ, MUTED, align='r')

    # 3) 좌하단 — Certificate (*)
    head(X1, ROW2, 'Certificate', 'star')
    for i, (name, period) in enumerate(PROFILE['cert']):
        y = ROW2 - 51 - i * ROW_H
        d.t(name, X1, y, ROW_SZ, INK)
        d.t(period, X1 + COL, y, DATE_SZ, MUTED, align='r')

    # 4) 우하단 — Skill & Tool (■) — 레벨 막대 없이 아이콘만
    head(X2, ROW2, 'Skill & Tool', 'square')
    icons = tool_icons.build_all()
    tile, icon, icon_step = COL / 4, 34.0, 60.0
    for i, name in enumerate(PROFILE['tools']):
        cx = X2 + tile * (i % 4) + tile / 2
        iy = ROW2 - 50 - (i // 4) * icon_step - icon
        c.drawImage(str(icons[name]), cx - icon / 2, iy, icon, icon, mask='auto')
        d.t(name, cx, iy - 9.8, 6.8, MUTED, align='c')

    d.caption(2, PROFILE['note'], 40)
    d.page_break()


def p03(d):
    """3쪽 목차 — 큰 CONTENTS와 목차 5행.

    2026-11-22 사용자 지시로 부제·축 요약·원칙 문장·읽는 순서 안내를 걷어내고,
    두 프로젝트 행에 기간·역할·산출물을 붙였다. 라벨은 오른쪽 정렬(x=446),
    값은 모두 같은 x(456)에서 시작해 세 줄이 자로 잰 듯 나란히 선다.
    """
    d.bg(dark=True)
    d.chrome(3, CONTENTS['kicker'], dark=True)
    d.t(CONTENTS['title'], M, 402, 34, WHITE, True, tracking=1.0)

    ROW, PROJ, META = 54.0, 88.0, 17.0
    total = sum(PROJ if meta else ROW for _, _, _, meta in CONTENTS['rows'])
    top = 268.0 + total / 2
    for no, title, page, meta in CONTENTS['rows']:
        h = PROJ if meta else ROW
        d.t(no, 368, top - 14, 17, HexColor('#4E4E57'), True)
        d.t(title, 404, top - 13, 11.4,
            WHITE if meta else HexColor('#D8D3CB'), bool(meta))
        d.t(page, PAGE_W - M, top - 13, 8.0, CRIMSON_L, True, align='r')
        y = top - 34
        for label, value in meta:
            d.t(label, 446, y, 8.2, MUTED_D, align='r')
            d.t(value, 456, y, 8.2, HexColor('#B5AFA6'))
            y -= META
        d.rule(368, PAGE_W - M, top - h + 10, dark=True)
        top -= h
    d.page_break()


def _sidebar(d, data, y_top=470, ink=INK, accent=CRIMSON, muted=MUTED):
    d.t(data['kicker'], M, y_top, 6.6, accent, True, tracking=2.0)
    lines = data['title'].split('\n')
    y = y_top - 26
    for line in lines:
        d.t(line, M, y, 24, ink, True)
        y -= 26
    d.para(data['sub'], M, y + 6, 236, 7.8, 11.6, muted)
    y -= 18
    d.t('ABOUT', M, y - 6, 6.2, accent, True, tracking=1.6)
    y -= 22
    for label, value in data['about']:
        d.t(label, M, y, 6.0, muted, tracking=0.8)
        h = d.para(value, M + 40, y + 1.6, 196, 7.2, 10.8, ink)
        y -= max(h + 5, 15)
    return y


def p05(d):
    """4쪽 PROJECT 01 · INTRO — 제목 3줄, ABOUT 정렬, 앵글드 아이폰 히어로.

    2026-11-22 사용자 지시: 제목을 `2030을 타깃으로 한 부스터 글로우 마케팅 전략`으로
    바꾸고, ABOUT의 라벨·값을 3쪽 목차처럼 오른쪽 정렬 라벨 + 고정 x 값으로 맞췄다.
    오른쪽 아이폰은 슬랙에 올린 Pinterest `Floating Angled` 레퍼런스처럼 원근·측면
    두께·두 겹 그림자를 준 `phone_endcard_angled.png`로 교체했다.
    """
    d.bg(color=AQ_BG)
    d.chrome(4, P01['kicker'] + ' · INTRO', accent=AQ_TEAL, label=AQ_MUTED, hair=AQ_HAIR)

    # ── 왼쪽 — 제목 3줄 + ABOUT ─────────────────────────────────────
    X, LABEL_R, VAL_X = M, 104.0, 116.0
    d.t(P01['kicker'], X, 470, 6.6, AQ_TEAL, True, tracking=2.0)
    y = 442
    for line in P01['title'].split('\n'):
        d.t(line, X, y, 21.0, AQ_INK, True)
        y -= 25
    d.para(P01['sub'], X, y + 6, 232, 7.8, 11.6, AQ_MUTED)

    ay = y - 22
    d.t('ABOUT', X, ay, 6.2, AQ_TEAL, True, tracking=1.6)
    ay -= 24
    for label, value in P01['about']:
        d.t(label, LABEL_R, ay, 6.4, AQ_MUTED, align='r')
        h = d.para(value, VAL_X, ay + 2.0, 318 - VAL_X, 7.3, 11.0, AQ_INK)
        ay -= max(h + 10, 20)

    # ── 오른쪽 — 아쿠아 키비주얼 위에 떠 있는 앵글드 아이폰 ─────────
    PX, PY, PH = 318.0, 54.0, 416.0
    d.panel(PX, PY, PAGE_W - PX, PH, color=AQ_PANEL)
    VX = 470.0
    hero = cover_fade(KEYVIS, 'p04_hero', PAGE_W - VX, PH, 104, AQ_PANEL, valign='t')
    d.img(hero, VX, PY, w=PAGE_W - VX, h=PH)
    d.img(MOCK / 'phone_endcard_angled.png', 352, 60, h=392)
    d.caption(4, P01['caption'], 40, AQ_MUTED)
    d.page_break()


def p06(d):
    """5쪽 PROJECT 01 · 근거 — 왼쪽 리뷰 막대 + 샷 3개를 아이폰 목업으로 크게.

    2026-11-22 사용자 지시: 오른쪽 KPI·설명 글씨는 모두 걷어내고, 샷 1·2·3을
    각각 목업으로 세워 그 아래에 '인물의 고민 → 부스터 글로우의 케어'를 짝지어 놓았다.
    """
    d.bg(color=AQ_BG)
    d.chrome(5, P01E['kicker'], accent=AQ_TEAL, label=AQ_MUTED, hair=AQ_HAIR)
    d.t(P01E['title'], M, 452, 23, AQ_INK, True)
    d.para(P01E['lead'], M, 428, 620, 8.4, 12.8, AQ_MUTED)

    # ── 왼쪽 — 리뷰 코드 막대(샷 목업과 같은 높이의 판 위에) ────────
    d.panel(M, 96, 256, 248, color=AQ_PANEL)
    d.t('공식몰 리뷰 217건', M + 14, 320, 6.2, AQ_TEAL, True, tracking=1.4)
    d.t('코드 상위', M + 14, 308, 6.2, AQ_TEAL, True, tracking=1.4)
    y = 276
    maxv = max(v for _, v in P01E['bars'])
    for label, value in P01E['bars']:
        d.t(label, M + 14, y, 7.4, AQ_INK)
        w = 92 * value / maxv
        d.c.setFillColor(AQ_TEAL)
        d.c.rect(M + 14, y - 12.6, w, 6.6, stroke=0, fill=1)
        d.t(f'{value}건', M + 14 + w + 7, y - 5.2, 7.2, AQ_MUTED, True)
        y -= 34
    d.rule(M + 14, M + 242, 168, color=AQ_HAIR)
    d.t('글로우픽 15건 포함', M + 14, 150, 6.2, AQ_MUTED)
    d.t('전수 코딩', M + 14, 138, 6.2, AQ_MUTED)

    # ── 오른쪽 — 샷 3개 ────────────────────────────────────────────
    for i, (no, place, pain, care) in enumerate(P01E['shots']):
        cx = 386 + i * 200
        d.rule(cx - 62, cx + 116, 406, color=AQ_HAIR)
        d.t(no, cx - 62, 392, 6.6, AQ_TEAL, True, tracking=0.8)
        d.t(place, cx - 44, 392, 6.6, AQ_MUTED)
        d.t('고민', cx - 62, 374, 6.0, AQ_MUTED, True, tracking=1.2)
        d.para(pain, cx - 62, 366, 178, 7.4, 10.4, AQ_INK, bold=True)
        d.img(MOCK / f'phone_shot{i + 1}.png', cx, 96, h=248)
        d.t('부스터 글로우 케어', cx - 62, 84, 6.0, AQ_TEAL, True, tracking=1.2)
        d.para(care, cx - 62, 76, 178, 7.2, 10.4, AQ_MUTED)
    d.caption(5, P01E['note'], 40, AQ_MUTED)
    d.page_break()


def p07(d):
    """6쪽 PROJECT 01 · CRM STRATEGY — 디지털 클리닉 앱 업그레이드 3화면.

    2026-11-22 사용자 지시: 0~21초 인물 샷 3개를 걷어내고(5쪽으로 이동), 앱을 루틴
    관리 중심으로 확장한 화면 ①설정 ②데일리 푸시 ③달성 리포트를 목업 3대에 넣었다.
    """
    d.bg(color=AQ_BG)
    d.chrome(6, P01S['kicker'], accent=AQ_TEAL, label=AQ_MUTED, hair=AQ_HAIR)

    LX, LW = M, 330.0
    y = 452
    for line in P01S['title'].split('\n'):
        d.t(line, LX, y, 18.0, AQ_INK, True)
        y -= 23
    y -= 4
    for line in P01S['lead'].split('|'):
        y -= d.para(line, LX, y, LW, 7.8, 11.6, AQ_MUTED) + 2
    y -= 10

    for no, head, body in P01S['points']:
        d.t(no, LX, y - 1, 8.6, AQ_TEAL, True)
        d.t(head, LX + 15, y, 8.2, AQ_INK, True)
        y -= 12
        h = d.para(body, LX + 15, y, LW - 15, 7.2, 10.4, AQ_MUTED)
        y -= h + 12

    # CRM 여정 — 기존 접점이 앱 안으로 이어지는 순서
    d.rule(LX, LX + LW, 214, color=AQ_HAIR)
    d.t('CRM 여정', LX, 198, 6.0, AQ_TEAL, True, tracking=1.4)
    d.para(P01S['flow'], LX, 188, LW, 7.0, 10.2, AQ_MUTED)

    # 오른쪽 — 앱 화면 3대
    labels = ('① 루틴 · 알림 설정', '② 설정 시간 데일리 푸시', '③ 달성 트래커 · 리포트')
    for i, (name, label) in enumerate(zip(('phone_app_setup.png', 'phone_app_push.png',
                                           'phone_app_report.png'), labels)):
        x = 404 + i * 172
        w, h = d.img(MOCK / name, x, 92, h=322)
        d.t(label, x + w / 2, 424, 6.6, AQ_INK, True, align='c')
    d.caption(6, P01S['note'], 40, AQ_MUTED)
    d.page_break()


def p08(d):
    """7쪽 PROJECT 01 · OUTPUT — 아이폰 목업 없이 인쇄물 7종만 크게.

    2026-11-22 사용자 지시: 샷 3개 목업을 빼고 브릿지 3종·엔드카드·메인 포스터·
    헬로키티 에디션·아쿠아 키비주얼만 남겼다. 7장이 한 줄에 들어가도록 높이를
    폭에서 역산해(7장 + 6틈 = 지면 폭) 각 인쇄물을 최대 크기로 세웠다.
    """
    d.bg(color=AQ_DARK)
    d.chrome(7, P01O['kicker'], dark=True, accent=AQ_TEAL_L,
             label=AQ_MUTED_D, hair=AQ_HAIR_D)
    d.t(P01O['title'], M, 452, 21, WHITE, True)
    d.para(P01O['lead'], M, 428, 640, 7.6, 11.2, AQ_SOFT_D)

    items = P01O['items']
    ratios = []
    for *_, name, _desc in items:
        iw, ih = PILImage.open(MOCK / name).size
        ratios.append(iw / ih)
    gap = 9.0
    h = (CW - gap * (len(items) - 1)) / sum(ratios)
    x = M
    bottom = 175.0
    for (no, title, spec, name, desc), ratio in zip(items, ratios):
        w = h * ratio
        d.img(MOCK / name, x, bottom, w=w, h=h)
        d.t(no, x, bottom - 14, 6.0, AQ_TEAL_L, True, tracking=0.6)
        d.t(title, x + 12, bottom - 14, 6.0, AQ_SOFT_D)
        d.t(desc, x, bottom - 25, 5.7, AQ_TEAL_L)
        x += w + gap
    d.rule(M, PAGE_W - M, 104, dark=True, color=AQ_HAIR_D)
    d.t('포스터 2종 1080×1350 · 엔드카드·키비주얼·루틴 카드 1080×1920',
        M, 90, 6.2, AQ_MUTED_D)
    d.t('포스터 재생성본 반영', PAGE_W - M, 90, 6.2, AQ_TEAL_L, align='r')
    d.caption(7, P01O['note'], 40, AQ_MUTED_D)
    d.page_break()


def p09(d):
    d.bg()
    d.chrome(8, P02['kicker'] + ' · INTRO')
    _sidebar(d, P02)
    d.panel(320, 58, PAGE_W - M - 320, 404)
    d.img(MOCK / 'print_teaser.png', 344, 100, h=296)
    d.img(MOCK / 'print_details.png', 604, 128, h=240)
    d.caption(8, P02['caption'], 40)
    d.page_break()


def p10(d):
    d.bg()
    d.chrome(9, P02E['kicker'])
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
    d.caption(9, P02E['note'], 40)
    d.page_break()


def p11(d):
    d.bg()
    d.chrome(10, P02S['kicker'])
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
    d.caption(10, P02S['note'], 40)
    d.page_break()


def p12(d):
    d.bg(dark=True)
    d.chrome(11, P02O['kicker'], dark=True)
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
    d.caption(11, P02O['note'], 40)
    d.page_break()


def p13(d):
    d.bg()
    d.chrome(12, PROCESS['kicker'])
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
    d.t('그래서 13쪽에 미확정을 먼저 적었습니다.', M, 176, 7.8, MUTED)

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
    d.caption(12, PROCESS['note'], 40)
    d.page_break()


def p14(d):
    d.bg(dark=True)
    d.chrome(13, LIMITS['kicker'], dark=True)
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
    d.caption(13, LIMITS['note'], 40)
    d.page_break()


PAGE_FUNCS = (p01, p02, p03, p05, p06, p07, p08, p09, p10, p11, p12, p13, p14)


# ── MD ─────────────────────────────────────────────────────────────────────
def write_md():
    L = []
    A = L.append

    A('# 메디큐브 콘텐츠 마케팅 포트폴리오')
    A('')
    A(f'> **13쪽 Behance식 가로형 덱 · {VERSION}** · 최종 수정 2026-11-22 KST · 김윤서 · 2026.11')
    A('> 에이피알(APR) [마케팅 특별채용] 국내 콘텐츠 마케팅 신입 지원 (마감 2026-11-22 23:59)')
    A('>')
    A('> 표지·프로필·5060·부록은 딥 차콜 `#18181B` / 웜 오프화이트 `#F8F7F5`와 크림슨 한 색,')
    A('> 2030 파트(4~7쪽)는 아쿠아 키비주얼의 물빛(`#F3F9FB`·`#E2F0F5`·`#165B72`,')
    A('> 어두운 7쪽은 `#0E1E26`·`#6EC4DB`)으로 조판했습니다.')
    A('> 검증 수치와 방법론은 13쪽·깃허브 보고서 8편으로 보냈습니다.')
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
    A(f"# {PROFILE['name']} — {PROFILE['role']}")
    A('')
    A(' · '.join(PROFILE['tags']))
    A('')
    A('**Contacts**')
    A('')
    A('| 항목 | 내용 |')
    A('|---|---|')
    for label, value in PROFILE['contacts']:
        A(f'| {label} | {value} |')
    A('')
    A('**Education**')
    A('')
    A('| 기간 | 학교 · 과정 |')
    A('|---|---|')
    for name, period in PROFILE['education']:
        A(f'| {period} | {name} |')
    A('')
    A('**Certificate**')
    A('')
    A('| 기간 또는 점수 | 자격 |')
    A('|---|---|')
    for name, period in PROFILE['cert']:
        A(f'| {period} | {name} |')
    A('')
    A('**Skill & Tool**')
    A('')
    A(' · '.join(PROFILE['tools']))
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
    A(f"# {CONTENTS['title']}")
    A('')
    A('| 쪽 | 제목 |')
    A('|---|---|')
    for no, title, page, meta in CONTENTS['rows']:
        A(f'| {page} | {no} · {title} |')
        for label, value in meta:
            A(f'| | {label} · {value} |')
    A('')
    A('---')
    A('')

    # 4쪽 · 8쪽 — 프로젝트 인트로
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

    project_intro(4, P01)

    # 5쪽
    A('## 5쪽 · PROJECT 01 — 근거 & 숏폼 3샷')
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
    A('글로우픽 15건 포함 · 전수 코딩')
    A('')
    A('| 샷 | 장면 | 인물의 고민 | 부스터 글로우의 케어 |')
    A('|---|---|---|---|')
    for no, place, pain, care in P01E['shots']:
        A(f'| {no} | {place} | {pain} | {care} |')
    A('')
    A(f"> {P01E['note']}")
    A('')
    A('---')
    A('')

    # 6쪽
    A('## 6쪽 · PROJECT 01 — CRM STRATEGY')
    A('')
    A(f"# {P01S['title'].replace(chr(10), ' ')}")
    A('')
    A(P01S['lead'].replace('|', ' '))
    A('')
    A('| 순서 | 화면 | 설계 |')
    A('|---|---|---|')
    for no, head, body in P01S['points']:
        A(f'| {no} | {head} | {body} |')
    A('')
    A('CRM 여정')
    A('')
    A(P01S['flow'])
    A('')
    A(f"> {P01S['note']}")
    A('')
    A('---')
    A('')

    # 7쪽
    A('## 7쪽 · PROJECT 01 — 결과물')
    A('')
    A(f"# {P01O['title']}")
    A('')
    A(P01O['lead'])
    A('')
    A('| 연번 | 인쇄물 | 규격 | 설명 |')
    A('|---|---|---|---|')
    for no, title, spec, _, desc in P01O['items']:
        A(f'| {no} | {title} | {spec} | {desc} |')
    A('')
    A('포스터 2종 1080×1350 · 엔드카드·키비주얼·루틴 카드 1080×1920')
    A('')
    A('숏폼 완본은 편집 진행 중(보류 가능) · 포스터 재생성본 반영')
    A('')
    A(f"> {P01O['note']}")
    A('')
    A('---')
    A('')

    project_intro(8, P02)

    # 9쪽
    A('## 9쪽 · PROJECT 02 — 근거')
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

    # 10쪽
    A('## 10쪽 · PROJECT 02 — 개선안 & CRM')
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

    # 11쪽
    A('## 11쪽 · PROJECT 02 — 결과물')
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

    # 12쪽
    A('## 12쪽 · 일하는 방식')
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
    A('그래서 13쪽에 미확정을 먼저 적었습니다.')
    A('')
    A('TOOL | ' + ' | '.join(PROCESS['tools']))
    A('')
    A('판단은 직접, 생성은 도구로 — 인물 클립·내레이션·연출 컷은 AI로 만들고 검수는 직접 했습니다.')
    A('')
    A(f"> {PROCESS['note']}")
    A('')
    A('---')
    A('')

    # 13쪽
    A('## 13쪽 · 한계 · 부록')
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
