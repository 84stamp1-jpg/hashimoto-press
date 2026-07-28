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

from PIL import Image, ImageDraw, ImageFont, ImageOps

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


def trim(im, border=8, bg=248):
    """白背景を詰めて白縁を付ける"""
    g = im.convert('L').point(lambda p: 0 if p >= bg else 255)
    bbox = g.getbbox()
    if bbox:
        im = im.crop(bbox)
    return ImageOps.expand(im, border=border, fill='white')


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


def rplain(im, cx, cy, text, fg, f, angle):
    """任意角度の無地テキストを中央(cx,cy)に貼る"""
    d0 = ImageDraw.Draw(im)
    w, h = tsize(d0, text, f)
    tmp = Image.new('RGBA', (w + 8, h + 8), (255, 255, 255, 0))
    ImageDraw.Draw(tmp).text((4, 2), text, fill=fg, font=f)
    tmp = tmp.rotate(angle, expand=True, resample=Image.BICUBIC)
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
    # 縦積み（図1上・図2下）を横並び（図1左・図2右）に組み替えて余白を減らす
    w, h = im.size
    fig1 = trim(im.crop((0, 0, w, 468)))
    fig2 = trim(im.crop((0, 476, w, h)))
    gap = 48
    nh = max(fig1.height, fig2.height)
    out = Image.new('RGB', (fig1.width + gap + fig2.width, nh), 'white')
    out.paste(fig1, (0, (nh - fig1.height) // 2))
    out.paste(fig2, (fig1.width + gap, (nh - fig2.height) // 2))
    return out


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


# ============================================================ 順6-1 コイル投入ガイド
def relabel_順6_1(im):
    d = ImageDraw.Draw(im)
    for box in [(108, 10, 402, 58), (338, 186, 442, 234),
                (338, 276, 442, 324), (278, 448, 368, 492)]:
        wbox(d, *box)
    f20 = font(20)
    plain(d, 114, 18, '(2)ノックピンで位置決め', INK, f20)
    vplain(im, 275, 230, '(3)材料幅+0.5', INK, f20)
    d = ImageDraw.Draw(im)
    plain(d, 344, 194, '〈+0.1/0〉', INK, font(18))
    plain(d, 344, 284, '〈+0.1/0〉', INK, font(18))
    plain(d, 286, 456, '〈図1〉', INK, f20)


# ============================================================ 順6-6 材料リフト
def relabel_順6_6(im):
    d = ImageDraw.Draw(im)
    for box in [(28, 18, 168, 78), (222, 14, 388, 64), (620, 28, 788, 80),
                (6, 162, 220, 216), (700, 130, 872, 198), (698, 334, 878, 394),
                (396, 436, 494, 486)]:
        wbox(d, *box)
    f20 = font(20)
    f16 = font(16)
    plain(d, 34, 26, 'FEED', INK, font(30))
    plain(d, 228, 24, '(6)テーパ加工', INK, f20)
    plain(d, 628, 38, '(4)ガイドピン', INK, f20)
    plain(d, 14, 176, '(1)ブロックガイドリフター', INK, f20)
    plain(d, 712, 154, '(4)ガイドブシュ', INK, f20)
    plain(d, 704, 350, '(5)ストリッパボルト', INK, f16)
    plain(d, 404, 446, '〈図1〉', INK, f20)


# ============================================================ 順6-8 位置決め用ブロック
def relabel_順6_8(im):
    d = ImageDraw.Draw(im)
    for box in [(85, 0, 800, 30),                # 上端の切れた赤断片
                (4, 138, 240, 200), (40, 246, 230, 302),   # 取付ボルト/ノックピン
                (110, 344, 260, 408),            # FEED
                (1140, 136, 1560, 228),          # (1)接触面…（2行・赤）
                (758, 682, 856, 716)]:           # 〈図1〉
        wbox(d, *box)
    f20 = font(20)
    f18 = font(18)
    chip(d, 14, 152, '(2)取付ボルト(1本以上)', GREEN, WHITE, f18, padx=5)
    chip(d, 48, 256, '(2)ノックピン(2本)', CYAN, NAVY, f18, padx=5)
    plain(d, 118, 356, 'FEED', INK, font(30))
    plain(d, 1150, 154, '(1)接触面は、硬度HRC45以上のこと', RED, f18)
    plain(d, 1160, 186, '（高周波焼入れ、フレムハード等）', RED, f18)
    plain(d, 768, 690, '〈図1〉', INK, f20)


# ============================================================ 順6-9 ストリップ振れ止め
def relabel_順6_9(im):
    d = ImageDraw.Draw(im)
    for box in [(184, 26, 372, 80),              # パイロット径(A)
                (948, 0, 1428, 92),              # 材料送り時の/製品端…(C) 2行・黄
                (280, 398, 326, 446), (280, 636, 326, 684),  # A / A'
                (480, 390, 772, 448),            # ガイド-製品のスキ(B)
                (548, 578, 838, 628),            # 式1
                (942, 388, 996, 574),            # C≧10mm 縦・黄
                (494, 646, 592, 694), (1064, 586, 1322, 634)]:  # 〈図1〉/〈図2〉
        wbox(d, *box)
    f20 = font(20)
    f18 = font(18)
    chip(d, 192, 40, 'パイロット径(A)', GREEN, WHITE, f18, padx=5)
    chip(d, 952, 6, '材料送り時の', YELLOW, NAVY, f18, padx=5)
    chip(d, 952, 50, '製品端からガイド上端までの高さ(C)', YELLOW, NAVY, f18, padx=5)
    plain(d, 290, 408, 'A', INK, f20)
    plain(d, 288, 646, "A'", INK, f20)
    plain(d, 490, 408, 'ガイド-製品のスキ(B)', INK, f20)
    x = chip(d, 558, 590, 'B', CYAN, NAVY, f20, padx=5)
    plain(d, x + 6, 594, '=(A/2)-1 …〈式1〉', INK, f20)
    vchip(im, 968, 480, 'C≧10mm', YELLOW, NAVY, f18, padx=5)
    d = ImageDraw.Draw(im)
    plain(d, 504, 656, '〈図1〉', INK, f20)
    plain(d, 1074, 596, "〈図2 A-A'断面〉", INK, f20)


# ============================================================ 順6-10 ストリップ引き上げ防止
def relabel_順6_10(im):
    d = ImageDraw.Draw(im)
    for box in [(88, 48, 192, 102), (366, 14, 592, 62),   # FEED/(バネで…)
                (249, 310, 302, 362), (344, 310, 397, 362),  # A/A
                (774, 100, 906, 148), (746, 382, 868, 432),  # 案内ブロック/調整シム
                (744, 412, 958, 464),            # *B寸法調整用
                (144, 558, 264, 608),            # A-A断面
                (0, 582, 172, 658),              # ワーク入口に/C5面取り
                (890, 584, 1007, 660)]:          # 案内ストッパ/B≒3.0（右下・切れ）
        wbox(d, *box)
    f20 = font(20)
    f18 = font(18)
    plain(d, 94, 56, 'FEED', INK, font(30))
    plain(d, 374, 24, '（バネで可動しても可）', INK, f18)
    plain(d, 262, 320, 'A', INK, f20)
    plain(d, 357, 320, 'A', INK, f20)
    plain(d, 784, 112, '案内ブロック', RED, f20)
    plain(d, 758, 396, '調整シム', RED, f20)
    x = plain(d, 756, 426, '＊', INK, f18)
    x = chip(d, x, 424, 'B', GREEN, WHITE, f18, padx=4)
    plain(d, x + 4, 428, '寸法調整用', INK, f18)
    plain(d, 156, 572, "A-A断面", INK, f20)
    plain(d, 4, 590, '＊ワーク入口に', RED, f18)
    plain(d, 4, 622, 'C5以上面取り', RED, f18)


FIGS = {'共C2-10': relabel_順4_7, '共C2-9': relabel_共C2_9,
        '共C2-6': relabel_共C2_6, '共C3-15': relabel_共C3_15,
        '共C3-21': relabel_共C3_21, '共C5-7': relabel_共C5_7,
        '順5-12': relabel_順5_12, '順6-1': relabel_順6_1,
        '順6-6': relabel_順6_6, '順6-8': relabel_順6_8,
        '順6-9': relabel_順6_9, '順6-10': relabel_順6_10}


def relabel_順6_5(im):
    d = ImageDraw.Draw(im)
    for box in [(143, 10, 780, 58),                             # 〈理由〉…
                (0, 80, 224, 126), (496, 60, 780, 108), (806, 60, 1064, 108),  # 3種の見出し
                (0, 294, 320, 332),                             # ミスミ&製作品…
                (603, 114, 726, 154),                           # 厚肉ワッシャ
                (416, 116, 574, 274),                           # かかり代=3mm 斜め
                (790, 114, 830, 298),                           # かかり代=2mm 縦
                (1050, 260, 1094, 300),                         # キー
                (350, 456, 454, 494), (580, 484, 750, 524), (890, 484, 1040, 524),  # 油溝/ツバ×2
                (80, 490, 164, 530), (740, 490, 824, 530), (1376, 490, 1460, 530),  # 図1/2/3
                (1483, 12, 1612, 58), (1178, 220, 1322, 274)]:  # ガイドリフター/FEED
        wbox(d, *box)
    f20 = font(20)
    f18 = font(18)
    f16 = font(16)
    plain(d, 150, 20, '〈理由〉摩耗による孔拡大防止の為', INK, f20)
    plain(d, 4, 88, '(ミスミ ガイドリフター)', INK, f16)
    plain(d, 500, 70, '(製作品ブロックガイドリフター)', INK, f16)
    plain(d, 810, 70, '(ミスミ ブロックガイドリフター)', INK, f16)
    plain(d, 4, 302, '(ミスミ&製作品 ブロックガイドリフター)', INK, f16)
    plain(d, 608, 122, '厚肉ワッシャ', INK, f20)
    rplain(im, 495, 195, 'かかり代=3mm以上', RED, f18, 48)
    vplain(im, 810, 205, 'かかり代=2mm以上', RED, f18)
    d = ImageDraw.Draw(im)
    chip(d, 236, 244, 'A', CYAN, NAVY, f20, padx=6, anchor='mm')
    chip(d, 236, 460, 'A', CYAN, NAVY, f20, padx=6, anchor='mm')
    plain(d, 1056, 266, 'キー', INK, f20)
    plain(d, 356, 462, '(2)油溝', INK, f20)
    plain(d, 586, 492, 'ワッシャ止め用ツバ', INK, f16)
    plain(d, 896, 492, 'キー止め用ツバ', INK, f16)
    plain(d, 86, 498, '〈図1〉', INK, f20)
    plain(d, 746, 498, '〈図2〉', INK, f20)
    plain(d, 1382, 498, '〈図3〉', INK, f20)
    plain(d, 1488, 20, 'ガイドリフター', INK, f16)
    plain(d, 1184, 228, 'FEED', INK, font(28))


def relabel_順6_7(im):
    d = ImageDraw.Draw(im)
    for box in [(16, 140, 130, 184), (428, 16, 518, 54),        # 段取時/部品B
                (616, 10, 985, 50),                             # ボルトを緩めて…（青・切れ）
                (18, 314, 732, 406), (740, 350, 804, 400),      # 本文2行/⚠18
                (48, 434, 602, 480), (604, 434, 968, 516),      # (1)/(2)本文
                (418, 624, 550, 670), (270, 650, 460, 724),     # 点付け溶接/合わせ部
                (670, 610, 794, 650), (634, 700, 760, 740),     # 10mm以上 ×2
                (194, 804, 284, 844)]:                          # 〈図1〉
        wbox(d, *box)
    f20 = font(20)
    f18 = font(18)
    f16 = font(16)
    plain(d, 24, 150, '段取時', INK, f20)
    plain(d, 434, 24, '部品B', INK, f20)
    plain(d, 620, 18, 'ボルトを緩めてスライドしレイアウトを取る', WHITE, f16)
    plain(d, 26, 322, '2.振れ垂れ防止のリフターバーを片側キャリアに取り付ける場合、', INK, f20)
    plain(d, 62, 362, '以下のいずれかの仕様を満たすこと〈図1〉〈図2〉', INK, f20)
    x = plain(d, 52, 444, '(1)溶接部は点付けせず、', INK, f18)
    x = plain(d, x, 444, '連続溶接', RED, f18)
    plain(d, x, 444, 'すること', INK, f18)
    plain(d, 608, 444, '(2)ボルト留めの場合10mm以上', INK, f18)
    plain(d, 658, 478, '肉厚を確保すること', INK, f18)
    plain(d, 424, 632, '点付け溶接', INK, f18)
    plain(d, 276, 658, '合わせ部を', INK, f18)
    plain(d, 276, 690, '全て連続溶接', INK, f18)
    plain(d, 676, 616, '10mm以上', RED, f18)
    plain(d, 640, 706, '10mm以上', RED, f18)
    plain(d, 200, 810, '〈図1〉', INK, f20)


FIGS['順6-5'] = relabel_順6_5
FIGS['順6-7'] = relabel_順6_7


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else None
    if key not in FIGS:
        print('対象:', ', '.join(FIGS)); return
    path = os.path.join(FIGDIR, 'hms_%s.png' % key)
    im = Image.open(path).convert('RGB')
    result = FIGS[key](im)     # 画像を返す関数（レイアウト変更）はそれを保存する
    (result if result is not None else im).save(path)
    print('書き換え:', path)


if __name__ == '__main__':
    main()
