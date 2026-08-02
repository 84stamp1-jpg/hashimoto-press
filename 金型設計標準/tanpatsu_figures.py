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


def draw_texts(im, texts):
    """最終画像へ文字を差し替え描画する。texts は dict のリスト。
      box  … (x0,y0,x1,y1) 割合。まず白で消してから中央へ描く
      text … 描く文字列
      size … フォント高さ(px)、rot … 反時計回りの回転角、color … 既定は黒
    元図(高木)の寸法数値を当社基準へ書き換える等の最小限の用途に使う。"""
    from PIL import ImageDraw, ImageFont
    w, h = im.size
    d = ImageDraw.Draw(im)
    try:
        fnt_path = r'C:\Windows\Fonts\arial.ttf'
    except Exception:
        fnt_path = None
    for t in texts:
        x0, y0, x1, y1 = t['box']
        d.rectangle([x0 * w, y0 * h, x1 * w, y1 * h], fill='white')
        font = ImageFont.truetype(fnt_path, t.get('size', 18)) if fnt_path else \
            ImageFont.load_default()
        # いったん横書きで作字→回転して貼る（縦寸法に合わせる）
        s = t['text']
        bb = d.textbbox((0, 0), s, font=font)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        tile = Image.new('RGBA', (tw + 4, th + 4), (255, 255, 255, 0))
        ImageDraw.Draw(tile).text((2 - bb[0], 2 - bb[1]), s, font=font,
                                  fill=t.get('color', (0, 0, 0)))
        rot = t.get('rot', 0)
        if rot:
            tile = tile.rotate(rot, expand=True)
        cx = int((x0 + x1) / 2 * w) - tile.width // 2
        cy = int((y0 + y1) / 2 * h) - tile.height // 2
        im.paste(tile, (cx, cy), tile)
    return im


# 図の定義。page=PDFページ番号(1始まり)、box=ページに対する割合、hide=固有情報の白塗り
FIGS = {
    # 単発 4-1 ワークのセット方向（p20 例1〜3。TPSヘッダー・フッターは範囲外）
    '単4-1': dict(page=20, box=(0.06, 0.235, 0.965, 0.895), hide=[]),
    # 単発 4-9 アテピン（p19 抜き落とし型・コンパウンド型の断面。社内規格番号は範囲外）
    # ・下部に漏れ込んだ本文行（先頭に改訂△マーク）は削除する。
    '単4-9': dict(page=19, box=(0.06, 0.475, 0.96, 0.615), hide=[],
                  hide_final=[(0.00, 0.86, 1.00, 1.00)]),
    # 単発 2-4 材料の送り方向：高木図の切り出しは廃止。当社規定（手前→奥は無し、
    #   送り装置使用時は右→左）に合わせ feed_dir_tan_2_4.py で自社線図として作図する。
    #   （このエントリを復活させると旧・高木図で上書きされるため注意）
    # 単発 3-3 ストリッパガイド設置条件（p8 断面＋×/○）
    '単3-3': dict(page=8, box=(0.05, 0.375, 0.98, 0.56), hide=[]),
    # 単発 4-6 ガイドの固定・材質（p21 ガイドブロック/ガイドピン/位置決めブロック/位置決めピン）
    '単4-6': dict(page=21, box=(0.05, 0.235, 0.96, 0.575), hide=[]),
    # 共通 C3-1 ガイドポスト（p9 下段の断面図）
    # ・上部見出しと右側「(7)20mm以上重なる事」の寸法は、本文C3-1の
    #   「ポスト径の1.5倍勘合」と矛盾するため白塗りで除去する（顧客指摘）。
    '共C3-1': dict(page=9, box=(0.05, 0.69, 0.95, 0.905), hide=[],
                  hide_final=[(0.00, 0.00, 1.00, 0.135),
                              (0.528, 0.12, 0.605, 0.83),
                              (0.510, 0.60, 0.535, 0.80)]),
    # 共通 C3-8 ストロークエンドブロック（p17 160トン以下／200トン以上のレイアウト）
    # ・A部のスキ寸法を 0.2→0.3 に是正（本文C3-8＝スキ0.3mmと整合。先頭桁のみ差替）。
    # ・右端の改訂マーク（△2・6）と断片は削除（本文にない表記）。「2±0.01」は残す。
    '共C3-8': dict(page=17, box=(0.05, 0.575, 0.95, 0.805), hide=[],
                  hide_final=[(0.855, 0.00, 1.00, 1.00),   # 右端の改訂△2・6と断片
                              (0.71, 0.918, 0.78, 0.99)],  # A部の加工記号△2（0.3は残す）
                  text_final=[dict(box=(0.752, 0.832, 0.787, 0.876),
                                   text='3', size=17, rot=90)]),
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
    # 最終画像への後処理（白塗り／数値書換）。※再トリミングは割合座標が動いて
    # 調整が不安定になるため行わない（白塗り跡の余白は残る＝autotrim後基準で固定）。
    if fig.get('hide_final'):
        im = white_boxes(im, fig['hide_final'])
    if fig.get('text_final'):
        im = draw_texts(im, fig['text_final'])
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
