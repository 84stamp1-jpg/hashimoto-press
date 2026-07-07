/**
 * 橋本工業 総務・経理AIシステム
 * Phase 1 - セットアップスクリプト
 *
 * 役割：Google Drive のフォルダ構成と、管理用スプレッドシート（5シート）を
 *       ワンクリックで自動生成する。生成したIDはスクリプトプロパティに保存し、
 *       以降のスクリプト（OCR・振り分け・CSV出力）から参照できるようにする。
 *
 * 使い方：GASエディタで setup() を1回だけ実行する。
 *         2回目以降は「すでにセットアップ済み」と表示され、重複作成しない。
 */

// ===== 設定（必要なら名前だけ変更可。基本このままでOK） =====
const ROOT_FOLDER_NAME = '総務_経理システム';
const SUB_FOLDERS = ['01_レシート投入箱', '02_処理済み', '03_月別アーカイブ', '04_弥生取込用CSV'];
const SPREADSHEET_NAME = '総務_経理_管理表';

/**
 * メイン：1回だけ実行する
 */
function setup() {
  const props = PropertiesService.getScriptProperties();

  if (props.getProperty('SPREADSHEET_ID')) {
    Logger.log('⚠️ すでにセットアップ済みです。重複作成を防ぐため処理を中止しました。');
    Logger.log('やり直したい場合は resetSetup() を実行してから setup() を再実行してください。');
    showSummary_();
    return;
  }

  // --- 1) フォルダ構成を作成 ---
  const rootFolder = DriveApp.createFolder(ROOT_FOLDER_NAME);
  const folderIds = { ROOT: rootFolder.getId() };

  SUB_FOLDERS.forEach(function (name) {
    const f = rootFolder.createFolder(name);
    // 「01_レシート投入箱」→「INBOX」のようなキーで保存
    const key = folderKey_(name);
    folderIds[key] = f.getId();
  });

  // --- 2) スプレッドシートを作成し、ルートフォルダへ移動 ---
  const ss = SpreadsheetApp.create(SPREADSHEET_NAME);
  const ssFile = DriveApp.getFileById(ss.getId());
  rootFolder.addFile(ssFile);
  DriveApp.getRootFolder().removeFile(ssFile); // マイドライブ直下からは外す

  // --- 3) 各シートを作成・整形 ---
  buildSheets_(ss);

  // --- 4) IDをスクリプトプロパティに保存 ---
  props.setProperty('SPREADSHEET_ID', ss.getId());
  props.setProperty('ROOT_FOLDER_ID', folderIds.ROOT);
  props.setProperty('INBOX_FOLDER_ID', folderIds.INBOX);
  props.setProperty('DONE_FOLDER_ID', folderIds.DONE);
  props.setProperty('ARCHIVE_FOLDER_ID', folderIds.ARCHIVE);
  props.setProperty('CSV_FOLDER_ID', folderIds.CSV);

  Logger.log('✅ セットアップが完了しました！');
  showSummary_();
}

/**
 * 各シートの作成とヘッダー・初期データの投入
 */
function buildSheets_(ss) {
  // 既定の「シート1」は後で消す
  const defaultSheet = ss.getSheets()[0];

  // 未処理：OCR結果の一時保管
  makeSheet_(ss, '未処理', [
    'ファイルID', 'ファイル名', '取込日時', '抽出_日付', '抽出_金額', '抽出_店名', 'OCR全文', 'ステータス'
  ]);

  // 仕訳候補：科目自動振り分け後
  makeSheet_(ss, '仕訳候補', [
    '日付', '店名', '金額', '借方科目', '貸方科目', '摘要', '信頼度', '元ファイルID', 'ステータス'
  ]);

  // 確認待ち：人間の判断が必要なもの
  makeSheet_(ss, '確認待ち', [
    '日付', '店名', '金額', '借方科目', '貸方科目', '摘要', '要確認理由', '元ファイルID', 'ステータス'
  ]);

  // 完了済み：弥生に送り込んだもの
  makeSheet_(ss, '完了済み', [
    '日付', '借方科目', '借方金額', '貸方科目', '貸方金額', '摘要', 'CSV出力日時', '元ファイルID'
  ]);

  // 科目マスタ：勘定科目と振り分けルール（ノーコードで編集可）
  const masterSheet = makeSheet_(ss, '科目マスタ', [
    'キーワード（カンマ区切り）', '借方科目', '貸方科目', '備考'
  ]);
  const masterRows = [
    ['ガソリン,燃料,給油,ENEOS,出光,コスモ,シェル', '車両費', '現金', '車両の燃料代'],
    ['高速,ETC,料金所,NEXCO', '旅費交通費', '現金', '高速道路・有料道路'],
    ['駐車,パーキング,コインパーキング', '旅費交通費', '現金', '駐車場代'],
    ['文具,コピー用紙,事務用品,ボールペン,ノート', '消耗品費', '現金', '事務用消耗品'],
    ['接待,飲食,居酒屋,レストラン,会食', '交際費', '現金', '取引先との飲食'],
    ['宅急便,ゆうパック,宅配,送料,ヤマト,佐川', '荷造運賃', '現金', '荷物の発送'],
    ['切手,はがき,郵便,郵送', '通信費', '現金', '郵便物'],
    ['工具,部品,ネジ,材料,金物', '消耗品費（製造）', '現金', '製造現場の消耗品'],
    ['コーヒー,お茶,飲料,お菓子', '福利厚生費', '現金', '来客用・休憩用'],
    ['', '', '', '↑ここに行を追加すればルールを増やせます']
  ];
  masterSheet.getRange(2, 1, masterRows.length, 4).setValues(masterRows);
  masterSheet.setColumnWidth(1, 360);
  masterSheet.setColumnWidth(4, 220);

  // 既定シートを削除
  ss.deleteSheet(defaultSheet);

  // シートの並び順を整える
  ['未処理', '仕訳候補', '確認待ち', '完了済み', '科目マスタ'].forEach(function (name, i) {
    ss.setActiveSheet(ss.getSheetByName(name));
    ss.moveActiveSheet(i + 1);
  });
}

/**
 * シートを作成しヘッダー行を装飾する小道具
 */
function makeSheet_(ss, name, headers) {
  const sheet = ss.insertSheet(name);
  sheet.getRange(1, 1, 1, headers.length).setValues([headers])
    .setFontWeight('bold')
    .setBackground('#D9EAD3')
    .setHorizontalAlignment('center');
  sheet.setFrozenRows(1);
  sheet.autoResizeColumns(1, headers.length);
  return sheet;
}

/**
 * フォルダ名→保存キーの対応
 */
function folderKey_(name) {
  if (name.indexOf('投入箱') >= 0) return 'INBOX';
  if (name.indexOf('処理済み') >= 0) return 'DONE';
  if (name.indexOf('アーカイブ') >= 0) return 'ARCHIVE';
  if (name.indexOf('CSV') >= 0) return 'CSV';
  return name;
}

/**
 * 作成結果をログに表示
 */
function showSummary_() {
  const props = PropertiesService.getScriptProperties();
  const ssId = props.getProperty('SPREADSHEET_ID');
  Logger.log('──────── セットアップ内容 ────────');
  Logger.log('管理表スプレッドシート: https://docs.google.com/spreadsheets/d/' + ssId);
  Logger.log('レシート投入箱フォルダID: ' + props.getProperty('INBOX_FOLDER_ID'));
  Logger.log('処理済みフォルダID      : ' + props.getProperty('DONE_FOLDER_ID'));
  Logger.log('月別アーカイブフォルダID: ' + props.getProperty('ARCHIVE_FOLDER_ID'));
  Logger.log('弥生CSVフォルダID       : ' + props.getProperty('CSV_FOLDER_ID'));
  Logger.log('────────────────────────────────');
}

/**
 * 【注意】やり直し用：保存したIDを消す（フォルダ・シート自体は消えません）
 * これを実行後に setup() を再実行すると、新しく作り直せます。
 * 古いフォルダ・シートはDriveから手動で削除してください。
 */
function resetSetup() {
  PropertiesService.getScriptProperties().deleteAllProperties();
  Logger.log('スクリプトプロパティを消去しました。setup() を再実行できます。');
}
