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

import csv
import re
import sys
import zipfile
from datetime import date as _date
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import pymupdf
from PIL import Image as PILImage
from PIL import ImageDraw
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

# ── 5060 파트(9~11쪽) 플럼 팔레트 ───────────────────────────────────────────
# 사용자가 확정한 5060 홍보물 2종(`x2_gsshop_promo_hero_plum_v3.jpg`·`x2_home_modes_guide_plum_v2.png`)의
# 딥 플럼 + 소프트 블러시 핑크에서 뽑은 색만 쓴다. 9·10쪽은 밝은 블러시 면,
# 11쪽은 #1E1019 다크 쇼케이스이며, 2030 아쿠아 파트와 정반대 온도로 마주 세운다.
PLUM_BG = HexColor('#F9F4F7')       # 소프트 블러시 화이트(밝은 면 배경)
PLUM_PANEL = HexColor('#F3D5E5')    # 블러시 핑크(버튼·칩·강조 면)
PLUM_INK = HexColor('#2A1020')      # 딥 플럼 잉크(밝은 면 본문)
PLUM_MUTED = HexColor('#7A5A6B')    # 플럼 그레이(보조 글자)
PLUM_HAIR = HexColor('#EAD8E2')     # 밝은 면 헤어라인
PLUM = HexColor('#6B2A50')          # 딥 플럼 포인트(라벨·막대)
PLUM_L = HexColor('#D8A8C4')        # 어두운 면 포인트(블러시 릴리프)
PLUM_DARK = HexColor('#1E1019')     # 11쪽 다크 쇼케이스 바탕
PLUM_DEEP = HexColor('#4A1C3A')     # 9쪽 무드 패널 그라데이션 상단
PLUM_DEEP2 = HexColor('#240E1C')    # 9쪽 무드 패널 그라데이션 하단
PLUM_SOFT_D = HexColor('#C9A9BC')   # 어두운 면 본문
PLUM_MUTED_D = HexColor('#9B7A8C')  # 어두운 면 보조 글자
PLUM_HAIR_D = HexColor('#3A2331')   # 어두운 면 헤어라인
CLICK_LINE = HexColor('#B06C93')    # 10쪽 52주 그래프의 클릭 계열(검색 PLUM과 구분)
SEARCH_AREA = HexColor('#F6E9F1')   # 10쪽 검색 계열 아래 면

FONT, BOLD = 'NotoKR', 'NotoKR-Bold'
pdfmetrics.registerFont(TTFont(FONT, str(HERE / 'fonts/NotoSansKR-Regular.ttf')))
pdfmetrics.registerFont(TTFont(BOLD, str(HERE / 'fonts/NotoSansKR-Bold.ttf')))
pdfmetrics.registerFontFamily(FONT, normal=FONT, bold=BOLD, italic=FONT, boldItalic=BOLD)

PAGE_W, PAGE_H = 960.0, 540.0
M = 44.0
CW = PAGE_W - 2 * M
TOTAL = 14
VERSION = 'v2.2'

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
    # 2026-11-22 사용자 지시(1번): 타깃·제품·역할이 한눈에 들어오는 표현으로.
    'axes': ('01  2030 타깃 부스터 글로우 마케팅', '02  5060 타깃 부스터 프로 X2 마케팅'),
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
    # 2026-11-22 사용자 지시(2번): 자격 3개는 날짜 뒤에 `취득`, TOEIC은 점수로.
    'cert': (('빅데이터분석기사', '2026.07 취득'), ('SQLD', '2025.04 취득'),
             ('ADsP', '2025.09 취득'), ('TOEIC', '925점')),
    'tools': ('Python', 'SQL', 'Notion', 'Figma', 'MCP',
              'Codex', 'CapCut', 'Higgsfield', 'Kling', 'ElevenLabs'),
}

CONTENTS = {
    'kicker': 'CONTENTS',
    'title': 'CONTENTS',
    # 2026-11-22 사용자 지시(3번): 목차 제목은 영어로 통일하고, 산출물은 실제로 넣은 것만 적는다.
    'rows': (
        ('01', 'PROFILE', '02', ()),
        ('02', 'PROJECT 01 — 2030 타깃 · 부스터 글로우 유입·전환 캠페인', '04',
         (('기간', '2026.11'),
          # 2026-11-22 지시(2번): 3·4쪽 역할을 `리뷰 수집 · 숏폼 콘티 · 시안 · CRM 설계`로 통일.
          ('역할', '리뷰 수집 · 숏폼 콘티 · 시안 · CRM 설계'),
          ('산출물', '숏폼 콘티 · 브릿지 카드 · 포스터 2종 · 자사몰 앱 CRM'))),
        ('03', 'PROJECT 02 — 5060 타깃 · GS샵 X2 홈쇼핑 연계 캠페인', '09',
         (('기간', '2026.11'),
          # 3·9쪽 역할 통일(`CRM 설계` 제거) · 산출물에서 `사후 CRM` 제거 (지시 2·3·4번).
          ('역할', '리뷰 수집 · 채널 선정 · 홍보물 제작'),
          # 2026-11-22 4차 지시(1번): 완성본 이름(방송 홍보 · 모드 가이드)을 그대로 적는다.
          ('산출물', 'GS샵 1주년 홍보물 2종(방송 홍보 · 모드 가이드) · 사용 장벽 리뷰 분석'))),
        ('04', 'WORK PROCESS', '13', ()),
        # 2026-11-22 5차 지시(16번): 14쪽에서 APPENDIX를 걷어냈으므로 목차도 `05 CLOSING`만.
        ('05', 'CLOSING', '14', ()),
    ),
}

P01 = {
    'kicker': 'PROJECT 01',
    'title': '2030을 타깃으로 한\n부스터 글로우\n마케팅 전략',
    'sub': '숏폼 30초 · 연계 포스터 · 자사몰 CRM',
    'about': (('기간', '2026.11'), ('기여도', '100%'),
              # 2026-11-22 지시(2번): 3쪽 목차와 같은 문구로 통일.
              ('역할', '리뷰 수집 · 숏폼 콘티 · 시안 · CRM 설계'),
              # 2026-11-22 사용자 지시(4번): 실제로 쓴 툴만.
              ('툴', 'Python · Photoshop MCP · Kling · Higgsfield · Codex · Pickle'),
              # 2026-11-22 5차 지시(3번): 목표를 생활 고민 → 데일리 루틴 → 앱 리텐션으로.
              ('목표', '생활 속 피부 고민 공감에서 데일리 루틴 · 앱 리텐션까지 연결')),
    'caption': '아쿠아 키비주얼 1080×1920 · 엔드카드 1080×1920 — 실제 제품 사진 사용, 집행 전 시안',
    # 2026-11-22 5차 지시(3번): 캡션 바로 아래에 AI 활용 고지를 붙인다.
    'ai_note': '해당 이미지는 AI를 활용하여 생성함',
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
    'note': '장면별 숏폼 연출은 시안임. 해당 숏폼 이미지는 AI를 활용하여 생성함.',
}

P01S = {
    'kicker': 'PROJECT 01 · CRM STRATEGY',
    # 2026-11-22 사용자 지시: 오른쪽 앱 목업 3대가 내용을 다 보여 주므로 왼쪽 글씨는
    # 제목 2줄 + 리드 1줄 + 항목당 1줄 + 여정 1줄로 줄인다.
    'title': '매일 루틴으로 이어지는\n디지털 클리닉 앱 CRM',
    'lead': '알림이 오는 시간이 곧 디바이스를 켜는 시간이 됩니다.',
    'points': (('①', '루틴 · 알림 설정', '매일 밤 10:30 · 주 5회 · 모드별 3단계'),
               ('②', '설정 시간 데일리 푸시', '"오늘 밤 10:30, 글로우 12분 루틴"'),
               ('③', '달성 트래커 · 리포트', '주 5일 · 연속 12일 · 모드별 횟수')),
    'flow': '온사이트 배너 → D+1 모드 안내 → 매일 10:30 알림 → 주간 리포트',
    'note': '앱 화면은 기획 시안. 실제 앱 반영 및 발송 기록은 없음. 화면 목업 이미지는 AI를 활용하여 제작',
}

P01P = {
    'kicker': 'PROJECT 01 · OUTPUT — POSTERS',
    'title': '포스터 2종',
    # 2026-11-22 지시(1번): 제목 아래 3줄 세부설명을 걷어내고 규격·용도·비고만 남긴다.
    'lead': '',
    'about': (('규격', '1080×1350 · 인쇄 포스터'),
              ('용도', 'SNS · 매장 인쇄'),
              ('비고', '키티 에디션은 판매 CTA 없음')),
    'spec': '포스터 2종 1080×1350',
    'items': (('01', '메인 포스터', '1080×1350', 'print_poster.png', '하루의 세 순간'),
              ('02', '헬로키티 에디션', '1080×1350', 'print_kitty.png', '별도 기획 · 판매 CTA 없음')),
    'note': '포스터 연출 컷은 생성형 AI를 활용하여 제작. 실제 광고 집행과 성과는 없음.',
}

P01C = {
    'kicker': 'PROJECT 01 · OUTPUT — SHORTFORM CARDS',
    # 2026-11-22 사용자 지시(6번): `루틴 카드`는 임의 표현이므로 `브릿지 카드`로 통일.
    'title': '엔드카드와 브릿지 카드 3종',
    'lead': '숏폼 30초가 끝난 자리에서 자사몰 CTA로 잇는 엔드카드와, 초음파·모드·시간을 '
            '한 장씩 보여 주는 브릿지 카드입니다.',
    'spec': '엔드카드·브릿지 카드 4종 1080×1920',
    'items': (('01', '엔드카드 v3', '1080×1920', 'print_endcard.png', '제품 사진 + 자사몰 CTA'),
              ('02', '브릿지 01', '1080×1920', 'print_bridge1.png', '초음파 1–3–10MHz'),
              ('03', '브릿지 02', '1080×1920', 'print_bridge2.png', '5가지 모드'),
              ('04', '브릿지 03', '1080×1920', 'print_bridge3.png', '약 12분 데일리 루틴')),
    'note': '화면 목업 및 연출 컷은 생성형 AI를 활용하여 제작. 실제 광고 집행과 성과는 없음. 숏폼 원본은 편집 미완성',
}

P02 = {
    'kicker': 'PROJECT 02',
    'title': '5060을 타깃으로 한\n부스터 프로 X2\nGS샵 연계 전략',
    # 2026-11-22 지시(2번·3번 안 1): 사후 CRM을 걷어낸 만큼 9쪽 부제에서도 `배송 후 CRM`을 뺀다.
    # 제목·표지 디자인은 그대로다.
    'sub': 'GS샵 방송 연계 · 사용 장벽 리뷰 분석',
    'about': (('기간', '2026.11'), ('기여도', '100%'),
              ('역할', '리뷰 수집 · 채널 선정 · 홍보물 제작'),
              # 2026-11-22 사용자 지시(7번): 실제로 쓴 툴만.
              # 2026-11-22 5차 지시(8번): ABOUT의 `목표` 행을 통째로 걷어내 4행만 남긴다.
              ('툴', 'Python · Photoshop MCP · Codex · Pickle')),
    # 2026-11-22 5차 지시(9번): 하단 메시지.
    'caption': '해당 방송 홍보물은 AI를 활용하여 생성함. 실제 편성, 구성, 가격, 혜택 미확정',
}

P02E = {
    'kicker': 'PROJECT 02 · 사용 장벽 & 해법',
    # 2026-11-22 지시(4번·안 1): 한 면에 한 메시지. 제목은 한 문장,
    # 작은 숫자 블록(22건·35건·5.4%)은 걷어내고 장벽 막대와 해결 홍보물 2종만 남긴다.
    'title': "5060은 '성능'이 아니라 '사용법'에서 막힙니다",
    # 2026-11-22 5차 지시(12번): 본문 소제목을 짧은 사실 문장으로.
    'lead': 'GS샵 상품평 221건 전수 코딩하여 데이터 수집',
    'bars': (('자극 · 통증', 12), ('무게 · 크기', 10), ('부속품 부재', 7), ('설명 혼란', 6), ('버튼', 5)),
    'chart_label': 'GS샵 상품평 221건 · 장벽 언급',
    'chart_note': '단위: 상품평 1건에서 1회 이상 언급',
    # 2026-11-22 지시(4번): 사후 CRM 폰(D+0·D+14)은 지면에서 **완전히 제거**하고,
    # 확정 홍보물 2종을 폰 목업에 넣어 각각이 위 장벽을 어떻게 사전에 풀는지 잇는다.
    # ① 방송 홍보(`phone_x2_hero.png`) — `6단계 강도 · 1단계부터 시작` → 자극·버튼 우려 완화
    # ② 모드 가이드(`phone_x2_guide.png`) — `6가지 모드 한눈 정리` → 설명 혼란 해소
    'solutions': (('①', '방송 홍보', 'phone_x2_hero.png',
                   '6단계 강도 · 1단계부터 시작', '자극 · 버튼 우려 완화'),
                  ('②', '모드 가이드', 'phone_x2_guide.png',
                   '6가지 모드 한눈 정리', '설명 혼란 해소')),
    'note': '해당 홍보물은 AI를 활용하여 생성함.',
}

# 2026-11-22 4차 지시(2번)로 다시 짠 10쪽 — 1주년 방송을 기획한 근거(52주 추이)와 계획.
# 같은 날 3차 지시로 넣었던 `02 · 판단`(5060 기기 검색 5.6% · 이미용가전 클릭 74.3%)
# 카드와 `부스터 글로우 라인 +89.9%` 막대는 **사용자 요청으로 완전히 걷어냈다**
# ("판단에 나온 내용은 모두 제거", 2026-11-22 11:07). 근거는 원자료에서 직접 그린
# 52주 추이 두 선으로 대체한다.
#   · 검색 = `data/naver-datalab-v2/datalab_메디큐브 주력 라인 비교_여성5060.xlsx`의
#     `부스터 프로` 5060 검색 지수(2025-11-03~2026-11-09 주간 52점). 2026-05-04 = 100.0으로
#     52주 최고점이고, 직전 주는 30.85다.
#   · 클릭 = `data/naver-datalab-v2/쇼핑인사이트_5060_이미용가전.csv`의 `메디큐브` 5060
#     클릭 지수(2025-11-03~2026-10-26 주간 52점). 2026-04-27 = 38 → 2026-05-04 = 68.
# 두 파일은 도구(통합검색·쇼핑인사이트)와 모집단이 달라 각 계열의 최댓값을 100으로 둔
# 상대 지수이며, 그래프에서 높낮이를 비교하지 않는다는 캡션을 반드시 함께 적는다.
# 타임라인의 +27.3%는 `메디큐브_국내_피크주_광고_이벤트_대조분석` v1.5의 5060 검색
# (메디큐브 브랜드 · 데이터랩) 직전 주 대비 상승률이다. 클릭률(CTR)로 적지 않는다.
P02G = {
    'kicker': 'PROJECT 02 · 근거 & 1주년 기획',
    'title': '첫 론칭 주의 검색 급등을 1주년 재방송으로 잇다',
    'lead': '2026.05.09 GS샵 첫 방송 주의 5060 검색 +27.3%를 근거로, 1년 뒤 같은 주에 '
            '사용 장벽을 먼저 푸는 1주년 방송을 제안합니다.',
    'evidence': '01 · 근거 — 5060 검색·클릭 52주 추이 (2025.11 ~ 2026.11)',
    'series': (('검색 지수 · 부스터 프로', 'search'), ('클릭 지수 · 메디큐브', 'click')),
    'marker': '5/4 주 동시 급등 · 5/9 GS샵 첫 론칭',
    'chart_note': '검색 = 데이터랩 통합검색 부스터 프로(5060) 지수 · 클릭 = 쇼핑인사이트 이미용가전 '
                  '메디큐브(5060) 지수. 두 지표는 도구·모집단이 달라 각 계열의 최댓값을 100으로 둔 '
                  '상대 지수이며 높낮이는 비교하지 않습니다. 타임라인의 +27.3%는 메디큐브 브랜드 '
                  '검색(5060)의 직전 주 대비 상승률입니다.',
    'plan': '02 · 1주년 방송 연계 계획 — 2027.05.09 SUN 19:00',
    # 2026-11-22 4차 지시(2번): 첫 단계 문구를 `5060 검색 직전주 대비 27.3% 상승`으로.
    'steps': (('2026.05.09', 'GS샵 첫 론칭', '5060 검색 직전주 대비 27.3% 상승'),
              ('1년간', '리뷰 221건 사용 장벽 파악', '자극·통증 12건 · 버튼 5건'),
              ('2027.05.09', '1주년 방송 연계 제안', '불편 해소 홍보물 2종')),
    'card': '1주년 방송 홍보물',
    'note': '해당 방송 계획은 제안이며 편성, 구성, 가격, 혜택 미확정. 52주 추이는 검색과 클릭 지수일 뿐, '
            '매출과 성과와는 상관없음',
}

P02O = {
    'kicker': 'PROJECT 02 · OUTPUT',
    'title': '홍보물 2종',
    # 2026-11-22 사용자 지시(9번): 쪽 설명 문구(`방송 전 예고와 …`)는 걷어내고
    # 규격·용도·비고만 남긴다(MD도 같은 문자열에서 나오므로 빈 문자열로 둔다).
    'lead': '',
    'about': (('규격', '1080×1350 · 정적 이미지'),
              ('용도', 'GS샵 방송 홍보'),
              ('비고', '2027.05.09 19:00 편성 제안')),
    'spec': '홍보물 2종 1080×1350',
    'items': (('01', '방송 홍보', '1080×1350', 'print_x2_hero.png', '다시 만나는 X2'),
              ('02', '모드 가이드', '1080×1350', 'print_x2_modes.png', '6가지 모드 한눈에')),
    'note': '방송 편성, 구성, 가격, 혜택 미확정. 해당 홍보물은 AI를 활용하여 생성함.',
}

# 2026-11-22 4차 지시(3번 · 안 B): 13쪽을 아쿠아 × 플럼 **듀얼 트랙 플로우**로 다시 짠다.
# 글자 위주 4칸을 걷어내고 공통 출발점 → 두 트랙(2030 아쿠아 / 5060 플럼) → 합류점으로
# 읽히게 하고, 각 트랙 끝에 실제 산출물 미니 썸네일을 붙인다.
# `리뷰 438건` = 공식몰 217건 + GS샵 상품평 221건. `141항목` = verify2.py 재계산 항목 수.
PROCESS = {
    'kicker': '04 · WORK PROCESS',
    'title': '어떻게 만들었나',
    # 2026-11-22 5차 지시(14번): `도구는 생성과 렌더링에만…` 문장을 걷어냈다.
    'lead': '',
    'start': ('01', '원자료 수집', '& 전수 검증', '데이터랩 · 리뷰 438건', '원자료 대조'),
    'tracks': (
        {'label': '2030 · AQUA · 4~8쪽', 'page_tone': 'aqua',
         'from': ('타깃 인사이트', '광채 · 보습 · 결'),
         'to': ('숏폼 콘티 · 브릿지', '포스터 2종 · 앱 CRM'),
         'thumbs': ('print_poster.png', 'print_endcard.png')},
        # 2026-11-22 5차 지시(14번): 트랙 문구를 바꾸고, 5060 홍보물 2종을 모두 썸네일로.
        {'label': '5060 · PLUM · 9~12쪽', 'page_tone': 'plum',
         'from': ('5/9 GS샵 론칭 피크', '실사용 불편 키워드 도출'),
         'to': ('1주년 GS샵 재방송', '홍보물 2종'),
         'thumbs': ('print_x2_hero.png', 'print_x2_modes.png')},
    ),
    # 2026-11-22 5차 지시(15번): 검증 게이트 블록·연결선은 지면에서 걷어냈다.
    'gate': None,
    'tools': ('Python', 'Photoshop', 'Higgsfield', 'Kling', 'Codex', 'Pickle'),
    'note': '',
}

# 2026-11-22 5차 지시(16번): 14쪽은 `CLOSING` 단독 면이다. APPENDIX 섹션(보고서 8편
# 아카이브·저장소 링크)은 지면에서 전부 걷어내고, 감사 인사는 훨씬 크게, CONTACT
# (Email·Phone·GitHub)는 오른쪽에 균형 있게 둔다. 표지의 두 축 문장도 뻬고, 하단
# `[알림]`과 `[AI 제작]`은 바로 위아래로 붕여 둔다(두 줄 사이 간격 14pt = 이전 판의
# `01 2030…`·`02 5060…` 두 문장 줄 간격 그대로).
CLOSING = {
    'kicker': '05 · CLOSING',
    'title': 'CLOSING',
    'name': 'KIM YOONSEO · 김윤서',
    'thanks': '감사합니다',
    'close': '공개 데이터로 판단하고, 콘텐츠로 옮기겠습니다.',
    'contact': (('Email', 'rladbstj56@gmail.com', 'mailto:rladbstj56@gmail.com'),
                ('Phone', '010-9056-0349', None),
                ('GitHub', 'https://github.com/rladbstj56', 'https://github.com/rladbstj56')),
    'notice': '[알림] 본 덱의 수치는 공개 자료 기반이며, 집행 전 시안은 실제 성과·편성과 무관합니다.',
    'note': '[AI 제작] 숏폼 인물 클립 3개·내레이션 7구간·포스터 연출 컷은 생성형 AI 산출물이며 '
            '실제 촬영·광고 집행은 없습니다.',
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

    def grad(self, x, y, w, h, top, bottom, key='plum'):
        """위→아래 그라데이션 면(2026-11-22 5060 무드 패널).

        캔버스에 얇은 사각형을 쌓아 올리면 경계선이 보이므로, PIL로 2배 해상도
        이미지를 한 장 만들어 얹는다(`cover_fade()`와 같은 방식).
        """
        path = TMP / 'fade' / f'grad_{key}_{int(w)}x{int(h)}.png'
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            sw, sh = int(w * 2), int(h * 2)
            c1 = tuple(int(getattr(top, ch) * 255) for ch in ('red', 'green', 'blue'))
            c2 = tuple(int(getattr(bottom, ch) * 255) for ch in ('red', 'green', 'blue'))
            img = PILImage.new('RGB', (sw, sh))
            d = ImageDraw.Draw(img)
            for yy in range(sh):
                t = yy / max(1, sh - 1)
                d.line([(0, yy), (sw, yy)],
                       fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)))
            img.save(path)
        self.c.drawImage(str(path), x, y, w, h)

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

    def t_pair(self, left, right, cx, y, size, color_l, color_r, bold_l=False,
               bold_r=False, gap=5.0):
        """두 조각을 한 줄로 이어 그리고, 합친 폭의 중심을 cx에 맞춘다.

        `drawCentredString`은 한 번에 한 색만 칠할 수 있어, 왼쪽 조각(연번)·
        오른쪽 조각(이름)의 폭을 각각 재서 중심에서 되감아 그린다. 7·8·11쪽
        인쇄물 캡션의 가로 중앙 정렬에 쓴다(2026-11-22 사용자 지시 5·6·9번).
        """
        wl = pdfmetrics.stringWidth(left, BOLD if bold_l else FONT, size)
        wr = pdfmetrics.stringWidth(right, BOLD if bold_r else FONT, size)
        x = cx - (wl + gap + wr) / 2
        self.t(left, x, y, size, color_l, bold_l)
        self.t(right, x + wl + gap, y, size, color_r, bold_r)
        return wl + gap + wr

    def para(self, text, x, y_top, w, size=8.6, leading=13.4, color=INK, bold=False, align=0):
        style = ParagraphStyle('p', fontName=BOLD if bold else FONT, fontSize=size,
                               leading=leading, textColor=color, alignment=align,
                               wordWrap='CJK')
        p = Paragraph(esc(text), style)
        _, h = p.wrap(w, 1000)
        p.drawOn(self.c, x, y_top - h)
        return h

    def para_baseline(self, text, x, y_base, w, size=8.6, leading=13.4,
                      color=INK, bold=False, align=0):
        """첫 줄 베이스라인이 y_base에 정확히 오도록 문단을 그린다.

        reportlab 문단은 `drawOn(x, y_top - h)`일 때 첫 줄 베이스라인을
        `y_top - fontSize`에 놓는다(leading과 무관, `paraFontSizeHeightOffset`
        기본값). 그래서 `d.t()`로 그린 라벨(y=베이스라인)과 값을 한 줄에
        맞추려면 y_top을 `y_base + size`로 올려야 한다. 2026-11-22 4·7쪽
        ABOUT/규격 블록 정렬 수정에서 쓴다.
        """
        return self.para(text, x, y_base + size, w, size, leading, color, bold, align)

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
        # 14쪽 덱에서 어두운 바탕인 쪽은 1·3·8·12·14쪽이다(12쪽 홍보물 쇼케이스, 14쪽 부록).
        self.t(text, M, y, 6.1, color or (MUTED_D if no in (1, 3, 8, 12, 14) else MUTED))

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
    Certificate · Skill & Tool** 네 칸을 2×2로 두었다. 같은 날 마지막 지시로
    **섹션 제목 위의 기호(●·■·*)는 모두 걷어냈다** — 기호 없이 제목과 헤어라인만으로
    칸을 나누고, Skill & Tool은 레벨 막대 대신 툴 아이콘
    10개(5×2)와 작은 영문명만 둔다(2026-11-22 2차 지시 — GA4 → Notion, Higgsfield·
    Kling·ElevenLabs 추가로 7개에서 10개). 왼쪽 사진은 158×203pt 원본 비율 그대로이고
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

    def head(x, y, label):
        """섹션 제목 + 헤어라인 — 기호(●·■·*)는 2026-11-22 지시로 걷어냈다."""
        d.t(label, x, y - 16, TITLE, INK, True)
        d.rule(x, x + COL, y - 25)

    # 1) 좌상단 — Contacts
    head(X1, ROW1, 'Contacts')
    for i, (label, value) in enumerate(PROFILE['contacts']):
        y = ROW1 - 51 - i * ROW_H
        d.t(label, X1, y, 8.4, MUTED, True)
        w = d.t(value, X1 + VALUE_X, y, ROW_SZ, INK)
        c.linkURL(PROFILE['links'][label],
                  (X1 + VALUE_X, y - 2.6, X1 + VALUE_X + w, y + 9.6),
                  relative=0, thickness=0)

    # 2) 우상단 — Education
    head(X2, ROW1, 'Education')
    for i, (name, period) in enumerate(PROFILE['education']):
        y = ROW1 - 51 - i * ROW_H
        d.t(name, X2, y, ROW_SZ, INK)
        d.t(period, X2 + COL, y, DATE_SZ, MUTED, align='r')

    # 3) 좌하단 — Certificate
    head(X1, ROW2, 'Certificate')
    for i, (name, period) in enumerate(PROFILE['cert']):
        y = ROW2 - 51 - i * ROW_H
        d.t(name, X1, y, ROW_SZ, INK)
        d.t(period, X1 + COL, y, DATE_SZ, MUTED, align='r')

    # 4) 우하단 — Skill & Tool — 레벨 막대 없이 아이콘만
    head(X2, ROW2, 'Skill & Tool')
    icons = tool_icons.build_all()
    COLS = 5                       # 10개 → 5×2 (2026-11-22 2차 지시)
    tile, icon, icon_step = COL / COLS, 34.0, 60.0
    for i, name in enumerate(PROFILE['tools']):
        cx = X2 + tile * (i % COLS) + tile / 2
        iy = ROW2 - 50 - (i // COLS) * icon_step - icon
        c.drawImage(str(icons[name]), cx - icon / 2, iy, icon, icon, mask='auto')
        d.t(name, cx, iy - 9.8, 6.8, MUTED, align='c')

    d.caption(2, PROFILE['note'], 40) if PROFILE.get('note') else None
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


def p05(d):
    """4쪽 PROJECT 01 · INTRO — 제목 3줄, ABOUT 정렬, 앵글드 아이폰 히어로.

    2026-11-22 사용자 지시: 제목을 `2030을 타깃으로 한 부스터 글로우 마케팅 전략`으로
    바꿨다. 같은 날 2차 지시로 **라벨과 값의 y축(베이스라인)을 한 줄로 일치**시켰고,
    3차 지시로 **ABOUT과 그 아래 라벨을 모두 왼쪽 정렬**(x=44)로 바꿨다 —
    라벨을 x=104 오른쪽 정렬로 두면 `기간`·`역할`·`툴`은 안쪽으로 밀리고 `기여도`만
    왼쪽으로 나와 시작점이 라벨마다 달랐다.
    베이스라인을 맞춘 방법은 —
    `d.para()`의 `y_top`은 문단 첫 줄 베이스라인보다 fontSize만큼 위이므로,
    `d.para_baseline()`으로 `기간`↔`2026.11` 등이 정확히 같은 y에 놓인다.
    오른쪽 아이폰은 슬랙에 올린 Pinterest `Floating Angled` 레퍼런스처럼 원근·측면
    두께·두 겹 그림자를 준 `phone_endcard_angled.png`로 교체했다.
    """
    d.bg(color=AQ_BG)
    d.chrome(4, P01['kicker'] + ' · INTRO', accent=AQ_TEAL, label=AQ_MUTED, hair=AQ_HAIR)

    # ── 왼쪽 — 제목 3줄 + ABOUT ─────────────────────────────────────
    # `ABOUT`과 기간·기여도·역할·툴·목표 라벨은 모두 ABOUT의 왼쪽 끝선(x=44),
    # 값은 x=96 한 열에 세운다(2026-11-22 사용자 지시).
    X, VAL_X = M, 96.0
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
        d.t(label, X, ay, 6.4, AQ_MUTED)
        # 2026-11-22 사용자 지시: 라벨과 값의 첫 줄 베이스라인을 정확히 맞춘다.
        # (기존 `ay + 2.0`은 값의 베이스라인을 라벨보다 5.3pt 아래로 떨어뜨렸다.)
        h = d.para_baseline(value, VAL_X, ay, 318 - VAL_X, 7.3, 11.0, AQ_INK)
        ay -= max(h + 10, 20)

    # ── 오른쪽 — 아쿠아 키비주얼 위에 떠 있는 앵글드 아이폰 ─────────
    PX, PY, PH = 318.0, 54.0, 416.0
    d.panel(PX, PY, PAGE_W - PX, PH, color=AQ_PANEL)
    VX = 470.0
    hero = cover_fade(KEYVIS, 'p04_hero', PAGE_W - VX, PH, 104, AQ_PANEL, valign='t')
    d.img(hero, VX, PY, w=PAGE_W - VX, h=PH)
    d.img(MOCK / 'phone_endcard_angled.png', 352, 60, h=392)
    # 2026-11-22 5차 지시(3번): 캡션 바로 아래에 AI 활용 고지를 붙인다.
    d.caption(4, P01['caption'], 40, AQ_MUTED)
    d.t(P01['ai_note'], M, 30.5, 6.1, AQ_MUTED)
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
        LX = cx - 62          # 위아래 글씨의 왼쪽 기준선
        d.rule(LX, cx + 116, 406, color=AQ_HAIR)
        d.t(no, LX, 392, 6.6, AQ_TEAL, True, tracking=0.8)
        d.t(place, LX + 18, 392, 6.6, AQ_MUTED)
        d.t('고민', LX, 374, 6.0, AQ_MUTED, True, tracking=1.2)
        d.para(pain, LX, 366, 178, 7.4, 10.4, AQ_INK, bold=True)
        # 2026-11-22 사용자 지시: 목업 왼쪽 끝선을 위 기준선과 맞춘다. PNG 왼쪽에는
        # 그림자용 투명 여백(폭의 약 5%)이 있어 그만큼 당겨 놓아야 배젤이 선에 닿는다.
        path = MOCK / f'phone_shot{i + 1}.png'
        iw, ih = PILImage.open(path).size
        d.img(path, LX - _device_left_px(path) * 248 / ih, 96, h=248)
        d.t('부스터 글로우 케어', LX, 84, 6.0, AQ_TEAL, True, tracking=1.2)
        d.para(care, LX, 76, 178, 7.2, 10.4, AQ_MUTED)
    d.caption(5, P01E['note'], 40, AQ_MUTED)
    d.page_break()


def _device_left_px(path):
    """목업 PNG 안에서 기기 실루엣(불투명)이 시작하는 x(px). 왼쪽 그림자 여백은 뺀다."""
    alpha = PILImage.open(path).convert('RGBA').getchannel('A')
    box = alpha.point(lambda v: 255 if v > 250 else 0).getbbox()
    return box[0] if box else 0


def p07(d):
    """6쪽 PROJECT 01 · CRM STRATEGY — 디지털 클리닉 앱 업그레이드 3화면.

    2026-11-22 사용자 지시: 0~21초 인물 샷 3개를 걷어내고(5쪽으로 이동), 앱을 루틴
    관리 중심으로 확장한 화면 ①설정 ②데일리 푸시 ③달성 리포트를 목업 3대에 넣었다.
    같은 날 추가 지시로 왼쪽 글씨를 제목 2줄·리드 1줄·항목당 1줄로 줄였다 — 목업 3대가
    내용을 다 보여 주므로 글씨는 키워드만 남긴다.
    """
    d.bg(color=AQ_BG)
    d.chrome(6, P01S['kicker'], accent=AQ_TEAL, label=AQ_MUTED, hair=AQ_HAIR)

    LX, LW = M, 330.0
    y = 452
    for line in P01S['title'].split('\n'):
        d.t(line, LX, y, 21.0, AQ_INK, True)
        y -= 26
    y -= 10
    d.para(P01S['lead'], LX, y, LW, 8.0, 11.6, AQ_MUTED)

    # 세 항목은 같은 간격으로 내려 세우고, 아래 CRM 여정 줄과 사이를 띄운다
    y = 344
    for no, head, body in P01S['points']:
        d.t(no, LX, y - 1, 9.0, AQ_TEAL, True)
        d.t(head, LX + 16, y, 8.8, AQ_INK, True)
        d.para(body, LX + 16, y - 9, LW - 16, 7.6, 11.0, AQ_MUTED)
        y -= 56

    # CRM 여정 — 기존 접점이 앱 안으로 이어지는 순서
    d.rule(LX, LX + LW, 190, color=AQ_HAIR)
    d.t('CRM 여정', LX, 176, 6.0, AQ_TEAL, True, tracking=1.4)
    d.para(P01S['flow'], LX, 166, LW, 7.4, 10.6, AQ_MUTED)

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
    """7쪽 PROJECT 01 · OUTPUT — POSTERS — 포스터 2종만 큼직하게.

    2026-11-22 사용자 지시: 인쇄물 7종을 한 면에 몰아넣지 않고 7·8쪽 두 면으로 나눴다.
    아쿠아 키비주얼은 4쪽 히어로와 겹치므로 목록에서 빼고, 7쪽은 메인 포스터와
    헬로키티 에디션 두 장을 왼쪽 설명과 나란히, 오른쪽 지면을 반씩 쓰게 세운다.
    같은 날 2차 지시로 `규격·용도·비고` 라벨과 값의 y축(베이스라인)을 4쪽과 같은
    방식(`d.para_baseline()`)으로 한 줄에 맞췄다.
    """
    d.bg(color=AQ_BG)
    d.chrome(7, P01P['kicker'], accent=AQ_TEAL, label=AQ_MUTED, hair=AQ_HAIR)

    LX, LW = M, 236.0
    d.t(P01P['title'], LX, 442, 22.0, AQ_INK, True)
    y = 416
    # 2026-11-22 지시(1번): 세부설명 3줄을 걷어냈으므로 규격·용도·비고만 남긴다.
    for line in [s for s in P01P['lead'].split('|') if s.strip()]:
        y -= d.para(line, LX, y, LW, 7.6, 11.6, AQ_MUTED) + 2
    y -= 16
    for label, value in P01P['about']:
        d.t(label, LX, y, 6.2, AQ_TEAL, True, tracking=1.0)
        # 2026-11-22 사용자 지시: 규격·용도·비고의 라벨과 값도 한 줄에 맞춘다.
        y -= d.para_baseline(value, LX + 36, y, LW - 36, 7.2, 10.6, AQ_INK) + 9

    items = P01P['items']
    gap, x, bottom = 56.0, 330.0, 92.0
    w = (PAGE_W - M - x - gap * (len(items) - 1)) / len(items)
    for no, title, spec, name, desc in items:
        path = MOCK / name
        iw, ih = PILImage.open(path).size
        h = w * ih / iw
        d.img(path, x, bottom, w=w, h=h)
        # 2026-11-22 사용자 지시(5번): 설명을 왼쪽 정렬이 아니라 **각 이미지 가로 폭의
        # 중앙**에 맞춘다 — 연번·이름은 두 색을 이어 그리되(x + w/2 중심), 규격·설명
        # 한 줄은 이미지 폭보다 길 수 있으므로 같은 중심에 가운데 정렬로 그린다.
        cx = x + w / 2
        d.t_pair(no, title, cx, bottom - 14, 6.2, AQ_TEAL, AQ_INK, bold_r=True)
        d.t(f'{spec} · {desc}', cx, bottom - 25, 5.8, AQ_MUTED, align='c')
        x += w + gap
    d.t(P01P['spec'], PAGE_W - M, 442, 6.2, AQ_TEAL, True, align='r')
    d.caption(7, P01P['note'], 40, AQ_MUTED)
    d.page_break()


def p08b(d):
    """8쪽 PROJECT 01 · OUTPUT — SHORTFORM CARDS — 엔드카드·브릿지 카드 4종.

    2026-11-22 사용자 지시로 7쪽에서 갈라진 면. 어두운 물빛 위에 4장을 한 줄로
    크게 세우고, 숏폼 완본 보류 고지는 캡션에 그대로 남긴다.
    같은 날 지시 6번: `루틴 카드`는 임의 표현이라 제목·리드·우상단 라벨을
    `브릿지 카드`로 통일하고, 각 장 설명을 이미지 가로 폭 중심으로 정렬한다.
    """
    d.bg(color=AQ_DARK)
    d.chrome(8, P01C['kicker'], dark=True, accent=AQ_TEAL_L,
             label=AQ_MUTED_D, hair=AQ_HAIR_D)
    d.t(P01C['title'], M, 442, 22, WHITE, True)
    d.para(P01C['lead'], M, 418, 640, 7.6, 11.2, AQ_SOFT_D)
    d.t(P01C['spec'], PAGE_W - M, 442, 6.2, AQ_TEAL_L, True, align='r')

    items = P01C['items']
    gap, x, bottom = 48.0, M, 86.0
    w = (CW - gap * (len(items) - 1)) / len(items)
    for no, title, spec, name, desc in items:
        path = MOCK / name
        iw, ih = PILImage.open(path).size
        h = w * ih / iw
        d.img(path, x, bottom, w=w, h=h)
        # 2026-11-22 사용자 지시(6번): 7쪽과 같이 각 이미지 가로 폭 중심 정렬.
        cx = x + w / 2
        d.t_pair(no, title, cx, bottom - 14, 6.2, AQ_TEAL_L, WHITE, bold_r=True)
        d.t(f'{spec} · {desc}', cx, bottom - 25, 5.8, AQ_SOFT_D, align='c')
        x += w + gap
    d.caption(8, P01C['note'], 40, AQ_MUTED_D)
    d.page_break()


def radial_glow(name, w, h, color, peak=64, power=1.7):
    """어두운 면에 부드럽게 퍼지는 빛 한 겹(PNG 알파). 9쪽 플럼 패널이 쓴다.

    캔버스에 동심원을 쌓으면 띠가 보이므로, 픽셀 단위로 감쇠하는 알파를 만들어
    한 장으로 얹는다(`cover_fade()`와 같은 방식).
    """
    path = TMP / 'fade' / f'{name}.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        yy, xx = np.mgrid[0:h, 0:w]
        r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
        alpha = (peak * np.clip(1 - r, 0, 1) ** power).astype('uint8')
        rgb = [int(getattr(color, ch) * 255) for ch in ('red', 'green', 'blue')]
        arr = np.dstack([np.full((h, w), c, dtype='uint8') for c in rgb] + [alpha])
        PILImage.fromarray(arr, 'RGBA').save(path)
    return path


def p09(d):
    """9쪽 PROJECT 02 · INTRO — 4쪽과 같은 왼쪽 기둥 + 딥 플럼 무드 패널의 앵글드 아이폰.

    2026-11-22 사용자 지시: 5060 파트를 확정 홍보물 2종의 플럼 톤으로 다시 조판했다.
    제목은 `5060을 타깃으로 한 / 부스터 프로 X2 / GS샵 연계 전략` 3줄이고, ABOUT은
    4쪽(`p05`)과 **같은 규칙**으로 라벨을 x=44에 왼쪽 정렬, 값을 x=96 한 열에,
    `para_baseline()`으로 라벨과 첫 줄 베이스라인을 0pt로 맞춘다. 오른쪽은
    **딥 플럼 그라데이션 패널**(`#4A1C3A`→`#240E1C`) 위에 확정 홍보물을 넣은
    **Floating Angled 아이폰**(aspect-fit · 내용 잘림 없음)을 크게 띄운다.
    """
    d.bg(color=PLUM_BG)
    d.chrome(9, P02['kicker'] + ' · INTRO', accent=PLUM, label=PLUM_MUTED, hair=PLUM_HAIR)

    X, VAL_X = M, 96.0
    d.t(P02['kicker'], X, 470, 6.6, PLUM, True, tracking=2.0)
    y = 442
    for line in P02['title'].split('\n'):
        d.t(line, X, y, 21.0, PLUM_INK, True)
        y -= 25
    d.para(P02['sub'], X, y + 6, 236, 7.8, 11.6, PLUM_MUTED)

    ay = y - 22
    d.t('ABOUT', X, ay, 6.2, PLUM, True, tracking=1.6)
    ay -= 24
    for label, value in P02['about']:
        d.t(label, X, ay, 6.4, PLUM_MUTED)
        h = d.para_baseline(value, VAL_X, ay, 318 - VAL_X, 7.3, 11.0, PLUM_INK)
        ay -= max(h + 10, 20)

    # ── 오른쪽 — 딥 플럼 무드 패널 + 앵글드 아이폰 ──────────────────
    PX, PY, PH = 318.0, 54.0, 416.0
    PW = PAGE_W - M - PX
    d.grad(PX, PY, PW, PH, PLUM_DEEP, PLUM_DEEP2, key='p09')
    d.img(radial_glow('p09_glow', 560, 460, PLUM_PANEL, peak=58),
          PX + PW / 2 - 280, PY - 22, w=560, h=460)
    HERO_H = 400.0
    hero_w = HERO_H * 0.6781          # phone_x2_hero_angled.png 비율(1319:1945)
    d.img(MOCK / 'phone_x2_hero_angled.png', PX + (PW - hero_w) / 2, PY + 8, h=HERO_H)
    d.t('GS SHOP · 2027.05.09 SUN 19:00', PX + PW - 20, PY + 18, 6.0, PLUM_L,
        align='r', tracking=0.9)
    d.caption(9, P02['caption'], 40, PLUM_MUTED)
    d.page_break()


# ── 10쪽 52주 추이 — 원자료 직독 ──────────────────────────────────────────────
DATA_V2 = ROOT / 'data/naver-datalab-v2'
_SERIES = {}


def _xlsx_column(path, keyword):
    """xlsx를 zip+XML로 직접 읽어 (날짜, 값) 목록을 돌려준다(openpyxl 미사용).

    검색 지수 파일은 `날짜·값` 쌍이 다섯 벌 나란히 있으므로 짝수 열(1·3·5…)이 날짜다.
    헤더 행에서 `keyword`가 든 값을 골라 그 열만 뽑는다(예: `부스터 프로`).
    """
    NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    z = zipfile.ZipFile(path)
    shared = []
    if 'xl/sharedStrings.xml' in z.namelist():
        root = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in root.findall(NS + 'si'):
            shared.append(''.join(t.text or '' for t in si.iter(NS + 't')))
    sheet = sorted(n for n in z.namelist() if n.startswith('xl/worksheets/sheet'))[0]
    rows = {}
    for row in ET.fromstring(z.read(sheet)).iter(NS + 'row'):
        cells = {}
        for cell in row:
            col = 0
            for ch in cell.get('r'):
                if ch.isalpha():
                    col = col * 26 + (ord(ch.upper()) - 64)
                else:
                    break
            v = cell.find(NS + 'v')
            if v is None:
                continue
            cells[col] = shared[int(v.text)] if cell.get('t') == 's' else v.text
        rows[int(row.get('r'))] = cells
    hdr = next(r for r in sorted(rows) if rows[r].get(1) == '날짜')
    col = next(k for k in sorted(rows[hdr])
               if k % 2 == 0 and keyword in (rows[hdr][k] or ''))
    out = []
    for r in sorted(rows):
        if r <= hdr or not rows[r].get(1):
            continue
        out.append((rows[r][1][:10], float(rows[r].get(col) or 0)))
    return out


def _shop_column(path, keyword):
    """쇼핑인사이트 CSV에서 `keyword` 열의 (날짜, 값) 목록을 돌려준다.

    조회 시작 주의 빈 행(2025-11-01 · 값 0)은 그래프를 왜곡하므로 건너뛴다.
    """
    rows = list(csv.reader(open(path, encoding='utf-8-sig')))
    hdr = next(i for i, r in enumerate(rows) if r and r[0] == '날짜')
    ci = rows[hdr].index(keyword)
    out = []
    for r in rows[hdr + 1:]:
        if not r or not r[0][:4].isdigit():
            continue
        value = float((r[ci] or '0').replace(',', ''))
        if value == 0 and r[0].strip() <= '2025-11-02':
            continue
        out.append((r[0].strip(), value))
    return out


def series_5060():
    """10쪽 그래프의 두 실제 시계열 — 매 빌드마다 원자료에서 직접 읽는다."""
    if 'p10' not in _SERIES:
        _SERIES['p10'] = (
            _xlsx_column(DATA_V2 / 'datalab_메디큐브 주력 라인 비교_여성5060.xlsx', '부스터 프로'),
            _shop_column(DATA_V2 / '쇼핑인사이트_5060_이미용가전.csv', '메디큐브'),
        )
    return _SERIES['p10']


def trend_52w(d, x, y, w, h, search, click, marker, band_label):
    """52주 두 계열 꺾은선 — 같은 X축 위 검색(영역+선) · 클릭(선), 5/4 주 밴드·마커.

    두 계열은 도구와 모집단이 달라 각자의 최댓값을 100으로 둔 상대 지수다. 그래서
    한 축에 모양만 겹쳐 놓고 높낮이는 비교하지 않는다는 문구를 쪽에 함께 적는다.
    """
    C = d.c
    d0, d1 = _date(2025, 11, 3), _date(2026, 11, 9)
    span = (d1 - d0).days

    def X(s):
        return x + ((_date(*map(int, s.split('-'))) - d0).days / span) * w

    def Y(v):
        return y + (min(v, 100.0) / 100.0) * h

    # 5/4 주 하이라이트 밴드 — 5/9 GS샵 첫 론칭이 든 주(월~일)
    m0 = _date(*map(int, marker.split('-')))
    bx0 = x + ((m0 - d0).days - 3.5) / span * w
    bx1 = x + ((m0 - d0).days + 3.5) / span * w
    C.saveState()
    C.setFillColor(PLUM_L)
    C.setFillAlpha(0.30)
    C.rect(bx0, y, bx1 - bx0, h, stroke=0, fill=1)
    C.restoreState()

    # 눈금 0·50·100
    for v, lab in ((0, '0'), (50, '50'), (100, '100')):
        C.setStrokeColor(PLUM_HAIR)
        C.setLineWidth(0.5)
        C.line(x, Y(v), x + w, Y(v))
        d.t(lab, x - 5, Y(v) - 2.0, 5.4, PLUM_MUTED, align='r')

    # 검색 계열 — 선 아래를 옅게 칠해 클릭 선과 구분
    pts = [(X(s), Y(v)) for s, v in search]
    path = C.beginPath()
    path.moveTo(pts[0][0], Y(0))
    for a, b in pts:
        path.lineTo(a, b)
    path.lineTo(pts[-1][0], Y(0))
    path.close()
    C.setFillColor(SEARCH_AREA)
    C.drawPath(path, stroke=0, fill=1)

    for series, color, width in ((search, PLUM, 1.5), (click, CLICK_LINE, 1.2)):
        C.setStrokeColor(color)
        C.setLineWidth(width)
        path = C.beginPath()
        path.moveTo(X(series[0][0]), Y(series[0][1]))
        for s, v in series[1:]:
            path.lineTo(X(s), Y(v))
        C.drawPath(path, stroke=1, fill=0)

    # 5/4 주의 두 점만 짚어 두고 값은 상단 범례에 적는다
    for series, color in ((search, PLUM), (click, CLICK_LINE)):
        py = Y(dict(series)[marker])
        px = X(marker)
        C.setFillColor(PLUM_BG)
        C.circle(px, py, 3.4, stroke=0, fill=1)
        C.setStrokeColor(color)
        C.setLineWidth(1.0)
        C.circle(px, py, 2.6, stroke=1, fill=0)

    # X축 월 눈금 · 5/4 주 마커 문구
    for s, lab in (('2025-11-03', '2025.11'), ('2026-02-02', '2026.02'),
                   ('2026-05-04', '2026.05'), ('2026-08-03', '2026.08'),
                   ('2026-11-02', '2026.11')):
        d.t(lab, X(s), y - 10, 6.0, PLUM_MUTED, align='c')
    d.t(band_label, (bx0 + bx1) / 2, y + h + 8, 7.2, PLUM, True, align='c')


def p10(d):
    """10쪽 PROJECT 02 · 근거 & 1주년 기획 — 52주 추이 그래프 + 계획 타임라인.
    2026-11-22 4차 지시(2번): `02 · 판단`(5.6% · 74.3% 카드)과 `+89.9%` 막대를
    완전히 걷어냈습니다. `01 · 근거`는 실제 원자료에서 직접 읽은 **52주 두 계열**을
    같은 X축 위에 그립니다 — 검색(부스터 프로 5060 · 영역+선)과 클릭(메디큐브 5060 · 선).
    2026-05-04 주(5/9 GS샵 첫 론칭)에 수직 하이라이트 밴드와 마커를 달고, 두 계열의
    그 주 값을 점에 붙여 적었습니다. 판단 블록이 빠진 만큼 아래 `02 · 1주년 방송 연계
    계획`은 여백을 살려 타임라인과 홍보물 미니 카드만 남깁니다.
    """
    d.bg(color=PLUM_BG)
    d.chrome(10, P02G['kicker'], accent=PLUM, label=PLUM_MUTED, hair=PLUM_HAIR)
    d.t(P02G['title'], M, 452, 22.5, PLUM_INK, True)
    d.para(P02G['lead'], M, 432, 800, 8.0, 11.6, PLUM_MUTED)

    d.t(P02G['evidence'], M, 406, 7.4, PLUM, True, tracking=1.3)
    # 계열 이름과 5/4 주 값 — 오른쪽 끝에서부터 색 견본과 함께 오른쪽 정렬로 쌓는다
    # (밴드 안 두 점에 글자를 붙이면 급등 구간의 선과 겹쳐 읽기 어려워 범례에 적는다.)
    right = PAGE_W - M
    # 왼쪽부터 `검색 → 클릭` 순으로 읽히도록 오른쪽부터 거꾸로 쌓는다.
    for name, value, color in (('클릭 지수 · 메디큐브', '38 → 68', CLICK_LINE),
                               ('검색 지수 · 부스터 프로', '100.0 (52주 최고)', PLUM)):
        wv = pdfmetrics.stringWidth(value, BOLD, 7.4)
        wn = pdfmetrics.stringWidth(name, FONT, 7.4)
        d.t(value, right, 406, 7.4, color, True, align='r')
        d.t(name, right - wv - 7, 406, 7.4, PLUM_MUTED, align='r')
        d.c.setStrokeColor(color)
        d.c.setLineWidth(1.5)
        d.c.line(right - wv - wn - 24, 408.5, right - wv - wn - 12, 408.5)
        right -= wv + wn + 58

    search, click = series_5060()
    trend_52w(d, 62, 232, 854, 146, search, click, '2026-05-04', P02G['marker'])
    d.para(P02G['chart_note'], M, 210, 872, 6.1, 8.9, PLUM_MUTED)

    # ── 02 계획 — 3단 타임라인 + 확정 홍보물 미니 카드 ───────────────
    d.rule(M, PAGE_W - M, 178, color=PLUM_HAIR)
    d.t(P02G['plan'], M, 160, 7.4, PLUM, True, tracking=1.3)
    LINE_Y = 104.0
    d.rule(M, M + 700, LINE_Y, color=PLUM_HAIR)
    for i, (when, what, detail) in enumerate(P02G['steps']):
        nx = 56.0 + i * 238.0
        d.dot(nx, LINE_Y, 4.0, PLUM)
        d.c.setFillColor(PLUM_BG)
        d.c.circle(nx, LINE_Y, 2.0, stroke=0, fill=1)
        d.t(when, nx + 14, LINE_Y + 17, 8.2, PLUM, True, tracking=0.6)
        d.t(what, nx + 14, LINE_Y - 14, 9.8, PLUM_INK, True)
        d.t(detail, nx + 14, LINE_Y - 27, 7.8, PLUM_MUTED)
    card = ROOT / 'private_submission/5060/x2_gsshop_promo_hero_plum_v3.png'
    CW_, CH_ = 74.0, 92.5
    card_x, card_y = 806.0, LINE_Y - CH_ / 2
    d.c.setStrokeColor(PLUM_HAIR)
    d.c.setLineWidth(0.6)
    d.c.setDash(1.6, 2.0)
    d.c.line(M + 700, LINE_Y, card_x - 8, LINE_Y)
    d.c.setDash(1, 0)
    d.dot(card_x - 6, LINE_Y, 1.6, PLUM_MUTED)
    d.img(card, card_x, card_y, w=CW_, h=CH_)
    d.c.setStrokeColor(PLUM_HAIR)
    d.c.setLineWidth(0.6)
    d.c.rect(card_x, card_y, CW_, CH_, stroke=1, fill=0)
    d.t(P02G['card'], card_x + CW_ / 2, card_y - 11, 6.2, PLUM_MUTED, align='c')
    d.caption(10, P02G['note'], 40, PLUM_MUTED)
    d.page_break()


def p11(d):
    """11쪽 PROJECT 02 · 사용 장벽 & 해법 — 221건 장벽 도표 ↔ 홍보물 2종.

    2026-11-22 사용자 지시(3번 안 1·4번): 기존 10쪽을 개편했다. 사후 CRM 폰목업
    (`phone_x2_crm.png`)과 D+0·D+14 문구를 **완전히 제거**하고, 왼쪽은 GS샵 상품평
    221건 장벽 막대를 그대로 크게, 오른쪽은 **확정 홍보물 2종**을 폰 목업으로 크게 세워
    각각이 위 장벽을 어떻게 사전에 푸는지 두 줄로 잇는다 —
    ① 방송 홍보 `6단계 강도 · 1단계부터 시작` — 자극·버튼 우려 완화
    ② 모드 가이드 `6가지 모드 한눈 정리` — 설명 혼란 해소
    """
    d.bg(color=PLUM_BG)
    d.chrome(11, P02E['kicker'], accent=PLUM, label=PLUM_MUTED, hair=PLUM_HAIR)
    d.t(P02E['title'], M, 452, 23, PLUM_INK, True)
    d.para(P02E['lead'], M, 422, 640, 8.4, 12.8, PLUM_MUTED)

    # ── 왼쪽 — 장벽 막대를 지면 절반으로 키운다 ─────────────────
    d.t(P02E['chart_label'], M, 372, 6.6, PLUM, True, tracking=1.4)
    BX, BW = 176.0, 236.0           # 막대 시작 x · 가장 긴 막대 폭
    maxv = max(v for _, v in P02E['bars'])
    y = 330
    for label, value in P02E['bars']:
        d.t(label, M, y, 10.0, PLUM_INK, True)
        barlen = BW * value / maxv
        d.c.setFillColor(PLUM)
        d.c.rect(BX, y - 1.6, barlen, 12.0, stroke=0, fill=1)
        d.t(f'{value}건', BX + barlen + 11, y, 9.4, PLUM, True)
        y -= 52
    d.t(P02E['chart_note'], M, y + 30, 6.4, PLUM_MUTED)

    # ── 오른쪽 — 홍보물 2종 목업 + 장벽 해소 연결 ───────────────
    RX, RW = 480.0, PAGE_W - M - 480.0
    PH, PH_TOP = 288.0, 378.0        # 아이폰 높이 · 위끝
    for i, (no, head, name, how, effect) in enumerate(P02E['solutions']):
        cx = RX + RW * (0.27 if i == 0 else 0.73)
        path = MOCK / name
        iw, ih = PILImage.open(path).size
        w = PH * iw / ih
        d.img(path, cx - w / 2, PH_TOP - PH, h=PH)
        d.t(f'{no} {head}', cx, PH_TOP + 15, 8.0, PLUM, True, align='c')
        d.t(how, cx, PH_TOP - PH - 19, 7.8, PLUM_INK, True, align='c')
        d.t(effect, cx, PH_TOP - PH - 31, 7.0, PLUM_MUTED, align='c')
    d.caption(11, P02E['note'], 40, PLUM_MUTED)
    d.page_break()


def p12(d):
    """12쪽 PROJECT 02 · OUTPUT — 확정 홍보물 2종을 다크 플럼 쇼케이스에.

    2026-11-22 사용자 지시: `#1E1019` 다크 바탕에 확정 홍보물 2종
    (`x2_gsshop_promo_hero_plum_v3.png`·`x2_home_modes_guide_plum_v2.png`)을
    7쪽 포스터 2종처럼 큼직하게. 같은 날 지시 5번으로 첫 장 캡션을 `01 방송 예고`에서
    `01 방송 홍보`로 바로잡았고, 규격·용도·비고만 남겼으며(`용도`는 `GS샵 방송 홍보`),
    각 장 설명을 이미지 가로 폭 중심으로 정렬했다 — 라벨 x=44, 값 x=80,
    `para_baseline()`으로 베이스라인 0pt.
    """
    d.bg(color=PLUM_DARK)
    d.chrome(12, P02O['kicker'], dark=True, accent=PLUM_L,
             label=PLUM_MUTED_D, hair=PLUM_HAIR_D)

    LX, LW = M, 236.0
    d.t(P02O['title'], LX, 442, 22.0, WHITE, True)
    y = 410
    for line in [s for s in P02O['lead'].split('|') if s.strip()]:
        y -= d.para(line, LX, y, LW, 7.6, 11.6, PLUM_SOFT_D) + 2
    y -= 10
    for label, value in P02O['about']:
        d.t(label, LX, y, 6.2, PLUM_L, True, tracking=1.0)
        y -= d.para_baseline(value, LX + 36, y, LW - 36, 7.2, 10.6, WHITE) + 9

    items = P02O['items']
    gap, x, bottom = 56.0, 330.0, 92.0
    w = (PAGE_W - M - x - gap * (len(items) - 1)) / len(items)
    for no, title, spec, name, desc in items:
        path = MOCK / name
        iw, ih = PILImage.open(path).size
        h = w * ih / iw
        d.img(path, x, bottom, w=w, h=h)
        # 2026-11-22 사용자 지시(9번): 7·8쪽과 같이 각 이미지 가로 폭 중심 정렬.
        cx = x + w / 2
        d.t_pair(no, title, cx, bottom - 14, 6.2, PLUM_L, WHITE, bold_r=True)
        d.t(f'{spec} · {desc}', cx, bottom - 25, 5.8, PLUM_SOFT_D, align='c')
        x += w + gap
    d.t(P02O['spec'], PAGE_W - M, 442, 6.2, PLUM_L, True, align='r')
    d.caption(12, P02O['note'], 40, PLUM_MUTED_D)
    d.page_break()


def p13(d):
    """13쪽 WORK PROCESS — 아쿠아 × 플럼 듀얼 트랙 플로우(2026-11-22 4·5차 지시).

    4차 지시로 글자 위주 4칸을 걷어내고 **공통 출발점(차콜) → 2030 아쿠아 트랙 /
    5060 플럼 트랙** 으로 갈라지는 다이어그램을 그렸고, 5차 지시(15번)로 오른쪽
    **`검증 게이트` 블록과 그 연결선을 삭제**했습니다. 두 트랙은 이제 오른쪽 여백
    (x=916)까지 720pt 폭으로 늘어나고, 트랙 안의 두 칸·산출물 썸네일도 그 폭에 맞춰
    다시 배치해 오른쪽이 비지 않고 균형을 이루게 했습니다. 맨 아래 툴 칩은 6개.
    """
    d.bg()
    d.chrome(13, PROCESS['kicker'])
    d.t(PROCESS['title'], M, 452, 24, INK, True)
    C = d.c

    WIRE = HexColor('#C4BEB6')
    NX, NY, NW, NH = M, 206.0, 120.0, 118.0

    def arrow(x, y, color, size=4.0):
        C.setFillColor(color)
        C.setStrokeColor(color)
        p = C.beginPath()
        p.moveTo(x, y)
        p.lineTo(x - size, y + size * 0.62)
        p.lineTo(x - size, y - size * 0.62)
        p.close()
        C.drawPath(p, stroke=0, fill=1)

    # ── 공통 출발점(차콜) ────────────────────────────────────────
    no, t1, t2, d1, d2 = PROCESS['start']
    C.setFillColor(INK)
    C.rect(NX, NY, NW, NH, stroke=0, fill=1)
    d.t(no, NX + 12, NY + NH - 20, 6.8, CRIMSON_L, True, tracking=0.8)
    d.t(t1, NX + 12, NY + NH - 40, 10.4, WHITE, True)
    d.t(t2, NX + 12, NY + NH - 56, 10.4, WHITE, True)
    d.rule(NX + 12, NX + NW - 12, NY + 44, dark=True)
    d.t(d1, NX + 12, NY + 30, 6.0, HexColor('#B5AFA6'))
    d.t(d2, NX + 12, NY + 19, 6.0, HexColor('#B5AFA6'))

    # ── 두 트랙 — 검증 게이트가 빠진 만큼 오른쪽 끝(x=916)까지 넓힌다 ──
    BX0, BW = 196.0, PAGE_W - M - 196.0        # 196 ~ 916 = 720pt
    FROM_X, FROM_W = BX0 + 14.0, 200.0
    TO_X, TO_W = BX0 + 240.0, 260.0
    for tone, top in (('aqua', 308.0), ('plum', 126.0)):
        acc, panel, hair, ink, muted = (
            (AQ_TEAL, AQ_PANEL, AQ_HAIR, AQ_INK, AQ_MUTED) if tone == 'aqua' else
            (PLUM, PLUM_PANEL, PLUM_HAIR, PLUM_INK, PLUM_MUTED))
        spec = next(t for t in PROCESS['tracks'] if t['page_tone'] == tone)
        C.setFillColor(panel)
        C.rect(BX0, top, BW, 96, stroke=0, fill=1)
        C.setFillColor(acc)
        C.rect(BX0, top, 3.0, 96, stroke=0, fill=1)
        d.t(spec['label'], BX0 + 14, top + 82, 6.0, acc, True, tracking=1.3)
        for bx, bw, lines in ((FROM_X, FROM_W, spec['from']), (TO_X, TO_W, spec['to'])):
            C.setFillColor(WHITE)
            C.setStrokeColor(hair)
            C.setLineWidth(0.6)
            C.rect(bx, top + 12, bw, 52, stroke=1, fill=1)
            d.t(lines[0], bx + 12, top + 44, 8.6, ink, True)
            d.t(lines[1], bx + 12, top + 29, 7.2, muted)
        C.setStrokeColor(acc)
        C.setLineWidth(1.0)
        C.line(FROM_X + FROM_W + 4, top + 38, FROM_X + FROM_W + 20, top + 38)
        arrow(FROM_X + FROM_W + 26, top + 38, acc)

        # 실제 산출물 미니 썸네일 — 오른쪽 끝에서부터 쌓고, 칸과 썸네일 사이는 점선으로 잇는다
        xr = BX0 + BW - 14
        for name in reversed(spec['thumbs']):
            iw, ih = PILImage.open(MOCK / name).size
            tw = 62.0 * iw / ih
            xr -= tw
            d.img(MOCK / name, xr, top + 17, w=tw, h=62.0)
            C.setStrokeColor(hair)
            C.setLineWidth(0.5)
            C.rect(xr, top + 17, tw, 62.0, stroke=1, fill=0)
            xr -= 10
        C.setStrokeColor(muted)
        C.setLineWidth(0.6)
        C.setDash(1.6, 2.0)
        C.line(TO_X + TO_W + 10, top + 38, xr + 4, top + 38)
        C.setDash(1, 0)
        d.dot(xr + 6, top + 38, 1.6, muted)

    # ── 연결선 — 출발점에서 갈라져 두 트랙으로 ─────────────────────
    UY, LY, MY = 356.0, 174.0, 265.0
    C.setStrokeColor(WIRE)
    C.setLineWidth(0.9)
    C.line(NX + NW, MY, 180.0, MY)
    C.line(180.0, UY, 180.0, LY)
    for yy, color in ((UY, AQ_TEAL), (LY, PLUM)):
        C.setStrokeColor(color)
        C.setLineWidth(1.0)
        C.line(180.0, yy, BX0 - 6, yy)
        arrow(BX0, yy, color)

    # ── 툴 — 한 줄만 ───────────────────────────────────────────
    d.t('TOOL', M, 70, 6.2, CRIMSON, True, tracking=1.6)
    tx = M + 44
    for tool in PROCESS['tools']:
        tw = pdfmetrics.stringWidth(tool, FONT, 7.4) + 16
        C.setStrokeColor(HAIR)
        C.setLineWidth(0.6)
        C.roundRect(tx, 64, tw, 17, 8.5, stroke=1, fill=0)
        d.t(tool, tx + 8, 70, 7.4, INK)
        tx += tw + 8
    d.page_break()


def p14(d):
    """14쪽 CLOSING — 단독 면(2026-11-22 5차 지시 16번).

    APPENDIX 섹션(보고서 8편 아카이브·저장소 링크·역할·표지 두 축)을 지면에서
    **전부 걷어내고** `CLOSING` 한 면으로 다시 짰습니다. 왼쪽은 이름·`감사합니다`
    (56pt)·클로징 한 문장, 오른쪽은 CONTACT(Email·Phone·GitHub) 세 줄이고, 맨 아래
    `[알림]`과 `[AI 제작]` 고지는 14pt 간격(이전 판의 `01 2030…`·`02 5060…`
    두 줄과 같은 간격)으로 바로 붙여 둡니다.
    """
    d.bg(dark=True)
    d.chrome(14, CLOSING['kicker'], dark=True)
    C = d.c
    d.t(CLOSING['title'], M, 444, 44, WHITE, True, tracking=2.0)
    d.rule(M, PAGE_W - M, 418, dark=True)

    # ── 왼쪽 — 이름 · 감사 인사 · 클로징 한 문장 ─────────────────
    X = M
    d.t(CLOSING['name'], X, 380, 7.2, CRIMSON_L, True, tracking=1.5)
    d.t(CLOSING['thanks'], X, 292, 64, WHITE, True, tracking=1.0)
    d.para(CLOSING['close'], X, 252, 520, 10.0, 15.0, HexColor('#B5AFA6'))

    # ── CONTACT — Email·Phone·GitHub를 세 열로 고르게 ─────────────——
    d.rule(M, PAGE_W - M, 206, dark=True)
    d.t('CONTACT', M, 184, 6.4, CRIMSON_L, True, tracking=1.7)
    for (label, value, url), x in zip(CLOSING['contact'], (M, 356.0, 668.0)):
        d.t(label, x, 160, 6.8, MUTED_D)
        w = d.t(value, x, 140, 10.5, WHITE)
        if url:
            C.linkURL(url, (x, 137.2, x + w, 150.8), relative=0, thickness=0)

    # ── 하단 — [알림] · [AI 제작] (14pt 간격으로 붙여서) ────────────
    d.t(CLOSING['notice'], M, 96, 6.2, HexColor('#A8A29A'))
    d.t(CLOSING['note'], M, 82, 6.2, HexColor('#8A857E'))
    d.page_break()


PAGE_FUNCS = (p01, p02, p03, p05, p06, p07, p08, p08b, p09, p10, p11, p12, p13, p14)


# ── MD ─────────────────────────────────────────────────────────────────────
def write_md():
    L = []
    A = L.append

    A('# 메디큐브 콘텐츠 마케팅 포트폴리오')
    A('')
    A(f'> **14쪽 Behance식 가로형 덱 · {VERSION}** · 최종 수정 2026-11-22 KST · 김윤서 · 2026.11')
    A('> 에이피알(APR) [마케팅 특별채용] 국내 콘텐츠 마케팅 신입 지원 (마감 2026-11-22 23:59)')
    A('>')
    A('> 표지·프로필·일하는 방식·CLOSING은 딥 차콜 `#18181B` / 웜 오프화이트 `#F8F7F5`와 크림슨 한 색,')
    A('> 2030 파트(4~8쪽)는 아쿠아 키비주얼의 물빛(`#F3F9FB`·`#E2F0F5`·`#165B72`,')
    A('> 어두운 8쪽은 `#0E1E26`·`#6EC4DB`), 5060 파트(9~12쪽)는 확정 홍보물 2종의 딥 플럼')
    A('> (`#4A1C3A`~`#240E1C`)과 소프트 블러시 핑크(`#F9F4F7`·`#F3D5E5`), 어두운 12쪽은 `#1E1019`로 조판했습니다.')
    A('> 검증 수치와 방법론은 깃허브 보고서 8편으로 보냈습니다(14쪽은 CLOSING 한 면).')
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
    # 2026-11-22 5차 지시(1번): `사진과 이력은…` 고지를 걷어냈으므로 줄도 남기지 않는다.
    if PROFILE.get('note'):
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
        # 2026-11-22 5차 지시(3번): 4쪽은 캡션 아래 AI 활용 고지를 한 줄 더 둔다.
        if data.get('ai_note'):
            A(f"> {data['ai_note']}")
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

    # 7쪽 · 8쪽 — PROJECT 01 결과물 두 면 (포스터 / 숏폼 카드)
    def output_page(no_page, data):
        A(f'## {no_page}쪽 · {data["kicker"].replace(" · ", " — ")}')
        A('')
        A(f"# {data['title']}")
        A('')
        # 2026-11-22 지시 1번으로 7쪽 리드를 지웠다 — 빈 문자열이면 줄도 남기지 않는다.
        if data['lead']:
            A(data['lead'].replace('|', ' '))
            A('')
        for label, value in data.get('about', ()):
            A(f'| {label} | {value} |')
        if data.get('about'):
            A('')
        A('| 연번 | 인쇄물 | 규격 | 설명 |')
        A('|---|---|---|---|')
        for no, title, spec, _, desc in data['items']:
            A(f'| {no} | {title} | {spec} | {desc} |')
        A('')
        A(data['spec'])
        A('')
        A(f"> {data['note']}")
        A('')
        A('---')
        A('')

    output_page(7, P01P)
    output_page(8, P01C)

    project_intro(9, P02)

    # 10쪽 — 2026-11-22 4차 지시(2번): 판단 카드를 걷어내고 52주 추이 그래프로.
    A('## 10쪽 · PROJECT 02 — 근거 & 1주년 기획')
    A('')
    A(f"# {P02G['title']}")
    A('')
    A(P02G['lead'])
    A('')
    A(P02G['evidence'])
    A('')
    A('| 계열 | 2026-05-04 주 |')
    A('|---|---|')
    A('| 검색 지수 · 부스터 프로 | 100.0 |')
    A('| 클릭 지수 · 메디큐브 | 38 → 68 |')
    A('')
    A('52주 최고')
    A('')
    A(P02G['marker'])
    A('')
    A(P02G['chart_note'])
    A('')
    A(P02G['plan'])
    A('')
    A('| 시점 | 계획 | 내용 |')
    A('|---|---|---|')
    for when, what, detail in P02G['steps']:
        A(f'| {when} | {what} | {detail} |')
    A('')
    A(P02G['card'])
    A('')
    A(f"> {P02G['note']}")
    A('')
    A('---')
    A('')

    # 11쪽
    A('## 11쪽 · PROJECT 02 — 사용 장벽 & 해법')
    A('')
    A(f"# {P02E['title']}")
    A('')
    A(P02E['lead'])
    A('')
    A(P02E['chart_label'])
    A('')
    A('| 장벽 | 언급 |')
    A('|---|---|')
    for label, value in P02E['bars']:
        A(f'| {label} | {value}건 |')
    A('')
    A(P02E['chart_note'])
    A('')
    A('| 해법 | 홍보물 문구 | 해소하는 장벽 |')
    A('|---|---|---|')
    for no, head, _name, how, effect in P02E['solutions']:
        A(f'| {no} {head} | {how} | {effect} |')
    A('')
    A(f"> {P02E['note']}")
    A('')
    A('---')
    A('')

    # 12쪽
    output_page(12, P02O)

    # 13쪽 — 2026-11-22 4·5차 지시: 듀얼 트랙 플로우(검증 게이트 삭제)
    A('## 13쪽 · WORK PROCESS — 듀얼 트랙 플로우')
    A('')
    A(f"# {PROCESS['title']}")
    A('')
    A('| 출발점 | 트랙 | 결과물 |')
    A('|---|---|---|')
    start = PROCESS['start']
    A(f"| {start[0]} | {start[1]} {start[2]} | {start[3]} · {start[4]} |")
    for spec in PROCESS['tracks']:
        A(f"| {spec['label']} | {spec['from'][0]} · {spec['from'][1]} | "
          f"{spec['to'][0]} · {spec['to'][1]} |")
    A('')
    A('TOOL | ' + ' | '.join(PROCESS['tools']))
    A('')
    A('---')
    A('')

    # 14쪽 — 2026-11-22 5차 지시(16번): CLOSING 단독 면
    A('## 14쪽 · CLOSING')
    A('')
    A(f"# {CLOSING['title']}")
    A('')
    A(CLOSING['name'])
    A('')
    A(CLOSING['thanks'])
    A('')
    A(CLOSING['close'])
    A('')
    A('**CONTACT**')
    A('')
    A('| 항목 | 내용 |')
    A('|---|---|')
    for label, value, _url in CLOSING['contact']:
        A(f'| {label} | {value} |')
    A('')
    A(f"> {CLOSING['notice']}")
    A('')
    A(f"> {CLOSING['note']}")
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
