// H-Hub 呼び出し → SwitchBot中継（回転灯ON/OFF）
// ブラウザから直接SwitchBot APIを叩くとCORSで止まる＋署名用のSecretを
// リポジトリ（公開）に置けないため、GASを間に挟む。
//
// ■ デプロイ手順
// 1. https://script.google.com で新規プロジェクトを作り、このファイルの中身を貼る
// 2. 左の「プロジェクトの設定」→「スクリプト プロパティ」で以下を登録する
//      SWITCHBOT_TOKEN  … SwitchBotアプリ「プロフィール→設定→アプリバージョンを10回タップ→開発者向けオプション」で発行したトークン
//      SWITCHBOT_SECRET … 同じ画面で発行したシークレットキー
//      RELAY_KEY        … H-Hub側と合わせる合言葉（適当な文字列でよい。公開リポジトリに書かないこと）
// 3. 「デプロイ」→「新しいデプロイ」→ 種類「ウェブアプリ」
//      実行ユーザー: 自分／アクセスできるユーザー: 全員
// 4. 発行されたURLを H-Hub の 呼び出し設定（⚙「💡回転灯（SwitchBot）」欄）に
//    「中継先URL」として登録する。RELAY_KEY も同じ画面に入れる
// 5. SwitchBotアプリでデバイス一覧を開き、対象デバイスのIDを控えて同じ設定欄に登録する
//    （デバイスIDの調べ方 = test_listDevices を実行してログを見る）

function doPost(e) {
  var result = { ok: false };
  try {
    var payload = JSON.parse(e.postData.contents);
    var props = PropertiesService.getScriptProperties();
    var relayKey = props.getProperty('RELAY_KEY') || '';
    if (!relayKey || payload.key !== relayKey) {
      return _json({ ok: false, error: 'unauthorized' });
    }
    var deviceId = String(payload.deviceId || '');
    var action = payload.action === 'off' ? 'off' : 'on';
    if (!deviceId) return _json({ ok: false, error: 'deviceId_missing' });
    result = switchbotCommand(deviceId, action === 'on' ? 'turnOn' : 'turnOff');
  } catch (err) {
    result = { ok: false, error: err.message };
  }
  return _json(result);
}

// SwitchBot API v1.1 署名付きリクエスト
// 仕様: sign = Base64( HMAC-SHA256( secret, token + t + nonce ) )
function switchbotCommand(deviceId, command) {
  var props = PropertiesService.getScriptProperties();
  var token = props.getProperty('SWITCHBOT_TOKEN');
  var secret = props.getProperty('SWITCHBOT_SECRET');
  if (!token || !secret) return { ok: false, error: 'switchbot_credentials_missing' };

  var t = Date.now().toString();
  var nonce = Utilities.getUuid();
  var strToSign = token + t + nonce;
  var signatureBytes = Utilities.computeHmacSha256Signature(strToSign, secret);
  var sign = Utilities.base64Encode(signatureBytes);

  var url = 'https://api.switch-bot.com/v1.1/devices/' + encodeURIComponent(deviceId) + '/commands';
  var options = {
    method: 'post',
    contentType: 'application/json',
    headers: {
      'Authorization': token,
      'sign': sign,
      't': t,
      'nonce': nonce
    },
    payload: JSON.stringify({ command: command, parameter: 'default', commandType: 'command' }),
    muteHttpExceptions: true
  };
  var res = UrlFetchApp.fetch(url, options);
  var code = res.getResponseCode();
  var body = {};
  try { body = JSON.parse(res.getContentText()); } catch (e2) {}
  // ★未検証（実機・APIキーがまだ無いため）。もし turnOn/turnOff が通らない場合は
  //   sign を sign.toUpperCase() に変えて試すこと（SwitchBot API v1.0時代の名残で
  //   大文字化を要求する実装例が一部に残っている）
  return { ok: code === 200 && body.statusCode === 100, httpCode: code, body: body };
}

function _json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

// ── 動作確認用（スクリプトエディタの実行ボタンから直接呼ぶ） ──

// デバイスID一覧をログに出す（最初の1回だけ使う）
function test_listDevices() {
  var props = PropertiesService.getScriptProperties();
  var token = props.getProperty('SWITCHBOT_TOKEN');
  var secret = props.getProperty('SWITCHBOT_SECRET');
  var t = Date.now().toString();
  var nonce = Utilities.getUuid();
  var sign = Utilities.base64Encode(Utilities.computeHmacSha256Signature(token + t + nonce, secret));
  var res = UrlFetchApp.fetch('https://api.switch-bot.com/v1.1/devices', {
    method: 'get',
    headers: { 'Authorization': token, 'sign': sign, 't': t, 'nonce': nonce },
    muteHttpExceptions: true
  });
  Logger.log(res.getContentText());
}

function test_turnOn()  { Logger.log(switchbotCommand('YOUR_DEVICE_ID', 'turnOn')); }
function test_turnOff() { Logger.log(switchbotCommand('YOUR_DEVICE_ID', 'turnOff')); }
