#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""高木・単発ダイセット金型仕様書(67-025-02.xls)から、HMS用の図を切り出す

社内限定で使用する(正式に受領した資料。順送と同じ扱い)。
xls を Excel COM で PDF 化し(キャッシュ)、各ページの図の領域を切り出す。
TPSヘッダー・高木製作所フッター・改定欄・品番等の固有情報は切り出し範囲から外す。
ラベルはExcel由来で全角のためフォント打ち直しは基本不要（必要な図のみ relabel_figures.py で対応）。

使い方: python tanpatsu_figures.py 単4-1
依存: pip install pymupdf pillow ／ Excel(COM) は PDF 化の初回のみ
"""
import os
import sys

import fitz
from PIL import Image, ImageOps

SRC_XLS = r'C:\Users\Owner\Desktop\金型仕様書\資料\【67-025-02】単発ダイセット金型仕様書 .xls'
PDF = os.path.join(os.environ.get('LOCALAPPDATA', ''), r'Temp\claude\tanpatsu_単発仕様書.pdf')
OUT = r'C:\Users\Owner\Desktop\金型仕様書\HMS図'


def ensure_pdf():
    if os.path.exists(PDF):
        return
    os.makedirs(os.path.dirname(PDF), exist_ok=True)
    import win32com.client as w
    xl = w.Dispatch('Excel.Application')
    xl.Visible = False
    xl.DisplayAlerts = False
    wb = xl.Workbooks.Open(SRC_XLS, 0, True)
    wb.ExportAsFixedFormat(0, PDF)
    wb.Close(False)
    xl.Quit()


def whiten(im, thr=205, keep_sat=32):
    """薄いグレー(ロゴ・透かし)を白へ。色線・黒線は残す。"""
    im = im.convert('RGB')
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if max(r, g, b) - min(r, g, b) < keep_sat and min(r, g, b) > thr:
                px[x, y] = (255, 255, 255)
    return im


def autotrim(im, border=14, bg=250):
    g = im.convert('L').point(lambda p: 0 if p >= bg else 255)
    bbox = g.getbbox()
    if bbox:
        im = im.crop(bbox)
    return ImageOps.expand(im, border=border, fill='white')


def white_boxes(im, boxes):
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    w, h = im.size
    for (x0, y0, x1, y1) in boxes:
        d.rectangle([x0 * w, y0 * h, x1 * w, y1 * h], fill='white')
    return im


# 図の定義。page=PDFページ番号(1始まり)、box=ページに対する割合、hide=固有情報の白塗り
FIGS = {
    # 単発 4-1 ワークのセット方向（p20 例1〜3。TPSヘッダー・フッターは範囲外）
    '単4-1': dict(page=20, box=(0.06, 0.235, 0.965, 0.895), hide=[]),
}


def build(key, dpi=2.4):
    ensure_pdf()
    fig = FIGS[key]
    d = fitz.open(PDF)
    pg = d[fig['page'] - 1]
    pm = pg.get_pixmap(matrix=fitz.Matrix(dpi, dpi))
    im = Image.frombytes('RGB', (pm.width, pm.height), pm.samples)
    w, h = im.size
    x0, y0, x1, y1 = fig['box']
    im = im.crop((int(w * x0), int(h * y0), int(w * x1), int(h * y1)))
    if fig.get('hide'):
        im = white_boxes(im, fig['hide'])
    im = whiten(im)
    im = autotrim(im)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'hms_%s.png' % key)
    im.save(path)
    print('図:', path)


if __name__ == '__main__':
    key = sys.argv[1] if len(sys.argv) > 1 else None
    if key not in FIGS:
        print('対象:', ', '.join(FIGS))
    else:
        build(key)
