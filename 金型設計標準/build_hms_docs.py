#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HMS金型設計標準の3編を、清書したPDF／PowerPointにする

Excelはドラフト用（作業メモ・採否・過去トラ等の欄を持つ）。ここではそこから
「規定内容」だけを取り出して、社内で読む・外注へ渡せる体裁に清書する。

■ 出さないもの（Excelの作業欄）
  備考（担当者の疑問メモ）／過去トラ／相関図／移行元／要検討 は最終文書に載せない。
  採否＝対象外・不要 の項目は本文から外し、巻末に「適用対象外」として一覧で残す
  （黙って消すと、後で「なぜ無いのか」が分からなくなるため）。

■ クリアランス基準
  共通編の第5章（設計値の決め方）に本文として織り込む。
  別ブック「金型設計クリアランス基準書.xlsx」の数表をそのまま章内へ差し込む。

使い方:
    python build_hms_docs.py            # 3編すべて pdf/ へ出力
    python build_hms_docs.py 共通         # 共通編だけ

依存: pip install openpyxl reportlab python-pptx
"""
import os
import re
import sys
import warnings

import openpyxl

warnings.filterwarnings('ignore')

BASE = r'C:\Users\Owner\Desktop\金型仕様書'
OUT = os.path.join(BASE, '出力')
FIGDIR = os.path.join(BASE, 'HMS図')
CLEAR_XLSX = os.path.join(BASE, '金型設計クリアランス基準書.xlsx')

# (Excelファイル, シート名, 表示名, 図ファイルの接頭辞)
EDITIONS = {
    '共通': ('HMS金型設計標準_共通編.xlsx', '01_共通編', '共通編', '共'),
    '単発': ('HMS金型設計標準_単発編_骨格.xlsx', '01_単発編', '単発編', '単'),
    '順送': ('HMS金型設計標準_順送編_骨格.xlsx', '01_順送編', '順送編', '順'),
}

# クリアランス基準書のうち本文へ入れるシート（表紙は除く）
CLEAR_SHEETS = ['ピアス・抜き', 'バーリング', '曲げ', '順送レイアウト', '設計チェックリスト']


# ================================================================ 読み込み
def _cols(hdr):
    def find(*names):
        for n in names:
            if n in hdr:
                return hdr.index(n) + 1
        return None
    return {
        'no': find('No'),
        'item': find('項目'),
        'rule': find('規定内容', '規定内容（案）'),
        'dec': find('採否'),
    }


def load_edition(path, sheet):
    """[(章, [item...]), ...] を返す。item は dict。"""
    ws = openpyxl.load_workbook(path, data_only=True)[sheet]
    hdr = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    col = _cols(hdr)
    chapters = []
    cur_name = None
    cur_items = None
    chap = ''
    for r in range(2, ws.max_row + 1):
        c1 = str(ws.cell(r, 1).value or '').strip()
        if c1:
            chap = c1
        no = str(ws.cell(r, col['no']).value or '').strip()
        if not no:
            continue
        if chap != cur_name:
            cur_name = chap
            cur_items = []
            chapters.append((chap, cur_items))
        if no == '→':                     # 共通編を参照する行
            ref = str(ws.cell(r, 4).value or '')
            cur_items.append({'kind': 'ref', 'text': ref})
            continue
        cur_items.append({
            'kind': 'item',
            'no': no,
            'item': str(ws.cell(r, col['item']).value or ''),
            'rule': str(ws.cell(r, col['rule']).value or ''),
            'dec': str(ws.cell(r, col['dec']).value or '') if col['dec'] else '',
        })
    return chapters


def load_intro(path):
    ws = openpyxl.load_workbook(path, data_only=True)['00_はじめに']
    rows = []
    for r in range(2, ws.max_row + 1):
        a = str(ws.cell(r, 1).value or '').strip()
        b = str(ws.cell(r, 2).value or '').strip()
        if a or b:
            rows.append((a, b))
    return rows


def load_clearance():
    """クリアランス基準書の各シートを block 列に変換して返す。
    block = ('title'|'sub'|'head'|'note'|'para', text) または ('table', [row...])"""
    wb = openpyxl.load_workbook(CLEAR_XLSX, data_only=True)
    out = []
    for sh in CLEAR_SHEETS:
        if sh not in wb.sheetnames:
            continue
        ws = wb[sh]
        rows = []
        for r in range(1, ws.max_row + 1):
            vals = [('' if ws.cell(r, c).value in (None, '') else
                     str(ws.cell(r, c).value).strip())
                    for c in range(1, ws.max_column + 1)]
            rows.append(vals)
        out.append((sh, _parse_clear_sheet(rows)))
    return out


def _parse_clear_sheet(rows):
    blocks = []
    tbl = []
    seen_title = False

    def flush():
        nonlocal tbl
        if tbl:
            # 右端の全空列を落とす
            w = max((len(r) for r in tbl), default=0)
            while w > 1 and all(len(r) < w or r[w - 1] == '' for r in tbl):
                w -= 1
            blocks.append(('table', [r[:w] + [''] * (w - len(r)) for r in tbl]))
            tbl = []

    for vals in rows:
        filled = [i for i, v in enumerate(vals) if v != '']
        if not filled:
            flush()
            continue
        if len(filled) == 1:
            flush()
            t = vals[filled[0]]
            if not seen_title:
                blocks.append(('title', t))
                seen_title = True
            elif t.startswith('■'):
                blocks.append(('head', t.lstrip('■ ').strip()))
            elif t.startswith('※'):
                blocks.append(('note', t.lstrip('※ ').strip()))
            else:
                blocks.append(('sub', t))
        else:
            tbl.append([vals[i] for i in range(filled[-1] + 1)])
    flush()
    return blocks


# ================================================================ PDF
def build_pdf(chapters, intro, title_ja, clearance, prefix, out_path):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether,
                                    NextPageTemplate, PageBreak, PageTemplate,
                                    Paragraph, Spacer, Table, TableStyle)
    from reportlab.lib.utils import ImageReader

    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
    F = 'HeiseiKakuGo-W5'
    NAVY = colors.HexColor('#1F3864')
    TEAL = colors.HexColor('#1C6B63')
    GRAY = colors.HexColor('#555555')
    LIGHT = colors.HexColor('#EAF0F6')
    GREENBG = colors.HexColor('#E1EFDA')
    LINE = colors.HexColor('#B7C2D0')

    def ps(name, **kw):
        kw.setdefault('fontName', F)
        return ParagraphStyle(name, **kw)

    def esc(s):
        # reportlab の Paragraph は <, &, > をタグとして解釈するため無害化する。
        # そのうえで改行だけ <br/> に戻す。
        s = str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return s.replace('\n', '<br/>')

    st_cover_t = ps('ct', fontSize=24, leading=32, textColor=NAVY)
    st_cover_s = ps('cs', fontSize=13, leading=20, textColor=GRAY)
    st_cover_org = ps('co', fontSize=12, leading=18, textColor=colors.black)
    st_intro_h = ps('ih', fontSize=11, leading=16, textColor=NAVY)
    st_intro_b = ps('ib', fontSize=9.5, leading=15, textColor=colors.black)
    st_chap = ps('ch', fontSize=14, leading=18, textColor=colors.white)
    st_item = ps('it', fontSize=10.5, leading=14, textColor=NAVY)
    st_body = ps('bd', fontSize=9.5, leading=15, textColor=colors.black,
                 alignment=TA_LEFT)
    st_ref = ps('rf', fontSize=9, leading=13, textColor=TEAL)
    st_head = ps('hd', fontSize=10.5, leading=15, textColor=TEAL)
    st_sub = ps('sb', fontSize=9.5, leading=14, textColor=GRAY)
    st_note = ps('nt', fontSize=8.5, leading=12, textColor=GRAY)
    st_tc = ps('tc', fontSize=8.5, leading=11.5, textColor=colors.black)
    st_th = ps('th', fontSize=8.5, leading=11.5, textColor=colors.white)
    st_appx = ps('ax', fontSize=9, leading=13, textColor=colors.black)
    st_foot = ps('ft', fontSize=8, leading=10, textColor=GRAY)

    story = []

    # ---- 表紙
    story.append(Spacer(1, 55 * mm))
    story.append(Paragraph('HMDS 金型設計標準', st_cover_t))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph('【%s】' % title_ja, st_cover_t))
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph('橋本工業株式会社　技術部', st_cover_org))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph('HASHIMOTO KOGYO — Mold Design Standard（HMDS）', st_cover_s))
    story.append(Spacer(1, 16 * mm))
    intro_tbl = []
    for a, b in intro:
        if a and b:
            intro_tbl.append([Paragraph(esc(a), st_intro_h), Paragraph(esc(b), st_intro_b)])
        elif a:
            intro_tbl.append([Paragraph(esc(a), st_intro_h), ''])
    if intro_tbl:
        t = Table(intro_tbl, colWidths=[34 * mm, 128 * mm])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LINEBELOW', (0, 0), (-1, -2), 0.4, LINE),
        ]))
        story.append(t)
    story.append(NextPageTemplate('body'))
    story.append(PageBreak())

    # ---- 本文
    def chapter_bar(name):
        t = Table([[Paragraph(name, st_chap)]], colWidths=[162 * mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), NAVY),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        return t

    def render_table(rows, first_is_header=True):
        data = []
        for i, r in enumerate(rows):
            style = st_th if (first_is_header and i == 0) else st_tc
            data.append([Paragraph(esc(c), style) for c in r])
        ncol = max(len(r) for r in rows)
        # 1列目やや広め、残り均等
        avail = 162 * mm
        if ncol == 1:
            widths = [avail]
        else:
            first = avail * 0.26
            widths = [first] + [(avail - first) / (ncol - 1)] * (ncol - 1)
        t = Table(data, colWidths=widths, repeatRows=1 if first_is_header else 0)
        ts = [
            ('GRID', (0, 0), (-1, -1), 0.4, LINE),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F8FB')]),
        ]
        if first_is_header:
            ts.append(('BACKGROUND', (0, 0), (-1, 0), TEAL))
        t.setStyle(TableStyle(ts))
        return t

    def clearance_flowables():
        flow = [Spacer(1, 3 * mm),
                chapter_bar('5-補. クリアランス基準（早見表）'),
                Spacer(1, 2 * mm),
                Paragraph('材質と板厚でクリアランスを決めるための早見表。'
                          '数値は標準値で、材料ロット・型構造・製品要求により調整する。',
                          st_body),
                Spacer(1, 2 * mm)]
        for sh, blocks in clearance:
            for kind, payload in blocks:
                if kind == 'title':
                    flow.append(Spacer(1, 2 * mm))
                    flow.append(Paragraph('◆ ' + esc(payload), st_item))
                    flow.append(Spacer(1, 1 * mm))
                elif kind == 'sub':
                    flow.append(Paragraph(esc(payload), st_sub))
                elif kind == 'head':
                    flow.append(Spacer(1, 1 * mm))
                    flow.append(Paragraph('■ ' + esc(payload), st_head))
                elif kind == 'note':
                    flow.append(Paragraph('※ ' + esc(payload), st_note))
                elif kind == 'para':
                    flow.append(Paragraph(esc(payload), st_body))
                elif kind == 'table':
                    flow.append(Spacer(1, 1 * mm))
                    flow.append(render_table(payload))
                    flow.append(Spacer(1, 1 * mm))
        return flow

    def figure_for(no):
        """項目番号に対応する図があれば、幅に収めた Image を返す。"""
        path = os.path.join(FIGDIR, 'hms_%s%s.png' % (prefix, no))
        if not os.path.exists(path):
            return None
        iw, ih = ImageReader(path).getSize()
        maxw = 150 * mm
        maxh = 95 * mm
        scale = min(maxw / iw, maxh / ih)
        return Image(path, width=iw * scale, height=ih * scale)

    appendix = []       # 適用対象外の一覧
    for cname, items in chapters:
        block = [Spacer(1, 3 * mm), chapter_bar(cname), Spacer(1, 2 * mm)]
        for it in items:
            if it['kind'] == 'ref':
                block.append(Paragraph('▶ ' + esc(it['text']), st_ref))
                block.append(Spacer(1, 1 * mm))
                continue
            if it['dec'] in ('対象外', '不要'):
                appendix.append((it['no'], it['item'], it['dec']))
                continue
            head = esc('%s　%s' % (it['no'], it['item']))
            # 「※図は他社資料Sxxxを参照」は、図を自社標準へ取り込んだので削除する
            # （他社資料の整理番号を標準に残さない）。
            rule = re.sub(r'※?\s*図は他社資料[^。]*?参照。?', '', it['rule']).strip()
            body = esc(rule)
            group = [Paragraph(head, st_item), Paragraph(body, st_body)]
            fig = figure_for(it['no'])
            if fig is not None:
                group += [Spacer(1, 1.5 * mm), fig,
                          Paragraph('図：原資料をもとに作成（社内用）', st_body)]
            group.append(Spacer(1, 2.5 * mm))
            block.append(KeepTogether(group))
        story.extend(block)
        # 共通編の第5章の直後にクリアランス基準を差し込む
        if clearance and '設計値' in cname:
            story.extend(clearance_flowables())

    # ---- 巻末：適用対象外
    if appendix:
        story.append(PageBreak())
        story.append(chapter_bar('付. 適用対象外とした項目'))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph('次の項目は、当社の運用上あてはまらないため本標準では規定しない。',
                               st_appx))
        story.append(Spacer(1, 2 * mm))
        rows = [['No', '項目', '区分']] + [[a, b, c] for a, b, c in appendix]
        story.append(render_table(rows))

    # ---- レイアウト
    def on_page(canv, doc):
        canv.saveState()
        canv.setFont(F, 8)
        canv.setFillColor(GRAY)
        canv.drawString(20 * mm, 12 * mm,
                        'HMDS 金型設計標準【%s】　橋本工業株式会社' % title_ja)
        canv.drawRightString(190 * mm, 12 * mm, '%d' % doc.page)
        canv.setStrokeColor(LINE)
        canv.setLineWidth(0.4)
        canv.line(20 * mm, 15 * mm, 190 * mm, 15 * mm)
        canv.restoreState()

    def on_cover(canv, doc):
        canv.saveState()
        canv.setFillColor(NAVY)
        canv.rect(0, 272 * mm, 210 * mm, 25 * mm, fill=1, stroke=0)
        canv.restoreState()

    doc = BaseDocTemplate(out_path, pagesize=A4,
                          leftMargin=20 * mm, rightMargin=20 * mm,
                          topMargin=20 * mm, bottomMargin=18 * mm)
    fw = A4[0] - 40 * mm
    fh = A4[1] - 38 * mm
    frame = Frame(20 * mm, 18 * mm, fw, fh, id='f')
    doc.addPageTemplates([
        PageTemplate(id='cover', frames=[frame], onPage=on_cover),
        PageTemplate(id='body', frames=[frame], onPage=on_page),
    ])
    story.insert(0, NextPageTemplate('cover'))
    doc.build(story)
    return out_path


# ================================================================ 実行
def main():
    os.makedirs(OUT, exist_ok=True)
    keys = [sys.argv[1]] if len(sys.argv) > 1 else list(EDITIONS)
    clearance = load_clearance()
    for k in keys:
        fname, sheet, ja, prefix = EDITIONS[k]
        path = os.path.join(BASE, fname)
        chapters = load_edition(path, sheet)
        intro = load_intro(path)
        cl = clearance if k == '共通' else None
        out = os.path.join(OUT, 'HMDS金型設計標準_%s.pdf' % ja)
        build_pdf(chapters, intro, ja, cl, prefix, out)
        print('PDF:', out)


if __name__ == '__main__':
    main()
