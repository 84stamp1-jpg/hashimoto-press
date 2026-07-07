# SYSTEMS.md — HHub 配下システム一覧

最終更新: 2026-07-04(実リポジトリと照合し内容を修正)
運用ルール: システムの追加・大きな仕様変更時は必ずこのファイルを更新すること。

## 本リポジトリ収録ファイル(実体との対応)

`84stamp1-jpg/hashimoto-press` のルートに置かれている単一ファイルHTMLと、対応するシステムは以下の通り。
(GitHub Pages のルート = `index.html`)

| ファイル | `<title>` | 対応システム |
|----------|-----------|--------------|
| `index.html` | 進捗管理ボード｜橋本工業 | プレス進捗管理ダッシュボード(2) |
| `dantori_navi.html` | H-Hub｜橋本工業 | 段取りナビ / H-Hubポータル本体(1) |
| `material_price_update.html` | 材料単価改訂システム｜橋本工業 | 材料単価改訂システム(3) |
| `hinshitsu_check.html` | 品質チェックシート記録 | 品質チェックシート記録システム(4) |
| `mold_cost_system.html` | 金型製作原価管理システム | 金型製作原価管理システム(5) |
| `mold_repair_plan.html` | 金型管理システム | 金型修繕計画表(6) |
| `upload_tool_v2.html` | 生産予定表アップロード | 生産予定表アップロードツール(7) |
| `start.html` | 橋本工業 プレス管理 スタートページ | プレス管理スタートページ(8) |

※ かつてルート直下にあった重複の入れ子フォルダ `hashimoto-press/`(誤アップロード由来。
  start/upload_tool_v2 の同一コピーと進捗ボードの旧版)は 2026-07-04 に削除済み(git履歴から復元可)。

## 稼働中

### 1. 段取りナビ / H-Hubポータル(dantori_navi.html)
- **目的**: 金型段取り時間の短縮。品番検索→標準作業表示、BLEビーコンによる位置追跡
- **兼務**: `<title>` は「H-Hub」。HHubポータル本体を兼ね、2026-06-03に進捗管理タブを統合済み
- **構成**: BLEビーコン(MM-BLEBC5)+ 常時稼働PC(Node.jsスキャナー)→ Firebase → HTML表示。
  品番マスタは kintone App7
- **表示**: 工場レイアウトSVG v11(viewBox="0 0 824 446")
- **設置**: GitHub Pages 単体 + kintoneポータル埋め込み(kintone.api()直接呼び出し版)
- **既知の課題**: ビーコンアイコンの「ac」表示問題(MACアドレスプレフィックス由来)、
  一部PCでPDF直接表示不可(JSONP方式で対応)

### 2. プレス進捗管理ダッシュボード(index.html)
- **目的**: プレスラインの進捗見える化
- **指標**: CT達成率(作業効率)と計画達成率(計画数比)の2指標体制
- **構成**: Firebase + GitHub Pages。入力履歴スナップショット機能あり
- **メモ**: C-2シート(CラインP3-2)追加済み。
  GitHub Pages のルート(`index.html`)として配信される(旧称 press_dashboard_v11)

### 3. 材料単価改訂システム(material_price_update.html)
- **目的**: 材料単価の改訂管理(ユタカ材料・スクラップ単価改定などに使用)
- **構成**: GitHub Pages(シングルファイルHTML)

### 4. 品質チェックシート記録システム(hinshitsu_check.html)
- **目的**: 品質チェック記録のデジタル化
- **構成**: GitHub Pages + GAS + Google Sheets
  (作業予定一覧スプレッドシートID: 1eBz1ryWajBQzMugr_5vBoUK41fGmKznnEBP8kSpL7vA)
- **実装済み**: EXIF対応写真回転、部品番号グループ表示、累計進捗バー
- **コード**: GAS側は v9.gs まで進化

### 5. 金型製作原価管理システム(mold_cost_system.html)
- **目的**: 金型の見積依頼→見積比較→注文書作成のワークフロー管理
- **構成**: Firebase + GitHub Pages(シングルファイル)。材料費・外注費・購入品費タブ。kintone連携
- **バージョン形式**: `v2026.MM.DD-N`
- **現行バージョン**: v2026.05.15-24(2026-07-06修正・2026-07-07リポジトリ反映)
- **直近の変更(-24)**: 材料の仕上げ選択に「なし」を追加。
  チェックなし時のデフォルトを「6F(全面)」から「仕上なし」に変更

### 6. 金型修繕計画表(mold_repair_plan.html)
- **目的**: 金型修繕のガントチャート管理(担当: 松本・松永)。`<title>` は「金型管理システム」
- **構成**: GitHub Pages + GAS JSONP + Firebase(`/moldRepairPlan/tasks`)。
  kintone App6からデータ取得。Gantt表示(08:10〜20:00)

### 7. 生産予定表アップロードツール(upload_tool_v2.html)
- **目的**: 生産予定表データの取り込み・アップロード補助ツール
- **構成**: GitHub Pages(シングルファイルHTML)

### 8. プレス管理スタートページ(start.html)
- **目的**: プレス管理系画面へのスタート/入口ページ
- **構成**: GitHub Pages(シングルファイルHTML)

### 9. 保全スケジュール自動化(maint_schedule_v7)
- **目的**: kintone App6 → PDF/HTML生成 → Slack投稿の自動パイプライン
- **構成**: Pythonスクリプト5本(現場PC `C:\Users\Owner\Desktop\maint_schedule\`)。
  Slack Bot「Kanagata-Bot」
- **注記**: 本リポジトリには未収録(現場PCローカル運用)

### 10. 月次会レポート自動生成
- **目的**: #月次会チャンネル(C06PJTWQJ15)の投稿からA4 2ページのPDFレポートを生成
- **運用**: チャット側で「月次会の実績をPDFにまとめて」で生成。
  リマインダーは毎月5日・10日・14日に自動送信。報告締切は毎月15日
- **注記**: 本リポジトリには未収録(チャット環境側で運用)

### 11. プレス見積システム(press_estimator_v19.html)
- **目的**: 重量積み上げ方式のプレス加工費・金型費計算。図面AI解析機能(Anthropic API)付き
- **構成**: GAS(NTT共有クラウド環境)でデータ共有。APIキー埋め込み方式
  ※公開リポジトリに置く場合はキーの扱いに注意(CLAUDE.mdのセキュリティ項参照)
- **注記**: 本リポジトリには未収録(GAS/NTT共有クラウド環境で運用)

### 12. 基準遵守手当システム
- **目的**: 減点式の手当計算(残ポイント×100円)。kintone + GAS + Sheets + Excel + Slack統合
- **状態**: 試行運用中(Rev.1.2)。残タスク: Slack一括通知ボタン、
  kintone JSカスタマイズのGASデプロイURL更新、App75連携、社労士確認
- **注記**: 本リポジトリには未収録(kintone/GAS側で運用)

## 構築中

### 13. プレス機ショットカウンターIoT
- **構成**: ESP32 + PC817Cフォトカプラ → Firebase。約20台のプレス機対象
- **状態**: 現場WiFi環境でのFirebase接続テスト未完了。CT自動計算・チョコ停検知は今後

### 14. カメラ監視システム(新規)
- **仕様書**: `docs/camera_system_spec.md`
- **状態**: 要件定義完了、Phase 1(カメラ選定・設置検証)から着手予定

## テンプレート・資産

- 月次会レポート: `/home/claude/monthly_report_template.py`(チャット環境側に保存)
- 会社ロゴ: HASHIMOTO KOGYOアーチ型マーク(暗色背景では filter:invert(1))
- 工場レイアウトSVG: v11(viewBox="0 0 824 446")— 段取りナビから流用可
