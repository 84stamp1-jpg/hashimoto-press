// ビーコンのスキャナー用：App Check の通し札を取る部品
//
// ★2026-10-26 なぜ要るか
//   2026-10-04 に Firebase を「H-Hubの画面から来た通信しか受けない」設定
//   （App Check）にした。ブラウザではないこのスキャナーは、そのままだと
//       401 Missing appcheck token
//   で弾かれ、書き込みが届かなくなる。実際、4台とも 10/05 の朝を最後に
//   ビーコンの位置が更新されなくなっていた。
//
// 使い方
//   1) Firebase コンソール → App Check → アプリ → デバッグトークンを登録し、
//      その文字列を scanner のフォルダに appcheck_debug_token.txt として保存する
//      （★この札は秘密。GitHub には置かない）
//   2) スキャナー本体の先頭で読み込む
//        const { appCheckHeader } = require('./beacon_appcheck');
//   3) Firebase へ書くところで、ヘッダーに足す
//        const h = await appCheckHeader();          // {} か {'X-Firebase-AppCheck': '...'}
//        ... headers: { 'Content-Type': 'application/json', ...h }
//
//   札が無い・取れないときは {} を返す（＝今までどおり送るが 401 になる）。
//   取った札は1時間ほど使い回す。

const fs    = require('fs');
const path  = require('path');
const https = require('https');

const TOKEN_FILE = path.join(__dirname, 'appcheck_debug_token.txt');
const APP_ID  = '1:508495109760:web:53d266bb4483ab04a29065';
const WEB_KEY = 'AIzaSyCvh4rDrk6ljWhNBJc-Kt_YFpvEevLxb6o';

let cache = { token: null, exp: 0 };

function post(url, body) {
  return new Promise((resolve, reject) => {
    const data = Buffer.from(JSON.stringify(body), 'utf8');
    const u = new URL(url);
    const req = https.request({
      hostname: u.hostname, path: u.pathname + u.search, method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': data.length },
      timeout: 20000,
    }, res => {
      let buf = '';
      res.on('data', c => { buf += c; });
      res.on('end', () => {
        try { resolve({ status: res.statusCode, json: JSON.parse(buf) }); }
        catch (e) { resolve({ status: res.statusCode, json: null, raw: buf }); }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => req.destroy(new Error('timeout')));
    req.end(data);
  });
}

async function appCheckHeader() {
  const now = Date.now();
  if (cache.token && now < cache.exp) return { 'X-Firebase-AppCheck': cache.token };

  let debugToken = '';
  try { debugToken = fs.readFileSync(TOKEN_FILE, 'utf8').trim(); } catch (_) { return {}; }
  if (!debugToken) return {};

  const url = 'https://firebaseappcheck.googleapis.com/v1/projects/hashimoto-press/apps/'
            + encodeURIComponent(APP_ID) + ':exchangeDebugToken?key=' + WEB_KEY;
  try {
    const r = await post(url, { debug_token: debugToken });
    const t = r.json && r.json.token;
    if (!t) {
      console.log('[appcheck] 札を取れませんでした', r.status, (r.raw || '').slice(0, 200));
      return {};
    }
    // ttl は "3600s" のような文字列。少し早めに取り直す
    const sec = parseInt(String((r.json.ttl || '3600s')).replace('s', ''), 10) || 3600;
    cache = { token: t, exp: now + Math.max(60, sec - 300) * 1000 };
    return { 'X-Firebase-AppCheck': t };
  } catch (e) {
    console.log('[appcheck] 札を取れませんでした', e.message);
    return {};
  }
}

module.exports = { appCheckHeader };
