# -*- coding: utf-8 -*-
"""정적 스토리보드 SVG를 rsvg-convert로 PNG(2880×1395)에 렌더링한다."""

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SVG = ROOT / 'design/gs_x2_2027_static_storyboard.svg'
PNG = ROOT / 'design/gs_x2_2027_static_storyboard.png'
WIDTH = 2880
HEIGHT = 1395


def render():
    """로컬 SVG를 입력받아 PNG를 저장하고 출력 크기 `(너비, 높이)`를 반환한다.

    PDF용 Python 패키지에 의존하지 않고 글자 위치가 확인된 SVG 렌더러를 쓴다.
    """
    subprocess.run(
        ['rsvg-convert', '-w', str(WIDTH), '-h', str(HEIGHT),
         '-o', str(PNG), str(SVG)],
        check=True,
    )
    return WIDTH, HEIGHT


if __name__ == '__main__':
    print(PNG.relative_to(ROOT), *render())
