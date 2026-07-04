# CLAUDE.md — 橋本工業 HHub 開発ガイド

このリポジトリは橋本工業株式会社(プレス加工・金型製造、従業員約35名)の
社内ポータル **HHub** と、その配下の業務システム群です。
Claude Code は作業開始時に必ずこのファイルと `docs/` 配下を読み、
全体構成を踏まえてから作業してください。

## HHubとは

GitHub Pages (`84stamp1-jpg.github.io/hashimoto-press/`) でホストする
社内システム群の入り口(ポータル)。各システムはシングルファイルHTMLで構成。

## 共通基盤

| 基盤 | 内容 |
|------|------|
| ホスティング | GitHub Pages(リポジトリ: 84stamp1-jpg/hashimoto-press) |
| リアルタイムDB | Firebase Realtime Database(hashimoto-press-default-rtdb.asia-southeast1.firebasedatabase.app) |
| 業務DB | kintone(hashimoto-kogyo.cybozu.com)。App6=金型保全、App7=段取りナビ、App75=プロセス管理 |
| サーバーレス処理 | GAS(Google Apps Script)。kintoneプロキシ・PDF生成・Sheets連携に使用 |
| 通知 | Slack(#月次会 C06PJTWQJ15、#生産準備 C08JYRHSPFA ほか) |
| 現場IoT | ESP32(ショットカウンター等)、MM-BLEBC5 BLEビーコン |

## 統一ルール

### コーディング
- **シングルファイルHTML方式**: 各システムはHTML 1ファイルにCSS/JSを内包する
- **バージョン表記**: `v2026.MM.DD-N` 形式(例: v2026.07.04-1)。ファイル内ヘッダーとUI上に明記
- **Firebaseデータパス**: システムごとにトップレベルのパスを分ける
  (例: `/moldRepairPlan/tasks`, `/beacons/...`)。他システムのパスに書き込まない
- **kintoneアクセス**: kintone内(ポータル埋め込み)では `kintone.api()` を直接使用。
  GitHub Pages単体で開く場合はGASプロキシ(JSONP)経由。両対応のフォールバック実装を推奨
- **PDF表示**: 一部PCで直接表示不可のためJSONP方式でのフォールバックを維持する

### セキュリティ
- **APIトークン・APIキーをこのリポジトリにコミットしない**(GitHub Pagesは公開リポジトリ)。
  トークン類はGASのスクリプトプロパティ、またはkintone側カスタマイズに置く。
  既存コードに埋め込みが残っている場合は発見次第、移設を提案すること

### UI
- 背景は白基調、現在地・重要情報が目立つ配色(プレス進捗ボードの書式に準拠)
- 工場レイアウトSVGは v11(`viewBox="0 0 824 446"`)を共通利用
- 会社ロゴ: HASHIMOTO KOGYOアーチ型マーク。暗色ヘッダーでは `filter:invert(1)` で白抜き

## ドキュメント運用ルール(重要)

セッション間・チャット⇔Code間の連携はこのリポジトリのドキュメントで行う。

1. **新システム追加・大きな仕様変更をしたら `docs/SYSTEMS.md` を必ず更新する**
2. 構成(Firebase/kintone/GASの接続関係)が変わったら `docs/ARCHITECTURE.md` を更新する
3. 仕様書は `docs/<システム名>_spec.md` に置く。実装はまず仕様書を読んでから始める
4. 作業終了時、変更内容を該当ドキュメントに反映してからコミットする

## 主要メンバー(通知・担当者設定で使用)

見原(製造Tリーダー)、八木(品管Tリーダー)、大石・遠藤(技術T)、
木村(納入管理)、長岡(組立検査)、松本・松永(金型修繕)。
代表: 橋本健介(Slack ID: U06DBE92Y84)

## 現在進行中のプロジェクト

- **カメラ監視システム**(新規): `docs/camera_system_spec.md` 参照。Phase 1〜4で段階実装
- 段取りナビ: ビーコンアイコンの「ac」表示問題(MACプレフィックス由来)が未解決
- ショットカウンターIoT: 現場WiFi環境でのFirebase接続テスト未完了
