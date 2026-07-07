/**
 * 橋本工業 総務・経理AIシステム
 * Phase 2 - 実務用Webアプリ（サーバー側）
 *
 * 役割：ブラウザの画面（index.html）から呼ばれる処理。
 *       ・OCR実行 / 自動振り分け
 *       ・現状サマリー（投入箱・仕訳候補・確認待ちの件数）
 *       ・確認待ちの一覧取得 / 確定（仕訳候補へ移動）
 *
 * 使い方：このプロジェクトを「ウェブアプリ」としてデプロイし、
 *         発行されたURLを実務PCで開く。
 */

/** Webアプリの入口：画面を表示する */
function doGet() {
  return HtmlService.createHtmlOutputFromFile('index')
    .setTitle('総務経理 レシート処理')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

/** 画面上部のサマリー情報を返す */
function getDashboard() {
  const props = PropertiesService.getScriptProperties();
  const ss = SpreadsheetApp.openById(props.getProperty('SPREADSHEET_ID'));

  // 投入箱の枚数
  let inboxCount = 0;
  const files = DriveApp.getFolderById(props.getProperty('INBOX_FOLDER_ID')).getFiles();
  while (files.hasNext()) {
    const f = files.next();
    const mime = f.getMimeType();
    if (mime.indexOf('image/') === 0 || mime === MimeType.PDF) inboxCount++;
  }

  return {
    inbox: inboxCount,
    koho: countUnprocessed_(ss.getSheetByName('仕訳候補')),
    kakunin: countUnprocessed_(ss.getSheetByName('確認待ち')),
    sheetUrl: ss.getUrl()
  };
}

/** ステータスが「確定済」でない行数を数える */
function countUnprocessed_(sheet) {
  const data = sheet.getDataRange().getValues();
  let n = 0;
  for (let r = 1; r < data.length; r++) {
    if (!data[r][0]) continue;
    if (data[r][8] !== '確定済') n++;
  }
  return n;
}

/** 画面の「OCR実行」ボタン */
function webRunOcr() {
  return runOcr();        // 02_ocr.gs
}

/** 画面の「自動振り分け」ボタン */
function webCategorize() {
  return categorize();    // 03_categorize.gs
}

/** 確認待ちの一覧を返す（未確定のものだけ） */
function getKakuninList() {
  const ss = SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty('SPREADSHEET_ID'));
  const sheet = ss.getSheetByName('確認待ち');
  const data = sheet.getDataRange().getValues();
  // 列: 0日付 1店名 2金額 3借方 4貸方 5摘要 6要確認理由 7元ファイルID 8ステータス
  const list = [];
  for (let r = 1; r < data.length; r++) {
    if (!data[r][0] && !data[r][1]) continue;
    if (data[r][8] === '確定済') continue;
    list.push({
      row: r + 1,                                  // シート上の行番号
      date: formatCell_(data[r][0]),
      store: data[r][1],
      amount: data[r][2],
      kari: data[r][3],
      kashi: data[r][4],
      tekiyo: data[r][5],
      reason: data[r][6],
      fileId: data[r][7]
    });
  }
  return list;
}

/** 確認待ちの1件を確定 → 仕訳候補へ移動 */
function confirmKakunin(item) {
  const ss = SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty('SPREADSHEET_ID'));
  const kakunin = ss.getSheetByName('確認待ち');
  const koho = ss.getSheetByName('仕訳候補');

  // 仕訳候補へ追加（人が確認済みなので信頼度は「確認済」）
  koho.appendRow([
    item.date, item.store, item.amount, item.kari, item.kashi, item.tekiyo,
    '確認済', item.fileId, '未確認'
  ]);

  // 確認待ち側を確定済みにする（行は消さずステータス変更）
  kakunin.getRange(item.row, 9).setValue('確定済');
  return 'ok';
}

/** 確認待ちの1件を削除する（テストデータや不要レシートの除去用） */
function deleteKakunin(item) {
  const ss = SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty('SPREADSHEET_ID'));
  const sheet = ss.getSheetByName('確認待ち');

  // 安全確認：画面のデータと実際の行がズレていないか照合
  const rowVals = sheet.getRange(item.row, 1, 1, 9).getValues()[0];
  if (String(rowVals[7]) !== String(item.fileId) && String(rowVals[1]) !== String(item.store)) {
    throw new Error('データがずれています。「再読み込み」してからやり直してください。');
  }

  sheet.deleteRow(item.row);
  return 'ok';
}

/** 勘定科目の選択肢（科目マスタの借方科目）を返す */
function getKamokuList() {
  const ss = SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty('SPREADSHEET_ID'));
  const data = ss.getSheetByName('科目マスタ').getDataRange().getValues();
  const set = {};
  for (let r = 1; r < data.length; r++) {
    const k = String(data[r][1] || '').trim();
    if (k) set[k] = true;
  }
  return Object.keys(set);
}

/** 日付セルを yyyy/MM/dd 文字列に整える */
function formatCell_(v) {
  if (v instanceof Date) return Utilities.formatDate(v, 'Asia/Tokyo', 'yyyy/MM/dd');
  return v;
}
