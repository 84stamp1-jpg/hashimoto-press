#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""他社仕様書から図を取り出す（HMS作成の作図参考用）

2つの方法で取り出す:
  slides … スライドを1枚ずつ画像化する（図と寸法線・説明が揃った状態で見られる）
  media  … 埋め込み画像を個別に取り出す（図だけが欲しいとき）

⚠️ 取り出した図の扱い
  元資料は他社の「関係者外秘」文書。**そのまま自社標準へ貼り付けない。**
  形状・寸法の考え方を読み取り、自社の図として作図し直すための参考とする。
  取り出したファイルは作業用フォルダに置き、共有フォルダやリポジトリへ置かない。

使い方:
    python extract_figures.py slides 仕様書.pptx 出力先フォルダ [--dpi 150]
    python extract_figures.py media  仕様書.pptx 出力先フォルダ [--min-kb 20]

依存: slides は PyMuPDF＋LibreOffice、media は標準ライブラリのみ
"""
import os
import re
import shutil
import subprocess
import sys
import zipfile
from xml.dom import minidom


def slide_image_map(pptx):
    """スライド番号 → [画像ファイル名] の対応を返す"""
    z = zipfile.ZipFile(pptx)
    out = {}
    for n in z.namelist():
        m = re.match(r'ppt/slides/_rels/slide(\d+)\.xml\.rels$', n)
        if not m:
            continue
        d = minidom.parseString(z.read(n))
        imgs = [r.getAttribute('Target').split('/')[-1]
                for r in d.getElementsByTagName('Relationship')
                if '/media/' in r.getAttribute('Target')]
        if imgs:
            out[int(m.group(1))] = imgs
    return out


def slide_titles(pptx):
    """スライド番号 → 先頭のテキスト（見出し代わり）"""
    z = zipfile.ZipFile(pptx)
    out = {}
    for n in z.namelist():
        m = re.match(r'ppt/slides/slide(\d+)\.xml$', n)
        if not m:
            continue
        d = minidom.parseString(z.read(n))
        ts = [t.firstChild.nodeValue for t in d.getElementsByTagName('a:t')
              if t.firstChild and t.firstChild.nodeValue.strip()]
        # 数字だけ・記号だけの断片を飛ばして最初のまとまった語を見出しにする
        title = ''
        for t in ts:
            s = t.strip()
            if len(s) >= 2 and not s.isdigit():
                title = s
                break
        out[int(m.group(1))] = re.sub(r'[\\/:*?"<>|]', '_', title)[:28]
    return out


def cmd_media(pptx, outdir, min_kb):
    """埋め込み画像を、使われているスライド番号つきで取り出す"""
    os.makedirs(outdir, exist_ok=True)
    z = zipfile.ZipFile(pptx)
    smap = slide_image_map(pptx)
    titles = slide_titles(pptx)

    used = {}
    for sn, imgs in smap.items():
        for im in imgs:
            used.setdefault(im, []).append(sn)

    n = skip = 0
    for name in z.namelist():
        if not name.startswith('ppt/media/'):
            continue
        base = name.split('/')[-1]
        size = z.getinfo(name).file_size
        if size < min_kb * 1024:
            skip += 1
            continue
        slides = sorted(used.get(base, []))
        tag = ('S%03d' % slides[0]) if slides else 'S___'
        ttl = titles.get(slides[0], '') if slides else ''
        dst = os.path.join(outdir, '%s_%s_%s' % (tag, ttl, base) if ttl else '%s_%s' % (tag, base))
        with open(dst, 'wb') as f:
            f.write(z.read(name))
        n += 1
    print('取り出しました: %d件（%dKB未満は除外: %d件）' % (n, min_kb, skip))
    print('  →', outdir)


def cmd_slides(pptx, outdir, dpi):
    """スライドを1枚ずつ画像化する（PDF経由）"""
    try:
        import fitz
    except ImportError:
        print('PyMuPDF が必要です: pip install pymupdf')
        return
    os.makedirs(outdir, exist_ok=True)

    soffice = shutil.which('soffice') or shutil.which('soffice.exe')
    if not soffice:
        for c in (r'C:\Program Files\LibreOffice\program\soffice.exe',
                  r'C:\Program Files (x86)\LibreOffice\program\soffice.exe'):
            if os.path.exists(c):
                soffice = c
                break
    if not soffice:
        print('LibreOffice が見つかりません。')
        print('  代わりに PowerPoint で「PDFとして保存」し、そのPDFに対して')
        print('  python extract_figures.py pdf 仕様書.pdf 出力先 を実行してください。')
        return

    print('PDFへ変換しています...')
    subprocess.run([soffice, '--headless', '--convert-to', 'pdf',
                    '--outdir', outdir, pptx], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pdf = os.path.join(outdir, os.path.splitext(os.path.basename(pptx))[0] + '.pdf')
    cmd_pdf(pdf, outdir, dpi, titles=slide_titles(pptx))


def cmd_pdf(pdf, outdir, dpi, titles=None):
    """PDFの各ページを画像化する"""
    import fitz
    os.makedirs(outdir, exist_ok=True)
    d = fitz.open(pdf)
    for i, page in enumerate(d, 1):
        ttl = (titles or {}).get(i, '')
        name = 'S%03d_%s.png' % (i, ttl) if ttl else 'S%03d.png' % i
        page.get_pixmap(dpi=dpi).save(os.path.join(outdir, name))
    print('%d ページを画像化しました → %s' % (len(d), outdir))


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    mode, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
    dpi = 150
    min_kb = 20
    if '--dpi' in sys.argv:
        dpi = int(sys.argv[sys.argv.index('--dpi') + 1])
    if '--min-kb' in sys.argv:
        min_kb = int(sys.argv[sys.argv.index('--min-kb') + 1])

    if mode == 'media':
        cmd_media(src, out, min_kb)
    elif mode == 'slides':
        cmd_slides(src, out, dpi)
    elif mode == 'pdf':
        cmd_pdf(src, out, dpi)
    else:
        print(__doc__)
        sys.exit(1)
