#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ラップ形状パターン A〜H の参考図（手書き加筆用のたたき台）

もとは客先の変更依頼書に手書きされていた8パターン。スキャンのままでは
標準に貼れない（客先の車種・品番・承認印が入っているため）ので、
形状と寸法だけを取り出して描き直す。

いまの図は原図から読み取った推測にすぎない。印刷して手書きで直してもらい、
それを見て描き直す前提のもの。書き込めるよう各図の右側を空けてある。

出力:
    lap_patterns.png / .pdf   8パターンを1枚に（PDFはA3縦・印刷用）
    lap_A.png 〜 lap_H.png    1パターンずつ

依存: pip install matplotlib
"""
import math
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Arc

plt.rcParams['font.family'] = 'Meiryo'
plt.rcParams['axes.unicode_minus'] = False

LW = 2.0
LW_THIN = 0.9
GRAY = '#888888'
BLUE = '#1d4ed8'
RED = '#c00000'


# ---------------------------------------------------------------- 作図の道具
def fillet_path(pts, radii, rscale=0.32):
    """折れ線の角をRで丸めた輪郭を返す。
    radii は呼びR（R8など）。そのままだと図が見づらいので rscale で縮めて描く。"""
    out = [pts[0]]
    labels = []
    for i in range(1, len(pts) - 1):
        p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
        v1 = (p0[0] - p1[0], p0[1] - p1[1])
        v2 = (p2[0] - p1[0], p2[1] - p1[1])
        l1 = math.hypot(*v1) or 1e-9
        l2 = math.hypot(*v2) or 1e-9
        u1 = (v1[0] / l1, v1[1] / l1)
        u2 = (v2[0] / l2, v2[1] / l2)
        ang = math.acos(max(-1, min(1, u1[0] * u2[0] + u1[1] * u2[1])))
        r = radii[i - 1] * rscale
        if ang < 1e-6 or abs(ang - math.pi) < 1e-6:
            out.append(p1)
            continue
        t = min(r / math.tan(ang / 2), l1 * 0.9, l2 * 0.9)
        a = (p1[0] + u1[0] * t, p1[1] + u1[1] * t)
        b = (p1[0] + u2[0] * t, p1[1] + u2[1] * t)
        out.append(a)
        for k in range(1, 13):
            s = k / 13.0
            out.append(((1 - s) ** 2 * a[0] + 2 * (1 - s) * s * p1[0] + s ** 2 * b[0],
                        (1 - s) ** 2 * a[1] + 2 * (1 - s) * s * p1[1] + s ** 2 * b[1]))
        out.append(b)
        bis = (u1[0] + u2[0], u1[1] + u2[1])
        bl = math.hypot(*bis) or 1e-9
        labels.append((p1[0] + bis[0] / bl * (r + 1.3), p1[1] + bis[1] / bl * (r + 1.3)))
    out.append(pts[-1])
    return out, labels


def draw(ax, pts, radii=None, rlabels=None, rscale=0.32, color='#111111'):
    path, lp = fillet_path(pts, radii, rscale) if radii else (pts, [])
    ax.plot([p[0] for p in path], [p[1] for p in path], '-',
            color=color, lw=LW, solid_capstyle='round')
    if rlabels:
        for (x, y), txt in zip(lp, rlabels):
            ax.text(x, y, txt, fontsize=10, color=BLUE, ha='center', va='center',
                    bbox=dict(fc='white', ec='none', pad=0.6))


def datum(ax, x, y0, y1):
    ax.plot([x, x], [y0, y1], '-', color=GRAY, lw=LW_THIN, dashes=(7, 4))


def vdim(ax, x, y0, y1, txt):
    ax.annotate('', xy=(x, y0), xytext=(x, y1),
                arrowprops=dict(arrowstyle='<->', color=GRAY, lw=LW_THIN))
    ax.text(x - 0.5, (y0 + y1) / 2, txt, fontsize=10, color='#333333',
            ha='right', va='center')


def angle(ax, cx, cy, a0, a1, r, txt):
    ax.add_patch(Arc((cx, cy), r * 2, r * 2, theta1=a0, theta2=a1,
                     color=GRAY, lw=LW_THIN))
    m = math.radians((a0 + a1) / 2)
    ax.text(cx + math.cos(m) * (r + 1.4), cy + math.sin(m) * (r + 1.4), txt,
            fontsize=10, color='#333333', ha='center', va='center')


def pinkaku(ax, x, y, dx=3.2, dy=2.6, ha='left'):
    ax.plot([x], [y], 'o', ms=7, mfc='none', mec=RED, mew=1.6)
    ax.annotate('ピン角', xy=(x, y), xytext=(x + dx, y + dy), fontsize=10,
                color=RED, ha=ha, va='center',
                arrowprops=dict(arrowstyle='-', color=RED, lw=LW_THIN))


# ---------------------------------------------------------------- 各パターン
def p_A(ax):
    draw(ax, [(-11, 8), (-3, 8), (3, 0), (3, -8)], [10, 8], ['R10', 'R8'])
    datum(ax, 3, -9, 9)


def p_B(ax):
    draw(ax, [(-11, 8), (-3, 8), (3, 0), (3, -8)], [5, 3], ['R5', 'R3'])
    datum(ax, 3, -9, 9)
    ax.text(6.5, 4, '±0.5', fontsize=10, color='#333333', ha='left')


def _CD(ax, r_small, lbl):
    draw(ax, [(-12, -6), (-6, -6), (-6, 4), (0, 4), (0, -6), (9, -6)],
         [20, r_small, r_small, 20], ['R20', lbl, lbl, 'R20'], rscale=0.14)
    vdim(ax, -13.5, -6, 4, '8')
    vdim(ax, 11, -6, -1, '5')
    datum(ax, -3, -8, 7)


def p_C(ax):
    _CD(ax, 3, 'R3')


def p_D(ax):
    _CD(ax, 5, 'R5')


def p_E(ax):
    draw(ax, [(-11, 7), (0, 0), (11, 7)], [3], ['R3'])
    draw(ax, [(0, 0), (0, -9)])
    datum(ax, 0, -9, 8)


def p_F(ax):
    draw(ax, [(-11, 7), (0, 0), (11, 7)])
    draw(ax, [(0, 0), (0, -9)])
    pinkaku(ax, 0, 0, dx=5.0, dy=-2.6)
    datum(ax, 0, -9, 8)


def p_G(ax):
    a = math.radians(45)
    draw(ax, [(-11, -1), (0, -1), (math.cos(a) * 13, -1 + math.sin(a) * 13)], [3], ['R3'])
    pinkaku(ax, 0, -1, dx=-2.5, dy=-4.5, ha='right')
    angle(ax, 0, -1, 0, 45, 7.0, '45°')
    datum(ax, 0, -7, 11)


def p_H(ax):
    a = math.radians(30)
    draw(ax, [(-11, -1), (0, -1), (math.cos(a) * 13, -1 + math.sin(a) * 13)])
    pinkaku(ax, 0, -1, dx=-2.5, dy=-4.5, ha='right')
    angle(ax, 0, -1, 0, 30, 7.0, '30°')
    datum(ax, 0, -7, 11)


T2_6 = '板厚2.6以上は2mm'
PATS = [
    ('A', p_A, 'R10 → R8'),
    ('B', p_B, 'R5 → R3、±0.5'),
    ('C', p_C, 'R20 / R3、' + T2_6),
    ('D', p_D, 'R20 / R5、' + T2_6),
    ('E', p_E, 'R3、' + T2_6),
    ('F', p_F, 'ピン角（Rなし）'),
    ('G', p_G, 'R3、45°、ピン角'),
    ('H', p_H, '30°、ピン角'),
]


def setup(ax, key, dims):
    ax.set_aspect('equal')
    # 右側は手書きで書き込めるよう広めに空ける
    ax.set_xlim(-17, 27)
    ax.set_ylim(-12, 13)
    ax.axis('off')
    ax.text(-16.5, 12, key, fontsize=13, fontweight='bold', va='top', color='#111111')
    ax.text(-16.5, -11.3, dims, fontsize=9.5, color='#444444', va='bottom')


def render(outdir):
    fig, axes = plt.subplots(4, 2, figsize=(11.7, 16.5))   # A3縦
    lookup = {k: (fn, d) for k, fn, d in PATS}
    for key, r, c in [('A', 0, 0), ('B', 0, 1), ('C', 1, 0), ('D', 1, 1),
                      ('E', 2, 0), ('F', 2, 1), ('G', 3, 0), ('H', 3, 1)]:
        fn, dims = lookup[key]
        ax = axes[r][c]
        fn(ax)
        setup(ax, key, dims)
    fig.suptitle('ラップ形状パターン（加筆用）', fontsize=15, fontweight='bold', y=0.978)
    fig.text(0.5, 0.952,
             '原図から読み取った推測です。違うところを直接書き込んでください。',
             fontsize=10, color='#666666', ha='center')
    fig.tight_layout(rect=[0, 0.005, 1, 0.943])
    png = os.path.join(outdir, 'lap_patterns.png')
    fig.savefig(png, dpi=170, facecolor='white')
    fig.savefig(os.path.join(outdir, 'lap_patterns.pdf'), facecolor='white')
    plt.close(fig)

    for key, fn, dims in PATS:
        f, ax = plt.subplots(figsize=(5.0, 3.4))
        fn(ax)
        setup(ax, key, dims)
        f.tight_layout()
        f.savefig(os.path.join(outdir, 'lap_%s.png' % key), dpi=170, facecolor='white')
        plt.close(f)
    return png


if __name__ == '__main__':
    outdir = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(outdir, exist_ok=True)
    print('作成:', render(outdir))
