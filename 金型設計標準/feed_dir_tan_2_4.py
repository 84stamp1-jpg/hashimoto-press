#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""単発編 2-4「材料の送り方向」の図を自社線図で描き直す。

規定：材料の送り方向は使用設備により異なる。手前から奥へ送ることはない。
　　　送り装置を使用する場合は、右から左へ送ることがある。

旧図（高木・単発仕様書の切り出し hms_単2-4.png）は「手前から奥」「左から右」の
2例を載せていたため、当社の規定に合わせて「右から左へ送る」1例の平面図へ描き直す。

出力: hms_単2-4.png（build_hms_docs.py の figure_for が拾う）
依存: pip install matplotlib
"""
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrow, Polygon

plt.rcParams['font.family'] = 'Meiryo'
plt.rcParams['axes.unicode_minus'] = False

INK = '#111111'
GRAY = '#8a8a8a'
STEEL = '#dde5ef'
STRIP = '#eef3f9'
LW = 2.0
LWT = 0.9


def render(out_dir):
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    ax.set_aspect('equal')
    ax.set_xlim(-20, 27)
    ax.set_ylim(-14, 15)
    ax.axis('off')

    # ダイプレート（平面）
    ax.add_patch(Rectangle((-15, -9), 30, 18, fc=STEEL, ec=INK, lw=LW))
    # ガイドポスト（四隅：ブシュ角＋ポスト丸）
    for sx in (-12.5, 12.5):
        for sy in (-6.5, 6.5):
            ax.add_patch(Rectangle((sx - 1.4, sy - 1.4), 2.8, 2.8,
                                   fc='white', ec=INK, lw=LWT))
            ax.add_patch(Circle((sx, sy), 1.0, fc='white', ec=INK, lw=LWT))
    # クランプ耳（上下中央）
    for sy, dy in ((9, 1.6), (-9, -1.6)):
        ax.add_patch(Rectangle((-3, sy), 6, dy, fc=STEEL, ec=INK, lw=LWT))

    # 材料ストリップ（右から入り、左へ抜ける。右端はプレート外へ延ばす）
    ax.add_patch(Rectangle((-15, -2.6), 39, 5.2, fc=STRIP, ec=INK, lw=LWT))
    ax.plot([-15, 24], [0, 0], color=GRAY, lw=LWT, dashes=(5, 4))  # 中心線
    # 製品（抜き形状）の例を2つ、ダイ内に配置
    for cx in (-6.5, 3.0):
        ax.add_patch(Polygon([(cx - 3, -1.6), (cx + 3, -1.6), (cx + 3.8, 0),
                              (cx + 3, 1.6), (cx - 3, 1.6), (cx - 3.8, 0)],
                             closed=True, fc='white', ec=INK, lw=LWT))
        ax.add_patch(Circle((cx, 0), 0.55, fc='white', ec=INK, lw=LWT))

    # 送り方向の矢印（右→左）
    ax.add_patch(FancyArrow(9, -5.2, -17, 0, width=1.1, head_width=3.0,
                            head_length=2.6, length_includes_head=True,
                            fc=INK, ec=INK))
    ax.text(2, -7.7, '送り方向（右→左）', fontsize=12, color=INK,
            ha='center', va='center')

    # 材料ラベル（右側から引き出し）
    ax.annotate('材料', xy=(20, 1.3), xytext=(22.5, 6.5), fontsize=12,
                color=INK, ha='left', va='center',
                arrowprops=dict(arrowstyle='-', color=INK, lw=LWT))

    # 見出し
    ax.text(0, 13.4, '右から左へ材料を送る（送り装置を使用する場合）',
            fontsize=13, color=INK, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.4', fc='#eef3f9', ec=INK, lw=1.0))

    fig.tight_layout()
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, 'hms_単2-4.png')
    fig.savefig(p, dpi=175, facecolor='white')
    plt.close(fig)
    return p


if __name__ == '__main__':
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser('~'), 'Desktop', '橋本_作業データ', '金型仕様書', 'HMS図')
    print('作成:', render(outdir))
