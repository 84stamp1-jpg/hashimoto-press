#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""切り出した図の中の文字を、きれいなフォント・色・自社用語に貼り直す

原図（高木スライドから切り出したもの）は線図はそのまま活かし、焼き込まれた
文字だけを白塗りして、Meiryoで置き直す。ハイライト（色地）のラベルは
文字を白/濃紺にして黒のままにしない。パンチプレート等の用語も自社に直す。
高木の版マーク（⚠18等）は除去する。

図ごとに置き換え内容が違うので、関数を1図につき1つ用意する。
使い方: python relabel_figures.py 順4-7
依存: pip install pillow
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

FIGDIR = r'C:\Users\Owner\Desktop\金型仕様書\HMS図'
MEIRYO = r'C:\Windows\Fonts\meiryo.ttc'

MAGENTA = (214, 0, 160)
GREEN = (0, 160, 60)
YELLOW = (240, 200, 0)
CYAN = (0, 170, 210)
NAVY = (31, 56, 100)
INK = (17, 17, 17)
GRAY = (110, 110, 110)
WHITE = (255, 255, 255)


def font(sz):
    return ImageFont.truetype(MEIRYO, sz)


def wbox(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=WHITE)


def tsize(d, text, f):
    b = d.textbbox((0, 0), text, font=f)
    return b[2] - b[0], b[3] - b[1]


def chip(d, x, y, text, bg, fg, f, padx=8, pady=4, anchor='lt'):
    """色地のラベル。(x,y)を左上/中央に置く。戻り値=右端x"""
    w, h = tsize(d, text, f)
    if anchor == 'mm':
        x -= (w + 2 * padx) / 2
        y -= (h + 2 * pady) / 2
    d.rectangle([x, y, x + w + 2 * padx, y + h + 2 * pady], fill=bg)
    d.text((x + padx, y + pady - 2), text, fill=fg, font=f)
    return x + w + 2 * padx


def plain(d, x, y, text, fg, f):
    d.text((x, y), text, fill=fg, font=f)
    w, _ = tsize(d, text, f)
    return x + w


def vchip(im, cx, cy, text, bg, fg, f, padx=8, pady=4):
    """縦書き（下から上）の色地ラベルを中央(cx,cy)に貼る"""
    d0 = ImageDraw.Draw(im)
    w, h = tsize(d0, text, f)
    tmp = Image.new('RGBA', (w + 2 * padx, h + 2 * pady), bg + (255,))
    dt = ImageDraw.Draw(tmp)
    dt.text((padx, pady - 2), text, fill=fg, font=f)
    tmp = tmp.rotate(90, expand=True)
    im.paste(tmp, (int(cx - tmp.width / 2), int(cy - tmp.height / 2)), tmp)


# ============================================================ 順4-7
def relabel_順4_7(im):
    d = ImageDraw.Draw(im)
    # 元の文字・版マークを白塗り
    for box in [(150, 26, 300, 72),      # ツバ厚(mm)
                (0, 150, 40, 435),        # パンチプレート厚み(mm) 縦
                (170, 315, 220, 365),     # T
                (560, 242, 705, 305),     # 面取り
                (440, 452, 535, 500),     # ΦD
                (890, 100, 1265, 180),    # 式1 ΦD≦T
                (870, 182, 1452, 250),    # 式2 パンチプレート厚み=…
                (818, 280, 1452, 400)]:   # ⚠18 と注記
        wbox(d, *box)

    f22 = font(22)
    f20 = font(20)
    f30 = font(30)
    # 図中ラベル
    chip(d, 165, 32, 'ツバ厚(mm)', MAGENTA, WHITE, f22)
    vchip(im, 18, 290, 'パンチホルダー厚み(mm)', GREEN, WHITE, f20)
    d = ImageDraw.Draw(im)
    chip(d, 178, 320, 'T', CYAN, NAVY, f22, padx=6)
    plain(d, 572, 255, '面取り', GRAY, f22)
    chip(d, 452, 458, 'ΦD', YELLOW, NAVY, f22, padx=6)

    # 式1: ΦD ≦ T
    x = chip(d, 905, 118, 'ΦD', YELLOW, NAVY, f30, padx=6)
    x = plain(d, x + 14, 122, '≦', INK, f30)
    chip(d, x + 14, 118, 'T', CYAN, NAVY, f30, padx=8)
    # 式2: パンチホルダー厚み = ツバ厚 + T
    x = chip(d, 878, 196, 'パンチホルダー厚み', GREEN, WHITE, f30)
    x = plain(d, x + 12, 200, '＝', INK, f30)
    x = chip(d, x + 12, 196, 'ツバ厚', MAGENTA, WHITE, f30)
    x = plain(d, x + 12, 200, '＋', INK, f30)
    chip(d, x + 12, 196, 'T', CYAN, NAVY, f30, padx=8)
    # 注記
    plain(d, 895, 312, '＊パンチホルダーに入れ子を設定して', INK, f22)
    plain(d, 895, 348, '　厚みを確保しても可', INK, f22)


# 順4-7 は第3次移行で共通編C2-10へ移動（図中の文字書き換えは同じ関数を再利用）
FIGS = {'共C2-10': relabel_順4_7}


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else None
    if key not in FIGS:
        print('対象:', ', '.join(FIGS)); return
    path = os.path.join(FIGDIR, 'hms_%s.png' % key)
    im = Image.open(path).convert('RGB')
    FIGS[key](im)
    im.save(path)
    print('書き換え:', path)


if __name__ == '__main__':
    main()
