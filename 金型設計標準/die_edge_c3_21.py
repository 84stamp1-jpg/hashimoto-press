#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""共通編 C3-21「ダイの刃先形状・逃がし」の図を自社線図で描き直す。

高木スライドの切り出し（旧 hms_共C3-21.png）は色線と注記文字が焼き込まれて
重なっていたため、自社の線図として描き直す（社外へ他社ラスタを出さない方針）。
規定内容：
  ・刃先はプレスに直角（軟材）。590N/mm²以上・ステンレスは刃長部に5'〜7'の勾配。
  ・刃先の下に逃がし勾配か座ぐりを施す。ただし底面の肉がなくならぬよう注意。
  ・座ぐりの場合、オフセット量は1mm以内。

出力: hms_共C3-21.png（build_hms_docs.py の figure_for が拾う）
依存: pip install matplotlib
"""
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Arc

plt.rcParams['font.family'] = 'Meiryo'
plt.rcParams['axes.unicode_minus'] = False

INK = '#111111'
BLUE = '#1d4ed8'
RED = '#c00000'
GREEN = '#217a3b'
GRAY = '#8a8a8a'
STEEL = '#d7dee8'
LW = 2.2
LWT = 0.9

TOP = 6.0        # 刃先上面（材料側）
BOT = -16.0      # ダイ下面（スクラップ側）
LAND = 3.0       # 刃先ストレート下端の y（＝刃先長さ 3mm）


def _base(ax):
    ax.set_aspect('equal')
    ax.set_xlim(-16, 40)
    ax.set_ylim(-22, 12)
    ax.axis('off')


def _notes(ax, items):
    """右側に色対応の注記を積む（引き出し線は使わず、図中の色線と色で対応させる）。
    items = [(color, [行, ...]), ...] を上から順に配置する。"""
    x_sw, x_tx = 25.0, 27.5
    y = TOP + 0.5
    for color, lines in items:
        ax.plot([x_sw, x_sw], [y - 0.9, y + 0.9], color=color, lw=5)  # 色スウォッチ
        for i, s in enumerate(lines):
            ax.text(x_tx, y - i * 2.3, s, fontsize=10.5, color=color,
                    ha='left', va='center')
        y -= max(len(lines), 1) * 2.3 + 2.4


def _land_dim(ax, x):
    ax.annotate('', xy=(x, TOP), xytext=(x, LAND),
                arrowprops=dict(arrowstyle='<->', color=GRAY, lw=LWT))
    ax.text(x - 0.8, (TOP + LAND) / 2, '刃先長さ\n7mm', fontsize=9.5,
            color='#333', ha='right', va='center')


def _block(ax, left_pts):
    """ダイ断面を薄い輪郭で塗る。left_pts は刃先側（左壁）の点列。"""
    pts = left_pts + [(22, BOT), (22, TOP)]
    ax.add_patch(Polygon(pts, closed=True, fc=STEEL, ec=GRAY, lw=LWT))
    ax.plot([left_pts[0][0], 22], [TOP, TOP], color=INK, lw=LWT)  # 材料上面


def fig_soft(ax):
    """図1：引張り強さ590N/mm²未満の鋼材（刃先はプレス直角）"""
    _base(ax)
    relief_x = 4.0
    _block(ax, [(0, TOP), (0, LAND), (relief_x, BOT)])
    ax.plot([0, 0], [TOP, LAND], color=BLUE, lw=5)           # 刃先ストレート
    ax.plot([0, relief_x], [LAND, BOT], color=RED, lw=4)     # 逃がし勾配
    ax.plot([-0.9, 0.9], [LAND, LAND], color=GREEN, lw=5)    # 底面（刃先下端）
    _land_dim(ax, -3.5)
    _notes(ax, [(BLUE, ['(1) 刃先はプレスに直角']),
                (RED, ['(3) 逃がし勾配か', '　　座ぐりを施す事']),
                (GREEN, ['(3) 底面の肉が', '　　なくならぬよう注意'])])
    ax.text(11, BOT - 3.2, '引張り強さ590N/mm²未満の鋼材',
            fontsize=10.5, color=INK, ha='center', va='top')


def fig_hard(ax):
    """図2：引張り強さ590N/mm²以上及びステンレス（刃長部に5'〜7'の勾配）"""
    _base(ax)
    relief_x = 4.2
    taper = 0.9       # 刃長部の勾配（誇張）
    _block(ax, [(0, TOP), (taper, LAND), (relief_x, BOT)])
    ax.plot([0, taper], [TOP, LAND], color=BLUE, lw=5)         # 刃長部の勾配
    ax.plot([taper, relief_x], [LAND, BOT], color=RED, lw=4)   # 逃がし勾配
    ax.plot([taper - 0.9, taper + 0.9], [LAND, LAND], color=GREEN, lw=5)
    # 勾配を示す補助（垂直基準線＋角記号）
    ax.plot([0, 0], [TOP, LAND - 0.5], color=GRAY, lw=LWT, dashes=(4, 3))
    ax.add_patch(Arc((0, TOP), 5, 5, theta1=291, theta2=306, color=GRAY, lw=LWT))
    _land_dim(ax, -3.5)
    _notes(ax, [(BLUE, ["(2) 5'〜7'の勾配", '　　（刃長部位）']),
                (RED, ['(3) 逃がし勾配か', '　　座ぐりを施す事']),
                (GREEN, ['(3) 底面の肉が', '　　なくならぬよう注意'])])
    ax.text(11, BOT - 3.2, '590N/mm²以上及びステンレスの鋼材',
            fontsize=10.5, color=INK, ha='center', va='top')


def fig_counterbore(ax):
    """図3：座ぐりの場合（オフセット量≦1mm）"""
    _base(ax)
    off = 1.5         # オフセット量（誇張）。規定は≦1mm
    sbot = 0.0
    _block(ax, [(0, TOP), (0, sbot), (off, sbot), (off, BOT)])
    ax.plot([0, 0], [TOP, LAND], color=BLUE, lw=5)              # 刃先ストレート
    ax.plot([0, 0], [LAND, sbot], color=INK, lw=LW)            # ストレート継続
    ax.plot([0, off], [sbot, sbot], color=GREEN, lw=5)         # 座ぐり段
    ax.plot([off, off], [sbot, BOT], color=INK, lw=LW)
    ax.annotate('', xy=(0, sbot - 1.6), xytext=(off, sbot - 1.6),
                arrowprops=dict(arrowstyle='<->', color=GREEN, lw=LWT))
    ax.text(off / 2, sbot - 2.6, '≦1mm', fontsize=9.5, color=GREEN,
            ha='center', va='top')
    _land_dim(ax, -3.5)
    _notes(ax, [(BLUE, ['(1) 刃先はプレスに直角']),
                (GREEN, ['(3) 座ぐりの', '　　オフセット量 ≦1mm'])])
    ax.text(11, BOT - 3.2, '座ぐりの場合', fontsize=10.5,
            color=INK, ha='center', va='top')


def render(out_dir):
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.3))
    for ax, fn in zip(axes, (fig_soft, fig_hard, fig_counterbore)):
        fn(ax)
    # パネル間の仕切り線
    for xx in (0.353, 0.66):
        fig.add_artist(plt.Line2D([xx, xx], [0.08, 0.92], color=GRAY,
                                  lw=1.0, dashes=(6, 4), transform=fig.transFigure))
    fig.suptitle('ダイの刃先形状・逃がし', fontsize=13, fontweight='bold',
                 color=INK, y=0.98)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, 'hms_共C3-21.png')
    fig.savefig(p, dpi=170, facecolor='white')
    plt.close(fig)
    return p


if __name__ == '__main__':
    outdir = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\Owner\Desktop\金型仕様書\HMS図'
    print('作成:', render(outdir))
