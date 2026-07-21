#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""熱中症 緊急対応手順（掲示用A4 1枚）

労働安全衛生規則(2025年6月1日施行)で義務化された3項目
  ①報告体制の整備 ②悪化防止の手順作成 ③関係作業者への周知
を1枚でカバーする掲示物。

使い方:
    python heatstroke_poster.py 出力先.pdf

緊急連絡先は下の CONTACTS に書いた内容がそのまま印字される。
変更するときは CONTACTS を直して再生成すること。空文字にすると記入用の下線になる。

※ 以前はPDFの入力フォーム(AcroForm)にしていたが、ビューアによって入力値が
   表示されない事象が出たため、文字として直接描き込む方式に変更した(2026-07-21)。

WBGT基準値(WORKS)は H-Hub / 金型管理システムの設定 (/wbgt/config) と
**必ず揃えること**。掲示物と画面で違う基準が出ると現場が混乱し、
監督署の確認でも問題になる。

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
from reportlab.platypus import (HRFlowable, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
F = 'HeiseiKakuGo-W5'

# ---------------------------------------------------------------- 設定
# 危険域。この値以上は基準値にかかわらず全作業を中止・延期する（システム側の WB_DANGER と同じ）
DANGER = 31

# WBGT基準値 (作業名, 通常, 暑熱順化なし)。/wbgt/config の works と揃えること
WORKS = [
    ('現場作業', 30, 28),
]

# 緊急連絡先。ここに書いた内容がそのまま印字される。
# 以前はPDFの入力フォームにしていたが、ビューアによって入力値が表示されない
# 事象があったため、文字として直接描き込む方式に変更した（2026-07-21）。
# 変更するときはこの辞書を直して再生成する。空文字にすると記入用の下線になる。
CONTACTS = {
    'responsible':  '深津　英介',
    'hospital':     '藤枝市立総合病院',
    'hospital_tel': '054-646-1111',
    'address':      '藤枝市横内800-16',
    'restroom':     '事務所',
    'made_date':    '',
    'made_by':      '',
}

RED     = colors.HexColor('#c0392b')
DARKRED = colors.HexColor('#7f1d1d')
NAVY    = colors.HexColor('#2c3e6b')
LGRAY   = colors.HexColor('#f4f5f7')
MGRAY   = colors.HexColor('#dde1e8')
YELLOW  = colors.HexColor('#fef9e7')
WHITE   = colors.white

S = {
    'title':    ParagraphStyle('title', fontName=F, fontSize=20, textColor=DARKRED,
                               alignment=TA_CENTER, leading=24, spaceAfter=1),
    'subtitle': ParagraphStyle('subtitle', fontName=F, fontSize=8, textColor=colors.HexColor('#555555'),
                               alignment=TA_CENTER, leading=11),
    'sec':      ParagraphStyle('sec', fontName=F, fontSize=11, textColor=WHITE, backColor=NAVY,
                               leftIndent=4, spaceBefore=3, spaceAfter=2, leading=16),
    'secred':   ParagraphStyle('secred', fontName=F, fontSize=11, textColor=WHITE, backColor=DARKRED,
                               leftIndent=4, spaceBefore=3, spaceAfter=2, leading=16),
    'body':     ParagraphStyle('body', fontName=F, fontSize=9, textColor=colors.HexColor('#1a1a2e'), leading=13.5),
    'bodyc':    ParagraphStyle('bodyc', fontName=F, fontSize=9, textColor=colors.HexColor('#1a1a2e'),
                               leading=13.5, alignment=TA_CENTER),
    'step_no':  ParagraphStyle('step_no', fontName=F, fontSize=11, textColor=WHITE, alignment=TA_CENTER, leading=14),
    'step_t':   ParagraphStyle('step_t', fontName=F, fontSize=11, textColor=DARKRED, leading=14),
    'step_b':   ParagraphStyle('step_b', fontName=F, fontSize=8.8, textColor=colors.HexColor('#1a1a2e'), leading=12.5),
    'warn':     ParagraphStyle('warn', fontName=F, fontSize=9, textColor=RED, leading=13),
    'big119':   ParagraphStyle('big119', fontName=F, fontSize=15, textColor=WHITE, alignment=TA_CENTER, leading=19),
    'fill':     ParagraphStyle('fill', fontName=F, fontSize=9.5, textColor=colors.HexColor('#1a1a2e'), leading=17),
    'note':     ParagraphStyle('note', fontName=F, fontSize=7.5, textColor=colors.HexColor('#555555'), leading=10.5),
}


class FilledField(Paragraph):
    """記入欄。値があればその文字を、無ければ記入用の下線だけを描く。

    PDFの入力フォーム（AcroForm）は、ビューアによって入力値が表示されない
    ことがあったため使わない。値は文字として直接描き込む。
    """

    def __init__(self, value, width):
        self._val = (value or '').strip()
        self._w = width
        super().__init__(
            ('<b>%s</b>' % self._val) if self._val else '', S['fill'])

    def wrap(self, aw, ah):
        self._w = min(self._w, aw)
        Paragraph.wrap(self, self._w, ah)
        return self._w, 14

    def drawOn(self, canv, x, y, _sW=0):
        # 記入線（未記入の欄は手書きできるように、記入済みでも下線を残す）
        canv.setStrokeColor(colors.HexColor('#9aa3b2'))
        canv.setLineWidth(0.5)
        canv.line(x, y, x + self._w, y)
        if self._val:
            Paragraph.drawOn(self, canv, x + 2, y + 3, _sW)


def build(out_path):
    doc = SimpleDocTemplate(out_path, pagesize=A4, leftMargin=11 * mm, rightMargin=11 * mm,
                            topMargin=8 * mm, bottomMargin=7 * mm,
                            title='熱中症 緊急対応手順', author='橋本工業株式会社')
    st = []

    st.append(Paragraph('熱中症　緊急対応手順', S['title']))
    st.append(Paragraph('橋本工業株式会社　／　作業場に掲示すること　（労働安全衛生規則 2025年6月施行の義務対応）', S['subtitle']))
    st.append(HRFlowable(width='100%', thickness=2, color=DARKRED, spaceAfter=4))

    # ── 1. 報告体制 ──
    st.append(Paragraph('■ １．おかしいと思ったら、すぐ報告（全員へ）', S['secred']))
    rep = [[Paragraph(
        '● <b>自分の体調がおかしい</b>と思ったら　→　<b>すぐ作業を止めて報告する</b><br/>'
        '● <b>誰かの様子がおかしい</b>と思ったら　→　<b>すぐ声をかけ、代わりに報告する</b><br/><br/>'
        '<b>報告先：　ラインリーダー　→　安全衛生担当</b>　（不在時は近くの社員なら誰でもよい）', S['body'])]]
    t = Table(rep, colWidths=[188 * mm])
    t.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 1, NAVY), ('BACKGROUND', (0, 0), (-1, -1), LGRAY),
                           ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                           ('LEFTPADDING', (0, 0), (-1, -1), 7)]))
    st.append(t)
    st.append(Paragraph('★ <b>我慢しない・させない。</b>本人の「大丈夫です」を信じないこと。熱中症は本人の判断力が落ちます。', S['warn']))

    # ── 2. 応急処置 ──
    st.append(Paragraph('■ ２．応急処置の手順', S['secred']))

    def step(no, title, body):
        return [Paragraph(no, S['step_no']), Paragraph(title, S['step_t']), Paragraph(body, S['step_b'])]

    steps = [
        step('1', '作業を離れる',
             'すぐに作業を中止し、<b>涼しい場所</b>へ移動する（エアコンのある休憩室・日陰）。<br/>'
             '<font color="#c0392b"><b>★ 絶対に一人にしない。必ず誰かが付き添う。</b></font>'),
        step('2', '体を冷やす',
             '衣服をゆるめる（ボタン・ベルト・作業着）。<br/>'
             '<b>首・わきの下・脚の付け根</b>を氷や冷たいペットボトルで冷やす。体に水をかけ、扇風機で風を当てる。'),
        step('3', '水分・塩分をとる',
             '<b>意識がはっきりしていて、自力で飲める場合のみ</b>。経口補水液・スポーツドリンクを与える。<br/>'
             '<font color="#c0392b"><b>★ 自力で飲めないなら、無理に飲ませない　→　すぐ医療機関へ。</b></font>'),
    ]
    t = Table(steps, colWidths=[10 * mm, 30 * mm, 148 * mm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), F),
        ('BACKGROUND', (0, 0), (0, -1), DARKRED),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, MGRAY),
        ('ROWBACKGROUNDS', (1, 0), (-1, -1), [WHITE, LGRAY]),
        ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    st.append(t)

    # ── 3. 119番 ──
    st.append(Spacer(1, 2 * mm))
    t = Table([[Paragraph('すぐに<b>１１９番</b>　―　迷ったら呼ぶ。ためらわない。', S['big119'])]], colWidths=[188 * mm])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), RED),
                           ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    st.append(t)

    chk = [
        [Paragraph('□　<b>意識がない</b>・呼びかけへの反応がおかしい', S['body']),
         Paragraph('□　<b>自力で水分がとれない</b>', S['body'])],
        [Paragraph('□　まっすぐ歩けない・けいれんしている', S['body']),
         Paragraph('□　体が熱いのに<b>汗が出ていない</b>', S['body'])],
        [Paragraph('□　冷やしても<b>症状が良くならない</b>', S['body']),
         Paragraph('□　嘔吐している・水分を受けつけない', S['body'])],
    ]
    t = Table(chk, colWidths=[94 * mm, 94 * mm])
    t.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 1.2, RED), ('INNERGRID', (0, 0), (-1, -1), 0.4, MGRAY),
                           ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fdecea')),
                           ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                           ('LEFTPADDING', (0, 0), (-1, -1), 6)]))
    st.append(t)
    st.append(Paragraph('※ 救急車を待つ間も、<b>体を冷やし続ける</b>こと。付き添いを離さない。', S['warn']))

    # ── 4. 緊急連絡先（入力フォーム） ──
    st.append(Paragraph('■ ３．緊急連絡先', S['sec']))
    C = CONTACTS
    contacts = [
        [Paragraph('救急', S['fill']), Paragraph('<b>１１９</b>', S['fill']),
         Paragraph('社内 責任者', S['fill']), FilledField(C.get('responsible'), 74 * mm)],
        [Paragraph('最寄り医療機関', S['fill']), FilledField(C.get('hospital'), 48 * mm),
         Paragraph('TEL', S['fill']), FilledField(C.get('hospital_tel'), 74 * mm)],
        [Paragraph('会社の所在地<br/>（救急に伝える）', S['fill']), FilledField(C.get('address'), 48 * mm),
         Paragraph('休憩場所', S['fill']), FilledField(C.get('restroom'), 74 * mm)],
    ]
    t = Table(contacts, colWidths=[32 * mm, 52 * mm, 26 * mm, 78 * mm])
    t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, MGRAY), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                           ('BACKGROUND', (0, 0), (0, -1), LGRAY), ('BACKGROUND', (2, 0), (2, -1), LGRAY),
                           ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                           ('LEFTPADDING', (0, 0), (-1, -1), 5)]))
    st.append(t)

    # ── 5. 予防（WBGT） ──
    st.append(Paragraph('■ ４．予防　―　暑さ指数（WBGT）を確認してから作業する', S['sec']))
    wbgt = [[Paragraph('<b>作業の種類</b>', S['bodyc']), Paragraph('<b>通常</b>', S['bodyc']),
             Paragraph('<b>暑熱順化なし</b>', S['bodyc'])]]
    for name, n, a in WORKS:
        wbgt.append([Paragraph('<b>%s</b>' % name, S['bodyc']),
                     Paragraph('<b>%g℃</b>' % n, S['bodyc']),
                     Paragraph('<font color="#c0392b"><b>%g℃</b></font>' % a, S['bodyc'])])
    t = Table(wbgt, colWidths=[74 * mm, 57 * mm, 57 * mm])
    t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, MGRAY), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                           ('BACKGROUND', (0, 0), (-1, 0), NAVY), ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                           ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LGRAY]),
                           ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6)]))
    st.append(t)
    st.append(Paragraph(
        '<b>暑熱順化なし</b>＝ ① この作業に慣れていない人　② 連休明けの人　③ 体調を崩して復帰した直後の人', S['note']))

    st.append(Spacer(1, 1 * mm))
    act = [[Paragraph(
        '<b>この値を超えたら</b>　→　① <b>休憩を増やす（60分作業　→　15分休憩）</b>　'
        '② <b>単独作業をさせない</b>', S['body'])]]
    t = Table(act, colWidths=[188 * mm])
    t.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e0c66b')),
                           ('BACKGROUND', (0, 0), (-1, -1), YELLOW),
                           ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                           ('LEFTPADDING', (0, 0), (-1, -1), 7)]))
    st.append(t)

    # 危険域は基準値に関わらず中止（システム側と同じ扱い）
    dg = [[Paragraph('<b>WBGT %d℃以上（危険）　→　上の基準値にかかわらず、全作業を中止・延期する。</b>'
                     'やむを得ず作業する場合は必ず監視者をつける。' % DANGER, S['big119'])]]
    t = Table(dg, colWidths=[188 * mm])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), RED),
                           ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                           ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7)]))
    st.append(t)

    st.append(Spacer(1, 1.5 * mm))
    st.append(Paragraph(
        '※ 暑さ指数計は<b>「屋内モード」</b>で使用。測定は<b>熱源の近く・風の通らない場所</b>（いちばん条件の悪い所）。'
        '黒球は安定に15〜20分かかるため、<b>持ち回りでの測定は不可</b>。測定場所ごとに常設すること。　'
        '／ 水分・塩分は<b>のどが渇く前に</b>。経口補水液・塩分タブレットを常備。　'
        '／ 測定値はH-Hub（製造現場）・金型管理システム（技術現場）に記録すること。', S['note']))
    st.append(HRFlowable(width='100%', thickness=0.8, color=MGRAY, spaceBefore=2))

    foot = [[Paragraph('作成日', S['note']), FilledField(C.get('made_date'), 28 * mm),
             Paragraph('作成者', S['note']), FilledField(C.get('made_by'), 32 * mm),
             Paragraph('橋本工業株式会社　安全衛生', S['note'])]]
    t = Table(foot, colWidths=[12 * mm, 30 * mm, 12 * mm, 34 * mm, 96 * mm])
    t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                           ('LEFTPADDING', (0, 0), (-1, -1), 2), ('TOPPADDING', (0, 0), (-1, -1), 2)]))
    st.append(t)

    doc.build(st)
    print('作成しました:', out_path)


if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else '熱中症_緊急対応手順_掲示用.pdf')
