#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HMS金型設計標準に載せる図を、自社の線図として描く

他社（高木）資料の写真は「どんな形状か」を読み取る参考にとどめ、
ここで自社の図として作図し直す。成果物には自社の線図だけを載せる
（他社の機密・個人情報を外注先へ再配布しないため）。

図は規定文に一対一で対応させる。関数名の末尾が対応する項目番号。

出力: 各図の PNG（既定は Desktop\金型仕様書\HMS図）
依存: pip install matplotlib
"""
import math
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, FancyArrowPatch, Polygon

plt.rcParams['font.family'] = 'Meiryo'
plt.rcParams['axes.unicode_minus'] = False

INK = '#111111'
BLUE = '#1d4ed8'
RED = '#c00000'
GRAY = '#8a8a8a'
STEEL = '#c9d3e0'      # 部品の塗り
STEEL2 = '#dde5ef'
LW = 2.0
LW_THIN = 0.9


def _base(ax, xl, yl):
    ax.set_aspect('equal')
    ax.set_xlim(*xl)
    ax.set_ylim(*yl)
    ax.axis('off')


def _dim_v(ax, x, y0, y1, txt, side='left', color=GRAY):
    ax.annotate('', xy=(x, y0), xytext=(x, y1),
                arrowprops=dict(arrowstyle='<->', color=color, lw=LW_THIN))
    dx = -1.0 if side == 'left' else 1.0
    ax.text(x + dx, (y0 + y1) / 2, txt, fontsize=10, color='#333',
            ha=('right' if side == 'left' else 'left'), va='center')


def _dim_h(ax, x0, x1, y, txt, color=GRAY, dy=1.2):
    ax.annotate('', xy=(x0, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle='<->', color=color, lw=LW_THIN))
    ax.text((x0 + x1) / 2, y + dy, txt, fontsize=10, color='#333',
            ha='center', va='bottom')


def _note(ax, x, y, txt, color=RED, ha='left'):
    ax.text(x, y, txt, fontsize=9.5, color=color, ha=ha, va='center')


def _title(ax, txt):
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    ax.text(x0, y1, txt, fontsize=12, fontweight='bold', va='top', color=INK)


# ================================================================ 図
def fig_clearance(ax):
    """クリアランスとせん断面／破断面（C5-5・クリアランス基準）"""
    _base(ax, (-16, 16), (-13, 11))
    _title(ax, 'クリアランスとせん断面')
    t = 6.0                       # 板厚
    c = 2.2                       # 片側クリアランス（誇張）
    # 材料（板）
    ax.add_patch(Polygon([(-15, 0), (0, 0), (0, t), (-15, t)],
                         closed=True, fc=STEEL2, ec=INK, lw=LW))
    # パンチ（上・可動）
    px = 0
    ax.add_patch(Polygon([(px, t + 1.5), (px, t + 9), (px - 7, t + 9), (px - 7, t + 1.5)],
                         closed=True, fc=STEEL, ec=INK, lw=LW))
    _note(ax, px - 3.5, t + 5.2, 'パンチ', color=INK, ha='center')
    # ダイ（下・固定、クリアランス分だけ離す）
    dx = px + c
    ax.add_patch(Polygon([(dx, 0), (dx, -9), (dx + 8, -9), (dx + 8, 0)],
                         closed=True, fc=STEEL, ec=INK, lw=LW))
    ax.add_patch(Polygon([(-15, 0), (dx, 0), (dx, -9), (-15, -9)],
                         closed=True, fc=STEEL, ec=INK, lw=LW))
    _note(ax, -7, -4.5, 'ダイ', color=INK, ha='center')
    # クリアランス寸法
    _dim_h(ax, px, dx, t + 10.5, 'c', color=RED, dy=0.6)
    _note(ax, (px + dx) / 2, t + 12.4, '片側クリアランス c ＝ 板厚t × 率(%)',
          color=RED, ha='center')
    _dim_v(ax, -15.8, 0, t, 't', side='left')
    # せん断面・破断面の帯（切口）
    ax.plot([0, c], [t, 0], color=RED, lw=2.4)
    _note(ax, 3.0, t - 1.0, 'せん断面', color=RED)
    _note(ax, 3.0, 1.2, '破断面（だれ・バリ）', color=RED)


def fig_die_edge_5_1(ax):
    """ダイの刃先形状：刃先長さ（ストレート）と勾配（順送5-1）"""
    _base(ax, (-13, 15), (-16, 10))
    _title(ax, 'ダイの刃先形状（ストレート＋勾配）')
    # ダイ断面（右側が肉、左に穴）
    top = 6
    edge = 3.0        # 刃先ストレート長さ
    ax.add_patch(Polygon([(0, top), (12, top), (12, -14), (0, -14)],
                         closed=True, fc=STEEL, ec=INK, lw=LW))
    # 刃先ストレート部（垂直）と、その下の逃がし勾配
    ax.plot([0, 0], [top, top - edge], color=RED, lw=3)      # ストレート
    ax.plot([0, -4.5], [top - edge, -14], color=BLUE, lw=2)  # 勾配（逃がし）
    _dim_v(ax, -6.5, top - edge, top, '刃先長さ\n3mm', side='left')
    # 勾配角
    ax.plot([0, 0], [top - edge, -14], color=GRAY, lw=LW_THIN, dashes=(4, 3))
    ax.add_patch(Arc((0, top - edge), 9, 9, theta1=250, theta2=270,
                     color=GRAY, lw=LW_THIN))
    _note(ax, -3.0, top - edge - 6, "5'〜7'\n（硬材）", color=BLUE)
    # 材料と製品
    ax.add_patch(Polygon([(0, top), (14, top), (14, top + 2.2), (0, top + 2.2)],
                         closed=True, fc=STEEL2, ec=INK, lw=1.2))
    _note(ax, 7, top + 1.1, '材料', color=INK, ha='center')
    _note(ax, 6, -8, 'ダイ', color=INK, ha='center')
    _note(ax, -9.5, -12, 'スクラップ\n落下', color=GRAY, ha='center')


def fig_die_relief_5_2(ax):
    """ダイの逃がし：座ぐりオフセット量は1mm以内（順送5-2）"""
    _base(ax, (-14, 14), (-15, 11))
    _title(ax, 'ダイの逃がし（座ぐりオフセット）')
    top = 7
    ax.add_patch(Polygon([(-12, top), (12, top), (12, -13), (-12, -13)],
                         closed=True, fc=STEEL, ec=INK, lw=LW))
    # 刃先の穴（垂直ストレート）→ 座ぐり（広い）
    hw = 3.0       # 刃先半幅
    off = 1.2      # オフセット量（下げてから広げる）
    bw = 6.0       # 座ぐり半幅
    for s in (-1, 1):
        ax.add_patch(Polygon([(s * hw, top), (s * hw, top - off),
                              (s * bw, top - off), (s * bw, -13),
                              (s * (bw + 6), -13), (s * (bw + 6), top),
                              (s * (hw + 6), top)],
                             closed=True, fc='white', ec='none'))
        ax.plot([s * hw, s * hw, s * bw, s * bw],
                [top, top - off, top - off, -13], color=INK, lw=LW)
    ax.plot([-hw, hw], [top, top], color='white', lw=LW + 1)   # 穴の口
    _note(ax, 0, top + 1.6, '刃先（ストレート）', color=RED, ha='center')
    ax.plot([-hw, hw], [top, top], color=RED, lw=3)
    _dim_v(ax, hw + 0.4, top - off, top, '', side='right')
    _note(ax, hw + 1.0, top - off / 2, 'オフセット量 ≦1mm', color=RED)
    _note(ax, 8, -6, 'ダイ', color=INK, ha='center')
    _note(ax, 0, -10, '座ぐり（スクラップ逃がし）', color=GRAY, ha='center')


FIGS = [
    ('clearance', fig_clearance, 'クリアランスとせん断面'),
    ('die_edge_5_1', fig_die_edge_5_1, 'ダイの刃先形状'),
    ('die_relief_5_2', fig_die_relief_5_2, 'ダイの逃がし'),
]


def render(outdir, combined=True):
    os.makedirs(outdir, exist_ok=True)
    for key, fn, _ in FIGS:
        f, ax = plt.subplots(figsize=(4.6, 3.6))
        fn(ax)
        f.tight_layout()
        f.savefig(os.path.join(outdir, 'fig_%s.png' % key), dpi=170, facecolor='white')
        plt.close(f)
    if combined:
        fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
        for ax, (key, fn, _) in zip(axes, FIGS):
            fn(ax)
        fig.tight_layout()
        p = os.path.join(outdir, 'fig_sample3.png')
        fig.savefig(p, dpi=150, facecolor='white')
        plt.close(fig)
        return p


if __name__ == '__main__':
    outdir = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\Owner\Desktop\金型仕様書\HMS図'
    print('作成:', render(outdir))
