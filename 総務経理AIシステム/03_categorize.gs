/**
 * 橋本工業 総務・経理AIシステム
 * Phase 2 - 自動振り分けスクリプト
 *
 * 役割：「未処理」シートの未振分データを科目マスタと照合し、
 *       ・勘定科目（借方）を自動判定
 *       ・支払方法から貸方（現金/未払金）を自動判定
 *       ・問題なければ「仕訳候補」へ、要確認は「確認待ち」へ振り分け
 *       処理した未処理行のステータスを「振分済」に更新する。
 *
 * 前提：02_ocr.gs の runOcr() で「未処理」シートにデータがある状態。
 * 使い方：categorize() を実行する（後でWebアプリのボタンから呼ぶ）。
 */

// ===== 設定 =====
const HIGH_AMOUNT = 100000; // この金額以上は「高額」として確認待ちへ（必要なら変更可）

/**
 * メイン：未処理シートの未振分データを振り分ける
 */
function categorize() {
  const ssId = PropertiesService.getScriptProperties().getProperty('SPREADSHEET_ID');
  const ss = SpreadsheetApp.openById(ssId);

  const mishori = ss.getSheetByName('未処理');
  const koho = ss.getSheetByName('仕訳候補');
  const kakunin = ss.getSheetByName('確認待ち');

  const rules = loadMaster_(ss);
  const corrections = loadStoreCorrections_(ss); // 店名補正表（無ければ自動作成）

  const data = mishori.getDataRange().getValues();
  // 列: 0=ファイルID 1=ファイル名 2=取込日時 3=日付 4=金額 5=店名 6=OCR全文 7=ステータス
  let toKoho = 0, toKakunin = 0;

  for (let r = 1; r < data.length; r++) {
    const row = data[r];
    if (row[7] === '振分済') continue;     // 処理済みはスキップ
    if (!row[0]) continue;                 // 空行スキップ

    const fileId = row[0];
    const date = row[3];
    const amount = row[4];
    const store = normalizeStore_(row[5], corrections); // 店名を補正
    const text = String(row[6] || '');

    // --- 借方科目を判定 ---
    const haystack = (store + ' ' + text);
    const matched = matchCategory_(haystack, rules); // {kari, kashi} or null

    // --- 貸方科目を判定（支払方法から）---
    const kashikata = detectPayment_(text);

    // --- 摘要（とりあえず店名。後で人が補える）---
    const tekiyo = store || '';

    // --- 確認待ち理由のチェック（異常値検知）---
    const reasons = [];
    if (!date) reasons.push('日付が読み取れない');
    if (!amount || amount === '') reasons.push('金額が読み取れない');
    if (!matched) reasons.push('科目を自動判定できない');
    if (amount && Number(amount) >= HIGH_AMOUNT) reasons.push('高額（要確認）');

    const kari = matched ? matched.kari : '';

    if (reasons.length > 0) {
      // 確認待ちへ
      // 列: 日付 店名 金額 借方 貸方 摘要 要確認理由 元ファイルID ステータス
      kakunin.appendRow([date, store, amount, kari, kashikata, tekiyo, reasons.join(' / '), fileId, '未確認']);
      toKakunin++;
    } else {
      // 仕訳候補へ
      // 列: 日付 店名 金額 借方 貸方 摘要 信頼度 元ファイルID ステータス
      const confidence = matched.hits >= 2 ? '高' : '中';
      koho.appendRow([date, store, amount, kari, kashikata, tekiyo, confidence, fileId, '未確認']);
      toKoho++;
    }

    // 未処理側を振分済みに
    mishori.getRange(r + 1, 8).setValue('振分済');
  }

  const msg = '振り分け完了：仕訳候補 ' + toKoho + '件／確認待ち ' + toKakunin + '件';
  Logger.log(msg);
  return msg;
}

/**
 * 科目マスタを読み込み、ルール配列にする
 * 戻り値: [{ keywords:[...], kari:'車両費', kashi:'現金' }, ...]
 */
function loadMaster_(ss) {
  const sheet = ss.getSheetByName('科目マスタ');
  const data = sheet.getDataRange().getValues();
  // 列: 0=キーワード 1=借方科目 2=貸方科目 3=備考
  const rules = [];
  for (let r = 1; r < data.length; r++) {
    const kw = String(data[r][0] || '').trim();
    const kari = String(data[r][1] || '').trim();
    if (!kw || !kari) continue;
    const keywords = kw.split(',').map(function (s) { return s.trim(); }).filter(function (s) { return s.length > 0; });
    rules.push({ keywords: keywords, kari: kari, kashi: String(data[r][2] || '').trim() });
  }
  return rules;
}

/**
 * 文字列を科目マスタと照合し、最も一致したルールを返す
 * 戻り値: { kari, kashi, hits } または null
 */
function matchCategory_(haystack, rules) {
  let best = null;
  for (let i = 0; i < rules.length; i++) {
    const rule = rules[i];
    let hits = 0;
    for (let k = 0; k < rule.keywords.length; k++) {
      if (haystack.indexOf(rule.keywords[k]) >= 0) hits++;
    }
    if (hits > 0 && (!best || hits > best.hits)) {
      best = { kari: rule.kari, kashi: rule.kashi, hits: hits };
    }
  }
  return best;
}

/**
 * 支払方法を判定して貸方科目を返す
 * クレジット系の語があれば「未払金」、なければ「現金」
 */
function detectPayment_(text) {
  const creditWords = /(クレジット|カード|ＶＩＳＡ|VISA|MASTER|マスター|JCB|AMEX|アメックス|ダイナース|一括払|分割払|リボ|ご利用日|加盟店|承認番号)/i;
  return creditWords.test(text) ? '未払金' : '現金';
}

/**
 * 店名補正表を読み込む（無ければ自動作成して例を入れる）
 * 戻り値: [{ match:'DCMフジエダ', correct:'DCMフジエダミズモリテン' }, ...]
 */
function loadStoreCorrections_(ss) {
  let sheet = ss.getSheetByName('店名補正');
  if (!sheet) {
    sheet = ss.insertSheet('店名補正');
    sheet.getRange(1, 1, 1, 3).setValues([['一致キーワード（部分一致）', '正しい店名', '備考']])
      .setFontWeight('bold').setBackground('#D9EAD3').setHorizontalAlignment('center');
    sheet.setFrozenRows(1);
    sheet.getRange(2, 1, 1, 3).setValues([
      ['DCMフジエダ', 'DCMフジエダミズモリテン', 'OCRが記号や濁点でブレるため店名を固定']
    ]);
    sheet.setColumnWidth(1, 220);
    sheet.setColumnWidth(2, 260);
    sheet.setColumnWidth(3, 320);
  }
  const data = sheet.getDataRange().getValues();
  // 列: 0=一致キーワード 1=正しい店名 2=備考
  const list = [];
  for (let r = 1; r < data.length; r++) {
    const m = String(data[r][0] || '').trim();
    const c = String(data[r][1] || '').trim();
    if (m && c) list.push({ match: m, correct: c });
  }
  return list;
}

/**
 * 店名を正規化：余計な記号を除去し、補正表に一致すれば正しい店名に置換
 */
function normalizeStore_(rawStore, corrections) {
  let s = String(rawStore || '')
    .replace(/[”“"'｢｣「」『』*◆※]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
  for (let i = 0; i < corrections.length; i++) {
    if (s.indexOf(corrections[i].match) >= 0) return corrections[i].correct;
  }
  return s;
}
