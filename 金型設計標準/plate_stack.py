#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""順送 2-1「金型各プレートの名称」用の図を描く

規定文がプレート名を上から順に列挙しているだけで形がつかめないため、
各プレートを1枚ずつ名前付きで積層した断面図を描く。
（特定の金型の写しではなく、名称を示すための一般的な構成図）

出力: Desktop/金型仕様書/HMS図/hms_順2-1.png（貼り込み先の項目に合わせた名前）
依存: pip install matplotlib
"""
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

plt.rcParams['font.family'] = 'Meiryo'

INK = '#111111'
STEEL = '#d7deea'
STEEL_D = '#c2cad9'      # ダイ・切刃系は少し濃く
MAT = '#f6d68a'          # 材料
NAVY = '#1f3864'

# (名称, 高さ, 塗り)。上から順。None は 上型／下型の境（材料）
PLATES_UPPER = [
    ('上型ホルダ', 1.5, STEEL),
    ('上型スペーサ', 0.7, STEEL),
    ('上型バッキングプレート', 0.6, STEEL),
    ('パンチプレート', 1.1, STEEL),
    ('ストリッパバッキングプレート', 0.6, STEEL),
    ('ストリッパプレート', 1.1, STEEL_D),
]
PLATES_LOWER = [
    ('ダイプレート', 1.3, STEEL_D),
    ('下型バッキングプレート', 0.6, STEEL),
    ('下型スペーサ', 0.7, STEEL),
    ('下型ホルダ', 1.5, STEEL),
    ('取付位置決めプレート', 0.5, STEEL),
    ('ライナー', 0.4, STEEL),
]

W = 6.0        # プレート幅
X0 = 0.0
GAP = 0.55     # 上型と下型の間（材料の通り道）


def draw(ax):
    y = 0.0
    rows = []
    # 下から積むため、全体高さを先に計算して上から配置
    total = sum(h for _, h, _ in PLATES_LOWER) + GAP + \
        sum(h for _, h, _ in PLATES_UPPER)
    ytop = total
    y = ytop
    for name, h, fc in PLATES_UPPER:
        y -= h
        rows.append((name, y, h, fc))
    # 材料（薄板）を境に描く
    ymat = y - GAP / 2
    y -= GAP
    for name, h, fc in PLATES_LOWER:
        y -= h
        rows.append((name, y, h, fc))

    for name, yy, h, fc in rows:
        ax.add_patch(Rectangle((X0, yy), W, h, facecolor=fc, edgecolor=INK, lw=1.6))
        # 引出線＋名称（右側）
        ax.annotate(name, xy=(X0 + W, yy + h / 2),
                    xytext=(X0 + W + 1.2, yy + h / 2),
                    fontsize=11, va='center', ha='left', color=INK,
                    arrowprops=dict(arrowstyle='-', color='#888', lw=0.8))

    # 材料（ストリップ）
    ax.add_patch(Rectangle((X0 - 1.0, ymat - 0.14), W + 1.6, 0.28,
                           facecolor=MAT, edgecolor=INK, lw=1.2, zorder=5))
    ax.annotate('材料（ストリップ）', xy=(X0 + W + 0.6, ymat),
                xytext=(X0 + W + 1.2, ymat), fontsize=11, va='center', ha='left',
                color='#8a6d1a',
                arrowprops=dict(arrowstyle='-', color='#b08a20', lw=0.8))

    # 上型／下型の大かっこ（左側）
    def brace(y0, y1, label):
        x = X0 - 0.55
        ax.plot([x, x - 0.35, x - 0.35, x], [y0, y0, y1, y1], color=NAVY, lw=1.6)
        ax.text(x - 0.7, (y0 + y1) / 2, label, rotation=90, fontsize=13,
                fontweight='bold', va='center', ha='center', color=NAVY)
    up_bot = rows[5][1]                 # ストリッパプレート下端
    up_top = rows[0][1] + rows[0][2]    # 上型ホルダ上端
    brace(up_bot, up_top, '上型')
    lo_top = rows[6][1] + rows[6][2]    # ダイプレート上端
    lo_bot = rows[-1][1]                # ライナー下端
    brace(lo_bot, lo_top, '下型')

    ax.set_xlim(X0 - 2.2, X0 + W + 8.5)
    ax.set_ylim(-0.6, ytop + 0.6)
    ax.set_aspect('auto')
    ax.axis('off')


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\Owner\Desktop\金型仕様書\HMS図'
    os.makedirs(outdir, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.2, 6.4))
    draw(ax)
    fig.tight_layout()
    path = os.path.join(outdir, 'hms_順2-1.png')
    fig.savefig(path, dpi=170, facecolor='white')
    plt.close(fig)
    print('作成:', path)


if __name__ == '__main__':
    main()
