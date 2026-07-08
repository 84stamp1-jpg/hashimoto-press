# camera_setup_guide.md — カメラ一覧表示(Phase 2)導入手順書

対象: `camera_grid.html` + go2rtc(中継サーバー)
仕様書: `docs/camera_system_spec.md`
最終更新: 2026-07-08

## 全体像

```
Tapoカメラ×N ──RTSP(社内LAN)──→ 中継サーバーPC(go2rtc) ──→ camera_grid.html(ブラウザ)
```

映像は社内LAN内で完結し、社外(クラウド)には出ない。

---

## Step 1. Tapoカメラ側の設定(カメラごとに1回)

スマホのTapoアプリで各カメラについて:

1. **RTSPアカウント作成**: カメラを選択 → 設定(歯車) → 「詳細設定」 →
   「カメラのアカウント」→ ユーザー名とパスワードを設定
   ※Tapoアプリのログインとは別物。このユーザー名/パスワードをgo2rtc.yamlに書く
2. **IPアドレスの固定**: ルーターの管理画面で各カメラのMACアドレスに固定IPを割当
   (DHCP予約)。カメラのIPはTapoアプリ → カメラ設定 → 「デバイス情報」で確認できる
3. 機種・設置場所・IPを `docs/camera_system_spec.md` の付録A(カメラ台帳)に記入する

## Step 2. 中継サーバーPCにgo2rtcを導入

常時稼働しているPC(BLEビーコンスキャナーPCと兼用可)で:

1. https://github.com/AlexxIT/go2rtc/releases から
   `go2rtc_win64.zip` をダウンロードして展開(単一exe)
2. 同じフォルダに `go2rtc.yaml` を作成(リポジトリの `go2rtc.yaml.example` をコピーして
   実際のユーザー名/パスワード/IPに書き換える)
3. `go2rtc.exe` をダブルクリックで起動
4. ブラウザで `http://localhost:1984` を開き、各ストリームが再生できるか確認
5. **自動起動設定**: タスクスケジューラで「ログオン時」に `go2rtc.exe` を起動する
   タスクを登録(作業フォルダをexeのある場所に設定)

※Windowsファイアウォールの許可ダイアログが出たら「プライベートネットワーク」で許可

## Step 3. camera_grid.html の設定(閲覧端末ごとに1回)

1. `camera_grid.html` を開く(GitHub Pages または後述のローカル配信)
2. 右上「⚙ 設定」→
   - 中継サーバーURL: `http://<中継サーバーPCのIP>:1984`
   - カメラ一覧: ストリーム名(go2rtc.yamlのキー、例 cam1)と表示名を登録
   - エリアID: トラブルボタン(Phase 3)導入時に使用。未定なら空欄
3. 保存 → グリッドに映像が表示される

## HTTPS対応(GitHub Pagesから見る場合)

GitHub PagesはHTTPSのため、HTTP(:1984)の映像はブラウザにブロックされる(混在コンテンツ制限)。
camera_grid.html は該当時に画面上部へ警告を表示する。対処は次のいずれか:

- **(a) go2rtcをHTTPS化(推奨・仕様書の第一候補)**:
  自己署名証明書を作成し go2rtc.yaml に設定
  ```
  # PowerShellでの証明書作成例(opensslがある場合)
  openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 3650 -nodes -subj "/CN=go2rtc"
  ```
  go2rtc.yaml に `tls_listen: ":1985"` / `tls_cert` / `tls_key` を設定し、
  camera_grid.html のサーバーURLを `https://<IP>:1985` にする。
  各閲覧端末で初回に「この接続は安全ではありません→詳細→アクセスする」の許可が必要
- **(b) ローカルから開く**: camera_grid.html を中継サーバーPCから配布/共有し、
  `file://` またはローカル配信(`python -m http.server`)で開く(HTTPページからはブロックされない)

## トラブルシューティング

| 症状 | 確認ポイント |
|------|-------------|
| ストリームが映らない | go2rtcのWeb UI(`http://<IP>:1984`)で再生できるか。できなければRTSPユーザー/パス/IPを確認 |
| go2rtc UIでも映らない | Tapoアプリで「カメラのアカウント」を設定したか。VLCで `rtsp://user:pass@IP:554/stream1` を直接開いて切り分け |
| カクつく・重い | go2rtc.yamlのURLを `/stream2`(低画質)に変更。カメラのWiFi電波強度を確認 |
| HTTPSページで映らない | 上記「HTTPS対応」参照 |
| 別PCから1984に繋がらない | 中継サーバーPCのファイアウォールでポート1984(TLS時は1985)を許可 |

## セキュリティ・運用ルール(仕様書より)

- go2rtc.yaml(RTSP認証情報・カメラIP入り)は**リポジトリにコミットしない**
- カメラ映像のクラウド保存はしない。防犯録画はカメラ内SDカードを基本とする
- 撮影範囲・保存期間のルールを社内周知すること
