# -*- coding: utf-8 -*-
"""基準遵守手当 減点項目マスタ PDF生成（日本語版／英語版）

使い方:
    python master_pdf.py ja  出力先.pdf
    python master_pdf.py en  出力先.pdf

マスタの正本は Z:\全社共有\総務\基準遵守\【基準遵守手当】\【手当】基準遵守手当マスタ.xlsx。
改訂したら、このファイル下部の ITEMS を Excel に合わせて直し、REV / EFFECTIVE を更新する。
新規追加した項目は new=True にすると PDF 上に ★ と緑枠が付く（次の改訂では False に戻す）。

依存: pip install reportlab
日本語フォントは Windows の Meiryo / 游ゴシックを自動検出する。
"""
import os
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as _canvas
from reportlab.platypus import (BaseDocTemplate, Frame, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

REV = "Rev.1.3"
EFFECTIVE = {"ja": "2026年7月17日", "en": "July 17, 2026"}

# ---------------------------------------------------------------- fonts
FONT = FONT_B = None
for _name, _reg, _bold in [
    ("Meiryo", r"C:\Windows\Fonts\meiryo.ttc", r"C:\Windows\Fonts\meiryob.ttc"),
    ("YuGothic", r"C:\Windows\Fonts\YuGothM.ttc", r"C:\Windows\Fonts\YuGothB.ttc"),
]:
    if os.path.exists(_reg):
        try:
            pdfmetrics.registerFont(TTFont(_name, _reg, subfontIndex=0))
            pdfmetrics.registerFont(TTFont(_name + "-B", _bold, subfontIndex=0))
            FONT, FONT_B = _name, _name + "-B"
            break
        except Exception:
            pass
if not FONT:
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
    FONT = FONT_B = "HeiseiKakuGo-W5"

# ---------------------------------------------------------------- palette
NAVY = colors.HexColor("#1F4E79")
HDR = colors.HexColor("#2E75B6")
BAND = colors.HexColor("#DEEBF7")
A_BG = colors.HexColor("#DDEBF7")
B_BG = colors.HexColor("#FFF2CC")
C_BG = colors.HexColor("#FCE4E4")
GRID = colors.HexColor("#B4C7DC")
RED = colors.HexColor("#C00000")
BLUE = colors.HexColor("#1F6FC0")
AMBER = colors.HexColor("#BF8F00")
NEWBG = colors.HexColor("#E2EFDA")
NEWFG = colors.HexColor("#1E7B34")

PAGE_W, PAGE_H = landscape(A4)
MARGIN = 14 * mm
USABLE = PAGE_W - 2 * MARGIN


def hx(c):
    return "#" + c.hexval()[2:]


def P(txt, size=7.6, font=None, color=colors.black, align=TA_LEFT, lead=None):
    return Paragraph(txt, ParagraphStyle(
        "x", fontName=font or FONT, fontSize=size, leading=lead or size + 2.2,
        textColor=color, alignment=align))


st_h = lambda t: P(t, 7.6, FONT_B, colors.white, TA_CENTER)
st_c = lambda t: P(t, 7.6, FONT, align=TA_CENTER)
st_l = lambda t: P(t, 7.6, FONT)
st_note = lambda t: P(t, 7, FONT, colors.HexColor("#444444"))

# ---------------------------------------------------------------- 語彙
# 判定区分: キー -> (日本語, English, ●の色)
VERIFY = {
    "witness": ("現認", "Witnessed", RED),
    "patrol": ("巡回", "Inspection", AMBER),
    "kintone": ("キントーン", "Kintone", BLUE),
    "board": ("進捗ボード", "Progress Board", RED),
}

# 波及範囲
SCOPE = {
    "solo": ("個人のみ", "Individual only"),
    "team": ("個人＋チーム", "Individual + Team"),
    "all": ("個人＋チーム＋全社", "Individual + Team + Company-wide"),
    "press": ("個人＋チーム（プレス／組立）", "Individual + Team (Press / Assembly)"),
    "press_qa": ("個人＋チーム（プレス＋品質／組立＋品質）",
                 "Individual + Team (Press+QA / Assembly+QA)"),
    "qa": ("品質", "QA"),
    "solo_qa": ("個人＋品質", "Individual + QA"),
    "eng": ("技術", "Engineering"),
    "solo_eng": ("個人＋技術", "Individual + Engineering"),
    "ga": ("個人＋総務", "Individual + General Affairs"),
    "log": ("納入管理", "Logistics"),
    "solo_log": ("個人＋納入管理", "Individual + Logistics"),
}

# 記録者
REC = {
    "qa_lead": ("品管リーダー", "QA Team Lead"),
    "sup": ("直属リーダー", "Direct Supervisor"),
    "ga": ("総務", "General Affairs"),
    "sup_ga": ("直属リーダー・総務", "Direct Supervisor / General Affairs"),
    "card": ("タイムカード", "Time Card"),
    "prod": ("製造リーダー", "Production Lead"),
    "eng": ("技術担当", "Engineering Staff"),
    "payroll": ("給与確定時に判明", "At Payroll Finalization"),
    "post": ("事後確認", "Post-check"),
    "sheet": ("減点記録シート", "Deduction Record Sheet"),
}

# カテゴリ
CAT = {
    "quality": ("品質", "Quality"),
    "safety": ("安全", "Safety"),
    "5s": ("5S", "5S"),
    "attend": ("勤怠", "Attendance"),
    "report": ("報告", "Reporting"),
    "response": ("対応", "Response"),
    "productivity": ("生産性", "Productivity"),
    "records": ("記録", "Records"),
    "storage": ("保管", "Storage"),
    "delivery": ("納期", "Delivery"),
    "submission": ("提出物", "Submission"),
    "mgmt": ("管理", "Management"),
    "hs": ("安全衛生", "Health & Safety"),
    "qty": ("数量", "Quantity"),
    "docs": ("書類", "Documents"),
}


def I(no, cat, ja, en, pt, pat, scope, verify, rec, new=False):
    """減点項目1行。ja/en は項目・発動条件の本文。"""
    return dict(no=no, cat=cat, text=(ja, en), pt=pt, pat=pat,
                scope=scope, verify=verify, rec=rec, new=new)


# ---------------------------------------------------------------- ①共通
COMMON = [
    I(1, "quality", "客先流出不良　1件ごと",
      "Customer-reported defect, per occurrence",
      50, "C", "all", "witness", "qa_lead"),
    I(2, "safety", "労働災害・危険行為・安全装置の無効化／迂回",
      "Workplace accident, dangerous behavior, disabling/bypassing safety devices",
      50, "C", "all", "witness", "sup"),
    I(3, "safety", "安全ルールの違反・保護具の未着用",
      "Violation of safety rules / not wearing PPE",
      20, "A", "solo", "witness", "sup"),
    I(4, "5s", "5S巡回チェックで指摘（2回目から）　※金型・工具以外",
      "Flagged in 5S inspection (2nd time onward) * Excluding molds/tools",
      20, "B", "team", "patrol", "sup"),
    I(5, "5s", "指摘後3日以内に未対応",
      "No corrective action within 3 days of being flagged",
      30, "B", "team", "kintone", "sup"),
    I(6, "5s", "手順・ルール不遵守（報連相含む）",
      "Failure to follow procedures/rules (incl. reporting)",
      20, "B", "team", "witness", "sup"),
    I(7, "5s", "当番業務未実施（トイレ・2階・外周・休憩所清掃など）",
      "Failure to perform assigned duty (restroom, 2nd floor, perimeter, break room cleaning, etc.)",
      10, "A", "solo", "witness", "ga"),
    I(8, "attend", "遅刻・欠勤（事前連絡あり）　1回",
      "Late arrival/absence with prior notice, 1 occurrence",
      5, "A", "solo", "witness", "card"),
    I(9, "attend", "無断遅刻・欠勤　1回",
      "Unreported late arrival/absence, 1 occurrence",
      50, "A", "solo", "witness", "card"),
    I(10, "attend", "タイムカードの打刻忘れ　1回",
      "Failure to clock in/out, 1 occurrence",
      5, "A", "solo", "witness", "card", new=True),
    I(11, "report", "不具合の隠蔽・意図的な遅延報告",
      "Concealing a defect / intentionally delaying a report",
      50, "C", "all", "witness", "sup"),
    I(12, "response", "他部署からの要望放置（合意した期限を超えた場合）",
      "Ignoring a request from another department (beyond agreed deadline)",
      20, "A", "solo", "kintone", "sup"),
]

# ---------------------------------------------------------------- ②プレス・組立・品質
PRESS = [
    I(1, "productivity", "計画達成率 85〜89%（1日）",
      "Plan achievement rate 85-89% (per day)",
      10, "B", "press", "board", "prod"),
    I(2, "productivity", "計画達成率 85%未満（1日）",
      "Plan achievement rate below 85% (per day)",
      20, "B", "press", "board", "prod"),
    I(3, "productivity", "段取り時間が基準時間の150〜199%　1回",
      "Setup time 150-199% of standard time, 1 occurrence",
      20, "B", "press", "board", "prod"),
    I(4, "productivity", "段取り時間が基準時間の200%超　1回",
      "Setup time over 200% of standard time, 1 occurrence",
      30, "B", "press", "board", "prod"),
    I(5, "quality", "品質チェックシートの誤記・未記入／システム入力間違い・未入力　1回",
      "Quality checklist error/omission, 1 occurrence (System input mistake/omission)",
      10, "B", "press_qa", "witness", "prod"),
    I(6, "quality", "現品票の誤記（品名・数量等）・未添付",
      "Item tag error (product name, quantity, etc.) / not attached",
      10, "B", "press_qa", "witness", "sup"),
    I(7, "quality", "品質n=1確認の未実施",
      "Failure to perform n=1 quality check",
      20, "B", "solo_qa", "witness", "prod"),
    I(8, "quality", "後工程への不良流出　1件",
      "Defect passed to downstream process, 1 occurrence",
      20, "B", "press_qa", "witness", "qa_lead"),
    I(9, "records", "日常点検表の未提出（週末）　1件",
      "Daily inspection sheet not submitted (weekend), 1 occurrence",
      10, "A", "solo", "witness", "prod"),
    I(10, "storage", "金型・工具・測定具類の所定位置への未返却・保管ミス（終業時まで）",
      "Molds/tools/measuring instruments not returned to designated location by end of shift",
      10, "B", "press_qa", "patrol", "sup"),
    I(11, "storage", "保留品・不良品　処置遅れ（3日以内）",
      "Delayed handling of held/defective items, within 3 days",
      20, "B", "qa", "kintone", "prod"),
]

# ---------------------------------------------------------------- ③技術
ENG = [
    I(1, "delivery", "イベントの物出し納期遅延　1件",
      "Delivery delay for an event shipment, 1 occurrence",
      50, "B", "eng", "witness", "eng"),
    I(2, "delivery", "メンテナンス完了の予定日超過　1件",
      "Maintenance completion deadline overrun, 1 occurrence",
      30, "B", "eng", "kintone", "prod"),
    I(3, "quality", "新規金型製作ミス（ミスによる作り直し）　1件",
      "New mold manufacturing error (rework required), 1 occurrence",
      30, "B", "solo_eng", "witness", "eng"),
    I(4, "quality", "メンテ後の金型不良（メンテ起因）　1件",
      "Mold defect after maintenance (caused by maintenance), 1 occurrence",
      30, "B", "solo_eng", "witness", "eng"),
    I(5, "records", "金型実績記録（コスト・工数）の未入力（3日以内に入力完）　1件",
      "Mold performance record (cost/man-hours) not entered within 3 days",
      20, "A", "solo", "witness", "eng"),
    I(6, "records", "日常点検表の未提出（週末）　1件",
      "Daily inspection sheet not submitted (weekend), 1 occurrence",
      10, "A", "solo", "witness", "eng"),
    I(7, "storage", "金型の所定位置への未返却・保管ミス（終業時まで）",
      "Mold not returned to designated location / storage error by end of shift",
      10, "B", "eng", "patrol", "eng"),
    I(8, "storage", "工具・測定器の管理不備（紛失・未返却）、作業台・工具台の整理整頓",
      "Improper management of tools/measuring instruments (lost/not returned), workbench/tool stand organization",
      15, "B", "eng", "patrol", "eng"),
    I(9, "safety", "機械操作ミス（設備への過負荷・損傷）",
      "Machine operation error (overload/damage to equipment)",
      30, "B", "solo_eng", "witness", "eng"),
]

# ---------------------------------------------------------------- ④総務
GA = [
    I(1, "submission", "法定書類の期日遅延　1件",
      "Statutory document deadline overrun, 1 occurrence",
      30, "B", "ga", "witness", "sup"),
    I(2, "submission", "請求書発行（金額間違い・遅延・誤送付等）",
      "Invoice issuance error (wrong amount, delay, wrong recipient, etc.)",
      20, "A", "solo", "witness", "sup"),
    I(3, "submission", "給与計算・社会保険手続きの期日遅延　1件",
      "Payroll/social insurance procedure deadline overrun, 1 occurrence",
      20, "A", "solo", "witness", "sup"),
    I(4, "response", "社員・取引先からの問い合わせ未対応（3営業日超）",
      "No response to employee/client inquiry (over 3 business days)",
      20, "A", "solo", "witness", "sup"),
    I(5, "response", "電話・来客応対の不備（外部からの連絡の伝達漏れ）",
      "Phone/visitor handling failure (message not relayed)",
      20, "A", "solo", "witness", "sup"),
    I(6, "response", "電話着信への未応答（5コール以内に出ない）",
      "Failure to answer an incoming call (not answered within 5 rings)",
      20, "B", "ga", "witness", "sup", new=True),
    I(7, "mgmt", "システムなどへの入力ミス　1件",
      "Data entry error in system, 1 occurrence",
      10, "A", "solo", "witness", "sup"),
    I(8, "mgmt", "備品・消耗品の在庫切れ",
      "Out of stock for supplies/consumables",
      10, "B", "ga", "witness", "sup"),
    I(9, "mgmt", "勤怠集計ミス　1件（残業超過・有給未取得（年5日）／残数管理ミス）",
      "Attendance summary error, 1 occurrence (overtime overage, unused 5-day annual leave, balance management error)",
      20, "B", "ga", "witness", "payroll"),
    I(10, "mgmt", "証憑書類の紛失（領収書・請求書・契約書などの重要書類）",
      "Loss of supporting documents (receipts, invoices, contracts, etc.)",
      20, "B", "ga", "witness", "post"),
    I(11, "hs", "社内安全・5S巡回の未実施",
      "In-house safety/5S inspection not performed",
      30, "B", "ga", "witness", "sheet"),
]

# ---------------------------------------------------------------- ⑤納入管理
LOG = [
    I(1, "delivery", "客先への納期遅延　1件",
      "Delivery delay to customer, 1 occurrence",
      30, "C", "all", "witness", "sup"),
    I(2, "delivery", "社内への部品・材料供給遅延（生産ラインへの影響）",
      "Delay in supplying parts/materials internally (impacting production line)",
      20, "B", "log", "witness", "prod"),
    I(3, "qty", "出荷数量ミス（過不足）　1件",
      "Shipping quantity error (over/short), 1 occurrence",
      30, "B", "solo_log", "witness", "sup"),
    I(4, "qty", "在庫数量の誤記・未更新　1件",
      "Inventory quantity error/not updated, 1 occurrence",
      20, "A", "solo", "witness", "sup"),
    I(5, "docs", "出荷書類（納品書・出荷チェックシート）の記入ミス　1件",
      "Shipping document (delivery note/checklist) entry error, 1 occurrence",
      20, "B", "solo_log", "witness", "sup"),
    I(6, "docs", "出荷書類の提出遅延　1件",
      "Shipping document submission delay, 1 occurrence",
      10, "A", "solo", "witness", "sup"),
    I(7, "response", "電話着信への未応答（5コール以内に出ない）",
      "Failure to answer an incoming call (not answered within 5 rings)",
      20, "B", "solo_log", "witness", "sup_ga", new=True),
    I(8, "storage", "倉庫・棚の整理整頓：巡回指摘",
      "Warehouse/shelf organization: flagged during inspection",
      20, "B", "log", "patrol", "sup"),
    I(9, "storage", "先入先出しルール違反　1件",
      "FIFO (first-in, first-out) rule violation, 1 occurrence",
      20, "B", "log", "witness", "sup"),
    I(10, "records", "日常点検表の未提出（週末）　1件",
      "Daily inspection sheet not submitted (weekend), 1 occurrence",
      10, "A", "solo", "witness", "sup", new=True),
]

# ---------------------------------------------------------------- 部門別 基準pt
DEPTS = [
    (("プレス", "Press"), 200, 20000),
    (("金型製作・メンテ（技術）／品質管理",
      "Mold Manufacturing/Maintenance / Quality Assurance"), 150, 15000),
    (("納入管理／総務／組立", "Logistics / General Affairs / Assembly"), 100, 10000),
]

# ---------------------------------------------------------------- 文言
T = {
    "doc_title": ("橋本工業株式会社　基準遵守手当　減点項目マスタ",
                  "Hashimoto Kogyo Co., Ltd.  Compliance Allowance: Deduction Item Master"),
    "rev": ("{rev}　改訂日：{d}", "{rev}  Effective Date: {d}"),
    "rule_h": ("3層減点ルール　早見表", "3-Tier Deduction Rules"),
    "rule_n": ("個人の減点ポイントを起点に、波及パターンに応じてチーム・全社へ自動展開",
               "Starting from an individual's deduction points, points spill over to team / company-wide based on the pattern"),
    "rule_cols": (["パターン", "本人", "同チーム員\n（本人除く）", "全社員\n（チーム外）", "該当する項目の性質"],
                  ["Pattern", "Self", "Same Team\n(excl. self)", "Company-wide\n(outside team)", "Nature of Applicable Items"]),
    "pat_a": ("A　個人のみ", "A  Individual only"),
    "pat_b": ("B　個人＋チーム", "B  Individual + Team"),
    "pat_c": ("C　個人＋チーム＋全社", "C  Individual + Team + Company-wide"),
    "none": ("なし", "None"),
    "nat_a": ("完全に個人の行動責任（遅刻・保護具未着用・記録未記入など）",
              "Purely individual responsibility (tardiness, not wearing PPE, missing records, etc.)"),
    "nat_b": ("チームで管理すべき項目（5S・社内不良・段取・CT超過・納期遅延など）　※各項目 最大1回／週",
              "Items that should be managed at the team level (5S, in-house defects, setup time, CT overrun, delivery delays, etc.) * Max once per week per item"),
    "nat_c": ("会社の信用・安全に関わる重大事案（客先流出・危険行為・隠蔽など）",
              "Major incidents affecting company trust and safety (customer-reported defects, dangerous behavior, concealment, etc.)"),
    "ex_h": ("具体例　客先流出不良（パターンC・-50pt）が1件発生した場合",
             "Example: One customer-reported defect (Pattern C, -50pt) occurs"),
    "ex_cols": (["対象", "人数（例）", "1人あたり減点", "金額換算", "説明"],
                ["Affected", "Headcount (e.g.)", "Deduction per person", "Amount", "Reason"]),
    "ex_rows": ([("担当者（本人）", "1名", "-50pt", "▲5,000円", "直接責任"),
                 ("同チーム員", "5名", "各 -35pt（50×70%）", "各 ▲3,500円", "管理・連帯責任"),
                 ("全社員（チーム外）", "35名", "各 -25pt（50×50%）", "各 ▲2,500円", "会社信用への影響")],
                [("Person in charge (self)", "1", "-50pt", "JPY -5,000", "Direct responsibility"),
                 ("Same team members", "5", "-35pt each (50x70%)", "JPY -3,500 each", "Supervisory / joint responsibility"),
                 ("Company-wide (outside team)", "35", "-25pt each (50x50%)", "JPY -2,500 each", "Impact on company trust")]),
    "dept_h": ("部門別　基準手当早見表", "Allowance Reference Table by Department"),
    "dept_n": ("月初付与ポイント × 100円 ＝ 基準手当額。月末の残ポイントが実支給額になります。",
               "Points granted at the start of the month x JPY 100 = base allowance. The points remaining at month-end become the amount actually paid."),
    "dept_cols": (["適用部門", "基準pt", "基準手当額", "下限pt", "下限保証額", "備考"],
                  ["Department", "Base Pts", "Base Allowance", "Min. Pts", "Min. Guaranteed Amount", "Notes"]),
    "expect": ("【この設計が生む行動期待】　✔ チーム員が互いに声をかけ合うようになる（あの人のミスが自分にも返ってくるため放置できない）　"
               "✔ 重大案件ほど全社に響く（客先クレーム・安全事故を「自分ごと」として全員が意識する）　"
               "✔ リーダーが部下を気にかける理由ができる（チームの減点が自分にも波及するため、指導・フォローが自然に生まれる）",
               "[Intended behavior] &#10004; Team members start looking out for each other (another person's mistake comes back to you, so it cannot be ignored). "
               "&#10004; The more serious the case, the wider it spreads (customer complaints and safety incidents become everyone's concern). "
               "&#10004; Leaders have a reason to look after their members (team deductions reach the leader too, so coaching and follow-up happen naturally)."),
    "cols": (["No.", "カテゴリ", "減点項目・発動条件", "減点pt", "Pat.", "波及範囲", "判定", "記録者"],
             ["No.", "Category", "Deduction Item / Trigger Condition", "Pts", "Pat.", "Spillover Scope", "Verify", "Recorder"]),
    "s1": ("① 全部門共通　減点項目", "(1) Items Common to All Departments"),
    "s1n": ("全社員に適用。部門固有の項目は ②〜⑤ を参照。",
            "Applies to all employees. See (2)-(5) for department-specific items."),
    "s2": ("② プレス・組立・品質　減点項目", "(2) Press / Assembly / Quality Assurance"),
    "s3": ("③ 金型製作・メンテ（技術）　減点項目", "(3) Mold Manufacturing / Maintenance (Engineering)"),
    "s4": ("④ 総務　減点項目", "(4) General Affairs"),
    "s5": ("⑤ 納入管理　減点項目", "(5) Logistics"),
    "sn": ("共通項目（①）に加えて適用。", "Applies in addition to common items (1)."),
    "press_note": ("※ 段取り時間は150〜199%でNo.3、200%超でNo.4のみ適用（重複カウントなし）。計画達成率はプレス進捗ダッシュボードのデータを参照。",
                   "* For setup time, only No.3 (150-199%) or No.4 (over 200%) applies, never both. Plan achievement rate is based on the Press Production Progress Dashboard."),
    "lg_v": ("【判定区分】", "[Verification Type]"),
    "lg_witness": ("現認＝その場の目撃・証拠が必要", "Witnessed = requires on-the-spot observation/evidence"),
    "lg_patrol": ("巡回＝5S／安全巡回チェックで判定", "Inspection = determined by the 5S / safety inspection"),
    "lg_kintone": ("キントーン＝kintoneの記録から判定", "Kintone = determined from kintone records"),
    "lg_board": ("進捗ボード＝プレス進捗ダッシュボード参照", "Progress Board = based on the Press Progress Dashboard"),
    "lg_p": ("【パターン】", "[Pattern]"),
    "lg_a": ("A＝個人のみ", "A = Individual only"),
    "lg_b": ("B＝個人100%＋チーム×50%", "B = Individual 100% + Team x50%"),
    "lg_c": ("C＝個人100%＋チーム×70%＋全社×50%", "C = Individual 100% + Team x70% + Company-wide x50%"),
    "lg_note": ("（個人が特定できない場合はチームが100%）", "(If the individual cannot be identified, the team is treated as 100%)"),
    "lg_new": ("★＝{rev} 新規追加項目", "&#9733; = newly added in {rev}"),
}


def t(key, lang):
    v = T[key]
    return v[0] if lang == "ja" else v[1]


# ---------------------------------------------------------------- cells
def c_pt(v):
    return P('<font color="%s"><b>-%dpt</b></font>' % (hx(RED), v), 7.8, FONT_B, align=TA_CENTER)


def c_pat(p):
    return P('<font color="%s"><b>%s</b></font>' % (hx({"A": BLUE, "B": AMBER, "C": RED}[p]), p),
             8, FONT_B, align=TA_CENTER)


def c_verify(key, lang):
    ja, en, col = VERIFY[key]
    return P('<font color="%s">&#9679;</font>%s' % (hx(col), ja if lang == "ja" else en),
             7.6, FONT, align=TA_CENTER)


def c_no(n, is_new):
    if is_new:
        return P('<font color="%s"><b>&#9733;%s</b></font>' % (hx(NEWFG), n), 7.6, FONT_B, align=TA_CENTER)
    return P(str(n), 7.6, FONT, align=TA_CENTER)


# 列幅の重み。英語はカテゴリ名が長い（Management / Productivity）ので広めに取る。
_COL_W = {
    "ja": [24, 46, 268, 42, 26, 150, 62, 84],
    "en": [22, 62, 252, 34, 26, 146, 66, 88],
}


def _cols(lang):
    w = _COL_W[lang]
    return [x * USABLE / sum(w) for x in w]


def item_table(rows, lang):
    i18 = 0 if lang == "ja" else 1
    data = [[st_h(h) for h in t("cols", lang)]]
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), HDR),
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]
    for i, r in enumerate(rows, start=1):
        data.append([
            c_no(r["no"], r["new"]),
            st_c(CAT[r["cat"]][i18]),
            st_l(r["text"][i18]),
            c_pt(r["pt"]),
            c_pat(r["pat"]),
            st_l(SCOPE[r["scope"]][i18]),
            c_verify(r["verify"], lang),
            st_l(REC[r["rec"]][i18]),
        ])
        style.append(("BACKGROUND", (0, i), (-1, i), {"A": A_BG, "B": B_BG, "C": C_BG}[r["pat"]]))
        if r["new"]:
            style.append(("BACKGROUND", (0, i), (0, i), NEWBG))
            style.append(("BOX", (0, i), (-1, i), 1.1, NEWFG))
    tb = Table(data, colWidths=_cols(lang), repeatRows=1)
    tb.setStyle(TableStyle(style))
    return tb


def legend(lang):
    dot = lambda col: '<font color="%s">&#9679;</font>' % hx(col)
    return (
        t("lg_v", lang) + "　" + dot(RED) + t("lg_witness", lang) + "　"
        + dot(AMBER) + t("lg_patrol", lang) + "　"
        + dot(BLUE) + t("lg_kintone", lang) + "　"
        + dot(RED) + t("lg_board", lang) + "<br/>"
        + t("lg_p", lang) + "　"
        + '<font color="%s"><b>A</b></font>' % hx(BLUE) + t("lg_a", lang)[1:] + "　"
        + '<font color="%s"><b>B</b></font>' % hx(AMBER) + t("lg_b", lang)[1:] + "　"
        + '<font color="%s"><b>C</b></font>' % hx(RED) + t("lg_c", lang)[1:] + "　"
        + t("lg_note", lang) + "　　"
        + '<font color="%s">' % hx(NEWFG) + t("lg_new", lang).format(rev=REV) + "</font>"
    )


def section(title, note=None):
    if note:
        row = [P(title, 10, FONT_B, NAVY), P(note, 7, FONT, colors.HexColor("#555555"))]
        cw = [USABLE * 0.42, USABLE * 0.58]
    else:
        row = [P(title, 10, FONT_B, NAVY)]
        cw = [USABLE]
    tb = Table([row], colWidths=cw)
    tb.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BAND),
        ("BOX", (0, 0), (-1, -1), 0.6, HDR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tb


def _plain_table(data, widths, body_bg=BAND):
    tb = Table(data, colWidths=widths)
    tb.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HDR),
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("BACKGROUND", (0, 1), (-1, -1), body_bg),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return tb


class NumberedCanvas(_canvas.Canvas):
    """総ページ数が確定してから "n / N" を刷るための2パス用キャンバス。"""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for i, state in enumerate(self._saved, 1):
            self.__dict__.update(state)
            self.saveState()
            self.setFillColor(colors.HexColor("#666666"))
            self.setFont(FONT, 7.5)
            self.drawRightString(PAGE_W - MARGIN, 7 * mm, "%d / %d" % (i, total))
            self.restoreState()
            super().showPage()
        super().save()


def build(path, lang):
    def header(canv, doc):
        canv.saveState()
        canv.setFillColor(NAVY)
        canv.rect(0, PAGE_H - 13 * mm, PAGE_W, 13 * mm, stroke=0, fill=1)
        canv.setFillColor(colors.white)
        canv.setFont(FONT_B, 11.5 if lang == "ja" else 10.5)
        canv.drawString(MARGIN, PAGE_H - 9 * mm, t("doc_title", lang))
        canv.setFont(FONT, 8.5)
        canv.drawRightString(PAGE_W - MARGIN, PAGE_H - 9 * mm,
                             t("rev", lang).format(rev=REV, d=EFFECTIVE[lang]))
        canv.restoreState()

    doc = BaseDocTemplate(
        path, pagesize=landscape(A4), leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=16 * mm, bottomMargin=10 * mm,
        title="%s %s" % (t("doc_title", lang), REV), author="Hashimoto Kogyo Co., Ltd.")
    doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(
        MARGIN, 10 * mm, USABLE, PAGE_H - 26 * mm, id="f",
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)], onPage=header)])

    S = []
    red_pct = lambda s: P('<font color="%s">%s</font>' % (hx(RED), s), 8, FONT_B, align=TA_CENTER)

    # ---- page 1: rules ----
    S.append(section(t("rule_h", lang), t("rule_n", lang)))
    S.append(Spacer(1, 3 * mm))
    w = [USABLE * x for x in (0.17, 0.09, 0.13, 0.13, 0.48)]
    d = [[st_h(h) for h in t("rule_cols", lang)],
         [P("<b>%s</b>" % t("pat_a", lang), 8.4, FONT_B, BLUE), st_c("100%"),
          st_c(t("none", lang)), st_c(t("none", lang)), st_l(t("nat_a", lang))],
         [P("<b>%s</b>" % t("pat_b", lang), 8.4, FONT_B, AMBER), st_c("100%"),
          red_pct("&#215; 50%"), st_c(t("none", lang)), st_l(t("nat_b", lang))],
         [P("<b>%s</b>" % t("pat_c", lang), 8.4, FONT_B, RED), st_c("100%"),
          red_pct("&#215; 70%"), red_pct("&#215; 50%"), st_l(t("nat_c", lang))]]
    tb = Table(d, colWidths=w)
    tb.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HDR), ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("BACKGROUND", (0, 1), (-1, 1), A_BG), ("BACKGROUND", (0, 2), (-1, 2), B_BG),
        ("BACKGROUND", (0, 3), (-1, 3), C_BG), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    S.append(tb)
    S.append(Spacer(1, 5 * mm))

    S.append(section(t("ex_h", lang)))
    S.append(Spacer(1, 3 * mm))
    w2 = [USABLE * x for x in (0.20, 0.12, 0.20, 0.15, 0.33)]
    d2 = [[st_h(h) for h in t("ex_cols", lang)]]
    for who, n, ded, amt, why in t("ex_rows", lang):
        d2.append([st_l(who), st_c(n),
                   P('<font color="%s"><b>%s</b></font>' % (hx(RED), ded), 8, FONT, align=TA_CENTER),
                   st_c(amt), st_l(why)])
    S.append(_plain_table(d2, w2, body_bg=colors.HexColor("#F7F9FC")))
    S.append(Spacer(1, 5 * mm))

    S.append(section(t("dept_h", lang), t("dept_n", lang)))
    S.append(Spacer(1, 3 * mm))
    w3 = [USABLE * x for x in (0.30, 0.12, 0.16, 0.12, 0.16, 0.14)]
    d3 = [[st_h(h) for h in t("dept_cols", lang)]]
    for (name, pts, yen) in DEPTS:
        amt = ("{:,}円".format(yen)) if lang == "ja" else ("JPY {:,}".format(yen))
        zero = "0円" if lang == "ja" else "JPY 0"
        d3.append([st_l(name[0] if lang == "ja" else name[1]), st_c("%dpt" % pts),
                   st_c(amt), st_c("0pt"), st_c(zero), st_c("")])
    S.append(_plain_table(d3, w3))
    S.append(Spacer(1, 5 * mm))
    S.append(st_note(t("expect", lang)))

    # ---- page 2: common ----
    S.append(PageBreak())
    S.append(section(t("s1", lang), t("s1n", lang)))
    S.append(Spacer(1, 3 * mm))
    S.append(item_table(COMMON, lang))
    S.append(Spacer(1, 3 * mm))
    S.append(st_note(legend(lang)))

    # ---- page 3: press + engineering ----
    S.append(PageBreak())
    S.append(section(t("s2", lang), t("sn", lang)))
    S.append(Spacer(1, 3 * mm))
    S.append(item_table(PRESS, lang))
    S.append(Spacer(1, 3 * mm))
    S.append(st_note(t("press_note", lang)))
    S.append(Spacer(1, 4 * mm))
    S.append(section(t("s3", lang), t("sn", lang)))
    S.append(Spacer(1, 3 * mm))
    S.append(item_table(ENG, lang))

    # ---- page 4: GA + logistics ----
    S.append(PageBreak())
    S.append(section(t("s4", lang), t("sn", lang)))
    S.append(Spacer(1, 3 * mm))
    S.append(item_table(GA, lang))
    S.append(Spacer(1, 3.5 * mm))
    S.append(section(t("s5", lang), t("sn", lang)))
    S.append(Spacer(1, 3 * mm))
    S.append(item_table(LOG, lang))
    S.append(Spacer(1, 3 * mm))
    S.append(st_note(legend(lang)))

    doc.build(S, canvasmaker=NumberedCanvas)
    print("built [%s]: %s" % (lang, path))


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("ja", "en"):
        print(__doc__)
        sys.exit(1)
    build(sys.argv[2], sys.argv[1])
