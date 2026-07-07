// ================================================================
// 橋本工業　基準遵守手当システム　GAS v3.8
// App74：週次チェック・減点記録
// App75：5S巡回チェック
// App73：減点項目マスタ
// App25：社員マスタ
// ================================================================

var CONFIG = {
  KINTONE_DOMAIN:       "hashimoto-kogyo.cybozu.com",
  SLACK_WEBHOOK_NORMAL: "https://hooks.slack.com/services/【★GASスクリプトプロパティで設定。公開リポジトリのためURL除去済み】",  // テスト用
  SLACK_WEBHOOK_URGENT: "https://hooks.slack.com/services/【★GASスクリプトプロパティで設定。公開リポジトリのためURL除去済み】", // 本番用
  APP_WEEKLY:  "74",
  APP_5S:      "75",
  APP_MASTER:  "73",
  APP_MEMBER:  "25",

  // チームコード→部門名マッピング（App73の波及範囲テキストと照合用）
  TEAM_KEYWORDS: {
    "T1": ["プレス"],
    "T2": ["金型"],
    "T3": ["組立"],
    "T4": ["品質", "品管"],
    "T5": ["納入"],
    "T6": ["総務"],
  },
  // 部門名（ライン名）リスト
  // App74の対象者欄にこれらの名前が入力された場合、チーム全員に50%波及として処理する
  DEPT_NAMES: ["プレス", "技術", "金型", "品質管理", "組立", "納入管理", "総務"],
  NOTIFY_THRESHOLD: 50, // 残pt50%以下で警告マーク

  // 強制チーム波及ルール：指定部門の指定項目は「個人減点なし／全員チーム波及50%」にする
  // 例）プレスの段取り時間・計画達成率は、誰が対象でも本人を含むプレス全員に50%波及
  FORCE_TEAM_DEPT:  "プレス",
  FORCE_TEAM_ITEMS: ["段取り時間", "計画達成率"],
};

// 強制チーム波及の対象か判定（対象者の部門が指定部門 かつ 項目名が対象）
function isForceTeamItem(itemName, dept) {
  if (dept !== CONFIG.FORCE_TEAM_DEPT) return false;
  for (var i = 0; i < CONFIG.FORCE_TEAM_ITEMS.length; i++) {
    if (itemName.indexOf(CONFIG.FORCE_TEAM_ITEMS[i]) >= 0) return true;
  }
  return false;
}

// ================================================================
// doGet
// ================================================================
function doGet(e) {
  var params = e.parameter;
  var action = params.action || "";

  // actionなし → 管理画面HTML表示
  if (!action) {
    return HtmlService.createHtmlOutput(buildAdminHtml())
      .setTitle("橋本工業 基準遵守手当 管理画面")
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
  }

  var result;
  try {
    if      (action === "deduct")      { result = handleDeduct(params); }
    else if (action === "get5S")       { result = handle5SCheck(params); }
    else if (action === "getMonthly")  { result = handleGetMonthly(params); }
    else if (action === "sendDigest")        { result = sendSummaryNotification(false); }
    else if (action === "sendDigestProd")    { result = sendSummaryNotification(true); }
    else if (action === "sendDigest5S")      { result = send5SSummaryNotification(false); }
    else if (action === "sendDigest5SProd")  { result = send5SSummaryNotification(true); }
    else if (action === "5sNotify")          { result = handle5SNotify(params); }
    else if (action === "qualityNew")        { result = handleQualityNew(params); }
    else if (action === "qualityComplete")   { result = handleQualityComplete(params); }
    else if (action === "setSetting") { result = handleSetSetting(params); }
    else if (action === "weeklyCheck") { result = runWeeklyCheck(); }
    else if (action === "runMonthly") {
      var monthlyUrl = runMonthlyAggregation();
      result = { status: "ok", message: "月次集計完了！Google Sheetsに出力しました。（Slack通知は停止中）", sheetUrl: monthlyUrl || "" };
    } else if (action === "testSlack") {
      postToSlack(":white_check_mark: テスト：基準遵守手当Bot正常動作中です", false);
      result = { status: "ok", message: "Slackテスト送信完了です" };
    } else {
      result = { status: "error", message: "unknown action: " + action };
    }
  } catch (err) {
    result = { status: "error", message: err.toString() };
    Logger.log("doGet error: " + err.toString());
  }
  return ContentService
    .createTextOutput(JSON.stringify(result))
    .setMimeType(ContentService.MimeType.JSON);
}

// ================================================================
// 機能設定の保存（管理画面トグルから呼び出し）
// ================================================================
function handleSetSetting(params) {
  var key = params.key   || "";
  var val = params.value || "";
  var allowed = ["SETTING_DIGEST", "SETTING_5S_DIGEST", "SETTING_SLACK_TEST"];
  if (allowed.indexOf(key) === -1 || (val !== "on" && val !== "off")) {
    return { status: "error", message: "invalid params" };
  }
  PropertiesService.getScriptProperties().setProperty(key, val);
  Logger.log("設定変更: " + key + " = " + val);
  return { status: "ok", key: key, value: val };
}

// ================================================================
// 管理画面HTML
// ================================================================
function buildAdminHtml() {
  var url   = ScriptApp.getService().getUrl();
  var today = Utilities.formatDate(new Date(), "Asia/Tokyo", "yyyy年MM月dd日");
  var month = Utilities.formatDate(new Date(), "Asia/Tokyo", "yyyy年MM月");

  // 設定・件数を取得
  var props = PropertiesService.getScriptProperties();
  var showDigest    = (props.getProperty("SETTING_DIGEST")     || "off") === "on";
  var show5SDigest  = (props.getProperty("SETTING_5S_DIGEST")  || "off") === "on";
  var showSlackTest = (props.getProperty("SETTING_SLACK_TEST") || "off") === "on";

  var pendingCount = 0;
  try { pendingCount = JSON.parse(props.getProperty("PENDING_DEDUCTS") || "[]").length; } catch(e) {}
  var pending5SCount = 0;
  try { pending5SCount = JSON.parse(props.getProperty("PENDING_5S") || "[]").length; } catch(e) {}

  // Google Sheetsリンク
  var sheetId  = props.getProperty("MONTHLY_SHEET_ID") || "";
  var sheetUrl = sheetId ? "https://docs.google.com/spreadsheets/d/" + sheetId : "";

  var html = [];
  html.push("<!DOCTYPE html><html lang='ja'><head><meta charset='UTF-8'>");
  html.push("<meta name='viewport' content='width=device-width,initial-scale=1'>");
  html.push("<title>基準遵守手当</title>");
  html.push("<style>");
  html.push("body{font-family:'Meiryo UI',sans-serif;background:#f0f4f8;margin:0;padding:16px;}");
  html.push(".wrap{max-width:560px;margin:0 auto;}");
  html.push(".hd{background:#1F4E79;color:#fff;padding:18px;border-radius:8px;margin-bottom:16px;}");
  html.push(".hd h1{margin:0;font-size:18px;}");
  html.push(".hd p{margin:4px 0 0;font-size:12px;opacity:.8;}");
  html.push(".card{background:#fff;border-radius:8px;padding:18px;margin-bottom:14px;box-shadow:0 2px 6px rgba(0,0,0,.1);}");
  html.push(".card h2{margin:0 0 6px;font-size:15px;color:#1F4E79;}");
  html.push(".card p{margin:0 0 12px;font-size:12px;color:#555;line-height:1.7;}");
  html.push(".steps{background:#EBF5FB;padding:10px 10px 10px 24px;border-radius:6px;font-size:12px;color:#1F4E79;margin-bottom:14px;}");
  html.push(".steps li{margin:3px 0;}");
  html.push(".btn{display:block;width:100%;padding:13px;font-size:14px;font-weight:bold;border:none;border-radius:6px;cursor:pointer;}");
  html.push(".btn-blue{background:#2E75B6;color:#fff;} .btn-blue:hover{background:#1F4E79;}");
  html.push(".btn-green{background:#70AD47;color:#fff;margin-top:8px;} .btn-green:hover{background:#548235;}");
  html.push(".btn-orange{background:#ED7D31;color:#fff;margin-top:8px;} .btn-orange:hover{background:#C65911;}");
  html.push(".btn:disabled{background:#bbb;cursor:not-allowed;}");
  html.push(".msg{margin-top:10px;padding:10px;border-radius:6px;font-size:12px;display:none;}");
  html.push(".ok{background:#E2EFDA;color:#375623;border:1px solid #70AD47;}");
  html.push(".err{background:#FCE4D6;color:#843c0c;border:1px solid #F4B183;}");
  html.push(".spin{display:none;text-align:center;color:#888;font-size:12px;margin-top:8px;}");
  html.push(".badge{display:inline-block;background:#C00000;color:#fff;border-radius:10px;padding:2px 8px;font-size:11px;margin-left:6px;}");
  // トグルスイッチ
  html.push(".setting-row{display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f0f0f0;}");
  html.push(".setting-row:last-child{border-bottom:none;}");
  html.push(".setting-label{font-size:13px;color:#333;}");
  html.push(".switch{position:relative;display:inline-block;width:46px;height:26px;flex-shrink:0;}");
  html.push(".switch input{opacity:0;width:0;height:0;}");
  html.push(".slider{position:absolute;cursor:pointer;top:0;left:0;right:0;bottom:0;background:#ccc;border-radius:26px;transition:.3s;}");
  html.push(".slider:before{position:absolute;content:'';height:20px;width:20px;left:3px;bottom:3px;background:#fff;border-radius:50%;transition:.3s;}");
  html.push("input:checked+.slider{background:#2E75B6;}");
  html.push("input:checked+.slider:before{transform:translateX(20px);}");
  html.push(".sheet-link{display:block;margin-top:10px;padding:9px 12px;background:#E8F4FD;border:1px solid #BDD7EE;border-radius:6px;font-size:12px;color:#1F4E79;text-decoration:none;word-break:break-all;}");
  html.push(".sheet-link:hover{background:#D0E8F5;}");
  html.push("</style></head><body><div class='wrap'>");

  // ヘッダー
  html.push("<div class='hd'><h1>橋本工業 基準遵守手当</h1>");
  html.push("<p>管理画面 &nbsp;&#x25cf;&nbsp; " + today + "</p></div>");

  // ─── 機能設定カード ───
  html.push("<div class='card'>");
  html.push("<h2>⚙ 機能設定</h2>");
  html.push("<p style='margin-bottom:12px;font-size:12px;color:#888;'>オフにすると該当カードが非表示になり、通知も停止されます。</p>");

  // まとめ通知（減点）
  html.push("<div class='setting-row'>");
  html.push("<span class='setting-label'>減点まとめ通知</span>");
  html.push("<label class='switch'>");
  html.push("<input type='checkbox' id='tog_digest'" + (showDigest ? " checked" : "") + " onchange='toggleFeature(\"SETTING_DIGEST\",\"card_digest\",this.checked)'>");
  html.push("<span class='slider'></span></label></div>");

  // まとめ通知（5S）
  html.push("<div class='setting-row'>");
  html.push("<span class='setting-label'>5Sまとめ通知</span>");
  html.push("<label class='switch'>");
  html.push("<input type='checkbox' id='tog_5s'" + (show5SDigest ? " checked" : "") + " onchange='toggleFeature(\"SETTING_5S_DIGEST\",\"card_5s\",this.checked)'>");
  html.push("<span class='slider'></span></label></div>");

  // Slackテスト
  html.push("<div class='setting-row'>");
  html.push("<span class='setting-label'>Slackテスト送信</span>");
  html.push("<label class='switch'>");
  html.push("<input type='checkbox' id='tog_slack'" + (showSlackTest ? " checked" : "") + " onchange='toggleFeature(\"SETTING_SLACK_TEST\",\"card_slack\",this.checked)'>");
  html.push("<span class='slider'></span></label></div>");

  html.push("</div>");

  // ─── 減点まとめ通知カード ───
  var badgeHtml = pendingCount > 0 ? "<span class='badge'>" + pendingCount + "件未送信</span>" : "";
  html.push("<div class='card' id='card_digest'" + (!showDigest ? " style='display:none'" : "") + ">");
  html.push("<h2>📋 減点まとめ通知" + badgeHtml + "</h2>");
  html.push("<p>kintoneで入力された減点記録をまとめてSlackに送信します。送信後はペンディングリストがリセットされます。</p>");
  html.push("<button class='btn btn-orange' id='btnDigest' onclick='sendDigest()'>🧪 テストに送信</button>");
  html.push("<button class='btn btn-blue' id='btnDigestProd' onclick='sendDigestProd()' style='margin-top:8px;'>📣 本番に送信（ペンディングをクリア）</button>");
  html.push("<div class='spin' id='sp3'>⏳ 送信中…</div>");
  html.push("<div class='msg' id='r3'></div></div>");

  // ─── 5Sまとめ通知カード ───
  var badge5SHtml = pending5SCount > 0 ? "<span class='badge'>" + pending5SCount + "件未送信</span>" : "";
  html.push("<div class='card' id='card_5s'" + (!show5SDigest ? " style='display:none'" : "") + ">");
  html.push("<h2>🔍 5S巡回まとめ通知" + badge5SHtml + "</h2>");
  html.push("<p>5S巡回チェックの指摘内容をまとめてSlackに送信します。</p>");
  html.push("<button class='btn btn-orange' id='btnDigest5S' onclick='sendDigest5S()'>🧪 テストに送信</button>");
  html.push("<button class='btn btn-blue' id='btnDigest5SProd' onclick='sendDigest5SProd()' style='margin-top:8px;'>📣 本番に送信（ペンディングをクリア）</button>");
  html.push("<div class='spin' id='sp4'>⏳ 送信中…</div>");
  html.push("<div class='msg' id='r4'></div></div>");

  // ─── 週次確認カード ───
  html.push("<div class='card'>");
  html.push("<h2>📆 週次確認</h2>");
  html.push("<p>今月の期間（前月21日〜本日）の減点状況を集計してGoogle Sheetsに出力します。手当計算には影響しません。</p>");
  if (sheetUrl) {
    html.push("<a class='sheet-link' href='" + sheetUrl + "' target='_blank'>📊 前回の集計結果を開く（Google Sheets）</a>");
  }
  html.push("<button class='btn btn-blue' id='btnWeekly' onclick='runWithSheet(\"weeklyCheck\",\"sp5\",\"r5\",\"btnWeekly\")' style='margin-top:10px;'>🔎 今月の途中経過を確認する</button>");
  html.push("<div class='spin' id='sp5'>⏳ 集計中…</div>");
  html.push("<div class='msg' id='r5'></div></div>");

  // ─── 月次集計カード ───
  html.push("<div class='card'>");
  html.push("<h2>📊 月次集計実行 &nbsp;<small style='font-weight:normal;color:#999;font-size:12px;'>対象：" + month + "</small></h2>");
  html.push("<p>App74（週次チェック）・App75（5S巡回）のデータを集計し、Google Sheetsに出力します。</p>");
  html.push("<ol class='steps'>");
  html.push("<li>App74・App75の入力が完了していることを確認</li>");
  html.push("<li>「月次集計実行」ボタンをクリック（1分程度かかります）</li>");
  html.push("<li>完了後に表示されるリンクからGoogle Sheetsを開く</li>");
  html.push("<li>Excelに3シート分を値のみ貼り付け → VBA「カード更新」ボタンを押す</li>");
  html.push("</ol>");
  if (sheetUrl) {
    html.push("<a class='sheet-link' href='" + sheetUrl + "' target='_blank'>📊 前回の集計結果を開く（Google Sheets）</a>");
  }
  html.push("<button class='btn btn-blue' id='btnRun' onclick='runMonthly()' style='margin-top:10px;'>▶ 月次集計を実行する</button>");
  html.push("<div class='spin' id='sp1'>⏳ 集計中…（1分程度）</div>");
  html.push("<div class='msg' id='r1'></div></div>");

  // ─── Slackテストカード ───
  html.push("<div class='card' id='card_slack'" + (!showSlackTest ? " style='display:none'" : "") + ">");
  html.push("<h2>🔔 Slackテスト</h2>");
  html.push("<p>Slackにテストメッセージを送信してBotの動作を確認します。</p>");
  html.push("<button class='btn btn-green' onclick='testSlack()'>✉ Slackテスト送信</button>");
  html.push("<div class='msg' id='r2'></div></div>");

  html.push("</div>");
  html.push("<script>");
  html.push("var U='" + url + "';");

  // 汎用action呼び出し
  html.push("function callAction(action,spinId,msgId,btnId,cb){");
  html.push("  var b=document.getElementById(btnId);");
  html.push("  b.disabled=true;");
  html.push("  document.getElementById(spinId).style.display='block';");
  html.push("  document.getElementById(msgId).style.display='none';");
  html.push("  fetch(U+'?action='+action)");
  html.push("    .then(function(r){return r.json();})");
  html.push("    .then(function(d){");
  html.push("      show(msgId,d.status==='ok',d.message);");
  html.push("      if(cb)cb(d);");
  html.push("      document.getElementById(spinId).style.display='none';");
  html.push("      b.disabled=false;");
  html.push("    }).catch(function(e){");
  html.push("      show(msgId,false,e.message);");
  html.push("      document.getElementById(spinId).style.display='none';");
  html.push("      b.disabled=false;");
  html.push("    });");
  html.push("}");

  // 週次・月次：完了後にシートリンクを表示
  html.push("function runWithSheet(action,spinId,msgId,btnId){");
  html.push("  callAction(action,spinId,msgId,btnId,function(d){");
  html.push("    if(d.sheetUrl){");
  html.push("      var el=document.getElementById(msgId);");
  html.push("      el.innerHTML+='<br><a href=\"'+d.sheetUrl+'\" target=\"_blank\" style=\"color:#1F4E79;font-weight:bold;\">📊 Google Sheetsを開く</a>';");
  html.push("    }");
  html.push("  });");
  html.push("}");

  html.push("function sendDigest()        { callAction('sendDigest',       'sp3','r3','btnDigest',null); }");
  html.push("function sendDigestProd()    { callAction('sendDigestProd',   'sp3','r3','btnDigestProd',null); }");
  html.push("function sendDigest5S()      { callAction('sendDigest5S',     'sp4','r4','btnDigest5S',null); }");
  html.push("function sendDigest5SProd()  { callAction('sendDigest5SProd', 'sp4','r4','btnDigest5SProd',null); }");

  html.push("function runMonthly(){");
  html.push("  runWithSheet('runMonthly','sp1','r1','btnRun');");
  html.push("}");

  html.push("function testSlack(){");
  html.push("  fetch(U+'?action=testSlack')");
  html.push("    .then(function(r){return r.json();})");
  html.push("    .then(function(d){show('r2',d.status==='ok',d.message);})");
  html.push("    .catch(function(e){show('r2',false,e.message);});");
  html.push("}");

  // 機能トグル
  html.push("function toggleFeature(key,cardId,isOn){");
  html.push("  fetch(U+'?action=setSetting&key='+key+'&value='+(isOn?'on':'off'))");
  html.push("    .then(function(r){return r.json();})");
  html.push("    .then(function(d){");
  html.push("      if(d.status==='ok'){");
  html.push("        document.getElementById(cardId).style.display=isOn?'block':'none';");
  html.push("      }");
  html.push("    });");
  html.push("}");

  html.push("function show(id,ok,msg){");
  html.push("  var el=document.getElementById(id);");
  html.push("  el.className='msg '+(ok?'ok':'err');");
  html.push("  el.innerHTML=(ok?'✅ ':'❌ ')+msg;");
  html.push("  el.style.display='block';");
  html.push("}");
  html.push("<\/script></body></html>");
  return html.join("\n");
}

// ================================================================
// 減点処理（kintoneカスタマイズから呼び出し）
// ※ 即時Slack通知を廃止 → ペンディングリストに蓄積してまとめ通知
// ================================================================
function handleDeduct(params) {
  var memberName = params.memberName || "";
  var deductItem = params.deductItem || "";
  var deductPt   = parseInt(params.deductPt || "0", 10);
  var pattern    = params.pattern    || "";
  var occurDate  = params.occurDate  || "";

  Logger.log("減点処理: " + memberName + " / " + deductItem + " / " + deductPt + "pt");

  // 社員マスタから基準pt・部署取得
  var memberInfo = getMemberInfo(memberName);
  var basePt     = memberInfo ? memberInfo.basePt : 150;
  var dept       = memberInfo ? memberInfo.dept : "";
  var monthly    = getMonthlyDeductTotal(memberName);
  var remaining  = basePt - monthly - deductPt;

  // ペンディングリストに追加（まとめ通知ボタン押下時に一括送信）
  addPendingDeduct({
    name:    memberName,
    dept:    dept,
    item:    deductItem,
    pt:      deductPt,
    pattern: pattern,
    date:    occurDate,
    basePt:  basePt,
  });

  return { status: "ok", memberName: memberName, deductPt: deductPt, remaining: remaining };
}

// ================================================================
// ペンディング減点リスト管理
// ================================================================
function addPendingDeduct(entry) {
  var props = PropertiesService.getScriptProperties();
  var list;
  try { list = JSON.parse(props.getProperty("PENDING_DEDUCTS") || "[]"); }
  catch(e) { list = []; }
  list.push(entry);
  props.setProperty("PENDING_DEDUCTS", JSON.stringify(list));
}

function clearPendingDeducts() {
  PropertiesService.getScriptProperties().setProperty("PENDING_DEDUCTS", "[]");
}

// ================================================================
// まとめ通知送信（管理画面ボタンから呼び出し）
// ================================================================
function sendSummaryNotification(toProduction) {
  var props = PropertiesService.getScriptProperties();
  var list;
  try { list = JSON.parse(props.getProperty("PENDING_DEDUCTS") || "[]"); }
  catch(e) { list = []; }

  if (list.length === 0) {
    return { status: "ok", message: "通知対象の減点記録がありません" };
  }

  // 集計期間（対象レコードの最小・最大日付）
  var dates = list.map(function(r) { return r.date; }).filter(Boolean).sort();
  var periodFrom = dates[0] || Utilities.formatDate(new Date(), "Asia/Tokyo", "yyyy-MM-dd");
  var periodTo   = dates[dates.length - 1] || periodFrom;

  // 現在の残ptを月次集計から取得
  var today  = new Date();
  var year   = today.getFullYear();
  var month  = today.getMonth();
  var df = Utilities.formatDate(new Date(year, month - 1, 21), "Asia/Tokyo", "yyyy-MM-dd");
  var dt = Utilities.formatDate(new Date(year, month,     20), "Asia/Tokyo", "yyyy-MM-dd");
  var monthlySummary = calcMonthlyFull(df, dt);
  var remainingMap = {};
  monthlySummary.forEach(function(s) {
    remainingMap[s.name] = { remaining: s.remaining, basePt: s.basePt };
  });

  // 人物別グループ化（部門順→氏名順）
  var DEPT_ORDER = ["プレス", "技術", "品質管理", "組立", "納入管理", "総務"];
  var personMap = {}; // { name: { dept, items:[] } }
  list.forEach(function(r) {
    if (!personMap[r.name]) personMap[r.name] = { dept: r.dept || "", items: [] };
    personMap[r.name].items.push(r);
  });

  // 部門順に並べた人物リストを作成
  var personOrder = [];
  DEPT_ORDER.forEach(function(dept) {
    Object.keys(personMap).forEach(function(name) {
      if (personMap[name].dept === dept && personOrder.indexOf(name) === -1) {
        personOrder.push(name);
      }
    });
  });
  // 上記に含まれない人物を末尾に追加
  Object.keys(personMap).forEach(function(name) {
    if (personOrder.indexOf(name) === -1) personOrder.push(name);
  });

  var text = ":clipboard: *基準遵守手当　減点まとめ通知*\n";
  text += ">集計期間：" + periodFrom + " ～ " + periodTo + "　件数：" + list.length + "件\n";

  personOrder.forEach(function(name) {
    var p    = personMap[name];
    var info = remainingMap[name] || { remaining: null, basePt: 150 };
    var rem  = info.remaining;
    var thresh = info.basePt * CONFIG.NOTIFY_THRESHOLD / 100;
    var warn   = (typeof rem === "number" && rem <= thresh) ? " ⚠️残pt要注意" : "";
    var remLabel = (typeof rem === "number") ? "　残" + rem + "pt" + warn : "";
    text += "\n*《" + name + "》*（" + p.dept + "）" + remLabel + "\n";
    p.items.forEach(function(r) {
      var dateStr = r.date || "";
      text += "> " + dateStr + " ／ " + r.item +
              " −" + r.pt + "pt [" + r.pattern + "]\n";
    });
  });

  postToSlack(text, toProduction);
  if (toProduction) {
    clearPendingDeducts();
    Logger.log("sendSummaryNotification 本番送信完了: " + list.length + "件");
    return { status: "ok", message: list.length + "件の減点を本番チャンネルに送信しました。ペンディングをクリアしました。" };
  } else {
    Logger.log("sendSummaryNotification テスト送信完了: " + list.length + "件");
    return { status: "ok", message: list.length + "件の減点をテストチャンネルに送信しました。確認後「本番送信」を押してください。" };
  }
}

// ================================================================
// 5Sまとめ通知送信（管理画面ボタンから呼び出し）
// ================================================================
function send5SSummaryNotification(toProduction) {
  var props = PropertiesService.getScriptProperties();
  var list5S;
  try { list5S = JSON.parse(props.getProperty("PENDING_5S") || "[]"); }
  catch(e) { list5S = []; }

  if (list5S.length === 0) {
    return { status: "ok", message: "通知対象の5S指摘がありません" };
  }

  var dates = list5S.map(function(r) { return r.date; }).filter(Boolean).sort();
  var periodFrom = dates[0] || Utilities.formatDate(new Date(), "Asia/Tokyo", "yyyy-MM-dd");
  var periodTo   = dates[dates.length - 1] || periodFrom;

  // 部署別グループ化
  var AREA_ORDER = ["プレス", "技術", "品質管理", "組立", "納入管理", "総務"];
  var areaMap = {};
  list5S.forEach(function(r) {
    var a = r.area || "その他";
    if (!areaMap[a]) areaMap[a] = [];
    areaMap[a].push(r);
  });

  // 部署順に並べた一覧
  var areaOrder = [];
  AREA_ORDER.forEach(function(a) { if (areaMap[a]) areaOrder.push(a); });
  Object.keys(areaMap).forEach(function(a) { if (areaOrder.indexOf(a) === -1) areaOrder.push(a); });

  var text = ":mag: *5S巡回チェック　指摘まとめ通知*\n";
  text += ">集計期間：" + periodFrom + " ～ " + periodTo + "　件数：" + list5S.length + "件\n";

  areaOrder.forEach(function(area) {
    text += "\n*《" + area + "》*\n";
    areaMap[area].forEach(function(r) {
      var issueList = r.issues.split("|").filter(Boolean).join("｜");
      var inspector = r.inspector ? r.inspector : "−";
      text += "> " + r.date + " ｜ " + issueList + " ｜ " + inspector + "\n";
    });
  });

  postToSlack(text, toProduction);
  if (toProduction) {
    clearPending5S();
    Logger.log("send5SSummaryNotification 本番送信完了: " + list5S.length + "件");
    return { status: "ok", message: "5S指摘" + list5S.length + "件を本番チャンネルに送信しました。ペンディングをクリアしました。" };
  } else {
    Logger.log("send5SSummaryNotification テスト送信完了: " + list5S.length + "件");
    return { status: "ok", message: "5S指摘" + list5S.length + "件をテストチャンネルに送信しました。確認後「本番送信」を押してください。" };
  }
}

// ================================================================
// 5Sプロセス即時通知（指摘ボタン・報告するボタン押下時）
// 本番チャンネルに即時送信
// ================================================================
function handle5SNotify(params) {
  var type         = params.type         || "";
  var area         = params.area         || "";
  var text         = "";

  if (type === "report") {
    // 指摘ボタン押下時
    var inspector = params.inspector || "";
    var date      = params.date      || "";
    var issues    = params.issues    || "";
    var issueList = issues.split("|").filter(Boolean);
    var issueText = issueList.length > 0
      ? issueList.map(function(i) { return "> • " + i; }).join("\n")
      : "> （指摘内容なし）";

    text  = ":mag: *5S巡回　指摘通知*\n";
    text += "> エリア：*" + area + "*\n";
    text += "> 日付：" + date + "\n";
    text += "> 記入者：" + inspector + "\n";
    text += "> 指摘内容：\n" + issueText;

  } else if (type === "complete") {
    // 報告するボタン押下時
    var reporter     = params.reporter     || "";
    var responseDate = params.responseDate || "";

    text  = ":white_check_mark: *5S巡回　改善完了報告*\n";
    text += "> エリア：*" + area + "*\n";
    text += "> 完了日：" + responseDate + "\n";
    text += "> 報告者：" + reporter;
  }

  if (!text) {
    return { status: "ok", message: "通知スキップ（typeなし）" };
  }

  postToSlack(text, true); // 本番チャンネルに即時送信
  Logger.log("handle5SNotify: " + type + " / " + area);
  return { status: "ok", message: "5S通知送信: " + type + " / " + area };
}

// ================================================================
// 5Sチェック（kintoneカスタマイズから呼び出し）
// ※ 即時Slack通知を廃止 → ペンディングリストに蓄積してまとめ通知
// ================================================================
function handle5SCheck(params) {
  var area      = params.area      || "";
  var inspector = params.inspector || "";
  var date      = params.date      || "";
  var issues    = params.issues    || "";

  if (!area || !issues) {
    return { status: "ok", message: "指摘なし・スキップ" };
  }

  addPending5S({
    area:      area,
    inspector: inspector,
    date:      date,
    issues:    issues, // "|"区切りの文字列
  });

  return { status: "ok", area: area };
}

function addPending5S(entry) {
  var props = PropertiesService.getScriptProperties();
  var list;
  try { list = JSON.parse(props.getProperty("PENDING_5S") || "[]"); }
  catch(e) { list = []; }
  list.push(entry);
  props.setProperty("PENDING_5S", JSON.stringify(list));
}

function clearPending5S() {
  PropertiesService.getScriptProperties().setProperty("PENDING_5S", "[]");
}

// ================================================================
// 月次集計データ取得（doGet用）
// ================================================================
function handleGetMonthly(params) {
  var year  = parseInt(params.year  || new Date().getFullYear(), 10);
  var month = parseInt(params.month || (new Date().getMonth() + 1), 10);
  var df    = Utilities.formatDate(new Date(year, month - 2, 21), "Asia/Tokyo", "yyyy-MM-dd");
  var dt    = Utilities.formatDate(new Date(year, month - 1, 20), "Asia/Tokyo", "yyyy-MM-dd");
  var result = calcMonthlyFull(df, dt);
  return { status: "ok", period: df + " ～ " + dt, records: result };
}

// ================================================================
// スプレッドシート名を生成（締め月ベース）
// 期首=21日 → 翌月20日締め。締め月(yyyy-MM)をファイル名に使う。
// 例: 期首2026-05-21（5/21〜6/20の期間）→「橋本工業_基準遵守手当_2026-06」
// ================================================================
function buildSheetName(dateFrom) {
  var p = dateFrom.split("-");
  // pは1始まりの月。new Date(年, 1始まり月, 20)で「翌月20日」=締め日になる
  var closeDate = new Date(parseInt(p[0], 10), parseInt(p[1], 10), 20);
  var label = Utilities.formatDate(closeDate, "Asia/Tokyo", "yyyy-MM");
  return "橋本工業_基準遵守手当_" + label;
}

// ================================================================
// 週次確認（途中経過チェック・手当計算に影響しない）
// ================================================================
function runWeeklyCheck() {
  var today = new Date();
  var year  = today.getFullYear();
  var month = today.getMonth();
  var day   = today.getDate();
  // 20日締め：21日以降は「当月21日」が期首、20日以前は「前月21日」が期首
  var startDate = (day >= 21)
    ? new Date(year, month,     21)
    : new Date(year, month - 1, 21);
  var df    = Utilities.formatDate(startDate, "Asia/Tokyo", "yyyy-MM-dd");
  var dt    = Utilities.formatDate(today, "Asia/Tokyo", "yyyy-MM-dd");
  var label = Utilities.formatDate(today, "Asia/Tokyo", "M/d");
  var elapsed = Math.floor((today - new Date(df)) / (1000 * 60 * 60 * 24)) + 1;

  Logger.log("週次確認 集計期間: " + df + " ～ " + dt);

  var summary = calcMonthlyFull(df, dt);
  if (!summary || summary.length === 0) {
    return { status: "ok", message: "集計対象データがありません" };
  }

  // ── Google Sheetsに出力 ──
  var props   = PropertiesService.getScriptProperties();
  var sheetId = props.getProperty("MONTHLY_SHEET_ID");
  var ss;
  if (sheetId) {
    try { ss = SpreadsheetApp.openById(sheetId); } catch(e) { ss = null; }
  }
  if (!ss) {
    ss = SpreadsheetApp.create(buildSheetName(df));
    props.setProperty("MONTHLY_SHEET_ID", ss.getId());
  }
  // ファイル名を締め月に自動更新
  try { ss.rename(buildSheetName(df)); } catch(e) { Logger.log("rename失敗: " + e); }

  // 週次集計タブ
  var tabName1 = "週次集計_" + label;
  var ws1 = ss.getSheetByName(tabName1);
  if (ws1) ss.deleteSheet(ws1);
  ws1 = ss.insertSheet(tabName1);

  var h1 = ["従業員番号","氏名","部門","基準pt","個人減点","チーム波及","全社波及","合計減点pt","残pt","手当見込み額"];
  ws1.getRange(1,1,1,h1.length).setValues([h1]).setFontWeight("bold")
     .setBackground("#2E75B6").setFontColor("#FFFFFF");

  var DEPT_ORDER = ["プレス","技術","品質管理","組立","納入管理","総務"];
  summary.sort(function(a,b){
    var ai = DEPT_ORDER.indexOf(a.dept); var bi = DEPT_ORDER.indexOf(b.dept);
    if (ai === -1) ai = 99; if (bi === -1) bi = 99;
    return ai !== bi ? ai - bi : (a.name > b.name ? 1 : -1);
  });

  var rows1 = summary.map(function(s) {
    return [s.empNo, s.name, s.dept, s.basePt,
            s.personal, s.teamWave, s.allWave, s.totalDeduct, s.remaining, s.allowance];
  });
  ws1.getRange(2,1,rows1.length,h1.length).setValues(rows1);

  // 残pt 50%以下を黄色ハイライト
  rows1.forEach(function(row, i) {
    if (typeof row[8] === "number" && row[8] <= row[3] * CONFIG.NOTIFY_THRESHOLD / 100) {
      ws1.getRange(i + 2, 9).setBackground("#FFE699");
    }
  });

  // 合計行
  var lr1 = rows1.length + 2;
  ws1.getRange(lr1, 1).setValue("合計");
  ws1.getRange(lr1, 8).setValue("=SUM(H2:H" + (rows1.length+1) + ")");
  ws1.getRange(lr1, 9).setValue("=SUM(I2:I" + (rows1.length+1) + ")");
  ws1.getRange(lr1, 10).setValue("=SUM(J2:J" + (rows1.length+1) + ")");
  ws1.getRange(lr1, 1, 1, h1.length).setFontWeight("bold").setBackground("#D9E1F2");
  ws1.autoResizeColumns(1, h1.length);

  // 週次明細タブ
  var tabName2 = "週次明細_" + label;
  var ws2 = ss.getSheetByName(tabName2);
  if (ws2) ss.deleteSheet(ws2);
  ws2 = ss.insertSheet(tabName2);

  var h2 = ["従業員番号","氏名","部門","減点理由","対象者","減点項目","発生日","減点pt","パターン","ソース"];
  ws2.getRange(1,1,1,h2.length).setValues([h2]).setFontWeight("bold")
     .setBackground("#2E75B6").setFontColor("#FFFFFF");

  var members    = fetchAllMembers();
  var records74  = fetchApp74Records(df, dt);
  var records75  = fetchApp75Records(df, dt);
  var masterMap  = fetchDeductMaster();
  var detailRows = buildPersonalDetails(members, records74, records75, masterMap, df, dt);
  if (detailRows.length > 0) {
    ws2.getRange(2,1,detailRows.length,h2.length).setValues(detailRows);
  }
  ws2.autoResizeColumns(1, h2.length);

  var sheetUrl = ss.getUrl();
  Logger.log("週次確認 Sheets出力: " + tabName1 + " / " + tabName2);

  // ── Slack通知（要注意メンバー＋リンク） ──
  var warned   = summary.filter(function(s) { return s.remaining <= s.basePt * CONFIG.NOTIFY_THRESHOLD / 100 && s.totalDeduct > 0; });
  var deducted = summary.filter(function(s) { return s.totalDeduct > 0; });

  var text = ":bar_chart: *週次確認　基準遵守手当　途中経過*\n";
  text += ">集計期間：" + df + " ～ " + dt + "（" + elapsed + "日経過）\n";
  text += ">対象：" + summary.length + "名　減点あり：" + deducted.length + "名\n";

  if (warned.length > 0) {
    text += "\n*⚠️ 残pt要注意（" + warned.length + "名）*\n";
    warned.forEach(function(s) {
      var zeroMark = s.remaining === 0 ? " 🚨ゼロ" : "";
      text += "> " + s.name + "（" + s.dept + "）残" + s.remaining + "pt" + zeroMark + "\n";
    });
  } else {
    text += "\n>✅ 残pt要注意メンバーはいません\n";
  }

  text += "\n>:link: *詳細（全員の内訳）はこちら:* " + sheetUrl;

  // ※ Slack通知は現在停止中（再開時は下2行のコメントを解除）
  // postToSlack(text, false);
  // postToSlack(text, true);

  Logger.log("runWeeklyCheck 完了: 減点あり " + deducted.length + "名");
  return { status: "ok", message: "週次確認完了。減点あり：" + deducted.length + "名", sheetUrl: sheetUrl };
}

// ================================================================
// 月次集計メイン（毎月20日トリガー）
// ================================================================
function runMonthlyAggregation() {
  var today  = new Date();
  var year   = today.getFullYear();
  var month  = today.getMonth(); // 0-indexed

  var dateFrom = Utilities.formatDate(new Date(year, month - 1, 21), "Asia/Tokyo", "yyyy-MM-dd");
  var dateTo   = Utilities.formatDate(new Date(year, month,     20), "Asia/Tokyo", "yyyy-MM-dd");

  Logger.log("集計期間: " + dateFrom + " ～ " + dateTo);

  var summary = calcMonthlyFull(dateFrom, dateTo);
  if (!summary || summary.length === 0) {
    Logger.log("★ データなし");
    return;
  }

  var ss = writeToSpreadsheet(dateFrom, dateTo, summary);
  // ※ Slack通知は現在停止中（再開時は下2行のコメントを解除）
  // var slackText = buildMonthlySlackMessage(dateFrom, dateTo, summary, ss.getUrl());
  // postToSlack(slackText, false);
  Logger.log("runMonthlyAggregation 完了: " + summary.length + "名分出力");
  return ss.getUrl();
}

// ================================================================
// 月次集計コア：波及計算込み
// ================================================================
function calcMonthlyFull(dateFrom, dateTo) {
  // 1. 社員マスタ取得
  var members = fetchAllMembers();
  if (!members.length) { Logger.log("ERROR: 社員マスタ取得失敗"); return []; }

  // 2. 減点項目マスタ取得
  var masterMap = fetchDeductMaster(); // key=減点項目名

  // 3. App74減点記録取得
  var records74 = fetchApp74Records(dateFrom, dateTo);
  // App75（5S巡回）減点記録取得・変換
  var records75 = fetchApp75Records(dateFrom, dateTo);
  Logger.log("App74取得: " + records74.length + "件 / App75変換: " + records75.length + "件");

  // グループ項目（1日1回制限）と通常項目に分類
  var nonGroupedRecs74 = [];
  var groupedRecs74 = [];
  records74.forEach(function(rec) {
    var itemName = rec["ルックアップ_0"]["value"] || "";
    var master = masterMap[itemName];
    var group = master ? (master.group || "") : "";
    if (group) { groupedRecs74.push(rec); } else { nonGroupedRecs74.push(rec); }
  });
  Logger.log("通常項目: " + nonGroupedRecs74.length + "件 / グループ項目(1日1回): " + groupedRecs74.length + "件");

  // 4. 社員ごとの減点集計テーブルを初期化
  var deductTable = {}; // { 氏名: { personal:0, teamWave:0, allWave:0 } }
  members.forEach(function(m) {
    deductTable[m.name] = { personal: 0, teamWave: 0, allWave: 0, basePt: m.basePt, team: m.team, dept: m.dept };
  });

  // 5. App74 通常項目レコードを処理
  nonGroupedRecs74.forEach(function(rec) {
    var targetName = rec["ルックアップ"]["value"]   || "";
    var itemName   = rec["ルックアップ_0"]["value"] || "";
    var pt         = parseInt(rec["数値"]["value"] || "0", 10);
    var pattern    = (rec["文字列__1行_"]["value"] || "").toUpperCase();

    if (!targetName || pt === 0) return;

    var master   = masterMap[itemName] || null;
    var waveText = master ? master.waveText : "";

    // 対象者がチーム代表かどうか
    // ①★で始まる  ②部門名（ライン名）そのもの  ③社員マスタに存在しない名前
    var isTeamRep = targetName.indexOf("★") === 0 ||
                    CONFIG.DEPT_NAMES.indexOf(targetName) >= 0;
    if (!isTeamRep && targetName) {
      var foundInMembers = false;
      for (var mi = 0; mi < members.length; mi++) {
        if (members[mi].name === targetName) { foundInMembers = true; break; }
      }
      if (!foundInMembers) isTeamRep = true;
    }

    // 強制チーム波及ルール：プレスの段取り時間・計画達成率は
    // 個人減点なし→全員チーム波及50%（パターンB扱い・isTeamRep扱い）
    var tgtDeptNG = "";
    for (var fdi = 0; fdi < members.length; fdi++) {
      if (members[fdi].name === targetName) { tgtDeptNG = members[fdi].dept; break; }
    }
    if (isForceTeamItem(itemName, tgtDeptNG)) {
      isTeamRep = true;
      pattern   = "B";
    }

    if (pattern === "A") {
      // パターンA：個人のみ
      if (!isTeamRep && deductTable[targetName]) {
        deductTable[targetName].personal += pt;
      } else if (isTeamRep) {
        // ★チーム代表のパターンAはチーム全員に波及
        var teamCode = getTeamCodeByRepName(targetName, members);
        applyTeamWave(deductTable, members, teamCode, pt);
      }

    } else if (pattern === "B") {
      // パターンB：個人 + 対象者部門全員 + 品管（波及範囲に品管含む場合）
      if (!isTeamRep && deductTable[targetName]) {
        deductTable[targetName].personal += pt;
        applyWaveByText(deductTable, members, waveText, pt, targetName);
      } else if (isTeamRep) {
        // ★チーム代表：そのチーム全員 + 品管（波及範囲に品管含む場合）
        var repDept = "";
        for (var ri = 0; ri < members.length; ri++) {
          if (members[ri].name === targetName) { repDept = members[ri].dept; break; }
        }
        // ★チーム代表はApp25に存在しないので代表名から部門を抽出
        if (!repDept) {
          repDept = extractDeptFromRepName(targetName);
        }
        var incHinkan = waveText.indexOf("品質") >= 0;
        var wPt = Math.floor(pt * 0.5); // チーム波及×50%
        members.forEach(function(m) {
          if (!deductTable[m.name]) return;
          if (m.dept === repDept) deductTable[m.name].teamWave += wPt;
          else if (incHinkan && m.dept === "品質管理" && repDept !== "品質管理") {
            deductTable[m.name].teamWave += wPt;
          }
        });
      }

    } else if (pattern === "C") {
      // パターンC：
      //   個人が対象者の場合 → 本人100% + 同チーム×70% + チーム外×50%
      //   ★チーム代表が対象者の場合 → チーム全員100% + チーム外×50%
      var targetDeptC = "";
      // 部門名そのものが対象者の場合はそのまま使用
      if (CONFIG.DEPT_NAMES.indexOf(targetName) >= 0) {
        targetDeptC = targetName;
      } else {
        for (var ci = 0; ci < members.length; ci++) {
          if (members[ci].name === targetName) { targetDeptC = members[ci].dept; break; }
        }
        if (!targetDeptC && isTeamRep) targetDeptC = extractDeptFromRepName(targetName);
      }
      // パターンCで波及範囲に品管が含まれる場合、品管は100%扱い
      var cIncludesHinkan = waveText.indexOf("品質") >= 0;

      members.forEach(function(m) {
        if (!deductTable[m.name]) return;
        // 品管メンバーで波及範囲に品管が含まれる場合は100%
        var isHinkanFull = cIncludesHinkan && m.dept === "品質管理";

        if (isTeamRep) {
          // ★チーム代表：チーム全員100%、品管（波及範囲指定あり）100%、チーム外50%
          if (targetDeptC && m.dept === targetDeptC) {
            deductTable[m.name].personal += pt;
          } else if (isHinkanFull && targetDeptC !== "品質管理") {
            deductTable[m.name].teamWave += pt; // 品管100%
          } else {
            deductTable[m.name].allWave += Math.floor(pt * 0.5);
          }
        } else {
          // 個人対象者：本人100%、同チーム×70%、品質管理×70%（同チーム扱い）、チーム外×50%
          if (m.name === targetName) {
            deductTable[m.name].personal += pt;
          } else if (targetDeptC && m.dept === targetDeptC) {
            deductTable[m.name].teamWave += Math.floor(pt * 0.7);
          } else if (isHinkanFull && targetDeptC !== "品質管理") {
            deductTable[m.name].teamWave += Math.floor(pt * 0.7); // 品質管理×70%
          } else {
            deductTable[m.name].allWave += Math.floor(pt * 0.5);
          }
        }
      });
    }
  });

  // 5a. App74 グループ項目（1日1回制限）を処理
  // 同一人物×同一日×同一グループで、各人が受け取る最大ptの1件のみを適用
  processGroupedRecords(groupedRecs74, masterMap, members, deductTable);
  Logger.log("グループ項目処理完了: " + groupedRecs74.length + "件（1日1回制限適用）");

  // 5b. App75（5S巡回）減点を処理
  records75.forEach(function(r75) {
    var area    = r75.area;    // 部門・エリア（「プレス」「組立」等）
    var pt      = r75.pt;
    var pattern = r75.pattern; // 常にB

    if (!area || pt === 0) return;

    // 「全体」は全社員に波及（パターンB扱いで全チーム×50%）
    var isAll = area === "全体";
    var wavePt = Math.floor(pt * 0.5);

    members.forEach(function(m) {
      if (!deductTable[m.name]) return;
      if (isAll) {
        // 全体→全員にチーム波及×50%
        deductTable[m.name].teamWave += wavePt;
      } else if (m.dept === area) {
        // 対象部門のメンバー全員→チーム波及として加算（部門全員100%）
        // ※personalではなくteamWaveに入れることでApp74の個人減点と区別
        deductTable[m.name].teamWave += pt;
      }
    });
  });

  // 6. 手当計算して結果配列に変換
  var result = members.map(function(m) {
    var d = deductTable[m.name] || { personal: 0, teamWave: 0, allWave: 0 };
    var totalDeduct  = d.personal + d.teamWave + d.allWave;
    var remaining    = m.basePt - totalDeduct;
    if (remaining < 0) remaining = 0;
    var allowance    = calcAllowance(m.basePt, remaining);
    return {
      empNo:       m.empNo,
      name:        m.name,
      dept:        m.dept,
      team:        m.team,
      basePt:      m.basePt,
      personal:    d.personal,
      teamWave:    d.teamWave,
      allWave:     d.allWave,
      totalDeduct: totalDeduct,
      remaining:   remaining,
      allowance:   allowance,
    };
  });

  return result;
}

// ================================================================
// 手当額計算（基準ptに応じたスライド）
// ================================================================
function calcAllowance(basePt, remaining) {
  // 残pt × 100円
  return remaining * 100;
}

// ================================================================
// 波及適用ヘルパー
// ================================================================
function applyWaveByText(deductTable, members, waveText, pt, targetName) {
  // パターンB波及ルール：
  //   同チーム員（本人除く）→ ×50%
  //   App73波及範囲に品管が含まれ、対象者が品管以外 → 品管メンバーも×50%
  if (!targetName) return;

  var targetDept = "";
  for (var i = 0; i < members.length; i++) {
    if (members[i].name === targetName) { targetDept = members[i].dept; break; }
  }

  var includesHinkan = waveText.indexOf("品質") >= 0;
  var wavePt = Math.floor(pt * 0.5); // チーム波及は×50%

  members.forEach(function(m) {
    if (m.name === targetName) return; // 本人除外
    var hit = false;
    if (targetDept && m.dept === targetDept) hit = true;
    if (includesHinkan && m.dept === "品質管理" && targetDept !== "品質管理") hit = true;
    if (hit) deductTable[m.name].teamWave += wavePt;
  });
}

function applyTeamWave(deductTable, members, teamCode, pt) {
  members.forEach(function(m) {
    if (m.teamCode === teamCode && deductTable[m.name]) {
      deductTable[m.name].teamWave += pt;
    }
  });
}

function getTeamCodeByRepName(repName, members) {
  // "★プレスチーム" → T1 のような変換
  for (var i = 0; i < members.length; i++) {
    var m = members[i];
    if (m.name === repName) return m.teamCode;
  }
  return null;
}

// ================================================================
// グループ項目（1日1回制限）処理
// 各人が同一日×同一グループから受け取る減点を最大pt1件分のみに制限する
// 入力元レコードが何件あっても、受け取り側で上限を適用する
// ================================================================
function processGroupedRecords(groupedRecs, masterMap, members, deductTable) {
  // maxContrib[personName + "|" + date + "|" + group] = { pt, bucket }
  var maxContrib = {};

  function consider(personName, date, group, pt, bucket) {
    if (!deductTable[personName]) return;
    var key = personName + "|" + date + "|" + group;
    if (!maxContrib[key] || pt > maxContrib[key].pt) {
      maxContrib[key] = { pt: pt, bucket: bucket };
    }
  }

  groupedRecs.forEach(function(rec) {
    var targetName = rec["ルックアップ"]["value"]   || "";
    var itemName   = rec["ルックアップ_0"]["value"] || "";
    var pt         = parseInt(rec["数値"]["value"] || "0", 10);
    var pattern    = (rec["文字列__1行_"]["value"] || "").toUpperCase();
    var date       = rec["日付_0"]["value"]         || "";
    var master     = masterMap[itemName] || {};
    var group      = master.group  || "";
    var waveText   = master.waveText || "";

    if (!targetName || pt === 0 || !group) return;

    // ①★で始まる  ②部門名（ライン名）そのもの  ③社員マスタに存在しない名前
    var isTeamRep = targetName.indexOf("★") === 0 ||
                    CONFIG.DEPT_NAMES.indexOf(targetName) >= 0;
    if (!isTeamRep) {
      var found = false;
      for (var mi = 0; mi < members.length; mi++) {
        if (members[mi].name === targetName) { found = true; break; }
      }
      if (!found) isTeamRep = true;
    }

    var targetDept = "";
    // 部門名そのものが対象者の場合はそのまま部門名として使用
    if (CONFIG.DEPT_NAMES.indexOf(targetName) >= 0) {
      targetDept = targetName;
    } else {
      for (var ti = 0; ti < members.length; ti++) {
        if (members[ti].name === targetName) { targetDept = members[ti].dept; break; }
      }
      if (!targetDept && isTeamRep) targetDept = extractDeptFromRepName(targetName);
    }

    // 強制チーム波及ルール：プレスの段取り時間・計画達成率は
    // 個人減点なし→全員チーム波及50%（パターンB扱い・isTeamRep扱い）
    if (isForceTeamItem(itemName, targetDept)) {
      isTeamRep = true;
      pattern   = "B";
    }

    var incHinkan = waveText.indexOf("品質") >= 0;
    var wavePt    = Math.floor(pt * 0.5);

    if (pattern === "A") {
      if (!isTeamRep) {
        consider(targetName, date, group, pt, "personal");
      } else {
        members.forEach(function(m) {
          if (m.dept === targetDept) consider(m.name, date, group, pt, "teamWave");
        });
      }

    } else if (pattern === "B") {
      if (!isTeamRep) {
        consider(targetName, date, group, pt, "personal");
        members.forEach(function(m) {
          if (m.name === targetName) return;
          var hit = (targetDept && m.dept === targetDept) ||
                    (incHinkan && m.dept === "品質管理" && targetDept !== "品質管理");
          if (hit) consider(m.name, date, group, wavePt, "teamWave");
        });
      } else {
        members.forEach(function(m) {
          var hit = (targetDept && m.dept === targetDept) ||
                    (incHinkan && m.dept === "品質管理" && targetDept !== "品質管理");
          if (hit) consider(m.name, date, group, wavePt, "teamWave");
        });
      }

    } else if (pattern === "C") {
      members.forEach(function(m) {
        var isHinkanFull = incHinkan && m.dept === "品質管理";
        if (isTeamRep) {
          if (targetDept && m.dept === targetDept) {
            consider(m.name, date, group, pt, "personal");
          } else if (isHinkanFull && targetDept !== "品質管理") {
            consider(m.name, date, group, pt, "teamWave");
          } else {
            consider(m.name, date, group, Math.floor(pt * 0.5), "allWave");
          }
        } else {
          if (m.name === targetName) {
            consider(m.name, date, group, pt, "personal");
          } else if (targetDept && m.dept === targetDept) {
            consider(m.name, date, group, Math.floor(pt * 0.7), "teamWave");
          } else if (isHinkanFull && targetDept !== "品質管理") {
            consider(m.name, date, group, Math.floor(pt * 0.7), "teamWave");
          } else {
            consider(m.name, date, group, Math.floor(pt * 0.5), "allWave");
          }
        }
      });
    }
  });

  // 各人×日×グループで最大ptのみをdeductTableに加算
  Object.keys(maxContrib).forEach(function(key) {
    var personName = key.split("|")[0];
    var c = maxContrib[key];
    if (deductTable[personName] && c.pt > 0) {
      deductTable[personName][c.bucket] += c.pt;
    }
  });
}

// ★チーム代表名から部門名を抽出（App74の部門フィールド削除後の代替）
// 例: "★プレスチーム" → "プレス"
function extractDeptFromRepName(repName) {
  if (!repName) return "";
  var DEPT_KEYWORDS = ["プレス", "技術", "金型", "品質管理", "組立", "納入管理", "総務"];
  for (var i = 0; i < DEPT_KEYWORDS.length; i++) {
    if (repName.indexOf(DEPT_KEYWORDS[i]) >= 0) return DEPT_KEYWORDS[i];
  }
  return "";
}

// ================================================================
// kintone: 社員マスタ取得
// ================================================================
function fetchAllMembers() {
  var props = PropertiesService.getScriptProperties();
  var token = props.getProperty("KINTONE_TOKEN_25") || props.getProperty("KINTONE_TOKEN") || "";
  var url   = "https://" + CONFIG.KINTONE_DOMAIN +
    "/k/v1/records.json?app=" + CONFIG.APP_MEMBER + "&limit=100";
  var res = UrlFetchApp.fetch(url, {
    method: "get", headers: { "X-Cybozu-API-Token": token }, muteHttpExceptions: true,
  });
  if (res.getResponseCode() !== 200) {
    Logger.log("fetchAllMembers エラー: " + res.getContentText());
    return [];
  }
  var records = JSON.parse(res.getContentText()).records || [];
  return records.map(function(rec) {
    function fv(code) { return (rec[code] && rec[code]["value"]) ? rec[code]["value"] : ""; }
    function fi(code, def) { return parseInt(fv(code) || def, 10) || def; }
    var dept = fv("部署"); // 部署
    return {
      empNo:    fv("従業員番号"), // 従業員番号
      name:     fv("氏名"),
      dept:     dept,
      team:     dept,   // チーム＝部署
      teamCode: dept,   // チームコード＝部署
      basePt:   fi("基準pt", 150),
    };
  }).filter(function(m) {
    if (!m.name) return false;
    if (!m.dept) return false;                              // 部署空白は除外
    if (m.dept === "役員") return false;         // 役員は除外
    if (m.dept === "その他") return false;  // その他は除外
    return true;
  });
}

// ================================================================
// 【一回実行用】指定部署の基準ptを一括更新（社員マスタApp25）
//   ※ KINTONE_TOKEN_25 に「レコード編集」権限が必要
//   実行例：update組立基準pt100() を GASエディタから実行
// ================================================================
function updateBasePtByDept(deptName, newBasePt) {
  var props = PropertiesService.getScriptProperties();
  var token = props.getProperty("KINTONE_TOKEN_25") || props.getProperty("KINTONE_TOKEN") || "";

  // 対象部署のレコードを取得
  var url = "https://" + CONFIG.KINTONE_DOMAIN +
    "/k/v1/records.json?app=" + CONFIG.APP_MEMBER + "&limit=100";
  var res = UrlFetchApp.fetch(url, {
    method: "get", headers: { "X-Cybozu-API-Token": token }, muteHttpExceptions: true,
  });
  if (res.getResponseCode() !== 200) {
    Logger.log("取得エラー: " + res.getContentText()); return;
  }
  var records = JSON.parse(res.getContentText()).records || [];

  var updates = [];
  records.forEach(function(rec) {
    var dept = (rec["部署"] && rec["部署"]["value"]) ? rec["部署"]["value"] : "";
    if (dept === deptName) {
      var name = (rec["氏名"] && rec["氏名"]["value"]) ? rec["氏名"]["value"] : "";
      var cur  = (rec["基準pt"] && rec["基準pt"]["value"]) ? rec["基準pt"]["value"] : "(空欄)";
      Logger.log("対象: " + name + " 基準pt " + cur + " → " + newBasePt);
      updates.push({
        id: rec["$id"]["value"],
        record: { "基準pt": { value: String(newBasePt) } }
      });
    }
  });

  if (updates.length === 0) { Logger.log("対象なし: 部署=" + deptName); return; }

  var putRes = UrlFetchApp.fetch("https://" + CONFIG.KINTONE_DOMAIN + "/k/v1/records.json", {
    method: "put", contentType: "application/json",
    headers: { "X-Cybozu-API-Token": token },
    payload: JSON.stringify({ app: CONFIG.APP_MEMBER, records: updates }),
    muteHttpExceptions: true,
  });
  Logger.log("更新結果(" + deptName + " → " + newBasePt + "pt / " + updates.length + "件): "
             + putRes.getResponseCode() + " / " + putRes.getContentText());
}

// 組立部署の基準ptを100に更新（GASエディタから実行）
function update組立基準pt100() {
  updateBasePtByDept("組立", 100);
}

// ================================================================
// kintone: 社員1名の情報取得
// ================================================================
function getMemberInfo(memberName) {
  var members = fetchAllMembers();
  for (var i = 0; i < members.length; i++) {
    if (members[i].name === memberName) return members[i];
  }
  return null;
}

// ================================================================
// kintone: 減点項目マスタ取得
// ================================================================
function fetchDeductMaster() {
  var props = PropertiesService.getScriptProperties();
  var token = props.getProperty("KINTONE_TOKEN_73") || props.getProperty("KINTONE_TOKEN") || "";
  var url   = "https://" + CONFIG.KINTONE_DOMAIN +
    "/k/v1/records.json?app=" + CONFIG.APP_MASTER + "&limit=100";
  var res = UrlFetchApp.fetch(url, {
    method: "get", headers: { "X-Cybozu-API-Token": token }, muteHttpExceptions: true,
  });
  if (res.getResponseCode() !== 200) {
    Logger.log("fetchDeductMaster エラー: " + res.getContentText());
    return {};
  }
  var records = JSON.parse(res.getContentText()).records || [];
  var map = {};
  // デバッグ：App73の最初のレコードのフィールドキーと波及範囲を確認
  if (records.length > 0) {
    var wvRaw = records[0]["波及範囲"];
  }
  records.forEach(function(rec) {
    var itemName = rec["文字列__1行_"] ? rec["文字列__1行_"]["value"] : "";
    if (itemName) {
      function mv(code) { return (rec[code] && rec[code]["value"]) ? rec[code]["value"] : ""; }
      // 波及範囲はCHECK_BOX型（配列）なので結合して文字列化
      var waveRaw = rec["波及範囲"];
      var waveText = "";
      if (waveRaw && waveRaw["value"]) {
        if (Array.isArray(waveRaw["value"])) {
          waveText = waveRaw["value"].join("＋"); // 「プレス＋組立＋品質管理」形式
        } else {
          waveText = waveRaw["value"];
        }
      }
      map[itemName] = {
        pt:       parseInt(mv("減点_0pt") || mv("数値") || "0", 10),
        pattern:  mv("パターン"),
        waveText: waveText,
        group:    mv("一日一回グループ"), // 1日1回制限グループ（空欄なら制限なし）
      };
    }
  });
  return map;
}

// ================================================================
// kintone: App74減点記録取得
// ================================================================
function fetchApp74Records(dateFrom, dateTo) {
  var props = PropertiesService.getScriptProperties();
  var token = props.getProperty("KT_TOKEN_74") || props.getProperty("KINTONE_TOKEN") || "";
  var query = encodeURIComponent(
    "日付_0 >= \"" + dateFrom + "\" and 日付_0 <= \"" + dateTo + "\""
  );
  var url = "https://" + CONFIG.KINTONE_DOMAIN +
    "/k/v1/records.json?app=" + CONFIG.APP_WEEKLY + "&query=" + query + "&limit=500";
  var res = UrlFetchApp.fetch(url, {
    method: "get", headers: { "X-Cybozu-API-Token": token }, muteHttpExceptions: true,
  });
  if (res.getResponseCode() !== 200) {
    Logger.log("fetchApp74Records エラー: " + res.getContentText());
    return [];
  }
  return JSON.parse(res.getContentText()).records || [];
}


// ================================================================
// kintone: App75（5S巡回チェック）減点記録取得
// ================================================================
function fetchApp75Records(dateFrom, dateTo) {
  var props = PropertiesService.getScriptProperties();
  var token = props.getProperty("KINTONE_TOKEN_75") || props.getProperty("KINTONE_TOKEN") || "";
  var today = Utilities.formatDate(new Date(), "Asia/Tokyo", "yyyy-MM-dd");

  // 巡回日が集計期間内のレコードを取得
  var query = encodeURIComponent(
    "日付 >= \"" + dateFrom + "\" and 日付 <= \"" + dateTo + "\""
  );
  var url = "https://" + CONFIG.KINTONE_DOMAIN +
    "/k/v1/records.json?app=" + CONFIG.APP_5S +
    "&query=" + query + "&limit=500";
  var res = UrlFetchApp.fetch(url, {
    method: "get", headers: { "X-Cybozu-API-Token": token }, muteHttpExceptions: true,
  });
  if (res.getResponseCode() !== 200) {
    Logger.log("fetchApp75Records エラー: " + res.getContentText());
    return [];
  }
  var records = JSON.parse(res.getContentText()).records || [];

  // 減点対象レコードに変換
  var result = [];
  records.forEach(function(rec) {
    function fv(code) { return (rec[code] && rec[code]["value"]) ? rec[code]["value"] : ""; }

    var area      = fv("ドロップダウン");    // 部門・エリア
    var visitDate = fv("日付");                                         // 巡回日
    var radioVal  = fv("ラジオボタン");             // 指摘回数
    var is2ndPlus = radioVal === "2回以上";                        // 2回以上

    // テーブル（指摘内容・指摘対応日）
    var tableRows = (rec["テーブル"] && rec["テーブル"]["value"])
                   ? rec["テーブル"]["value"] : [];

    tableRows.forEach(function(row) {
      var rv        = row["value"] || {};
      var item      = (rv["ドロップダウン_0"] && rv["ドロップダウン_0"]["value"])
                      ? rv["ドロップダウン_0"]["value"] : "";
      var respondDate = (rv["日付_0"] && rv["日付_0"]["value"])
                      ? rv["日付_0"]["value"] : "";

      if (!item) return; // 指摘内容なし行はスキップ

      // ① 2回以上の指摘 → 20pt（パターンB）
      if (is2ndPlus) {
        result.push({
          area:      area,
          item:      "5S指摘（2回目以降）: " + item,
          pt:        20,
          pattern:   "B",
          visitDate: visitDate,
          source:    "App75",
        });
      }

      // ② 指摘対応日が空 かつ 巡回日から3日超過 → 30pt（パターンB）
      if (!respondDate && visitDate) {
        var vd      = new Date(visitDate);
        var todayDt = new Date(Utilities.formatDate(new Date(), "Asia/Tokyo", "yyyy-MM-dd"));
        var diffDays = Math.floor((todayDt - vd) / (1000 * 60 * 60 * 24));
        if (diffDays > 3) {
          result.push({
            area:      area,
            item:      "5S指摘後3日以内未対応: " + item,
            pt:        30,
            pattern:   "B",
            visitDate: visitDate,
            source:    "App75",
          });
        }
      }
    });
  });

  return result;
}

// ================================================================
// 今月累計減点取得
// ================================================================
function getMonthlyDeductTotal(memberName) {
  var today    = new Date();
  var year     = today.getFullYear();
  var month    = today.getMonth();
  var dateFrom = Utilities.formatDate(new Date(year, month - 1, 21), "Asia/Tokyo", "yyyy-MM-dd");
  var dateTo   = Utilities.formatDate(new Date(year, month,     20), "Asia/Tokyo", "yyyy-MM-dd");
  var records  = fetchApp74Records(dateFrom, dateTo);
  var total    = 0;
  records.forEach(function(rec) {
    if ((rec["ルックアップ"]["value"] || "") === memberName) {
      total += parseInt(rec["数値"]["value"] || "0", 10);
    }
  });
  return total;
}

// ================================================================
// Google Sheetsへの出力
// ================================================================
function writeToSpreadsheet(dateFrom, dateTo, summary) {
  var props   = PropertiesService.getScriptProperties();
  var sheetId = props.getProperty("MONTHLY_SHEET_ID");
  var ss, sheet1, sheet2;

  if (sheetId) {
    try {
      ss = SpreadsheetApp.openById(sheetId);
    } catch(e) {
      sheetId = null;
    }
  }
  if (!sheetId) {
    ss = SpreadsheetApp.create(buildSheetName(dateFrom));
    props.setProperty("MONTHLY_SHEET_ID", ss.getId());
    Logger.log("スプレッドシート作成: " + ss.getUrl());
  }
  // ファイル名を締め月に自動更新
  try { ss.rename(buildSheetName(dateFrom)); } catch(e) { Logger.log("rename失敗: " + e); }

  // ── シート1：個人別集計（③月次減点記録シートへのコピペ用） ──
  sheet1 = ss.getSheetByName("個人別集計") || ss.insertSheet("個人別集計");
  sheet1.clearContents();

  var h1 = ["従業員番号", "氏名", "部門", "チーム", "基準pt",
            "個人減点", "チーム波及受取",
            "全社波及受取", "合計減点pt",
            "残pt", "手当支給額"];
  sheet1.getRange(1,1,1,h1.length).setValues([h1]).setFontWeight("bold");
  sheet1.getRange(1,1,1,h1.length).setBackground("#4472C4").setFontColor("#FFFFFF");

  var rows1 = summary.map(function(s) {
    return [s.empNo, s.name, s.dept, s.team, s.basePt,
            s.personal, s.teamWave, s.allWave, s.totalDeduct, s.remaining, s.allowance];
  });
  if (rows1.length) sheet1.getRange(2,1,rows1.length,h1.length).setValues(rows1);

  // 合計行
  var lastRow = rows1.length + 2;
  sheet1.getRange(lastRow, 1).setValue("合計");
  sheet1.getRange(lastRow, 10).setValue(
    "=SUM(J2:J" + (rows1.length + 1) + ")"
  );
  sheet1.getRange(lastRow, 1, 1, h1.length).setFontWeight("bold").setBackground("#D9E1F2");

  // ── シート2：減点記録一覧 ──
  sheet2 = ss.getSheetByName("減点記録一覧") || ss.insertSheet("減点記録一覧");
  sheet2.clearContents();
  var h2 = ["集計期間", dateFrom + " ～ " + dateTo];
  sheet2.getRange(1,1,1,2).setValues([h2]).setFontWeight("bold");

  var members = fetchAllMembers();
  var records74 = fetchApp74Records(dateFrom, dateTo);
  var records75 = fetchApp75Records(dateFrom, dateTo);
  // Excel③入力部に完全一致（C〜M列、H列判定区分は除外）
  // C:対象者 D:所属部門 E:減点項目 F:減点pt G:パターン I:発生日 K:チーム波及pt L:全社波及pt M:波及範囲
  var hdr2 = [
    "対象者",           // C：対象者
    "所属部門",    // D：所属部門
    "減点項目",    // E：減点項目
    "減点pt",                // F：減点pt
    "パターン",    // G：パターン
    "発生日",           // I：発生日
    "ソース",           // J：ソース(App74/App75)
    "波及範囲",    // M：波及範囲
  ];
  sheet2.getRange(2,1,1,hdr2.length).setValues([hdr2]).setFontWeight("bold").setBackground("#70AD47").setFontColor("#FFFFFF");

  var masterMap = fetchDeductMaster();
  // App74レコード
  var rows2 = records74.map(function(rec) {
    var itemName = rec["ルックアップ_0"]["value"] || "";
    var wave     = masterMap[itemName] ? masterMap[itemName].waveText : "";
    // 対象者の所属部門をApp25から取得
    var tgtDept = "";
    for (var di = 0; di < members.length; di++) {
      if (members[di].name === (rec["ルックアップ"]["value"] || "")) {
        tgtDept = members[di].dept; break;
      }
    }
    if (!tgtDept) tgtDept = extractDeptFromRepName(rec["ルックアップ"]["value"] || "");
    return [
      rec["ルックアップ"]["value"]  || "",  // C：対象者
      tgtDept,                                                              // D：所属部門
      itemName,                                                             // E：減点項目
      rec["数値"]["value"]                        || "0",        // F：減点pt
      rec["文字列__1行_"]["value"]     || "",          // G：パターン
      rec["日付_0"]["value"]                     || "",          // I：発生日
      "App74",                                                              // J：ソース
      wave,                                                                 // M：波及範囲
    ];
  });
  // App75レコードを追記
  records75.forEach(function(r) {
    rows2.push([
      r.area,      // C：対象者（部門名）
      r.area,      // D：所属部門（部門名と同じ）
      r.item,      // E：減点項目
      r.pt,        // F：減点pt
      r.pattern,   // G：パターン
      r.visitDate, // I：発生日
      "App75",     // J：ソース
      "対象部門+品質管理", // M：波及範囲
    ]);
  });
  if (rows2.length) sheet2.getRange(3,1,rows2.length,hdr2.length).setValues(rows2);

  // 列幅調整
  sheet1.autoResizeColumns(1, h1.length);
  sheet2.autoResizeColumns(1, hdr2.length);

  // ── シート3：個人別明細（フィードバックカード用）──
  var sheet3 = ss.getSheetByName("個人別明細")
               || ss.insertSheet("個人別明細");
  sheet3.clearContents();

  var hdr3 = [
    "従業員番号",  // 従業員番号
    "氏名",                         // 氏名
    "部門",                         // 部門
    "減点理由",           // 減点理由
    "元レコード",    // 元レコード（対象者）
    "減点項目",           // 減点項目
    "発生日",                  // 発生日
    "減点pt",                       // 減点pt
    "パターン",           // パターン
    "ソース",                  // ソース
  ];
  sheet3.getRange(1,1,1,hdr3.length).setValues([hdr3])
        .setFontWeight("bold")
        .setBackground("#1F4E79")
        .setFontColor("#FFFFFF");

  // 個人別明細を生成
  var detailRows = buildPersonalDetails(members, records74, records75, masterMap, dateFrom, dateTo);
  if (detailRows.length > 0) {
    sheet3.getRange(2,1,detailRows.length,hdr3.length).setValues(detailRows);
  }
  sheet3.autoResizeColumns(1, hdr3.length);
  Logger.log("個人別明細: " + detailRows.length + "行出力");

  return ss;
}


// ================================================================
// 個人別明細生成（フィードバックカード用）
// ================================================================
function buildPersonalDetails(members, records74, records75, masterMap, dateFrom, dateTo) {
  var rows = [];

  // グループ項目（1日1回制限）用：各人×日×グループの最大pt行のみ保持
  // key: "empNo|date|group" → { row, pt }
  var groupedRows = {};

  // App74の各レコードを処理
  records74.forEach(function(rec) {
    var targetName = rec["ルックアップ"]["value"]   || "";
    var itemName   = rec["ルックアップ_0"]["value"] || "";
    var pt         = parseInt(rec["数値"]["value"] || "0", 10);
    var pattern    = (rec["文字列__1行_"]["value"] || "").toUpperCase();
    var date       = rec["日付_0"]["value"] || "";
    var master     = masterMap[itemName] || {};
    var waveText   = master.waveText || "";

    // 対象者がメンバーに存在するか（個人 or チーム代表）
    var foundInMembers = false;
    for (var mi = 0; mi < members.length; mi++) {
      if (members[mi].name === targetName) { foundInMembers = true; break; }
    }
    var isTeamRep = !foundInMembers;
    var targetDept = isTeamRep
      ? extractDeptFromRepName(targetName)
      : (function(){ for(var i=0;i<members.length;i++){if(members[i].name===targetName)return members[i].dept;} return ""; })();

    // 強制チーム波及ルール：プレスの段取り時間・計画達成率は
    // 個人減点なし→全員チーム波及50%（パターンB扱い・isTeamRep扱い）
    if (isForceTeamItem(itemName, targetDept)) {
      isTeamRep = true;
      pattern   = "B";
    }

    var cIncludesHinkan = waveText.indexOf("品質") >= 0;

    members.forEach(function(m) {
      var reason = "";
      var myPt   = 0;

      if (pattern === "A") {
        if (!isTeamRep && m.name === targetName) {
          reason = "個人減点";
          myPt   = pt;
        }
      } else if (pattern === "B") {
        if (!isTeamRep && m.name === targetName) {
          reason = "個人減点";
          myPt   = pt;
        } else {
          var wavePt = Math.floor(pt * 0.5);
          var hit = false;
          if (isTeamRep && m.dept === targetDept) { hit = true; myPt = wavePt; }
          else if (!isTeamRep && m.dept === targetDept && m.name !== targetName) { hit = true; myPt = wavePt; }
          else if (cIncludesHinkan && m.dept === "品質管理" && targetDept !== "品質管理") { hit = true; myPt = wavePt; }
          if (hit) reason = "チーム波及(" + targetDept + "感染)";
        }
      } else if (pattern === "C") {
        var isHinkanFull = cIncludesHinkan && m.dept === "品質管理";
        if (isTeamRep) {
          if (m.dept === targetDept) {
            reason = "チーム責任(100%)";
            myPt   = pt;
          } else if (isHinkanFull && targetDept !== "品質管理") {
            reason = "品質管理連帯(100%)";
            myPt   = pt;
          } else {
            reason = "全社波及(50%)";
            myPt   = Math.floor(pt * 0.5);
          }
        } else {
          if (m.name === targetName) {
            reason = "個人減点";
            myPt   = pt;
          } else if (m.dept === targetDept) {
            reason = "同チーム波及(70%)";
            myPt   = Math.floor(pt * 0.7);
          } else if (isHinkanFull && targetDept !== "品質管理") {
            reason = "品質管理連帯(70%)";
            myPt   = Math.floor(pt * 0.7);
          } else {
            reason = "全社波及(50%)";
            myPt   = Math.floor(pt * 0.5);
          }
        }
      }

      if (reason && myPt > 0) {
        var dateStr = date ? date.replace(/-/g, "/") : "";
        var itemGroup = (masterMap[itemName] || {}).group || "";
        if (itemGroup) {
          // グループ項目：同一人物×同一日×同一グループで最大ptの1行だけ残す
          var gKey = m.empNo + "|" + date + "|" + itemGroup;
          if (!groupedRows[gKey] || myPt > groupedRows[gKey].pt) {
            groupedRows[gKey] = {
              row: [m.empNo, m.name, m.dept, reason, targetName, itemName, dateStr, myPt, pattern, "App74"],
              pt: myPt
            };
          }
        } else {
          // 通常項目：そのまま追加
          rows.push([m.empNo, m.name, m.dept, reason, targetName, itemName, dateStr, myPt, pattern, "App74"]);
        }
      }
    });
  });

  // グループ項目の最大pt行を追加（1日1回制限適用済み）
  Object.keys(groupedRows).forEach(function(k) {
    rows.push(groupedRows[k].row);
  });

  // App75の各レコードを処理
  records75.forEach(function(r75) {
    var area    = r75.area;
    var pt      = r75.pt;
    var isAll   = area === "全体";
    var wavePt  = Math.floor(pt * 0.5);

    members.forEach(function(m) {
      var reason = "";
      var myPt   = 0;
      if (isAll) {
        reason = "5S全体指摘波及(50%)";
        myPt   = wavePt;
      } else if (m.dept === area) {
        reason = "5S指摘(" + area + ")";
        myPt   = pt;
      }
      if (reason && myPt > 0) {
        var visitDateStr = r75.visitDate ? r75.visitDate.replace(/-/g, "/") : "";
        rows.push([
          m.empNo, m.name, m.dept,
          reason, area, r75.item, visitDateStr, myPt, r75.pattern, "App75"
        ]);
      }
    });
  });

  // 従業員番号・発生日でソート
  rows.sort(function(a, b) {
    if (a[0] !== b[0]) return a[0] > b[0] ? 1 : -1;
    return a[6] > b[6] ? 1 : -1;
  });

  return rows;
}

// ================================================================
// 期限管理アプリ（App77）：新規登録通知
// ================================================================
function handleQualityNew(params) {
  var type     = params.type     || "";
  var title    = params.title    || "";
  var occDate  = params.occDate  || "";
  var deadline = params.deadline || "";
  var person   = params.person   || "";
  var detail   = params.detail   || "";

  var urgentMark = deadline ? "" : "";
  var text  = ":clipboard: *期限管理　新規登録*\n";
  text += "> 種別：" + type + "\n";
  text += "> 件名：*" + title + "*\n";
  text += "> 発生日：" + occDate + "　　対応期限：*" + (deadline || "未設定") + "*\n";
  text += "> 担当者：" + (person || "未設定");
  if (detail) text += "\n> 内容：" + detail;

  postToSlack(text, true);
  Logger.log("handleQualityNew: " + title);
  return { status: "ok", message: "新規登録通知送信: " + title };
}

// ================================================================
// 期限管理アプリ（App77）：完了報告通知
// ================================================================
function handleQualityComplete(params) {
  var type         = params.type         || "";
  var title        = params.title        || "";
  var reporter     = params.reporter     || "";
  var completeDate = params.completeDate || "";
  var comment      = params.comment      || "";

  var text  = ":white_check_mark: *期限管理　完了報告*\n";
  text += "> 種別：" + type + "\n";
  text += "> 件名：*" + title + "*\n";
  text += "> 完了日：" + (completeDate || "未入力") + "\n";
  text += "> 報告者：" + reporter;
  if (comment) text += "\n> コメント：" + comment;

  postToSlack(text, true);
  Logger.log("handleQualityComplete: " + title);
  return { status: "ok", message: "完了報告通知送信: " + title };
}

// ================================================================
// 期限管理アプリ（App77）：毎朝の期限チェック
// GASのトリガーで毎朝8:00に実行
// ================================================================
function checkDeadlines() {
  var props = PropertiesService.getScriptProperties();
  var token = props.getProperty("KINTONE_TOKEN_77") || props.getProperty("KINTONE_TOKEN") || "";

  var today    = new Date();
  var todayStr    = Utilities.formatDate(today, "Asia/Tokyo", "yyyy-MM-dd");
  var tomorrow    = new Date(today.getTime() + 86400000);
  var tomorrowStr = Utilities.formatDate(tomorrow, "Asia/Tokyo", "yyyy-MM-dd");

  // 未完了レコードを期限順に取得
  var query = encodeURIComponent(
    'ステータス not in ("完了") order by 対応期限 asc limit 100'
  );
  var url = "https://" + CONFIG.KINTONE_DOMAIN +
    "/k/v1/records.json?app=77&query=" + query;
  var res = UrlFetchApp.fetch(url, {
    method: "get", headers: { "X-Cybozu-API-Token": token }, muteHttpExceptions: true,
  });
  if (res.getResponseCode() !== 200) {
    Logger.log("checkDeadlines エラー: " + res.getContentText()); return;
  }
  var records = JSON.parse(res.getContentText()).records || [];

  var overdue  = [];
  var dueToday = [];
  var dueSoon  = [];

  records.forEach(function(rec) {
    function fv(code) { return (rec[code] && rec[code]["value"]) ? rec[code]["value"] : ""; }
    var deadline = fv("対応期限");
    if (!deadline) return;
    var item = {
      type:     fv("種別"),
      title:    fv("件名"),
      deadline: deadline,
      person:   fv("担当者"),
    };
    if      (deadline < todayStr)    overdue.push(item);
    else if (deadline === todayStr)  dueToday.push(item);
    else if (deadline === tomorrowStr) dueSoon.push(item);
  });

  if (overdue.length === 0 && dueToday.length === 0 && dueSoon.length === 0) {
    Logger.log("checkDeadlines: 期限案件なし");
    return;
  }

  var text = ":alarm_clock: *期限管理　本日のアラート（" + todayStr + "）*\n";

  if (overdue.length > 0) {
    text += "\n*🚨 期限超過 " + overdue.length + "件*\n";
    overdue.forEach(function(r) {
      text += "> • " + r.title + "（" + r.type + "）　期限：" + r.deadline + "　担当：" + (r.person || "未設定") + "\n";
    });
  }
  if (dueToday.length > 0) {
    text += "\n*⚠️ 本日期限 " + dueToday.length + "件*\n";
    dueToday.forEach(function(r) {
      text += "> • " + r.title + "（" + r.type + "）　担当：" + (r.person || "未設定") + "\n";
    });
  }
  if (dueSoon.length > 0) {
    text += "\n*📅 明日期限 " + dueSoon.length + "件*\n";
    dueSoon.forEach(function(r) {
      text += "> • " + r.title + "（" + r.type + "）　担当：" + (r.person || "未設定") + "\n";
    });
  }

  postToSlack(text, true);
  Logger.log("checkDeadlines 完了: 超過" + overdue.length + "件 本日" + dueToday.length + "件 明日" + dueSoon.length + "件");
}

// ================================================================
// 朝のまとめ通知（毎朝7:30トリガー）
// ================================================================
function morningDigest() {
  var props       = PropertiesService.getScriptProperties();
  var token       = props.getProperty("KT_TOKEN_74") || props.getProperty("KINTONE_TOKEN") || "";
  var yesterday   = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  var yesterdayStr = Utilities.formatDate(yesterday, "Asia/Tokyo", "yyyy-MM-dd");

  var notifiedKey = "NOTIFIED_IDS_" + yesterdayStr;
  var notifiedIds;
  try { notifiedIds = JSON.parse(props.getProperty(notifiedKey) || "[]"); }
  catch(e) { notifiedIds = []; }

  var query = encodeURIComponent("日付_0 = \"" + yesterdayStr + "\"");
  var url   = "https://" + CONFIG.KINTONE_DOMAIN +
    "/k/v1/records.json?app=" + CONFIG.APP_WEEKLY + "&query=" + query + "&limit=100";
  var res = UrlFetchApp.fetch(url, {
    method: "get", headers: { "X-Cybozu-API-Token": token }, muteHttpExceptions: true,
  });
  if (res.getResponseCode() !== 200) {
    Logger.log("morningDigest エラー: " + res.getContentText()); return;
  }
  var allRecords = JSON.parse(res.getContentText()).records || [];
  var newRecords = allRecords.filter(function(rec) {
    return notifiedIds.indexOf(rec["レコード番号"]["value"]) === -1;
  });
  if (newRecords.length === 0) { Logger.log("morningDigest: 未通知データなし"); return; }

  var text = ":bento: *《朝のまとめ》 昨夜の減点記録*\n";
  text += ">*件数：* " + newRecords.length + "件 / *集計日：* " + yesterdayStr + "\n\n";
  newRecords.forEach(function(rec) {
    var name    = rec["ルックアップ"]["value"]     || "不明";
    var item    = rec["ルックアップ_0"]["value"]   || "";
    var pt      = rec["数値"]["value"]   || "0";
    var pattern = rec["文字列__1行_"]["value"] || "";
    text += ">*" + name + "* ： " + item + "  *−" + pt + "pt*  [パターン: " + pattern + "]\n";
  });
  text += "\n>_詳細は kintone App74 を確認してください_";
  postToSlack(text, false);

  var allIds = allRecords.map(function(r) { return r["レコード番号"]["value"]; });
  props.setProperty(notifiedKey, JSON.stringify(allIds));
  Logger.log("morningDigest 完了: " + newRecords.length + "件通知");
}

// ================================================================
// Slackメッセージ生成
// ================================================================
function buildDeductMessage(memberName, deductItem, deductPt, pattern, occurDate, remaining, isUrgent) {
  var icon  = isUrgent ? ":rotating_light:" : ":clipboard:";
  var label = isUrgent ? "《緊急》残pt残り少！" : "基準遵守手当　減点記録";
  var text  = icon + " *" + label + "*\n";
  text += ">*対象者：* " + memberName + "\n";
  text += ">*減点項目：* " + deductItem + "\n";
  text += ">*減点pt：* *−" + deductPt + "pt*  [パターン: " + pattern + "]\n";
  if (occurDate) text += ">*発生日：* " + occurDate + "\n";
  text += ">*今月残pt：* *" + (remaining < 0 ? 0 : remaining) + "pt*";
  if (isUrgent) text += "  :warning: *要注意*";
  return text;
}

function build5SMessage(record) {
  var area     = record["エリア"]        ? record["エリア"]["value"]        : "";
  var writer   = record["記入者"]       ? record["記入者"]["value"]       : "";
  var date     = record["巡回日"]       ? record["巡回日"]["value"]       : "";
  var deadline = record["対応期限"] ? record["対応期限"]["value"] : "";
  var remarks  = record["備考"]             ? record["備考"]["value"]             : "";
  if (!remarks) return null;
  var text = ":mag: *5S巡回チェック　指摘あり*\n";
  text += ">*エリア：* " + area + "  *記入者：* " + writer + "\n";
  text += ">*巡回日：* " + date;
  if (deadline) text += "  *対応期限：* " + deadline;
  text += "\n>*指摘内容：*\n";
  remarks.split("\n").forEach(function(line) { if (line.trim()) text += ">　• " + line + "\n"; });
  return text;
}

function buildMonthlySlackMessage(dateFrom, dateTo, summary, sheetUrl) {
  var totalAllowance = summary.reduce(function(s, r) { return s + r.allowance; }, 0);
  var zeroMembers    = summary.filter(function(r) { return r.allowance === 0; });
  var text = ":bar_chart: *月次集計完了　基準遵守手当*\n";
  text += ">*集計期間：* " + dateFrom + " ～ " + dateTo + "\n";
  text += ">*対象者数：* " + summary.length + "名  /  *全社実払合計：* " + totalAllowance.toLocaleString() + "円\n";
  if (zeroMembers.length > 0) {
    text += ">:x: *手当なし：* " + zeroMembers.map(function(r) { return r.name; }).join(" / ") + "\n";
  }
  text += ">\n>:link: *スプレッドシートを確認:* " + sheetUrl;
  return text;
}

// ================================================================
// Slack POST
// ================================================================
function postToSlack(text, toProduction) {
  var webhook = toProduction ? CONFIG.SLACK_WEBHOOK_URGENT : CONFIG.SLACK_WEBHOOK_NORMAL;
  var res = UrlFetchApp.fetch(webhook, {
    method: "post", contentType: "application/json",
    payload: JSON.stringify({ text: text, username: "基準遵守手当Bot", icon_emoji: ":factory:" }),
    muteHttpExceptions: true,
  });
  Logger.log("Slack(" + (toProduction ? "本番" : "テスト") + "): " + res.getResponseCode());
}

// ================================================================
// テスト関数
// ================================================================

// ================================================================
// 社員マスタ一覧をログ出力（従業員番号確認用・一回限り）
// ================================================================
function outputMemberList() {
  var members = fetchAllMembers();
  Logger.log("=== 社員一覧 (" + members.length + "名) ===");
  Logger.log("従業員番号\t氏名\t部署\t基準pt");
  members.forEach(function(m) {
    Logger.log(m.empNo + "\t" + m.name + "\t" + m.dept + "\t" + m.basePt);
  });
  Logger.log("=== 以上 ===");
}

function testMonthlyNoSlack() {
  var today  = new Date();
  var year   = today.getFullYear();
  var month  = today.getMonth();
  var df = Utilities.formatDate(new Date(year, month - 1, 21), "Asia/Tokyo", "yyyy-MM-dd");
  var dt = Utilities.formatDate(new Date(year, month,     20), "Asia/Tokyo", "yyyy-MM-dd");
  Logger.log("集計期間: " + df + " ～ " + dt);

  var summary = calcMonthlyFull(df, dt);
  if (!summary || summary.length === 0) { Logger.log("データなし"); return; }

  Logger.log("=== 個人別集計結果（波及計算農）===");
  summary.forEach(function(s) {
    if (s.totalDeduct > 0 || s.teamWave > 0 || s.allWave > 0) {
      Logger.log(s.name + "["+ s.dept +"] " +
        "個人:" + s.personal + "pt / " +
        "チーム波及:" + s.teamWave + "pt / " +
        "全社波及:" + s.allWave + "pt / " +
        "合計減点:" + s.totalDeduct + "pt / " +
        "残:" + s.remaining + "pt / " +
        "手当:" + s.allowance + "円");
    }
  });
  Logger.log("=== 集計完了（Slack通知スキップ）===");
}

function testMorningDigest() { morningDigest(); }
function test5SRun() {
  var text = ":mag: *5S巡回チェック　指摘あり*\n>エリア: プレス / 記入者: 杯山\n>巡回日: 2026-05-25  対応期限: 2026-05-28\n>指摘: 通路段ボール放置";
  postToSlack(text, false);
}
