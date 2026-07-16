# camera_system_spec.md — カメラ監視システム 要件定義書

最終更新: 2026-07-04
状態: 要件定義完了 / 実装は Phase 1 から順に着手

## 1. 目的

TP-Link Tapoカメラを活用し、以下を実現する。

1. 工場内カメラの**同時一覧表示**(HHubに組み込み)
2. **Wi-Fi物理ボタン**による現場からのトラブル発報(画面表示 + Slack通知)
3. 気になるエリアの**タイムラプス**による1日の作業俯瞰
4. **人の流れ**の可視化(将来的にゾーン別分析)
5. 夜間・休日の**防犯**

## 2. 全体構成

```
Tapoカメラ×N ──RTSP(社内LAN)──→ 中継サーバーPC(go2rtc)
                                    │  WebRTC/HLS
                                    ▼
                     camera_grid.html(HHub内・社内LANから閲覧)
                                    ▲
ESP32トラブルボタン ──→ Firebase(/trouble/...)──→ 画面表示 + Slack通知
中継サーバーPC(ffmpeg) ──→ タイムラプス生成 ──→ Firebase Storage → HHubから再生
```

- **映像は社外に出さない**。RTSPストリームは社内LAN内で完結。
  camera_grid.html自体はGitHub Pagesから配信されるが、映像ソースは社内サーバーのIPを指す
- 中継サーバーは既存のBLEビーコンスキャナー用常時稼働PCとの兼用を検討
  (負荷次第で分離。カメラ台数が増えたら専用ミニPC推奨)

## 3. Phase構成

### Phase 1: カメラ導入・設置検証(実装作業なし)
- Tapoカメラ2〜3台を購入し、Tapoアプリのマルチビューで運用開始
- 設置位置・画角・WiFi電波状況の検証
- カメラの設定: 固定IP割当、RTSPアカウント作成(Tapoアプリ→詳細設定→カメラのアカウント)
- **成果物**: カメラ機種・台数・設置場所・IPアドレスの一覧表(本ファイルの付録Aに記録)

### Phase 2: 一覧表示(camera_grid.html)+ HHub組み込み
- 中継サーバーPCに **go2rtc** を導入(単一バイナリ、設定は go2rtc.yaml)
  - 各カメラのRTSP(`rtsp://user:pass@<カメラIP>:554/stream1`)を登録
  - WebRTC(低遅延)を基本、HLSをフォールバックに
- `camera_grid.html` を新規作成(シングルファイルHTML、統一ルール準拠)
  - グリッド表示(2×2 / 3×3切替)、カメラ名ラベル、クリックで拡大
  - 中継サーバーのURLは画面内の設定欄でlocalStorage保存(サーバーIP変更に対応)
  - HHubポータルにリンク追加
- **注意**: GitHub PagesはHTTPS、go2rtcはデフォルトHTTPのため混在コンテンツ制限に当たる。
  対応方針: (a) go2rtcに自己署名証明書を設定、(b) 閲覧端末で社内サーバーHTMLを直接開く、
  (c) kintoneポータル同様にローカル配信 — 実装時にaを第一候補で検証すること

### Phase 3: Wi-Fiトラブルボタン
- **ハード**: ESP32 + 押しボタン(自作、ショットカウンターと同系統)。
  代替: Shelly Button 1(Webhook発火可能な市販品)
- **動作**:
  1. ボタン押下 → Firebase `/trouble/<エリアID>` に `{status:"active", ts:..., area:"C-line"}` を書き込み
  2. camera_grid.html がリッスンし、該当カメラ枠を赤点滅 + 「○○エリア トラブル発生」表示
  3. GAS(またはESP32から直接)でSlackの該当チャンネルへ通知
  4. 解除: 画面上の「対応完了」ボタン、またはESP32ボタン長押しで `status:"resolved"`
- **ファームウェア**: `firmware/trouble_button/` に配置(Arduino IDE、Freenove ESP32ボード)

### Phase 4: タイムラプス + 人流分析 + 防犯強化
- **タイムラプス**: 中継サーバーでffmpegを定時実行
  - 毎分1フレームをJPEG保存 → 終業後に1日分を動画化(約30秒/日)
  - Firebase Storageへアップロード、camera_grid.htmlに「昨日の1日」再生ボタン
- **人流分析**: **Frigate**(オープンソースAI-NVR)を中継サーバーに導入
  - TapoはONVIF対応でそのまま接続可
  - 人物検知・ゾーン別滞在カウント → 食堂レイアウト改善等の検証データに
  - 段取りナビのBLEビーコンデータと突合すれば「誰が・どこに・いつ」を分析可能
- **防犯**: 営業時間外に人物検知 → Slackへ静止画付き通知(Frigate)。
  Tapo側は夜間スケジュールで動体検知 + SDカード録画を併用

## 4. セキュリティ・運用ルール

- RTSPのユーザー名・パスワード、カメラIPは**リポジトリにコミットしない**
  (go2rtc.yamlは中継サーバーのローカル管理。リポジトリには `go2rtc.yaml.example` を置く)
- カメラ映像のクラウド保存はしない(タイムラプス動画のみFirebase Storage、
  従業員のプライバシーに配慮し撮影範囲・保存期間のルールを社内周知すること)
- 防犯録画はカメラ内SDカード(ローカル)を基本とする

## 5. 実装時の依頼テンプレート(Claude Code用)

```
docs/camera_system_spec.md の Phase 2 を実装してください。
CLAUDE.md と docs/ARCHITECTURE.md の統一ルールに従うこと。
```

## 付録A: カメラ台帳(Phase 1で記入)

機種: **TP-Link Tapo C210**(購入済み・**全7台**・RTSP対応・パンチルト可・ONVIF対応でPhase 4のFrigateにも接続可)
RTSP URL形式: `rtsp://<RTSPユーザー>:<パスワード>@<IP>:554/stream1`(高画質) / `/stream2`(低画質)
※C210はアプリからのWiFi接続先変更不可(変更には初期化→再セットアップが必要)

ネットワーク方針: **社内WiFiへ移行**（2026-07-14〜）。IPは 192.168.30.x 帯。

| No | go2rtcキー | 機種 | 設置場所 | 社内WiFi移行 | カメラアカウント | go2rtc表示 | 備考 |
|----|-----------|------|---------|:-----------:|:---------------:|:---------:|------|
| 1 | cam1 | Tapo C210 | 技術部 MILLAC | ✓ | ✓ | ✓ | 2026-07-14 表示OK |
| 2 | cam2 | Tapo C210 | プレス Aライン | ✓ | ✓ | ✓ | 2026-07-14 表示OK |
| 3 | cam3 | Tapo C210 | プレス Cライン | ✓ | ✓ | ✓ | 2026-07-14 表示OK |
| 4 | cam4 | Tapo C210 | 技術 MX55 | ✓ | ✓ | ✓ | 2026-07-15 表示OK |
| 5 | cam5 | Tapo C210 | 技術 ワイヤー | ✓ | ✓ | ✓ | 2026-07-15 表示OK |
| 6 | cam6 | Tapo C210 | プレス Bライン | ✓ | ✓ | ✓ | 2026-07-15 表示OK |
| － | (予備) | Tapo C210 | (未設置) | ― | ― | ― | 残り1台は予備・未設置 |

現在の稼働: **6台**（技術=MILLAC/MX55/ワイヤー、プレス=Aライン/Bライン/Cライン）。camera_grid の部署タブ 技術/プレス に対応。

※固定IP(192.168.30.x)・RTSPユーザー/パスワードは**公開リポジトリに載せず**、中継サーバーの go2rtc.yaml のみに保持する。
　RTSP URL形式: `rtsp://<ユーザー>:<パスワード>@<IP>:554/stream1`（山カッコは目印。実値では付けない）。

### ネットワーク課題(2026-07-08判明 → 2026-07-14解決)

- 当初: カメラはゲストWiFi「hashimoto-kogyo-free」(10.223.247.x)接続。事務所LAN(192.168.30.x)→
  ゲストWiFiは**TCP遮断**(pingのみ)で、事務所LAN側の中継サーバーから到達できなかった
- **採用した解決策: (1)社内WiFiへカメラを移行**。カメラを 192.168.30.x 帯に載せ替え、
  事務所LANの中継PC(go2rtc, 192.168.30.9)から直接RTSP到達できるようにした
- 中継PC: BLEスキャナーPC兼用(192.168.30.9)。go2rtc v1.9.14 を C:\Users\Owner\Desktop\go2rtc_win64\ で稼働

### つまずきメモ(2026-07-14・再発防止)
- go2rtc.yaml の RTSP URL に `<...>`(パスワードの目印カッコ)を残すと `net/url: invalid userinfo`。カッコは外す
- ポート554が `connectex: actively refused` = そのカメラのRTSPアカウント未作成。Tapoアプリで作成すれば開く
- go2rtc設定は Web UI の config タブで直接編集→Saveが確実(メモ帳の .txt 拡張子事故を回避)
- go2rtcを非表示(vbs)で起動していると Web UI の「Save & Restart」で**本体が再起動されず設定が反映されない**。
  対策: 設定変更後は `restart_go2rtc.bat`(kill→hidden再起動)を実行。config反映漏れの切り分けは
  `http://localhost:1984/api/streams` で読み込み中ストリームを確認する
- **自動起動(2026-07-16設定済み)**: PC再起動/ログオフでgo2rtc・ページ配信が両方落ち「カメラに繋がらない」
  事象が発生した。`schtasks`はAccess denied(要管理者)のため、**スタートアップフォルダにショートカットを配置**する方式で登録。
  `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\` に `go2rtc.lnk` / `camera_page_server.lnk`
  (いずれも wscript で各vbsを起動)。解除は当該.lnkを削除するだけ。
  復旧手順: 繋がらない時はまずポート1984/8080の待受を確認し、落ちていれば各vbsを実行する
- go2rtc.yaml の `api:`/`listen:` はインデントを崩すと "api"/"listen" が幽霊ストリーム化する。
  既定APIポートは :1984 なので、迷ったら api ブロックごと省略してよい(streams: と cam 行のみ)
- **config行の行頭を全角スペース（　）にすると go2rtc がその行を無視**する（日本語入力ON時に多発）。
  行頭は必ず半角スペース2つ。症状は「その1台だけ stream not found / 一覧に出ない」。

### Phase 3 トラブルボタン（2026-07-15・進行中）
- **専用ボタンは新設せず、既存の「進捗管理タブのトラブル記録」を発報源に流用**した。
- `dantori_navi.html`: `LINE_CAM_AREA`(ラインID→camera_gridエリアID) を追加。A1/A2→a-line、
  B1/B2/BP2/Bライン→b-line、CP3/Cライン①/CP3_2/Cライン②→c-line。ロボットライン・技術はカメラ無し。
- `addTrouble/endTrouble/deleteTrouble` にフックし `syncCamTrouble(area)` で Firebase `/trouble/<area>` を
  active/解除。camera_grid（受信側は既存実装）が該当カメラ枠を赤点滅＋バナー表示。
- 新規の進行中トラブルで `troubleSlackNotify()` → `settings/troubleSlackUrl`(Slack中継GAS)へPOST。
  GASコードは `docs/trouble_slack_gas.gs.example`。Slack Webhook URLはGASのスクリプトプロパティに保管（リポジトリ非掲載）。
- **前提**: camera_grid の各カメラのエリアIDが a-line/b-line/c-line と一致していること
  （cam2=a-line, cam3=c-line, cam6=b-line）。不一致だと点滅しない。
- 残: ESP32/Shelly等の物理ボタン化（同じ `/trouble/<area>` 書き込みをするだけ）。

### トラブル履歴の永続化（2026-07-15）
- 進捗管理(`lines/<id>/troubles`)は日次で使い捨てだが、トラブルは **Firebase `/troubleHistory/<lineId>/<troubleId>`** に
  別途永続化（addTrouble/endTrouble/deleteTroubleにフック、`_persistTroubleHist`/`_removeTroubleHist`）。日次リセットの影響を受けない。
- 履歴モーダル(`#troubleHistOv`): ライン絞り込み＋期間(開始日〜終了日)指定で一覧、行ごと削除・「表示中の期間をすべて削除」。
  入口はトラブル記録モーダルの「📋 履歴」ボタンと、設定の「📋 トラブル履歴を見る」。
- 削除はローカル即時反映＋裏でFirebase削除（get()はサーバ往復で遅延するため）。firebaseインポートに `get` を追加。
- **仕様変更(2026-07-16)**: トラブル記録モーダルの「削除」は当日一覧からのみ消し、**履歴(/troubleHistory)は残す**
  （「進捗は使い捨て・履歴だけ残す」意図に合わせ deleteTrouble から履歴削除を撤去）。履歴の削除は履歴画面からのみ。
- **CSV出力・月次集計を追加(2026-07-16)**: 履歴モーダルに「一覧／📊月次集計」切替と「⬇CSV出力」。
  月次集計＝月×ラインの件数・合計停止(分)。CSVはBOM付きUTF-8で日付/ライン/種類/開始/終了/停止分/メモ。
  ※履歴は機能公開後の記録から蓄積。過去の使い捨てデータや、旧仕様で削除された分は含まれない。

### camera_grid ↔ H-Hubレイアウト連携（2026-07-15）
- `camera_grid.html` は `?cams=cam2,cam6` で特定カメラだけ表示（部署タブは「← 全カメラ表示」に変わる）。
- `dantori_navi.html` の工場レイアウトSVG末尾 `<g id="cameraMarks">` に📷マークを配置。
  クリックで別タブに上記URLを開く。対応: プレスA=cam2 / プレスB=cam6 / プレスC=cam3 / 技術=cam1,cam4,cam5。
  **配信元IP(192.168.30.9:8080)を変えたら cameraMarks 内の4リンクを更新すること。**

※残り4台(cam4〜7)の設置場所が決まったら本表を更新すること

## 付録B: 変更履歴

- 2026-07-04: 初版作成(チャット側での要件整理を文書化)
- 2026-07-08: Phase 2 の camera_grid.html(v2026.07.08-1)を実装。
  go2rtc.yaml.example と導入手順書(docs/camera_setup_guide.md)を追加。
  カメラは購入済み(Tapoアプリのみで運用中)のため、Phase 1 の残作業は
  固定IP割当・RTSPアカウント作成・付録A記入
- 2026-07-14: 社内WiFiへ移行しネットワーク課題を解決。go2rtc(中継PC 192.168.30.9)で
  3台配信確認(cam1=技術MILLAC / cam2=プレスAライン / cam3=プレスCライン)。
  go2rtc.yaml.example を7台分に、付録Aを7行の記入枠に更新。残タスク: 残り4台展開・
  IP固定(DHCP予約)・go2rtc自動起動・HTTPS化・camera_grid本番表示。
- 2026-07-14: **camera_grid.html v2026.07.14-1** — 部署タブ機能を追加。カメラごとに
  `dept`(部署)を設定でき、上部にタブ(すべて/プレス/技術…)が出て部署別に絞り込み表示。
  選択中タブは localStorage(`hk_camgrid_config.activeDept`)に保存。cams[i] に `dept` 追加。
  中継PCでの配信は Desktop\camera_view\ にコピーを置き python http.server 8080 で社内LAN配信
  (閲覧URL http://192.168.30.9:8080/camera_grid.html)。**リポジトリの camera_grid.html を編集したら
  camera_view へコピーし直すこと**。自動起動スクリプトは Desktop\go2rtc_win64\ に
  start_go2rtc_hidden.vbs / start_camera_page_server.vbs / install_autostart.bat / restart_go2rtc.bat(英字のみ)。
- 2026-07-15: cam6(プレスBライン)追加で**6台稼働**。camera_grid v2026.07.15-1 で `?cams=` 対応。
  dantori_navi.html の工場レイアウトに📷カメラマークを追加(クリックで該当カメラを別タブ表示)。
