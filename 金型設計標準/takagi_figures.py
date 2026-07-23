#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""高木・順送プレス金型仕様書のスライドから、HMS用の図を切り出して清書する

社内限定で使用する（正式に受領した資料。外注先へは出さない）。
原図の schematic をそのまま使い、背景の高木ロゴ・透かし等は白く飛ばす。
品番・工場名・承認印・個人情報が写る箇所は切り出し範囲から外すか白塗りする。

処理:
  1. 指定スライドから図の領域を切り出す（座標は0〜1の割合で指定）
  2. 背景の薄いロゴ／透かしを白へ飛ばす（薄いグレーを白に、線と色は残す）
  3. 任意の白塗り矩形で固有情報を隠す
  4. 余白を詰め、白縁を付けて体裁を統一

使い方:
    python takagi_figures.py            # FIGS を全部処理
    python takagi_figures.py 5-1        # その図だけ（確認用）

依存: pip install pillow
"""
import os
import sys

from PIL import Image, ImageOps, ImageChops

SLIDES = (r'C:\Users\Owner\AppData\Local\Temp\claude'
          r'\C--Users-Owner-Desktop-513dcad3-989a-4a86-aede-4a6d6dbccb8c'
          r'\scratchpad\takagi_slides')
# ↑ 実行時に存在チェックして自動補正する（下の _slides_dir）
OUT = r'C:\Users\Owner\Desktop\金型仕様書\HMS図'


def _slides_dir():
    if os.path.isdir(SLIDES):
        return SLIDES
    # スクラッチパスは実行環境で変わるため、Temp配下を探す
    base = os.path.expandvars(r'%LOCALAPPDATA%\Temp\claude')
    for root, dirs, _ in os.walk(base):
        if os.path.basename(root) == 'takagi_slides':
            return root
    raise SystemExit('takagi_slides フォルダが見つかりません: %s' % SLIDES)


def whiten_watermark(im, thr=205, keep_sat=32):
    """薄いグレー（ロゴ・透かし）を白へ飛ばす。
    thr    … これより明るい無彩色画素は白にする
    keep_sat … 彩度がこれ以上（＝色線）の画素は残す。黒線も暗いので残る。
    """
    im = im.convert('RGB')
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            mx, mn = max(r, g, b), min(r, g, b)
            sat = mx - mn                 # 彩度の代用
            if sat < keep_sat and mn > thr:
                px[x, y] = (255, 255, 255)
    return im


def white_boxes(im, boxes):
    """固有情報を白塗りで隠す。boxes は (x0,y0,x1,y1) の割合。"""
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    w, h = im.size
    for (x0, y0, x1, y1) in boxes:
        d.rectangle([x0 * w, y0 * h, x1 * w, y1 * h], fill='white')
    return im


def autotrim(im, border=16, bg=250):
    """白背景を詰めて、一定の白縁を付ける。"""
    g = im.convert('L')
    mask = g.point(lambda p: 0 if p >= bg else 255)
    bbox = mask.getbbox()
    if bbox:
        im = im.crop(bbox)
    return ImageOps.expand(im, border=border, fill='white')


# 全スライド共通で右上に入る高木ロゴ＋ページ番号（色付きなので透かし処理では
# 消えない）。切り出し前にスライド全体で白塗りする。割合は全スライド共通。
LOGO_BOX = (0.90, 0.00, 1.00, 0.095)


def process(fig, slides_dir, out_dir):
    src = os.path.join(slides_dir, 'スライド%d.PNG' % fig['slide'])
    im = Image.open(src).convert('RGB')
    im = white_boxes(im, [LOGO_BOX])           # ロゴ・ページ番号を消す
    w, h = im.size
    x0, y0, x1, y1 = fig['box']
    im = im.crop((int(w * x0), int(h * y0), int(w * x1), int(h * y1)))
    if fig.get('hide'):
        im = white_boxes(im, fig['hide'])
    im = whiten_watermark(im, thr=fig.get('thr', 205))
    im = autotrim(im)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, 'hms_%s.png' % fig['id'])
    im.save(path)
    return path


# 図の定義。box/hide は 0〜1 の割合。id は対応するHMS項目番号。
FIGS = [
    # 順送 5-1/5-2 ダイの刃先形状・逃がし（スライド26 下段の図1・図2・図3）
    {'id': '順5-1', 'slide': 26, 'box': (0.00, 0.635, 1.00, 1.00),
     'thr': 200,
     # 右上に残る不具合ボックス（品番入り）の赤断片を白塗りで隠す
     'hide': [(0.74, 0.00, 1.00, 0.10)]},
    # 順送 5-10 座ぐりインサート部品（スライド45 右列の図1・図2）
    {'id': '順5-10', 'slide': 45, 'box': (0.575, 0.02, 1.00, 0.96),
     'thr': 200, 'hide': []},
    # 順送 5-12 最終分断ダイ・分断パンチ（スライド48 下段の図1・図2・図3）
    {'id': '順5-12', 'slide': 48, 'box': (0.00, 0.49, 1.00, 1.00),
     'thr': 200, 'hide': []},
]


def main():
    slides_dir = _slides_dir()
    sel = sys.argv[1] if len(sys.argv) > 1 else None
    for fig in FIGS:
        if sel and fig['id'] != sel:
            continue
        p = process(fig, slides_dir, OUT)
        print('図:', p)


if __name__ == '__main__':
    main()
