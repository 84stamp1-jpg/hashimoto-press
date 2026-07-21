#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""弥生会計 相談用ブリーフィング資料（A4縦 2ページ）

登崎さんの月次業務の流れを、社外の弥生インストラクターに короткое時間で
理解してもらうための資料。実測時間と、弥生の範囲内/範囲外の切り分けを明記し、
限られた面談時間を弥生で解決できる論点に集中させることを狙う。

使い方:
    python yayoi_briefing.py 出力先.pdf

依存: pip install reportlab
"""
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (HRFlowable, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
F = 'HeiseiKakuGo-W5'

NAVY   = colors.HexColor('#1f3864')
BLUE   = colors.HexColor('#2e5c9a')
LGRAY  = colors.HexColor('#f2f4f8')
MGRAY  = colors.HexColor('#c8cfda')
RED    = colors.HexColor('#c0392b')
AMBER  = colors.HexColor('#fdf6e3')
GREEN  = colors.HexColor('#eef7ee')

S = {
    'title':  ParagraphStyle('t', fontName=F, fontSize=16, textColor=NAVY, alignment=TA_CENTER, leading=21),
    'sub':    ParagraphStyle('s', fontName=F, fontSize=8.5, textColor=colors.HexColor('#555'), alignment=TA_CENTER, leading=12),
    'h':      ParagraphStyle('h', fontName=F, fontSize=11, textColor=colors.white, backColor=NAVY,
                             leftIndent=5, spaceBefore=6, spaceAfter=3, leading=17),
    'b':      ParagraphStyle('b', fontName=F, fontSize=9, textColor=colors.HexColor('#1a1a2e'), leading=13.5),
    'bc':     ParagraphStyle('bc', fontName=F, fontSize=9, textColor=colors.HexColor('#1a1a2e'), leading=13.5, alignment=TA_CENTER),
    # 濃色の見出し行に載せる白文字。TableStyleのTEXTCOLORはParagraphには効かない
    'hw':     ParagraphStyle('hw', fontName=F, fontSize=9, textColor=colors.white, leading=13.5),
    'hwc':    ParagraphStyle('hwc', fontName=F, fontSize=9, textColor=colors.white, leading=13.5, alignment=TA_CENTER),
    'small':  ParagraphStyle('sm', fontName=F, fontSize=8, textColor=colors.HexColor('#444'), leading=11.5),
    'q':      ParagraphStyle('q', fontName=F, fontSize=9.5, textColor=colors.HexColor('#1a1a2e'), leading=14),
    'note':   ParagraphStyle('n', fontName=F, fontSize=7.5, textColor=colors.HexColor('#666'), leading=10.5),
}
W = 188 * mm


def hdr(txt):
    return Paragraph('■ ' + txt, S['h'])


def box(rows, widths, style_extra=None, bg=None):
    t = Table(rows, colWidths=widths)
    base = [('GRID', (0, 0), (-1, -1), 0.5, MGRAY), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5)]
    if bg:
        base.append(('BACKGROUND', (0, 0), (-1, 0), bg))
        base.append(('TEXTCOLOR', (0, 0), (-1, 0), colors.white))
    if style_extra:
        base += style_extra
    t.setStyle(TableStyle(base))
    return t


def build(out):
    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=11 * mm, rightMargin=11 * mm,
                            topMargin=10 * mm, bottomMargin=10 * mm,
                            title='弥生会計 ご相談資料', author='橋本工業株式会社')
    st = []

    st.append(Paragraph('経理業務の流れと ご相談したいこと', S['title']))
    st.append(Paragraph('橋本工業株式会社　／　弥生会計 ご相談用　2026年7月', S['sub']))
    st.append(HRFlowable(width='100%', thickness=1.5, color=NAVY, spaceAfter=5))

    # ── 1. 前提 ──
    st.append(hdr('１．前提'))
    st.append(box([
        [Paragraph('会社', S['b']), Paragraph('プレス加工・金型製造　従業員 約35名', S['b'])],
        [Paragraph('経理担当', S['b']), Paragraph('<b>1名（総務と兼務）</b>　※属人化の解消が課題', S['b'])],
        [Paragraph('使用システム', S['b']), Paragraph('生産管理：<b>i-Pro</b>（他社製）　／　会計：<b>弥生会計</b>', S['b'])],
        [Paragraph('主要取引先', S['b']), Paragraph('ユタカ技研（売上の約67%、プレス仕入の約71%を占める）', S['b'])],
    ], [30 * mm, 158 * mm]))

    # ── 2. 全体構造 ──
    st.append(hdr('２．全体の構造　―　同じ金額を3か所に入力している'))
    flow = [[
        Paragraph('<b>客先請求書</b><br/>（PDF）', S['bc']),
        Paragraph('→', S['bc']),
        Paragraph('<b>i-Pro</b><br/>生産管理', S['bc']),
        Paragraph('→', S['bc']),
        Paragraph('<b>売上仕入明細表</b><br/>（Excel）', S['bc']),
        Paragraph('→', S['bc']),
        Paragraph('<b>弥生会計</b>', S['bc']),
    ]]
    t = Table(flow, colWidths=[36 * mm, 8 * mm, 34 * mm, 8 * mm, 44 * mm, 8 * mm, 34 * mm])
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (0, 0), 1, MGRAY), ('BACKGROUND', (0, 0), (0, 0), LGRAY),
        ('BOX', (2, 0), (2, 0), 1, BLUE), ('BOX', (4, 0), (4, 0), 1, BLUE),
        ('BOX', (6, 0), (6, 0), 1.5, NAVY), ('BACKGROUND', (6, 0), (6, 0), GREEN),
        ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    st.append(t)
    # 各ボックスの真下に注記が来るよう、上の flow と同じ列幅で組む
    note = [[
        Paragraph('', S['small']),
        Paragraph('<b>↑ 1個ずつ照合</b><br/><font color="#c0392b"><b>月5〜6日</b></font>', S['bc']),
        Paragraph('', S['small']),
        Paragraph('↑ 転記', S['bc']),
        Paragraph('', S['small']),
        Paragraph('↑ 計上入力<br/>＋伝票NOを手書き', S['bc']),
        Paragraph('', S['small']),
    ]]
    t2 = Table(note, colWidths=[18 * mm, 44 * mm, 18 * mm, 30 * mm, 22 * mm, 40 * mm, 16 * mm])
    t2.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('TOPPADDING', (0, 0), (-1, -1), 1),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 1)]))
    st.append(t2)

    # ── 3. 月次の流れ ──
    st.append(hdr('３．月次の流れ'))
    st.append(box([
        [Paragraph('<b>時期</b>', S['hwc']), Paragraph('<b>作業内容</b>', S['hw'])],
        [Paragraph('日々', S['bc']),
         Paragraph('i-Proへ入力（出荷入力・材料入力・仕入入力）', S['b'])],
        [Paragraph('3〜8日ごろ', S['bc']),
         Paragraph('客先請求書（PDF）が届く　→　<b>i-Proの金額と1個ずつ照合</b>　→　'
                   '消費税のズレを調整額で手入力　→　i-Proで一括計上<br/>'
                   '<font color="#c0392b">※ユタカ技研分は、請求内容を i-Pro へ<b>1行ずつ手入力</b>している</font>', S['b'])],
        [Paragraph('20日まで', S['bc']),
         Paragraph('Excel明細表へ転記　→　印刷して代表へ提出　→　支払処理　→　'
                   '<b>明細表を見ながら弥生へ計上入力（月 約50伝票）</b>　→　'
                   '明細表に<b>弥生の伝票NOを手書き</b>　→　科目ごとの合計一致を確認', S['b'])],
        [Paragraph('月末ごろ', S['bc']),
         Paragraph('i-Proで請求締め処理　→　売掛／買掛の残高一覧を出力　→　'
                   '<b>弥生の残高と一致したら完了</b>', S['b'])],
    ], [26 * mm, 162 * mm], bg=BLUE))

    # ── 4. 実測時間 ──
    st.append(hdr('４．どこに時間がかかっているか（担当者の実測）'))
    rows = [[Paragraph('<b>作業</b>', S['hw']), Paragraph('<b>頻度</b>', S['hwc']),
             Paragraph('<b>所要時間</b>', S['hwc']), Paragraph('<b>月換算</b>', S['hwc'])]]
    data = [
        ('売上・仕入を請求書と1個ずつ照合', '月1回', '5〜6日', '約5.5日', True),
        ('ユタカ技研の請求書を i-Pro へ1行ずつ入力', '月1回', '1日', '1日', False),
        ('明細表を見ながら弥生へ計上入力（約50伝票）', '月1回', '半日〜1日', '約0.75日', False),
        ('単価改定（部材・製品マスタを1件ずつ手入力）', '3ヶ月に1回', '6〜7時間', '約0.3日', False),
        ('売上仕入明細表（Excel）への転記', '月1回', '2〜3時間', '約0.35日', False),
    ]
    for nm, fr, tm, mo, big in data:
        b = '<b>%s</b>' if big else '%s'
        rows.append([Paragraph(b % nm, S['b']), Paragraph(fr, S['bc']),
                     Paragraph(b % tm, S['bc']), Paragraph(b % mo, S['bc'])])
    st.append(box(rows, [96 * mm, 24 * mm, 34 * mm, 34 * mm], bg=BLUE,
                  style_extra=[('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#fdecea'))]))
    st.append(Paragraph(
        '<b>合計 約8日／月（月20営業日の約4割・年間約95日）。うち照合作業だけで全体の約7割を占める。</b>', S['b']))

    # ── 5. 確認済みの制約 ──
    st.append(hdr('５．確認済みの制約'))
    st.append(box([
        [Paragraph('i-Pro', S['b']),
         Paragraph('仕入入力・支払入力・部材/製品マスタとも、<b>CSVやExcelからの一括取込機能は無い</b>', S['b'])],
        [Paragraph('客先データ', S['b']),
         Paragraph('ユタカ技研からの請求書は <b>PDF</b>（CSV・EDIでの提供は現状なし。別途照会予定）', S['b'])],
        [Paragraph('消費税', S['b']),
         Paragraph('弥生・i-Proとも<b>すでに一括（割戻し）設定</b>だが、集計時に数円のズレが出ることがある', S['b'])],
    ], [30 * mm, 158 * mm]))

    st.append(PageBreak())

    # ── 6. 相談したいこと ──
    st.append(Paragraph('ご相談したいこと', S['title']))
    st.append(HRFlowable(width='100%', thickness=1.5, color=NAVY, spaceAfter=6))

    st.append(hdr('６．弥生会計について教えていただきたいこと'))
    qs = [
        ('弥生への計上入力を減らせないか',
         '毎月 約50伝票を、Excelの明細表を見ながら手入力しています。'
         '<b>この明細表から仕訳CSVを作って弥生へ取り込むことは可能でしょうか。</b>'
         '可能な場合、<b>取込CSVの正式な列仕様</b>（項目名・並び順・文字コード・日付書式など）を教えてください。'),
        ('定型仕訳・仕訳辞書の活用',
         '毎月ほぼ同じ取引先・同じ科目の繰り返しです。'
         '定型仕訳や仕訳辞書、摘要辞書などで入力の手数を減らす方法があれば教えてください。'),
        ('スマート取引取込は使えるか',
         '当社の使い方（社内で作成したExcel明細表、PDFの客先請求書）で、'
         'スマート取引取込は実用になりますか。向き不向きを率直に伺いたいです。'),
        ('伝票NOの手書きをなくせないか',
         '弥生へ入力した後、<b>明細表に弥生の伝票NOを手書き</b>しています。'
         '後から弥生側で追跡できる運用にできれば、この手間はなくせないでしょうか。'),
        ('消費税の端数のズレ',
         '客先請求書と数円ズレることがあり、その都度、調整額を手入力しています。'
         '端数処理の設定や、ズレを定型的に処理する実務上の作法があれば教えてください。'),
        ('残高照合を楽にする機能',
         '月末に、i-Proの売掛／買掛残高一覧と弥生の残高を突き合わせています。'
         'この照合を効率化できる機能や、おすすめの進め方はありますか。'),
        ('生産管理システムとの連携事例',
         'i-Pro のような生産管理システムと弥生を連携している事例をご存じでしたら、'
         'どのような方法（CSV・API・中間ツール等）が使われているか教えてください。'),
        ('属人化への対策',
         '<b>経理担当が1名</b>のため、本人不在時に業務が止まるリスクがあります。'
         '弥生の運用面で、引き継ぎしやすくする工夫があれば教えてください。'),
        ('電子帳簿保存法への対応',
         '客先請求書がPDFで届きます。保存要件を満たす運用について、'
         '弥生の機能でカバーできる範囲を確認させてください。'),
    ]
    rows = []
    for i, (t, b) in enumerate(qs, 1):
        rows.append([Paragraph('<b>%d</b>' % i, S['bc']),
                     Paragraph('<b>%s</b><br/>%s' % (t, b), S['q'])])
    st.append(box(rows, [10 * mm, 178 * mm],
                  style_extra=[('BACKGROUND', (0, 0), (0, -1), LGRAY)]))

    # ── 7. 範囲外 ──
    st.append(hdr('７．（参考）弥生の範囲外ですが、最大の課題です'))
    st.append(box([[Paragraph(
        '<b>最も時間がかかっているのは「客先請求書と i-Pro の1個ずつの照合」で、月5〜6日・全体の約7割</b>を占めています。'
        'これは i-Pro と客先データの突合であり、弥生会計の管轄外であることは理解しております。'
        '当社側で、請求書PDFと i-Pro の出力を突き合わせて<b>差分だけを表示するツール</b>の内製を検討中です。<br/>'
        'もし同様のご相談を受けられた経験や、参考になる事例・製品をご存じでしたら、参考までに伺えれば幸いです。', S['b'])]],
        [188 * mm], style_extra=[('BACKGROUND', (0, 0), (-1, -1), AMBER),
                                 ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e0c66b'))]))

    st.append(Spacer(1, 3 * mm))
    st.append(hdr('８．当日お見せできる資料'))
    st.append(box([
        [Paragraph('・売上仕入明細表（Excel／実物）　　・i-Proの画面（仕入入力・支払入力・残高一覧）', S['b'])],
        [Paragraph('・客先請求書（PDF／実物）　　　　　・弥生の現在の設定', S['b'])],
    ], [188 * mm]))

    st.append(Spacer(1, 4 * mm))
    st.append(Paragraph(
        '※ 本資料は、限られたお時間で論点を絞るために当社で作成したものです。'
        '記載内容の誤りや、前提の思い違いがありましたらご指摘ください。', S['note']))

    doc.build(st)
    print('作成しました:', out)


if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else '弥生会計_ご相談資料.pdf')
