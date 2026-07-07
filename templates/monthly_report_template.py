#!/usr/bin/env python3
# =============================================================================
# 橋本工業 月次会レポート生成テンプレート
# =============================================================================
# 【使い方】
#   毎月「月次会の実績をPDFにまとめて」と Claude に伝えるだけ。
#   Claude が Slack #月次会 を読み取り、このテンプレートを元に
#   前月フォロー込みの A4 2ページ PDF を自動生成します。
#
# 【毎月の更新箇所】（★マークを検索して更新）
#   REPORT_MONTH   : レポート対象月（例: '4月'）
#   PERIOD_LABEL   : 期・月次ラベル（例: '71期 4月実績'）
#   ISSUE_DATE     : 発行日（例: '2026年5月'）
#   PAGE_LABEL     : フッター用ラベル（例: '2026年5月'）
#   各 DATA セクション : Slack 投稿内容をそのまま転記
# =============================================================================

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                 Paragraph, Spacer, Image, HRFlowable, PageBreak)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import io, os

# ── フォント ──────────────────────────────────────────────────────────────
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
JP_FONT = '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf'
if os.path.exists(JP_FONT):
    fm.fontManager.addfont(JP_FONT)
    plt.rcParams['font.family'] = 'IPAGothic'

# ── 色 ───────────────────────────────────────────────────────────────────
RED   = colors.HexColor('#e74c3c')
AMBER = colors.HexColor('#f39c12')
GREEN = colors.HexColor('#27ae60')
NAVY  = colors.HexColor('#2c3e6b')
LGRAY = colors.HexColor('#f4f5f7')
MGRAY = colors.HexColor('#dde1e8')
WHITE = colors.white
C_RED='#e74c3c'; C_GREEN='#27ae60'; C_BLUE='#5b7bd5'
C_AMBER='#f39c12'; C_NAVY='#2c3e6b'; C_GRAY='#95a5a6'

# ════════════════════════════════════════════════════════════════════════════
# ★ 毎月更新：レポート基本情報
# ════════════════════════════════════════════════════════════════════════════
REPORT_MONTH  = '4月'            # 対象月
PERIOD_LABEL  = '71期 4月実績'   # タイトル用
ISSUE_DATE    = '2026年5月'      # 発行月
PAGE_LABEL    = '2026年5月'      # フッター用

# ════════════════════════════════════════════════════════════════════════════
# ★ 毎月更新：グラフ用時系列データ
#    （確定値は翌月に追記、速報値は当月に仮入力）
# ════════════════════════════════════════════════════════════════════════════
MONTHS_6      = ['11月','12月','1月','2月','3月','4月\n(速報)']
DEFECT_6      = [78632, 175562, 608228, 116603, None, None]   # 工程内不良(円)  ← 3月確定・4月速報を入力
PROFIT_6      = [92, -1685, 3000, None, None, None]            # 粗利(千円)      ← 3月確定を入力

# ════════════════════════════════════════════════════════════════════════════
# ★ 毎月更新：社長コメント（Slack 投稿内容 + 前月フォロー所感を記入）
# ════════════════════════════════════════════════════════════════════════════
PRESIDENT_MSG = (
    'ここに社長コメントを記入。\n'
    '【前月フォロー】前月の指摘事項に対する今月の状況を記入。'
)

# ════════════════════════════════════════════════════════════════════════════
# ★ 毎月更新：品質実績（八木）
# ════════════════════════════════════════════════════════════════════════════
QUALITY_DATA = [
    ['指標', '今月実績', '月次目標', '71期累計', '年目標', '判定'],
    ['工程内不良金額', '???円',   '41,666円', '???円',    '500,000円', '???'],
    ['社内選別・修正', '???円',   '37,916円', '???円',    '455,000円', '???'],
    ['外部苦情件数',   '?件',     '—',        '?件',      '13件/年',   '???'],
]
QUALITY_NOTE = '※ ここに品質の補足コメントを記入。'

# ════════════════════════════════════════════════════════════════════════════
# ★ 毎月更新：製造実績（見原）
# ════════════════════════════════════════════════════════════════════════════
MFG_DATA = [
    ['項目', '内容・状況', '判定'],
    ['項目A', '内容を記入', '???'],
    ['項目B', '内容を記入', '???'],
]

# ════════════════════════════════════════════════════════════════════════════
# ★ 毎月更新：組立実績（永丘）
# ════════════════════════════════════════════════════════════════════════════
ASM_DATA = [
    ['項目', '内容・状況'],
    ['計画対実績', '内容を記入'],
    ['改善活動',   '内容を記入'],
]

# ════════════════════════════════════════════════════════════════════════════
# ★ 毎月更新：技術実績（大石・遠藤）
# ════════════════════════════════════════════════════════════════════════════
TECH_DATA = [
    ['項目', '内容・状況', '判定'],
    ['新規金型', '内容を記入', '???'],
    ['改修状況', '内容を記入', '???'],
]

# ════════════════════════════════════════════════════════════════════════════
# ★ 毎月更新：納入管理実績（木村）
# ════════════════════════════════════════════════════════════════════════════
DLV_DATA = [
    ['項目', '内容・状況', '判定'],
    ['納入異常', '?件', '???'],
    ['輸送費',   '売上対比?%', '???'],
]

# ════════════════════════════════════════════════════════════════════════════
# ★ 毎月更新：前月指摘フォローアップ
#    評価: ○=改善  △=継続課題  ✕=未対応
# ════════════════════════════════════════════════════════════════════════════
FOLLOW_DATA = [
    ['部署', '前月の指摘内容', '今月の状況', '評価'],
    ['全社',          '前月指摘内容', '今月の状況', '△'],
    ['製造T\n(見原)',  '前月指摘内容', '今月の状況', '△'],
    ['品管T\n(八木)',  '前月指摘内容', '今月の状況', '○'],
    ['技術T\n(大石・遠藤)', '前月指摘内容', '今月の状況', '△'],
    ['納入管理\n(木村)', '前月指摘内容', '今月の状況', '△'],
]

# ════════════════════════════════════════════════════════════════════════════
# ★ 毎月更新：来月の指摘・指示事項
# ════════════════════════════════════════════════════════════════════════════
INST_DATA = [
    ['対象', '指摘・指示内容', '重要度'],
    ['全社',             '指示内容を記入', '★★★'],
    ['製造T\n(見原)',    '指示内容を記入', '★★★'],
    ['品管T\n(八木)',    '指示内容を記入', '★★★'],
    ['技術T\n(大石・遠藤)', '指示内容を記入', '★★★'],
    ['納入管理\n(木村)', '指示内容を記入', '★★'],
    ['組立検査\n(永丘)', '指示内容を記入', '★★'],
]

# ════════════════════════════════════════════════════════════════════════════
# ★ 毎月更新：来月の重要対応アクション
# ════════════════════════════════════════════════════════════════════════════
ACT_DATA = [
    ['No.', '内容', '担当', '期限'],
    ['1', 'アクション内容', '担当者', '期限'],
    ['2', 'アクション内容', '担当者', '期限'],
    ['3', 'アクション内容', '担当者', '期限'],
]

# ════════════════════════════════════════════════════════════════════════════
# 以下は毎月変更不要（共通処理）
# ════════════════════════════════════════════════════════════════════════════

def make_styles():
    s = {}
    s['title'] = ParagraphStyle('title', fontSize=13, fontName='HeiseiKakuGo-W5',
                                 textColor=colors.HexColor('#1a1a2e'), alignment=TA_CENTER,
                                 spaceAfter=2, leading=16)
    s['sec'] = ParagraphStyle('sec', fontSize=9, fontName='HeiseiKakuGo-W5',
                               textColor=WHITE, backColor=NAVY,
                               leftIndent=4, spaceBefore=4, spaceAfter=2, leading=13)
    s['sec2'] = ParagraphStyle('sec2', fontSize=9, fontName='HeiseiKakuGo-W5',
                                textColor=WHITE, backColor=colors.HexColor('#7f1d1d'),
                                leftIndent=4, spaceBefore=4, spaceAfter=2, leading=13)
    s['note'] = ParagraphStyle('note', fontSize=7, fontName='HeiseiKakuGo-W5',
                                textColor=colors.HexColor('#c0392b'), leading=10, leftIndent=4)
    s['label'] = ParagraphStyle('label', fontSize=6.5, fontName='HeiseiKakuGo-W5',
                                  textColor=colors.HexColor('#555555'), alignment=TA_CENTER, leading=9)
    s['president'] = ParagraphStyle('president', fontSize=7.5, fontName='HeiseiKakuGo-W5',
                                     textColor=colors.HexColor('#1a1a2e'), leading=12, leftIndent=4,
                                     backColor=colors.HexColor('#fef9e7'))
    return s

def tbl_style_base():
    return [
        ('FONTNAME',      (0,0), (-1,-1), 'HeiseiKakuGo-W5'),
        ('FONTSIZE',      (0,0), (-1,-1), 6.8),
        ('BACKGROUND',    (0,0), (-1,0),  NAVY),
        ('TEXTCOLOR',     (0,0), (-1,0),  WHITE),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [LGRAY, WHITE]),
        ('GRID',          (0,0), (-1,-1), 0.4, MGRAY),
        ('TOPPADDING',    (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING',   (0,0), (-1,-1), 3),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ]

def chart_defect_trend():
    fig, ax = plt.subplots(figsize=(5.5, 2.6))
    vals = [v if v is not None else 0 for v in DEFECT_6]
    bcols = [C_RED if v > 41666 else (C_GRAY if DEFECT_6[i] is None else C_GREEN)
             for i, v in enumerate(vals)]
    bars = ax.bar(MONTHS_6, [v/1000 for v in vals], color=bcols, alpha=0.85, width=0.55, zorder=3)
    ax.axhline(41.666, color=C_NAVY, lw=1.3, ls='--', label='月次目標41.7千円')
    ax.set_ylabel('千円', fontsize=7)
    ax.tick_params(axis='both', labelsize=7)
    ax.yaxis.grid(True, linestyle='--', alpha=0.4, zorder=0); ax.set_axisbelow(True)
    for bar, v, orig in zip(bars, vals, DEFECT_6):
        label = f'{v/1000:.0f}' if orig is not None else '確定待ち'
        ax.text(bar.get_x()+bar.get_width()/2,
                bar.get_height()+3 if orig else 3,
                label, ha='center', fontsize=6, color='#333' if orig else '#888')
    ax.legend(fontsize=7, framealpha=0.8)
    ax.set_title('工程内不良金額推移', fontsize=8.5, fontweight='bold', pad=4)
    fig.tight_layout(pad=0.5)
    buf = io.BytesIO(); fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig); buf.seek(0); return buf

def chart_profit_trend():
    fig, ax = plt.subplots(figsize=(5.5, 2.6))
    disp = [v if v is not None else 0 for v in PROFIT_6]
    bcols = [C_GREEN if v >= 0 else (C_GRAY if PROFIT_6[i] is None else C_RED)
             for i, v in enumerate(disp)]
    bars = ax.bar(MONTHS_6, disp, color=bcols, alpha=0.85, zorder=3, width=0.55)
    known = [(i, v) for i, v in enumerate(PROFIT_6) if v is not None]
    if known:
        idx, vals = zip(*known)
        ax.plot([MONTHS_6[i] for i in idx], [8000]*len(idx), 'k--', lw=1.3, label='目標8,000千円')
    ax.axhline(0, color='#333', lw=0.7)
    ax.set_ylabel('千円', fontsize=7)
    ax.tick_params(axis='both', labelsize=7)
    ax.yaxis.grid(True, linestyle='--', alpha=0.4, zorder=0); ax.set_axisbelow(True)
    for bar, v, orig in zip(bars, disp, PROFIT_6):
        if orig is not None:
            ypos = bar.get_height()+100 if v >= 0 else bar.get_height()-400
            ax.text(bar.get_x()+bar.get_width()/2, ypos, f'{v:+,}', ha='center', fontsize=6, color='#333')
        else:
            ax.text(bar.get_x()+bar.get_width()/2, 200, '確定待ち', ha='center', fontsize=5.5, color='#888')
    ax.legend(fontsize=7, framealpha=0.8)
    ax.set_title('月次粗利推移', fontsize=8.5, fontweight='bold', pad=4)
    fig.tight_layout(pad=0.5)
    buf = io.BytesIO(); fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig); buf.seek(0); return buf

def make_table(data, col_widths, extra_style=None):
    style = tbl_style_base()
    if extra_style:
        style += extra_style
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle(style))
    return t

def build_pdf(out_path):
    doc = SimpleDocTemplate(out_path, pagesize=A4,
                             leftMargin=10*mm, rightMargin=10*mm,
                             topMargin=8*mm, bottomMargin=8*mm)
    s = make_styles()
    story = []

    # ═══ PAGE 1：当月実績 ════════════════════════════════════════════════════
    story.append(Paragraph(f'71期 月次会　{REPORT_MONTH}実績', s['title']))
    story.append(HRFlowable(width='100%', thickness=1.5, color=NAVY, spaceAfter=3))

    story.append(Paragraph('■ 社長より', s['sec2']))
    story.append(Paragraph(PRESIDENT_MSG, s['president']))

    story.append(Paragraph(f'■ {REPORT_MONTH} 品質実績（八木）', s['sec']))
    story.append(make_table(QUALITY_DATA, [36*mm, 30*mm, 24*mm, 40*mm, 24*mm, 26*mm],
        [('ALIGN',(1,0),(-1,-1),'CENTER'),
         ('TEXTCOLOR',(5,1),(5,2),RED), ('TEXTCOLOR',(5,3),(5,4),GREEN)]))
    story.append(Paragraph(QUALITY_NOTE, s['note']))

    story.append(Paragraph(f'■ {REPORT_MONTH} 製造実績（見原）', s['sec']))
    story.append(make_table(MFG_DATA, [26*mm, 140*mm, 14*mm],
        [('VALIGN',(0,0),(-1,-1),'TOP'),('ALIGN',(2,0),(2,-1),'CENTER')]))

    story.append(Paragraph(f'■ {REPORT_MONTH} 組立実績（永丘）', s['sec']))
    story.append(make_table(ASM_DATA, [26*mm, 154*mm],
        [('VALIGN',(0,0),(-1,-1),'TOP')]))

    story.append(Paragraph(f'■ {REPORT_MONTH} 技術実績（大石・遠藤）', s['sec']))
    story.append(make_table(TECH_DATA, [26*mm, 140*mm, 14*mm],
        [('VALIGN',(0,0),(-1,-1),'TOP'),('ALIGN',(2,0),(2,-1),'CENTER')]))

    story.append(Paragraph(f'■ {REPORT_MONTH} 納入管理実績（木村）', s['sec']))
    story.append(make_table(DLV_DATA, [24*mm, 142*mm, 14*mm],
        [('VALIGN',(0,0),(-1,-1),'TOP'),('ALIGN',(2,0),(2,-1),'CENTER')]))

    story.append(Spacer(1, 2*mm))
    story.append(HRFlowable(width='100%', thickness=0.8, color=MGRAY))
    story.append(Paragraph(f'橋本工業株式会社　71期 月次会資料　{PAGE_LABEL}　（1/2）', s['label']))

    # ═══ PAGE 2：フォロー・グラフ・指示 ════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph(f'71期 月次会　― 前月フォロー・指示事項 ―', s['title']))
    story.append(HRFlowable(width='100%', thickness=1.5, color=NAVY, spaceAfter=3))

    story.append(Paragraph('■ 主要指標推移', s['sec']))
    img1 = Image(chart_defect_trend(), width=88*mm, height=38*mm)
    img2 = Image(chart_profit_trend(), width=88*mm, height=38*mm)
    ct = Table([[img1, img2]], colWidths=[90*mm, 90*mm])
    ct.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'TOP'),
                             ('LEFTPADDING',(0,0),(-1,-1),1),('RIGHTPADDING',(0,0),(-1,-1),1),
                             ('TOPPADDING',(0,0),(-1,-1),1),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    story.append(ct)

    story.append(Paragraph('■ 前月実績報告 指摘事項フォローアップ', s['sec2']))
    story.append(make_table(FOLLOW_DATA, [20*mm, 54*mm, 88*mm, 18*mm],
        [('VALIGN',(0,0),(-1,-1),'TOP'),('ALIGN',(3,0),(3,-1),'CENTER'),
         ('FONTSIZE',(0,0),(-1,-1),6.5),
         ('TEXTCOLOR',(3,1),(3,1),GREEN),
         ('TEXTCOLOR',(3,2),(3,5),AMBER)]))
    story.append(Paragraph('○:改善　△:継続課題　✕:未対応', s['note']))

    story.append(Paragraph(f'■ 来月（{REPORT_MONTH}）指摘・指示事項', s['sec']))
    story.append(make_table(INST_DATA, [18*mm, 151*mm, 11*mm],
        [('ALIGN',(0,0),(0,-1),'CENTER'),('ALIGN',(2,0),(2,-1),'CENTER'),
         ('VALIGN',(0,0),(-1,-1),'TOP'),
         ('TEXTCOLOR',(2,1),(2,6),RED),('FONTSIZE',(1,1),(1,-1),7)]))

    story.append(Paragraph(f'■ 来月 重要対応アクション', s['sec']))
    story.append(make_table(ACT_DATA, [8*mm, 108*mm, 42*mm, 22*mm],
        [('ALIGN',(0,0),(0,-1),'CENTER'),('ALIGN',(3,0),(3,-1),'CENTER')]))

    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width='100%', thickness=0.8, color=MGRAY))
    story.append(Paragraph(f'橋本工業株式会社　71期 月次会資料　{PAGE_LABEL}　（2/2）', s['label']))

    doc.build(story)
    print(f'Done: {out_path}')

# ── 出力先（月ごとにファイル名が変わる）─────────────────────────────────
OUT_PATH = f'/mnt/user-data/outputs/71期_{REPORT_MONTH}実績_月次会報告.pdf'
build_pdf(OUT_PATH)
