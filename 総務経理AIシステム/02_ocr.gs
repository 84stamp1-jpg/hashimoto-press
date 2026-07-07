/**
 * 橋本工業 総務・経理AIシステム
 * Phase 1 - OCRスクリプト
 *
 * 役割：レシート投入箱フォルダ内の画像/PDFを Vision API で読み取り、
 *       日付・金額・店名を抽出して「未処理」シートに記録。
 *       処理した画像は「02_処理済み」フォルダへ移動する。
 *
 * 前提：01_setup_drive_sheets.gs の setup() が実行済みであること。
 *       スクリプトプロパティ VISION_API_KEY にAPIキーが保存済みであること。
 *
 * 使い方：runOcr() を実行する（後でWebアプリのボタンから呼ぶ）。
 */

/**
 * メイン：投入箱の未処理ファイルをすべてOCRする
 */
function runOcr() {
  const props = PropertiesService.getScriptProperties();
  const apiKey = props.getProperty('VISION_API_KEY');
  if (!apiKey) {
    throw new Error('APIキーが未設定です。saveApiKey() を実行してキーを保存してください。');
  }

  const inboxId = props.getProperty('INBOX_FOLDER_ID');
  const doneId = props.getProperty('DONE_FOLDER_ID');
  const ssId = props.getProperty('SPREADSHEET_ID');
  if (!inboxId || !ssId) {
    throw new Error('セットアップ情報が見つかりません。先に setup() を実行してください。');
  }

  const inbox = DriveApp.getFolderById(inboxId);
  const doneFolder = DriveApp.getFolderById(doneId);
  const sheet = SpreadsheetApp.openById(ssId).getSheetByName('未処理');

  const files = inbox.getFiles();
  let count = 0;
  const errors = [];

  while (files.hasNext()) {
    const file = files.next();
    const mime = file.getMimeType();

    // 画像・PDFのみ対象
    if (mime.indexOf('image/') !== 0 && mime !== MimeType.PDF) {
      continue;
    }

    try {
      const text = ocrFile_(file, apiKey);
      const info = extractInfo_(text);

      sheet.appendRow([
        file.getId(),
        file.getName(),
        new Date(),          // 取込日時
        info.date,           // 抽出_日付
        info.amount,         // 抽出_金額
        info.store,          // 抽出_店名
        text,                // OCR全文
        '未確認'             // ステータス
      ]);

      // 処理済みフォルダへ移動
      doneFolder.addFile(file);
      inbox.removeFile(file);
      count++;

    } catch (e) {
      errors.push(file.getName() + '：' + e.message);
    }
  }

  const msg = count + '件をOCRしました。' +
    (errors.length ? '\nエラー' + errors.length + '件：\n' + errors.join('\n') : '');
  Logger.log(msg);
  return msg;
}

/**
 * 1ファイルを Vision API でOCRし、全文テキストを返す。
 * 画像はimages:annotate、PDF（ドライブのスキャン保存形式）はfiles:annotateを使う。
 */
function ocrFile_(file, apiKey) {
  const base64 = Utilities.base64Encode(file.getBlob().getBytes());
  if (file.getMimeType() === MimeType.PDF) {
    return ocrPdf_(base64, apiKey);
  }
  return ocrImage_(base64, apiKey);
}

/**
 * 画像をOCR（JPEG/PNG等）
 */
function ocrImage_(base64, apiKey) {
  const payload = {
    requests: [{
      image: { content: base64 },
      features: [{ type: 'DOCUMENT_TEXT_DETECTION' }],
      imageContext: { languageHints: ['ja'] }
    }]
  };

  const json = callVision_('images:annotate', payload, apiKey);
  const r = json.responses && json.responses[0];
  if (!r || !r.fullTextAnnotation) return '';
  return r.fullTextAnnotation.text;
}

/**
 * PDFをOCR（ドライブのスキャン機能で保存される形式）。
 * 1リクエストで先頭5ページまで。レシートは通常1ページ。
 */
function ocrPdf_(base64, apiKey) {
  const payload = {
    requests: [{
      inputConfig: { content: base64, mimeType: 'application/pdf' },
      features: [{ type: 'DOCUMENT_TEXT_DETECTION' }],
      imageContext: { languageHints: ['ja'] }
    }]
  };

  const json = callVision_('files:annotate', payload, apiKey);
  const fileRes = json.responses && json.responses[0];
  if (!fileRes || !fileRes.responses) return '';
  // 各ページのテキストを連結
  const texts = [];
  fileRes.responses.forEach(function (page) {
    if (page.fullTextAnnotation) texts.push(page.fullTextAnnotation.text);
  });
  return texts.join('\n');
}

/**
 * Vision APIを呼ぶ共通処理
 */
function callVision_(endpoint, payload, apiKey) {
  const res = UrlFetchApp.fetch(
    'https://vision.googleapis.com/v1/' + endpoint + '?key=' + apiKey,
    {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    }
  );
  const json = JSON.parse(res.getContentText());
  if (json.error) {
    throw new Error('Vision APIエラー：' + json.error.message);
  }
  return json;
}

/**
 * OCR全文から 日付・金額・店名 を抽出する
 */
function extractInfo_(text) {
  return {
    date: extractDate_(text),
    amount: extractAmount_(text),
    store: extractStore_(text)
  };
}

/**
 * 日付抽出：和暦・西暦の候補をすべて集め、
 *           「今日以前で最も新しい日付」を採用する（誤読の古い日付に引っ張られない）。
 */
function extractDate_(text) {
  if (!text) return '';

  const cands = [];
  let m;

  // 1) 西暦 2026年6月25日 / 2026/6/25 / 2026-6-25
  const re1 = /(20\d{2})\s*[年\/\-\.]\s*(\d{1,2})\s*[月\/\-\.]\s*(\d{1,2})/g;
  while ((m = re1.exec(text)) !== null) {
    cands.push(new Date(parseInt(m[1], 10), parseInt(m[2], 10) - 1, parseInt(m[3], 10)));
  }

  // 2) 和暦 令和6年6月25日 / R6.6.25（令和1年=2019）
  const re2 = /(?:令和|R)\s*(\d{1,2})\s*[年\/\-\.]\s*(\d{1,2})\s*[月\/\-\.]\s*(\d{1,2})/g;
  while ((m = re2.exec(text)) !== null) {
    cands.push(new Date(2018 + parseInt(m[1], 10), parseInt(m[2], 10) - 1, parseInt(m[3], 10)));
  }

  if (!cands.length) return '';

  const today = new Date();
  today.setHours(23, 59, 59, 999);

  // 今日以前の中で最新を採用。全部未来なら最も古い未来日。
  const past = cands.filter(function (d) { return d <= today; });
  const pool = past.length ? past : cands;
  const pick = new Date(Math.max.apply(null, pool.map(function (d) { return d.getTime(); })));
  return Utilities.formatDate(pick, 'Asia/Tokyo', 'yyyy/MM/dd');
}

/**
 * 金額抽出：「通貨記号(¥)・カンマ・円」が付いた数字だけを金額とみなし、
 *           お預かり・お釣り等の行を除外したうえで最大額を採用する。
 *           （レシート番号や会員番号などのIDを金額と誤認しないため）
 */
function extractAmount_(text) {
  if (!text) return '';

  const lines = text.split(/\r?\n/);
  // 金額ではない行（お預かり額・お釣りは合計より大きいことがあるので除外）
  const excludeLine = /(預か|お預|釣|つり|お返し|返金|ポイント|point|残高|前回|点数|枚数|番号|No|TEL|電話)/i;

  // 通貨マーカー付きの数字： ¥123,456 / 123,456 / 1234円
  const amtRegex = /(?:[¥￥\\]\s*([0-9][0-9,]*)|([0-9]{1,3}(?:,[0-9]{3})+)|([0-9]+)\s*円)/g;

  const candidates = [];
  for (let i = 0; i < lines.length; i++) {
    if (excludeLine.test(lines[i])) continue;
    let m;
    amtRegex.lastIndex = 0;
    while ((m = amtRegex.exec(lines[i])) !== null) {
      const raw = m[1] || m[2] || m[3];
      const n = parseInt(raw.replace(/,/g, ''), 10);
      if (!isNaN(n) && n > 0 && n < 10000000) candidates.push(n);
    }
  }

  if (!candidates.length) return '';
  return Math.max.apply(null, candidates);
}

/**
 * 店名抽出：
 *   1) クレジット控え等の「加盟店」行があれば最優先で採用
 *   2) なければ先頭付近の、数字や記号でない最初の意味のある行
 */
function extractStore_(text) {
  if (!text) return '';
  const lines = text.split(/\r?\n/);

  // 1) 「加盟店 ○○○」（同じ行 or 次の行）を最優先
  for (let i = 0; i < lines.length; i++) {
    if (/加盟店/.test(lines[i])) {
      // 同じ行の「加盟店」より後ろを取る
      const sameLine = lines[i].replace(/^.*加盟店[:：\s]*/, '').trim();
      if (cleanStore_(sameLine).length >= 2) return cleanStore_(sameLine);
      // 同じ行に無ければ次の行
      const nextLine = (lines[i + 1] || '').trim();
      if (cleanStore_(nextLine).length >= 2) return cleanStore_(nextLine);
    }
  }

  // 2) フォールバック：先頭付近の意味のある行
  for (let i = 0; i < lines.length && i < 6; i++) {
    const line = lines[i].trim();
    if (line.length < 2) continue;
    if (/^\d/.test(line)) continue; // 日付・金額・番号っぽい行
    if (/(領収|レシート|TEL|電話|〒|住所)/.test(line)) continue;
    return cleanStore_(line);
  }
  return lines[0] ? cleanStore_(lines[0]) : '';
}

/**
 * 店名から余計な引用符・記号・前後の空白を取り除く
 */
function cleanStore_(s) {
  if (!s) return '';
  return s
    .replace(/[”“"'｢｣「」『』*◆※]/g, '') // 装飾の引用符・記号を除去
    .replace(/\s+/g, ' ')                  // 連続スペースを1つに
    .trim();
}

/**
 * 【1回だけ実行】APIキーをスクリプトプロパティに安全に保存する。
 * 下の 'ここにAPIキー' を、発行した AIza... のキーに書き換えてから実行。
 * 実行後はコード上のキーを消しておくこと（プロパティに保存済みなので消してOK）。
 */
function saveApiKey() {
  const KEY = 'ここにAPIキー';
  if (KEY === 'ここにAPIキー') {
    throw new Error('コード内の「ここにAPIキー」を実際のキーに書き換えてから実行してください。');
  }
  PropertiesService.getScriptProperties().setProperty('VISION_API_KEY', KEY);
  Logger.log('✅ APIキーを保存しました。コード上のキーは消してOKです。');
}

/**
 * 動作テスト用：投入箱の最初の1ファイルだけOCRしてログに全文表示（書き込みはしない）
 */
function testOcrOne() {
  const props = PropertiesService.getScriptProperties();
  const apiKey = props.getProperty('VISION_API_KEY');
  const inbox = DriveApp.getFolderById(props.getProperty('INBOX_FOLDER_ID'));
  const files = inbox.getFiles();
  if (!files.hasNext()) {
    Logger.log('投入箱にファイルがありません。テスト画像を1枚入れてください。');
    return;
  }
  const file = files.next();
  const text = ocrFile_(file, apiKey);
  Logger.log('ファイル名：' + file.getName());
  Logger.log('──── OCR全文 ────\n' + text);
  Logger.log('──── 抽出結果 ────\n' + JSON.stringify(extractInfo_(text), null, 2));
}
