#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""金型マニュアル要約版（社内教育用）A4縦

出典は中小企業総合事業団の公開マニュアル2冊（平成12〜13年度 ものづくり人材支援基盤整備事業）:
  ・プログレッシブプレス金型 設計マニュアル（179ページ）
  ・プレス加工用金型の組立・調整マニュアル（72ページ）
公的機関の技術伝承教材であり、社内教育に利用できる。要点を抜き出し社員が読める分量にまとめる。

使い方:
    python make_manual_digest.py 出力先.pdf

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
from reportlab.platypus import (HRFlowable, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
F = 'HeiseiKakuGo-W5'

NAVY  = colors.HexColor('#1f3864')
BLUE  = colors.HexColor('#2e5c9a')
LGRAY = colors.HexColor('#f2f4f8')
MGRAY = colors.HexColor('#c8cfda')
RED   = colors.HexColor('#a4262c')
AMBER = colors.HexColor('#fdf6e3')
GREEN = colors.HexColor('#eef6ee')

S = {
    'title': ParagraphStyle('t', fontName=F, fontSize=17, textColor=NAVY, alignment=TA_CENTER, leading=22),
    'sub':   ParagraphStyle('s', fontName=F, fontSize=8.5, textColor=colors.HexColor('#555'), alignment=TA_CENTER, leading=12),
    'h1':    ParagraphStyle('h1', fontName=F, fontSize=12, textColor=colors.white, backColor=NAVY,
                            leftIndent=5, spaceBefore=8, spaceAfter=4, leading=18),
    'h2':    ParagraphStyle('h2', fontName=F, fontSize=10.5, textColor=NAVY, spaceBefore=6, spaceAfter=2, leading=15),
    'b':     ParagraphStyle('b', fontName=F, fontSize=9, textColor=colors.HexColor('#1a1a2e'), leading=13.8),
    'bc':    ParagraphStyle('bc', fontName=F, fontSize=9, textColor=colors.HexColor('#1a1a2e'), leading=13.8, alignment=TA_CENTER),
    'hw':    ParagraphStyle('hw', fontName=F, fontSize=9, textColor=colors.white, leading=13.5),
    'hwc':   ParagraphStyle('hwc', fontName=F, fontSize=9, textColor=colors.white, leading=13.5, alignment=TA_CENTER),
    'note':  ParagraphStyle('n', fontName=F, fontSize=7.8, textColor=colors.HexColor('#666'), leading=11),
    'lead':  ParagraphStyle('l', fontName=F, fontSize=9.5, textColor=colors.HexColor('#1a1a2e'), leading=15),
}
W = 188 * mm


def h1(t):
    return Paragraph('■ ' + t, S['h1'])


def h2(t):
    return Paragraph('◆ ' + t, S['h2'])


def p(t):
    return Paragraph(t, S['b'])


def bullets(items):
    """・付きの箇条書き。1項目1段落"""
    return [Paragraph('・' + i, S['b']) for i in items]


def tbl(rows, widths, head=True, bg=None):
    t = Table(rows, colWidths=widths)
    st = [('GRID', (0, 0), (-1, -1), 0.5, MGRAY), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
          ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
          ('LEFTPADDING', (0, 0), (-1, -1), 5)]
    if head:
        st.append(('BACKGROUND', (0, 0), (-1, 0), BLUE))
    if bg:
        st.append(('BACKGROUND', (0, 1), (-1, -1), bg))
    t.setStyle(TableStyle(st))
    return t


def box(text, bg=AMBER, border='#e0c66b'):
    t = Table([[Paragraph(text, S['b'])]], colWidths=[W])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), bg),
                           ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor(border)),
                           ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                           ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8)]))
    return t


def build(out):
    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=11 * mm, rightMargin=11 * mm,
                            topMargin=10 * mm, bottomMargin=12 * mm,
                            title='プレス金型 設計・組立の基礎', author='橋本工業株式会社')
    st = []

    # ───────────────────────── 表紙相当 ─────────────────────────
    st.append(Paragraph('プレス金型　設計・組立の基礎', S['title']))
    st.append(Paragraph('社内教育用ダイジェスト　／　橋本工業株式会社　技術部', S['sub']))
    st.append(HRFlowable(width='100%', thickness=1.5, color=NAVY, spaceAfter=6))
    st.append(box(
        '本書は、中小企業総合事業団が公開している技術伝承マニュアル2冊（'
        '「プログレッシブプレス金型 設計マニュアル」179頁、「プレス加工用金型の組立・調整マニュアル」72頁）から、'
        '<b>現場ですぐ使う要点だけを抜き出した</b>ものです。<br/>'
        '詳しく知りたいときは原本を参照してください（技術部に保管）。'))

    # ───────────────────────── 1. 全体の流れ ─────────────────────────
    st.append(h1('１．金型ができるまでの流れ'))
    flow = [[Paragraph('<b>①製品図の理解</b>', S['hwc']), Paragraph('<b>②工程設計<br/>レイアウト</b>', S['hwc']),
             Paragraph('<b>③金型設計</b>', S['hwc']), Paragraph('<b>④部品加工</b>', S['hwc']),
             Paragraph('<b>⑤組立</b>', S['hwc']), Paragraph('<b>⑥トライ<br/>調整</b>', S['hwc'])],
            [p('材質・板厚<br/>公差・バリ方向<br/>基準穴'), p('工程順序<br/>ピッチ<br/>キャリア'),
             p('構造・材質<br/>部品配置<br/>逃がし'), p('精度が組立の<br/>手間を決める'),
             p('刃合わせ<br/>クリアランス<br/>調整'), p('実際に打って<br/>直す<br/>ここが本番')]]
    st.append(tbl(flow, [W / 6] * 6))
    st.append(Spacer(1, 2 * mm))
    st.append(box('<b>金型は「部品が全部できた時点」では完成していない。</b>'
                  '組立・調整で初めて金型になる。ここに時間がかかることを前提に日程を組むこと。', GREEN, '#9fbf9f'))

    # ───────────────────────── 2. 設計 ─────────────────────────
    st.append(h1('２．設計で押さえること'))

    st.append(h2('製品図から必ず読み取る項目'))
    st.extend(bullets([
        '<b>材質・板厚</b>　… トライは必ず量産と同じ材料で行う。材質が違えば結果は当てにならない',
        '<b>バリ方向の指定</b>　… 抜き方向が決まる。指定を見落とすと全数不良になる',
        '<b>基準穴・測定基準</b>　… どの穴を基準に測るか。パイロット位置と関係する',
        '<b>公差の厳しい寸法</b>　… 同一工程内で加工するのが原則。工程をまたぐとバラツキが乗る',
        '<b>曲げ部の近くの穴</b>　… 曲げで変形する。逃がすか、曲げ後に抜く',
    ]))

    st.append(h2('ストリップレイアウト（順送）の基本'))
    st.extend(bullets([
        '<b>難しい加工ほど前の工程に置く</b>　… 後工程でのやり直しが効かなくなるため',
        '<b>アイドルステージを入れる</b>　… ①材料の傾き防止 ②パンチ同士の干渉回避 ③強度確保',
        '<b>パイロットで位置決めする</b>　… 送り装置の精度だけに頼らない。製品穴を使う（直接）か'
        '捨て穴を明ける（間接）。<b>直接は材料が節約でき、間接は製品を選ばない</b>',
        '<b>キャリア（つなぎ）は、加工の邪魔をしない・製品品質に影響しない位置に</b>',
        '<b>材料歩留りを意識する</b>　… レイアウトで原価がほぼ決まる',
    ]))

    st.append(h2('部品を分割・入れ子にする理由'))
    st.append(p('1枚のダイで全部加工すると、<b>1箇所欠けただけで全部作り直し</b>になる。'
                'また抜き部と曲げ部では研磨の減り方が違うため、一体だと再研磨で高さが合わなくなる。'))
    st.append(tbl([
        [Paragraph('<b>構造</b>', S['hwc']), Paragraph('<b>長所</b>', S['hw']), Paragraph('<b>短所</b>', S['hw'])],
        [p('一体ダイ'), p('部品点数が少ない'), p('ピッチ誤差の修正が困難／再研磨が困難／破損時に全交換')],
        [p('入れ子・分割'), p('破損箇所だけ交換／再研磨後にシムで高さ調整できる／ノックアウト、ばねの取付が容易'),
         p('部品点数が増える／位置決め精度が必要')],
    ], [30 * mm, 84 * mm, 74 * mm]))
    st.append(Spacer(1, 1.5 * mm))
    st.append(p('<b>入れ子はボルトで固定する（圧入にしない）。</b>量産中の振動で緩んだり、'
                '交換時に外せなくなるのを防ぐため。'))

    st.append(PageBreak())

    # ───────────────────────── 3. 組立 ─────────────────────────
    st.append(h1('３．組立の勘どころ（熟練者のやり方）'))

    st.append(h2('着手前のチェック　― ここを飛ばすと後で必ず戻る'))
    st.append(tbl([
        [Paragraph('<b>確認すること</b>', S['hw']), Paragraph('<b>なぜ</b>', S['hw'])],
        [p('部品表どおり部品が揃っているか／検査表は付いているか'), p('欠品に組立途中で気づくと日程が崩れる')],
        [p('<b>図面の桁を確認する</b>（十分代・百分代・千分代）'), p('<b>一桁の間違いが実際によくある</b>')],
        [p('表裏が逆になっていないか'), p('加工者の取り違えが起きやすい')],
        [p('手で持てる部品は、パンチとダイを合わせてみる'), p('組む前に合うか分かる')],
        [p('刃物の焼入れ硬度（ヤスリが引っかかれば硬度不足）'), p('硬度不足の刃物はすぐ欠ける')],
        [p('刃先の欠け・チッピング、キズの有無'), p('傷は製品に転写する')],
        [p('プレス機械と金型の仕様が合っているか／ダイセットの平行'), p('取り付かない・精度が出ない')],
    ], [96 * mm, 92 * mm]))

    st.append(h2('組立の手順（順送型の例）'))
    st.extend(bullets([
        '<b>下型のダイから組む。</b>ダイプレートの位置決めはダイセットのポストから平行を出す'
        '（ここが狂うとフープ材が正しく送れない）',
        '<b>入れ子を組む前に側面にグリースを塗る。</b>入れ子と穴の両方を保護するため。省略しない',
        '入れ子とプレート面の段差は<b>爪で撫でて確認</b>する。引っかかれば 0.03〜0.05mm 程度の段差がある',
        '<b>ストリッパをかぶせるときはパンチを本締めしない。</b>穴に無理なく入るか確認してから、'
        '<b>大きいパンチから順に本締め</b>する',
        '細いパンチは音で分かる。<b>「ピン」という音がしたら、しなってガイド穴に入っている合図</b>。'
        '光明丹を使って当たりを見る',
        '<b>ボルトは対角線で少しずつ締める。</b>1本ずつ本締めしてはいけない。'
        '全体を仮締めしてからノックピンを打ち、その後に本締めする',
    ]))

    st.append(box('<b>クリアランスは目視だけで判断しない。</b>「だろう」で進めない。'
                  '隙間を感じたらルーペで拡大し、それでも見にくければ顕微鏡を使う。', GREEN, '#9fbf9f'))

    # ───────────────────────── 4. トライ ─────────────────────────
    st.append(h1('４．トライ（試し加工）の進め方'))
    st.append(tbl([
        [Paragraph('<b>段階</b>', S['hwc']), Paragraph('<b>やること</b>', S['hw'])],
        [p('<b>加工前</b>'), p('①ボルトの緩み点検　②摺動部への給油　③刃先の状態確認　④ミス検出装置の点検')],
        [p('<b>1回目</b>'), p('<b>破損しやすい部品は外しておく。下死点は少し高めにセット。</b>'
                            'まず空運転（手回しか寸動で1行程）。<b>異音に注意。</b>'
                            '順送では材料が金型を通過するまで手送り')],
        [p('<b>2回目以降</b>'), p('異常がないことを確認しながら、<b>少しずつ正しい下死点へ近づける</b>')],
        [p('<b>サンプル採取</b>'), p('<b>必ず正規のSPMで連続加工して採る。</b>'
                                 '寸動で打った分は除く（条件が違うため評価にならない）')],
        [p('<b>加工後</b>'), p('金型を開いてダイ・ストリッパ面を点検（破損、変形、金属粉の付着、焼き付き）／'
                            'ボルト・キーの緩み／ばねの破損・へたり')],
    ], [26 * mm, 162 * mm]))

    st.append(PageBreak())

    # ───────────────────────── 5. トラブル対応 ─────────────────────────
    st.append(h1('５．不具合が出たときの見どころ'))
    st.append(p('原本には12種類の「トラブル相関図」があり、症状から原因をたどれる。ここでは代表的なものを要約する。'))

    st.append(h2('バリが出る'))
    st.append(tbl([
        [Paragraph('<b>症状</b>', S['hw']), Paragraph('<b>主な原因と対策</b>', S['hw'])],
        [p('最初から全周にバリ'), p('クリアランスが大きい／プレスの剛性不足・水平精度不良／加工油が少ない')],
        [p('少し経つとバリが出る'), p('パンチ・ダイの摩耗　→　<b>研磨のタイミングを見直す</b>')],
        [p('片側だけバリ'), p('クリアランスの片寄り　→　芯出しをやり直す')],
    ], [46 * mm, 142 * mm]))

    st.append(h2('カス上がり・カス詰まり'))
    st.extend(bullets([
        '<b>クリアランスが大きすぎないか</b>を最初に確認する',
        '対策：①上からエアーで吹く　②吸引する　③両方併用　④抜き順序・形状を変えて浮きにくくする',
        '<b>逃がし穴は下へいくほど徐々に大きくする。</b>途中で引っかかると詰まる',
        '有効刃先以外の部分にスクラップが乗らない形にする',
    ]))

    st.append(h2('曲げの角度が出ない・割れる'))
    st.extend(bullets([
        '角度が開く　→　クリアランス調整／かみ合いを深くする／スプリングバック対策（曲げ部を強く押す）',
        '<b>曲げ部が割れる</b>　→　<b>バリ面が曲げ外側になっていないか</b>／'
        '<b>曲げ線と材料の目（ロール方向）が平行になっていないか</b>／曲げ幅が狭くないか',
        '曲げキズ　→　ダイ肩Rが小さい、またはRがきれいに出ていない　→　R を大きく・きれいに仕上げる',
    ]))

    st.append(h2('絞りのしわ・割れ'))
    st.extend(bullets([
        'しわ　→　しわ押え圧が弱い／ダイとしわ押えの当たりが一様でない／ダイRが大きい',
        '割れ　→　しわ押えが強すぎる／パンチ・ダイRが小さい／潤滑不足',
        '<b>カジリ</b>　→　ダイ面のキズ、コーティング剥がれ。<b>定期メンテと再コーティングで防ぐ</b>',
    ]))

    st.append(h2('順送で材料がうまく流れない'))
    st.append(tbl([
        [Paragraph('<b>症状</b>', S['hw']), Paragraph('<b>確認する場所</b>', S['hw'])],
        [p('パイロットで材料が吊り上がる'), p('穴とパイロット径／パイロットのストレート部の出寸法／リフターとの関係')],
        [p('材料にキズが付く'), p('リフターの面・角の仕上げ／リフターのばね強さ／ダイ・ストリッパ面の凹凸')],
        [p('送り途中で材料が座屈する'), p('ガイドピンの間隔／ガイドとリフターの関係／リフターの角R')],
    ], [56 * mm, 132 * mm]))

    # ───────────────────────── 6. まとめ ─────────────────────────
    st.append(h1('６．覚えておきたい要点'))
    st.append(tbl([
        [p('<b>1</b>'), p('<b>金型は組立・調整で完成する。</b>部品ができた時点では半分')],
        [p('<b>2</b>'), p('<b>トライは量産と同じ材料・同じSPMで。</b>条件が違えば評価にならない')],
        [p('<b>3</b>'), p('<b>入れ子・分割にしておく。</b>壊れた所だけ直せる。再研磨も楽になる')],
        [p('<b>4</b>'), p('<b>ボルトは対角線で。</b>1本ずつ本締めしない')],
        [p('<b>5</b>'), p('<b>「だろう」で進めない。</b>ルーペで見る、爪で触る、音を聞く')],
        [p('<b>6</b>'), p('<b>図面の桁を確認する。</b>一桁違いは実際に起きている')],
        [p('<b>7</b>'), p('<b>バリ方向・材料の目の向きは、割れに直結する</b>')],
    ], [12 * mm, 176 * mm], head=False, bg=LGRAY))

    st.append(Spacer(1, 3 * mm))
    st.append(Paragraph(
        '出典：中小企業総合事業団「プログレッシブプレス金型 設計マニュアル」（平成13年2月）／'
        '「プレス加工用金型の組立・調整マニュアル」。'
        'いずれも ものづくり人材支援基盤整備事業の成果物。原本は技術部に保管。', S['note']))

    doc.build(st)
    print('作成しました:', out)


if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else '金型マニュアル要約.pdf')
