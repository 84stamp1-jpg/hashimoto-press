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
RED = (200, 0, 0)


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


PURPLE = (120, 50, 160)
BLUE2 = (30, 110, 230)


def vplain(im, cx, cy, text, fg, f):
    """縦書き（下から上）の無地テキストを中央(cx,cy)に貼る"""
    d0 = ImageDraw.Draw(im)
    w, h = tsize(d0, text, f)
    tmp = Image.new('RGBA', (w + 6, h + 6), (255, 255, 255, 0))
    ImageDraw.Draw(tmp).text((3, 1), text, fill=fg, font=f)
    tmp = tmp.rotate(90, expand=True)
    im.paste(tmp, (int(cx - tmp.width / 2), int(cy - tmp.height / 2)), tmp)


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
# ============================================================ 共C2-9 プレート名称
def relabel_共C2_9(im):
    d = ImageDraw.Draw(im)
    # 右側のラベル帯・タイトル・左ラベル・図番号をまとめて白塗り（確実に消す）
    for box in [(10, 36, 545, 96),         # タイトル
                (548, 10, 715, 90),        # 上型ホルダ（上部中央）
                (856, 92, 1144, 948),      # 右側ラベル帯すべて
                (4, 536, 112, 634),        # ↑上型↓下型
                (2, 862, 124, 936),        # ライナー
                (435, 1076, 625, 1143)]:   # 〈図1〉→ PDF側の「図N」に任せ再追加しない
        wbox(d, *box)
    f24 = font(24)
    f22 = font(22)
    plain(d, 20, 50, '金型の各プレートの呼び名称〈図1〉', INK, f24)
    plain(d, 560, 44, '上型ダイセット', INK, f22)
    # 右側ラベル（leaderの終端 y に合わせて左寄せで並べる）
    R = 872
    plain(d, R, 108, '上型スペーサ', INK, f22)
    plain(d, R, 210, '上型バッキングプレート', INK, f22)
    plain(d, R, 296, 'パンチホルダ', INK, f22)
    plain(d, R, 388, 'ストリッパ', INK, f22)
    plain(d, R, 414, 'バッキングプレート', INK, f22)
    plain(d, R, 500, 'ストリッパプレート', INK, f22)
    plain(d, R, 606, 'ダイホルダ', INK, f22)
    plain(d, R, 676, '下型バッキングプレート', INK, f22)
    plain(d, R, 708, '下型スペーサ', INK, f22)
    plain(d, R, 828, '下型ダイセット', INK, f22)
    plain(d, R, 906, 'コモンプレート', INK, f22)
    plain(d, 14, 552, '↑上型', INK, f22)
    plain(d, 14, 592, '↓下型', INK, f22)
    plain(d, 18, 892, 'ライナー', INK, f22)


# ============================================================ 共C2-6 上型の取付
def relabel_共C2_6(im):
    d = ImageDraw.Draw(im)
    for box in [(0, 0, 118, 42),           # 左上の断片 刃〈図1〉
                (208, 24, 408, 90), (208, 94, 408, 155), (208, 159, 408, 220),  # 表左列
                (413, 24, 648, 90), (413, 94, 648, 155), (413, 159, 648, 220),  # 表右列
                (390, 232, 474, 276),       # 〈表1〉
                (300, 388, 424, 426),       # L±1.0mm
                (628, 456, 751, 504),       # 上型ホルダ
                (196, 646, 238, 692),       # U
                (56, 752, 102, 802),        # T
                (310, 1012, 420, 1058)]:    # 〈図1〉
        wbox(d, *box)
    f22 = font(22)
    for y, s in ((44, '≦200トン'), (109, '=300トン'), (172, '=300トンリンク')):
        plain(d, 252, y, s, INK, f22)
    for y, s in ((44, '40±1.0mm'), (109, '50±1.0mm'), (172, '40±1.0mm')):
        plain(d, 470, y, s, INK, f22)
    chip(d, 398, 240, '表1', GREEN, WHITE, f22, padx=6)
    chip(d, 306, 394, 'L±1.0mm', YELLOW, NAVY, f22, padx=6)
    plain(d, 590, 470, '上型ダイセット', INK, font(20))
    chip(d, 202, 652, 'U', CYAN, NAVY, f22, padx=6)
    chip(d, 62, 758, 'T', CYAN, NAVY, f22, padx=6)


# ============================================================ 共C3-15 座ぐりインサート
def relabel_共C3_15(im):
    d = ImageDraw.Draw(im)
    for box in [(28, 40, 228, 80), (58, 284, 248, 324),        # 15mm以上/インサート部
                (483, 330, 632, 370), (158, 383, 252, 422), (353, 390, 437, 430),  # 曲げ/偏荷重/図1
                (298, 546, 538, 603), (240, 692, 280, 808),    # オーバハング/15mm縦
                (68, 810, 238, 850), (498, 900, 684, 940),     # 10mm/曲げ
                (158, 1015, 252, 1054), (358, 1025, 442, 1065)]:  # 偏荷重/図2
        wbox(d, *box)
    f22 = font(22)
    plain(d, 34, 46, '15mm以上インサート', RED, f22)
    plain(d, 62, 290, 'インサート部で支える', RED, f22)
    plain(d, 488, 336, '曲げパンチorダイ', INK, f22)
    plain(d, 166, 388, '偏荷重', INK, f22)
    plain(d, 362, 396, '〈図1〉', INK, f22)
    plain(d, 308, 566, 'オーバハングで支える', RED, f22)
    vplain(im, 258, 750, '15mm', RED, f22)
    d = ImageDraw.Draw(im)
    plain(d, 76, 816, '10mm以上で可', INK, f22)
    plain(d, 502, 908, '曲げパンチorダイ', INK, font(20))
    plain(d, 166, 1021, '偏荷重', INK, f22)
    plain(d, 365, 1031, '〈図2〉', INK, f22)


# ============================================================ 共C3-21 ダイの刃先形状
def relabel_共C3_21(im):
    d = ImageDraw.Draw(im)
    # 旧の半角カナは想定より幅広なので右側を広めに白塗りする（各図の間に余白があり安全）
    for box in [(0, 36, 82, 72), (483, 44, 568, 80),          # 3mm ×2
                (148, 36, 450, 74),                            # (1)刃先はプレス直
                (146, 94, 450, 180), (696, 194, 965, 274),     # (3)逃がし… ×2
                (146, 210, 450, 296), (694, 282, 965, 356),    # (3)底面… ×2
                (686, 110, 728, 154),                          # A
                (993, 92, 1218, 134), (995, 126, 1218, 170),   # (2)5'〜7' / (刃長部位)
                (1011, 320, 1130, 366),                        # A部拡大
                (48, 368, 452, 412), (552, 368, 1150, 412),    # 鋼材ボックス内文字 ×2
                (185, 412, 292, 454), (756, 412, 862, 454),    # 〈図1〉〈図2〉
                (1232, 348, 1472, 392),                        # (3)オフセット量
                (1226, 386, 1300, 434),                        # ⚠18 → 消す
                (1298, 412, 1392, 454), (1385, 408, 1562, 454)]:  # 〈図3〉/座ぐりの場合
        wbox(d, *box)
    f20 = font(20)
    f18 = font(18)
    plain(d, 2, 44, '3mm', PURPLE, f20)
    plain(d, 488, 50, '3mm', PURPLE, f20)
    # 図1
    plain(d, 154, 44, '(1)刃先はプレス直', BLUE2, f20)
    plain(d, 150, 100, '(3)逃がし勾配か', RED, f20)
    plain(d, 172, 140, '座ぐりを施す事', RED, f20)
    plain(d, 150, 218, '(3)底面の肉が', GREEN, f20)
    plain(d, 150, 258, 'なくならぬよう注意', GREEN, f18)
    plain(d, 56, 378, '引張り強さ590材未満の鋼材', INK, f20)
    plain(d, 198, 420, '〈図1〉', INK, f20)
    # 図2
    plain(d, 696, 118, 'A', INK, f20)
    plain(d, 700, 200, '(3)逃がし勾配か', RED, f20)
    plain(d, 722, 240, '座ぐりを施す事', RED, f20)
    plain(d, 700, 288, '(3)底面の肉が', GREEN, f18)
    plain(d, 700, 322, 'なくならぬよう注意', GREEN, f18)
    plain(d, 998, 100, "(2)5'〜7'の勾配", BLUE2, f20)
    plain(d, 1000, 134, '（刃長部位）', BLUE2, f20)
    plain(d, 1018, 328, 'A部拡大', INK, f20)
    plain(d, 560, 378, '引張り強さ590N/mm2以上及びステンレスの鋼材', INK, f20)
    plain(d, 768, 420, '〈図2〉', INK, f20)
    # 図3
    plain(d, 1240, 358, '(3)オフセット量≦1mm', GREEN, f18)
    plain(d, 1308, 420, '〈図3〉', INK, f20)
    plain(d, 1392, 416, '座ぐりの場合', RED, f20)


# ============================================================ 共C5-7 パスライン
def relabel_共C5_7(im):
    d = ImageDraw.Draw(im)
    for box in [(0, 96, 46, 344),          # DH:ダイハイト 縦
                (674, 14, 722, 168),        # L:リフト量 縦・シアン
                (694, 168, 740, 366),       # H:下型高さ 縦・緑
                (1548, 168, 1596, 380),     # PL:パスライン 縦・黄
                (860, 448, 986, 496),       # ダイプレート
                (284, 456, 382, 502), (1110, 456, 1208, 502)]:  # 〈図1〉〈図2〉
        wbox(d, *box)
    f20 = font(20)
    vplain(im, 20, 220, 'DH:ダイハイト', INK, f20)
    vchip(im, 698, 92, 'L:リフト量', CYAN, NAVY, f20, padx=6, pady=4)
    vchip(im, 717, 267, 'H:下型高さ', GREEN, WHITE, f20, padx=6, pady=4)
    vchip(im, 1572, 274, 'PL:パスライン', YELLOW, NAVY, f20, padx=6, pady=4)
    d = ImageDraw.Draw(im)
    plain(d, 870, 466, 'ダイホルダ', INK, f20)
    plain(d, 294, 468, '〈図1〉', INK, f20)
    plain(d, 1120, 468, '〈図2〉', INK, f20)


# ============================================================ 順5-12 最終分断ダイ
def relabel_順5_12(im):
    d = ImageDraw.Draw(im)
    # 目視測定の誤差を吸収するため各方向へ広めに白塗りする
    for box in [(348, 14, 474, 64), (364, 140, 504, 196),        # 分断ダイ/ダイホルダ 上面
                (4, 242, 108, 294),                              # *上面視
                (376, 266, 504, 316), (364, 364, 504, 418),      # 分断ダイ/ダイホルダ 側面
                (4, 512, 108, 564), (142, 558, 246, 610),        # *側面視/〈図1〉
                (732, 290, 860, 344), (488, 512, 594, 564),      # 分断ダイ/*側面視
                (628, 558, 730, 610),                            # 〈図2〉
                (704, 492, 886, 546), (704, 532, 998, 588),      # バッキング/*ホルダー禁止
                (1050, 360, 1194, 416), (1388, 290, 1518, 344),  # ダイホルダ/分断ダイ
                (1050, 512, 1160, 564), (1184, 558, 1290, 610),  # *側面視/〈図3〉
                (1288, 512, 1468, 564), (1288, 558, 1570, 610)]:  # バッキング/*分断ダイより大きい
        wbox(d, *box)
    f20 = font(20)
    f18 = font(18)
    plain(d, 358, 28, '分断ダイ', INK, f20)
    plain(d, 376, 156, 'ダイホルダ', INK, f20)
    plain(d, 14, 256, '*上面視', INK, f20)
    plain(d, 386, 280, '分断ダイ', INK, f20)
    plain(d, 376, 380, 'ダイホルダ', INK, f20)
    plain(d, 14, 526, '*側面視', INK, f20)
    plain(d, 154, 572, '〈図1〉', INK, f20)
    plain(d, 744, 306, '分断ダイ', INK, f20)
    plain(d, 499, 526, '*側面視', INK, f20)
    plain(d, 639, 572, '〈図2〉', INK, f20)
    plain(d, 716, 506, 'バッキングプレート', INK, f20)
    plain(d, 716, 548, '*ホルダーへの掘り込み禁止', RED, f18)
    plain(d, 1061, 376, 'ダイホルダ', INK, f20)
    plain(d, 1399, 306, '分断ダイ', INK, f20)
    plain(d, 1061, 526, '*側面視', INK, f20)
    plain(d, 1196, 572, '〈図3〉', INK, f20)
    plain(d, 1298, 526, 'バッキングプレート', INK, f20)
    plain(d, 1298, 572, '*分断ダイより大きいこと', RED, f18)


FIGS = {'共C2-10': relabel_順4_7, '共C2-9': relabel_共C2_9,
        '共C2-6': relabel_共C2_6, '共C3-15': relabel_共C3_15,
        '共C3-21': relabel_共C3_21, '共C5-7': relabel_共C5_7,
        '順5-12': relabel_順5_12}


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
