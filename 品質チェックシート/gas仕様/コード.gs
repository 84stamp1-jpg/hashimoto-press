var FOLDER_NAME = '品質チェックシート記録';
var SHEET_NAME  = '記録一覧';
var SS_ID = '1t2yAEFJQ48AReMqr-CikN1HjVKMo5ko3xgZduUOzt7o';

function doGet() {
  return HtmlService.createHtmlOutputFromFile('index')
    .setTitle('品質チェックシート記録')
    .addMetaTag('viewport','width=device-width,initial-scale=1,maximum-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function doPost(e) {
  var result = {};
  try {
    var payload = JSON.parse(e.postData.contents);
    var action  = payload.action || '';
    if      (action === 'submitRecord')       { result = submitRecord(payload.data); }
    else if (action === 'updateRecord')       { result = updateRecord(payload.rowNum, payload.data); }
    else if (action === 'deleteRecord')       { result = deleteRecord(payload.rowNum); }
    else if (action === 'markAsInputted')     { result = markAsInputted(payload.rowNum); }
    else if (action === 'getSakuyoData')      { result = { ok: true, data: getSakuyoData() }; }
    else if (action === 'getRecords')         { result = { ok: true, records: getRecords() }; }
    else if (action === 'updateSakuyo')       { result = (typeof updateSakuyoFromXlsx === 'function') ? updateSakuyoFromXlsx() : { ok: false, err: 'updateSakuyoFromXlsx not defined' }; }
    else if (action === 'getKintonePartData') { result = getKintonePartData(payload); }
    else { result = { ok: true, message: '品質チェックシート記録 GAS v9' }; }
  } catch(err) {
    result = { ok: false, err: err.message };
  }
  return ContentService
    .createTextOutput(JSON.stringify(result))
    .setMimeType(ContentService.MimeType.JSON);
}

function getPartsData() {
  return [["11250-85U-0.6-BL", "CYLINDER BLOCK BL材 (0.6)"], ["11250-85U0-0010-4010", "COVER ,CYLINDER BLOCK EXH (DRT)"], ["11250-85U-1.2-BL", "CYLINDER BLOCK BL材 (1.2)"], ["11250-85U-A-BL", "STAY A BL材"], ["11250-85U-B-BL", "STAY B BL材"], ["14120-80U50-000", "COVER,EXH MANF        <  >  SM"], ["14120-80U50-1", "COVER   (DR,TRM,CUT)"], ["14120-80U50-2", "COVER   (BE,FO,C-PC1,C-PC2)"], ["14120-80U50-BL", "COVER   BL材（1.0）"], ["14213-25L00", "CHAMBER PREMUF INR UPR"], ["14213-25L00-BL", "CHAMBER PREMUF INR UPR"], ["14213-25L00-DW", "CHAMBER PREMUF INR UPR"], ["14214-25L00", "CHAMBER PREMUF INR LWR"], ["14214-25L00-BL", "CHAMBER PREMUF INR LWR"], ["14214-25L00-DW", "CHAMBER PREMUF INR LWR"], ["18120-5Y3-0.4-BL", "ｼｬｰﾘﾝｸﾞ (0.4)"], ["18120-5Y3-0.6-BL", "ｼｬｰﾘﾝｸﾞ (0.6)"], ["18120-5Y3-J000", "COVER COMP,CHAMBER  <> HM"], ["18120-5Y3-PR_TOX", "COVER ｼｶｶﾘ　(DR～TOX)"], ["18120-5YT -0001", "COVER COMP,T/C        <  >  HM"], ["18120-5YT-0.4-BL", "ｼｬｰﾘﾝｸﾞ (0.4)"], ["18120-5YT-0.8-BL", "ｼｬｰﾘﾝｸﾞ (0.8)"], ["18120-6MA-0.4-BL", "COVER COMP,CHAMBER"], ["18120-6MA-0.6-BL", "COVER COMP,CHAMBER"], ["18120-6MA-J000", "COVER COMP,CHAMBER"], ["18120-6MA-PR_TOX", "COVER ｼｶｶﾘ (DR～TOX)"], ["18120-6Y0 -0000-PR", "COVER,CONVERTER"], ["18120-6Y0-0.4-BL", "ｼｬｰﾘﾝｸﾞ (0.4)"], ["18120-6Y0-0.6-BL", "ｼｬｰﾘﾝｸﾞ (0.6)"], ["18120-6Y0-3100-22-PR", "PATCH A"], ["18120-6Y0-3100-23-PR", "PATCH B"], ["18121-5MS-0.4-BL", "ｼｬｰﾘﾝｸﾞ (0.4)"], ["18121-5MS-0.8-BL", "ｼｬｰﾘﾝｸﾞ (0.8)"], ["18121-5MS-0000", "COVER COMP CONVERTER  <  > CYT"], ["18121-5MS-0000-PR", "COVER CONVERTER COMP"], ["18160-6MA-C300-PR", "STAY A  <UGR>"], ["18160-6MA-C400-PR", "STAY B  <UGR>"], ["18160-6MA-C600-PR", "STAY D  <UGR>"], ["18160-6MA-C700-PR", "STAY E  <UGR>"], ["18160-6SG -J000-2100", "STAY A,CONVERTER COVER"], ["18160-6SG -J000-2300", "STAY D,CONVERTER COVER"], ["18161-59B-A/B-BL", "CONE A,B ﾌﾞﾗﾝｸ"], ["18161-59B-A-PR", "CONE A FR (脱脂前)"], ["18161-59B-B-PR", "CONE B FR (脱脂前)"], ["18161-5R0-J600-BL", "CASE A/B  ﾌﾞﾗﾝｸ"], ["18161-5R0-J600-H1-0110", "CASE A (ﾁｮｸｿｳ)"], ["18161-5R0-J600-H1-0210", "CASE B (ﾁｮｸｿｳ)"], ["18180-1794", "CHAMBER OTR UPPER"], ["18180-1794-BL", "CHAMBER OTR UPPER <ﾌﾞﾗﾝｸｻﾞｲ>"], ["18180-1795", "CHAMBER OTR LOWER"], ["18180-1795-BL", "CHAMBER OTR LOWER <ﾌﾞﾗﾝｸｻﾞｲ>"], ["18181-5R0 -J600", "COVER COMP LWR        <  >  HM"], ["18181-5R0-0.4-BL", "ｼｬｰﾘﾝｸﾞ (0.4)"], ["18181-5R0-0.6-BL", "ｼｬｰﾘﾝｸﾞ (0.6)"], ["18219-5R0 -0030-4000", "COVER,EXH"], ["18220-3N0 -9010-450C", "COVER C,EXH"], ["18220-T6A -J010-M1-420D", "COVER A EXH              <UGR>"], ["18220-T7A -9010-M1-4400", "COVER B,EXH"], ["18220-T7A -9010-M1-4500", "COVER C,EXH"], ["18220-T7D -9010-M1-4520", "COVER C.EXH"], ["18224-T6C-J010-Y1-4100", "END CHAMBER              <UGR>"], ["18224-T6C-J010Y141-BL", "END CHAMBER ﾌﾞﾗﾝｸ"], ["18224-TAA-0130-H1-4000", "SHELL                    <UGR>"], ["18307-TTC -0030-4000", "COVER A,EXH"], ["18307-TTC -0030-4110", "COVER B,EXH"], ["18307-TTC -0030-4310", "COVER D,EXH"], ["18307-TTC -0030-4410", "COVER E,EXH"], ["18307-TTC -0030-4700", "BRKT,EXH"], ["18307-TTC-A-BL", "COVER A ﾌﾞﾗﾝｸ"], ["18307-TTC-B/D-BL", "COVER B,D ﾌﾞﾗﾝｸ"], ["18307-TTC-E-BL", "COVER E ﾌﾞﾗﾝｸ"], ["18308-TAA -0030-  -4000", "SHELL                    <UGR>"], ["18308-TAB -0030-  -4000", "SHELL                    <UGR>"], ["18326-HL4-B700", "PROTECTOR A,HEAT     (小）"], ["18326-HL4-B700-BL", "PROTECTOR A,HEAT     (小）"], ["18327-HL4-B700", "PROTECTOR B,HEAT     (大）"], ["18327-HL4-B700-BL", "PROTECTOR B,HEAT     (大）"], ["18902-6A0 -P000", "COVER COMP,T/C        <  >  HM"], ["18902-6A0-0.4-BL", "ｼｬｰﾘﾝｸﾞ (0.4)"], ["18902-6A0-0.8-BL", "ｼｬｰﾘﾝｸﾞ (0.8)"], ["18902-6A0-A000-22-PR", "PLATE A"], ["18902-6A0-A000-23-PR", "PLATE B"], ["18902-6A0-A000-PR", "COVER,T/C"], ["46487/8-77R/78R00/50-BL", "BL材(W501,W609,W612)"], ["46487-77R00-PR  (W501)", "BRKT,LEADING ARM,R 　ﾌﾟﾚｽ単品"], ["46487-78R00-PR   (W609)", "BRKT,LEADING ARM,R 　ﾌﾟﾚｽ単品"], ["46487-78R50-BL  (W611)", "BRKT,LEADING ARM,R 　BL 材"], ["46487-78R50-PR  (W611)", "BRKT,LEADING ARM,R 　ﾌﾟﾚｽ単品"], ["46488-78R00-BL  (W610)", "BRKT,LEADING ARM,L 　BL 材"], ["46488-78R00-PR  (W610)", "BRKT,LEADING ARM,L 　ﾌﾟﾚｽ単品"], ["46488-78R50-PR  (W612)", "BRKT,LEADING ARM,L 　ﾌﾟﾚｽ単品"], ["57334-70U00-000", "REINF,FRONT HOOD FR"], ["57334-70U00-BL", "REINF,SIDE SILL BODY OTR EXT R/L FR BL"], ["59116-63J00-PR", "BRACKET 1 (PRﾀﾝﾋﾟﾝ)"], ["62133-51K00-PR1A", "BRACKET　INSTRUMENTPANEL"], ["63431-69T00P", "REINF,REAR PILLAR INNER,R"], ["63831-69T00P", "REINF,REAR PILLAR INNER,L"], ["64210-MLC-D900-20", "PLATE A"], ["64210-MLC-D900-20-A-BL", "PLATE A"], ["64210-MLC-D900-21", "PLATE B"], ["64210-MLC-D900-21/22", "PLATE B,C （DR、TRM）"], ["64210-MLC-D900-22", "PLATE C"], ["64291-80U60P", "BRKT,OVER HEAD BOX"], ["64291-80U60P-1", "BRKT,OVER HEAD BOX (DR～TM)"], ["64291-80U60P-BL", "BRKT,OVER HEAD BOX   BL材"], ["BK02A640G01", "MOTOR SUPPORT"], ["BK02A640G03", "MOTOR SUPPORT"], ["GLB8-20020-000", "ﾅｯﾄﾃﾞｨﾌｧﾚﾝｼｬﾙ"], ["GLB8-20020-BL", "ﾅｯﾄﾃﾞｨﾌｧﾚﾝｼｬﾙAD BL材"], ["GLB8-20030-000", "ﾅｯﾄﾃﾞｨﾌｧﾚﾝｼｬﾙAD"], ["GLB8-20030-BL", "ﾅｯﾄﾃﾞｨﾌｧﾚﾝｼｬﾙAD BL材 （材料202）"], ["GLB8-20040-000", "ﾅｯﾄﾃﾞｨﾌｧﾚﾝｼｬﾙAD"], ["GLB8-20040-PC", "ﾅｯﾄﾃﾞｨﾌｧﾚﾝｼｬﾙAD (ピアス)"], ["GLB8-20050-000", "ﾅｯﾄﾃﾞｨﾌｧﾚﾝｼｬﾙAD"], ["GLB8-20050-BL", "ﾅｯﾄﾃﾞｨﾌｧﾚﾝｼｬﾙAD BL材 （材料204）"], ["18120-6Y0 -0000", "COVER,CONVERTER       <  >  HM"], ["18160-6MA-J030-C300", "STAY COMP A,COVER        <UGR>"], ["18160-6MA-J030-C600", "STAY COMP D,COVER        <UGR>"], ["18160-6MA-J030-C700", "STAY COMP E,COVER        <UGR>"], ["18160-6MA-J040-C40D", "STAY COMP B,COVER        <UGR>"], ["18161-59B-3001--2100", "CONE A FR                <UGR>"], ["18161-59B-3001--2200", "CONE B,FR                <UGR>"], ["46487-77R00-000   (W501)", "BRKT,LEADING ARM,R 　(刻印　77RR0)"], ["46487-78R00-000   (W609)", "BRKT,LEADING ARM,R   (刻印　78RR0)"], ["46487-78R50-000   (W611)", "BRKT,LEADING ARM,R   (刻印　78RR5)"], ["46488-78R00-000   (Ｗ610）", "BRKT,LEADING ARM,L   (刻印　78RL0)"], ["46488-78R50-000   (W612)", "BRKT,LEADING ARM,L   (刻印　78RL5)"], ["62133-63J00-WE1A", "BRACKET PARKING CABLE"], ["14164-19K20", "PIPE EXH NO.2 3RD INR"], ["14165-19K20", "PIPE EXH NO.2 3RD OTR"], ["14213-48K02", "PLATE CHMBR OTR FR"], ["14213-48K02-BL", "PLATE CHMBR OTR FR"], ["18181/2-61B-0.4-BL", "ｼｬｰﾘﾝｸﾞ (0.4)"], ["18181/2-61B-0.6-BL", "ｼｬｰﾘﾝｸﾞ (0.6)"], ["18181-61B-0300-PR", "PLATE A <ﾅｯﾄなし>"], ["18181-61B-03NUT-PR", "PLATE A <ﾅｯﾄｸﾘﾝﾁ>"], ["18181-61B-0400-PR", "PLATE B <ﾅｯﾄなし>"], ["18181-61B-04NUT-PR", "PLATE B <ﾅｯﾄｸﾘﾝﾁ>"], ["18181-61B-0500-PR", "PLATE C <ﾅｯﾄなし>"], ["18181-61B-05NUT-PR", "PLATE C <ﾅｯﾄｸﾘﾝﾁ>"], ["18181-61B-0600-PR", "PLATE D <ﾅｯﾄなし>"], ["18181-61B-06NUT-PR", "PLATE D <ﾅｯﾄｸﾘﾝﾁ>"], ["18181-61B-A000-C100", "COVER COMP,LWR  < > CYT"], ["18181-61B-PLATE-BL", "PLATE A/B/C/D <ﾌﾞﾗﾝｸｻﾞｲ>"], ["18181-6S9 -A000-C100", "COVER COMP,LWR        <  > CYT"], ["18181-6S9-0.4-BL", "ｼｬｰﾘﾝｸﾞ (0.4)"], ["18181-6S9-0.6-BL", "ｼｬｰﾘﾝｸﾞ (0.6)"], ["18181-6S9-A000-0300-PR", "PLATE A"], ["18181-6S9-A000-0400-PR", "PLATE B"], ["18181-6S9-A000-0500-PR", "PLATE C"], ["18181-6S9-A000-0600-PR", "PLATE D"], ["18182-61B-A000-C100", "COVER COMP,UPR  < > CYT"], ["18182-6S9 -A000-C100", "COVER COMP,UPR        <  > CYT"], ["18182-6S9-0.4-BL", "ｼｬｰﾘﾝｸﾞ (0.4)"], ["18182-6S9-0.6-BL", "ｼｬｰﾘﾝｸﾞ (0.6)"], ["18191-6S9-20-BL", "FR CONE A ﾌﾞﾗﾝｸ"], ["18191-6S9-21-BL", "FR CONE B ﾌﾞﾗﾝｸ"], ["18191-6S9-A000-2020", "FR CONE A CONVERTER      <UGR>"], ["18191-6S9-A000-21-0000", "FR CONE B CONVERTER      <UGR>"], ["18192-61B -20/21-BL", "CONE A/B ﾌﾞﾗﾝｸ"], ["18192-61B -A000-  -2000", "CONE A                   <UGR>"], ["18192-61B -A000-  -2100", "CONE B                   <UGR>"], ["18192-6S9 -A000-H1-0200", "CONE B                   <UGR>"], ["18192-6S9 -A020-H1-0110", "CONE A                   <UGR>"], ["18192-6S9-A/B-BL", "CONE A/B ﾌﾞﾗﾝｸ"], ["18307-3T1 -0030-4000", "GUARD,EXH                <UGR>"], ["18307-T84 -0030-4200", "COVER C,EXH"], ["18307-T84 -0030-4300", "COVER D,EXH"], ["18307-TAB-0030--4100", "BRKT B                   <DRT>"], ["18308-TAB -0030-  -4500", "SEPARATOR B              <UGR>"], ["18901-6S9 -A001-2D00", "COVER COMP,E-WG ACT   <  > CYT"], ["18901-6S9-0.4-BL", "ｼｬｰﾘﾝｸﾞ (0.4)"], ["18901-6S9-0.6-BL", "ｼｬｰﾘﾝｸﾞ (0.6)"], ["18210-S3A -0030-70", "MT BKT A COMP              (S)"], ["34G-0055-11-1", "PLATE"], ["34G-1022-11-1", "ﾌﾟﾚｰﾄ"], ["34G-1022-11-3", "PLATE"], ["34G-1022-11-4", "PLATE"], ["34G-1022-11-4-BL", "PLATE"], ["5B6-22175-00-1000", "END 2　　（検査有）"], ["5PX-27883-00-00F", "ｷﾞｱﾘﾝｸﾞ　　（協栄）"], ["5PX-27883-20-000F", "ｷﾞｱﾘﾝｸﾞ　(t=2.3)　　（協栄）"], ["5TA-16168-00-0009", "ﾌﾟﾚｰﾄｻｲﾄﾞ 2　　（協栄）"], ["64124/524-70T00-BL", "REINF,SIDE SILL BODY OTR EXT R/L FR BL"], ["64124-70T00-000", "REINF,SIDE, SILL BODY OTR EXT,R FR"], ["64524-70T00-000", "REINF,SIDE, SILL BODY OTR EXT,L FR"], ["S170B-E0140", "INSULATOR SUB ASSY"], ["S170B-E0140-SP", "INSULATOR ｽﾎﾟｯﾄ　（PC前）"], ["14214-48K00", "REINF PIPE JT OTR"], ["14214-48K00-BL", "REINF PIPE JT OTR <ﾌﾞﾗﾝｸｻﾞｲ>"], ["14235-48K00", "REINF PIPE JT INR"], ["14261/2-48K00-BL", "PL CHMR IN FR UP/LWR ﾌﾞﾗﾝｸｻﾞｲ"], ["14261-48K00", "PL CHMBR INR FR UPPER"], ["14262-48K00", "PL CHMBR INR FR LOWER"], ["BK02A640G01", "MOTOR SUPPORT"], ["BK02A640G03", "MOTOR SUPPORT"], ["HK-0001-1-PR", "ｾｰﾌﾃｨﾌﾞﾛｯｸ ﾋｮｳｼﾞｭﾝ ﾎﾝﾀｲ"], ["HK-0001-2-PR", "ｾｰﾌﾃｨﾌﾞﾛｯｸ ﾋｮｳｼﾞｭﾝｱｼ"], ["HK-000-1-BL", "ｾｰﾌﾃｨﾌﾞﾛｯｸ <ﾎﾝﾀｲ> ﾌﾞﾗﾝｸｻﾞｲ"], ["HK-0001-CP", "ｾｰﾌﾃｨﾌﾞﾛｯｸ標準ﾀｲﾌﾟ"], ["HK-0002-1-PR", "ｾｰﾌﾃｨﾌﾞﾛｯｸ ﾎｿｶﾞﾀ ﾎﾝﾀｲ"], ["HK-0002-2-PR", "ｾｰﾌﾃｨﾌﾞﾛｯｸ ﾎｿｶﾞﾀｱｼ"], ["HK-000-2-BL", "ｾｰﾌﾃｨﾌﾞﾛｯｸ <ｱｼ> ﾌﾞﾗﾝｸｻﾞｲ"], ["HK-0002-CP", "ｾｰﾌﾃｨﾌﾞﾛｯｸ細型ﾀｲﾌﾟ"], ["18307-TTC -0030-4210", "COVER C,EXH"], ["11250-85U0-0010-4100", "STAY A          (DRT)"], ["11250-85U0-0010-4200", "STAY B          (DRT)"]];
}

var SAKUYO_SS_ID  = '18YV2Lenuz8_H-agR9jBLp3YZwtyxHtYGR1eiRjj05jA';
var SAKUYO_SS_GID = 1564607065;

// 作業予定一覧をスプレッドシートから読み込んで返す
// 列マッピング（スプレッドシート実測値）:
//   0:製造番号 1:工順 2:工程 3:品番 4:品名 5:工程納期 6:加工指示数
//   12:手配先名（フィルター不要） 25:作業票納期（納期表示に使用）
function getSakuyoData() {
  try {
    var ss = SpreadsheetApp.openById(SAKUYO_SS_ID);
    // 指定gidのシートを優先、なければ先頭シート
    var sheets = ss.getSheets();
    var sheet = sheets[0];
    for (var s = 0; s < sheets.length; s++) {
      if (sheets[s].getSheetId() === SAKUYO_SS_GID) { sheet = sheets[s]; break; }
    }
    var data = sheet.getDataRange().getValues();
    if (data.length <= 1) return getDefaultSakuyo();
    var result = [];
    for (var i = 1; i < data.length; i++) {
      var r = data[i];
      var seizoNo = String(r[0] || '').trim();
      if (!seizoNo) continue;
      // 納期は「作業票納期」(r[25]) を使用（工程納期r[5]は土曜にズレるため使わない）
      var nouki = '';
      if (r[25] instanceof Date) {
        nouki = Utilities.formatDate(r[25], 'Asia/Tokyo', 'MM/dd');
      } else if (r[25]) {
        try {
          nouki = Utilities.formatDate(new Date(r[25]), 'Asia/Tokyo', 'MM/dd');
        } catch(e) { nouki = ''; }
      }
      var junjo = parseInt(r[1]) || 1;
      var shiji = parseInt(String(r[6] || '').replace(/[^\d]/g, '')) || 0;
      result.push({
        seizoNo: seizoNo,
        junjo:   junjo,
        kosei:   String(r[2] || '').trim(),
        hinban:  String(r[3] || '').trim(),
        hinmei:  String(r[4] || '').trim(),
        shiji:   shiji,
        '納期':  nouki
      });
    }
    return result.length > 0 ? result : getDefaultSakuyo();
  } catch(e) {
    return getDefaultSakuyo();
  }
}

// Driveに作業予定xlsxがない場合のフォールバック（ビルトインデータ）
function getDefaultSakuyo() {
  return [{"seizoNo": "Y260203818", "junjo": 1, "kosei": "プレス　D", "hinban": "57334-70U00-000", "hinmei": "REINF,FRONT HOOD FR", "shiji": 2000, "納期": "03/24"}, {"seizoNo": "Y260204233", "junjo": 2, "kosei": "バフ", "hinban": "5PX-27883-20-000F", "hinmei": "ｷﾞｱﾘﾝｸﾞ　(t=2.3)　　（協栄）", "shiji": 300, "納期": "02/26"}, {"seizoNo": "Y260300019", "junjo": 2, "kosei": "プレス　C", "hinban": "18120-6MA-J000", "hinmei": "COVER COMP,CHAMBER", "shiji": 8000, "納期": "03/17"}, {"seizoNo": "Y260300241", "junjo": 1, "kosei": "プレス　A", "hinban": "18220-T7A -9010-M1-4400", "hinmei": "COVER B,EXH", "shiji": 5000, "納期": "03/11"}, {"seizoNo": "Y260300244", "junjo": 1, "kosei": "溶接(MAG)", "hinban": "18307-TZB-S010-M1-C300", "hinmei": "TAIL PIPE COMP", "shiji": 140, "納期": "03/20"}, {"seizoNo": "Y260300286", "junjo": 3, "kosei": "脱脂", "hinban": "18191-6S9-A000-21-0000", "hinmei": "FR CONE B CONVERTER      <UGR>", "shiji": 1000, "納期": "03/20"}, {"seizoNo": "Y260300462", "junjo": 1, "kosei": "プレス　D", "hinban": "GLB8-20050-000", "hinmei": "ﾅｯﾄﾃﾞｨﾌｧﾚﾝｼｬﾙAD", "shiji": 3000, "納期": "03/20"}, {"seizoNo": "Y260300474", "junjo": 1, "kosei": "溶接(スポット)", "hinban": "62133-63J00-WE1A", "hinmei": "BRACKET PARKING CABLE", "shiji": 4050, "納期": "03/17"}, {"seizoNo": "Y260300475", "junjo": 1, "kosei": "溶接(スポット)", "hinban": "62133-63J00-WE1A", "hinmei": "BRACKET PARKING CABLE", "shiji": 4050, "納期": "03/19"}, {"seizoNo": "Y260300491", "junjo": 1, "kosei": "溶接(スポット)", "hinban": "46488-78R50-000   (W612)", "hinmei": "BRKT,LEADING ARM,L   (刻印　78RL5)", "shiji": 400, "納期": "03/20"}, {"seizoNo": "Y260300495", "junjo": 1, "kosei": "溶接(スポット)", "hinban": "46487-78R00-000   (W609)", "hinmei": "BRKT,LEADING ARM,R   (刻印　78RR0)", "shiji": 300, "納期": "03/17"}, {"seizoNo": "Y260300503", "junjo": 1, "kosei": "溶接(スポット)", "hinban": "46487-78R50-000   (W611)", "hinmei": "BRKT,LEADING ARM,R   (刻印　78RR5)", "shiji": 400, "納期": "03/20"}, {"seizoNo": "Y260300647", "junjo": 1, "kosei": "プレス　B", "hinban": "64291-80U60P", "hinmei": "BRKT,OVER HEAD BOX", "shiji": 300, "納期": "03/16"}, {"seizoNo": "Y260300648", "junjo": 1, "kosei": "プレス　B", "hinban": "64291-80U60P-1", "hinmei": "BRKT,OVER HEAD BOX (DR～TM)", "shiji": 300, "納期": "03/13"}, {"seizoNo": "Y260300750", "junjo": 1, "kosei": "フート・油圧", "hinban": "18120-6Y0 -0000", "hinmei": "COVER,CONVERTER       <  >  HM", "shiji": 1440, "納期": "03/23"}, {"seizoNo": "Y260300750", "junjo": 2, "kosei": "検査", "hinban": "18120-6Y0 -0000", "hinmei": "COVER,CONVERTER       <  >  HM", "shiji": 1440, "納期": "03/23"}, {"seizoNo": "Y260300751", "junjo": 1, "kosei": "フート・油圧", "hinban": "18120-6Y0 -0000", "hinmei": "COVER,CONVERTER       <  >  HM", "shiji": 1440, "納期": "03/25"}, {"seizoNo": "Y260300751", "junjo": 2, "kosei": "検査", "hinban": "18120-6Y0 -0000", "hinmei": "COVER,CONVERTER       <  >  HM", "shiji": 1440, "納期": "03/25"}, {"seizoNo": "Y260302708", "junjo": 1, "kosei": "プレス　B", "hinban": "18120-6Y0 -0000-PR", "hinmei": "COVER,CONVERTER", "shiji": 10000, "納期": "03/27"}, {"seizoNo": "Y260302715", "junjo": 1, "kosei": "プレス　A", "hinban": "18120-6Y0-3100-22-PR", "hinmei": "PATCH A", "shiji": 20000, "納期": "03/27"}, {"seizoNo": "Y260302718", "junjo": 1, "kosei": "プレス　A", "hinban": "18120-6Y0-3100-23-PR", "hinmei": "PATCH B", "shiji": 20000, "納期": "03/27"}, {"seizoNo": "Y260302732", "junjo": 1, "kosei": "プレス　B", "hinban": "18161-59B-A-PR", "hinmei": "CONE A FR (脱脂前)", "shiji": 4000, "納期": "03/26"}, {"seizoNo": "Y260302733", "junjo": 1, "kosei": "プレス　B", "hinban": "18161-59B-A/B-BL", "hinmei": "CONE A,B ﾌﾞﾗﾝｸ", "shiji": 2812, "納期": "03/25"}, {"seizoNo": "Y260302734", "junjo": 1, "kosei": "プレス　B", "hinban": "18161-59B-B-PR", "hinmei": "CONE B FR (脱脂前)", "shiji": 4000, "納期": "03/26"}, {"seizoNo": "Y260302781", "junjo": 1, "kosei": "プレス　A", "hinban": "59116-63J00-PR", "hinmei": "BRACKET 1 (PRﾀﾝﾋﾟﾝ)", "shiji": 40000, "納期": "04/01"}, {"seizoNo": "Y260302801", "junjo": 1, "kosei": "プレス　D", "hinban": "GLB8-20020-000", "hinmei": "ﾅｯﾄﾃﾞｨﾌｧﾚﾝｼｬﾙ", "shiji": 300, "納期": "04/06"}, {"seizoNo": "", "junjo": 123, "kosei": "", "hinban": "", "hinmei": "", "shiji": 0, "納期": ""}];
}

function getRecords() {
  var ss = getOrCreateSheet();
  var sheet = ss.getSheetByName(SHEET_NAME);
  var data = sheet.getDataRange().getValues();
  if (data.length <= 1) return [];
  return data.slice(1).map(function(row, i){
    var arr = row.map(function(cell){
      return cell instanceof Date
        ? Utilities.formatDate(cell, 'Asia/Tokyo', 'yyyy/MM/dd HH:mm')
        : String(cell === null || cell === undefined ? '' : cell);
    });
    arr.push(String(i + 2));
    return arr;
  });
}

function markAsInputted(rowNum) {
  try {
    var sheet = getOrCreateSheet().getSheetByName(SHEET_NAME);
    sheet.getRange(parseInt(rowNum), 13).setValue('済');
    SpreadsheetApp.flush();
    return { ok: true };
  } catch(e) { return { ok: false, err: e.message }; }
}

function deleteRecord(rowNum) {
  try {
    var sheet = getOrCreateSheet().getSheetByName(SHEET_NAME);
    sheet.deleteRow(parseInt(rowNum));
    SpreadsheetApp.flush();
    return { ok: true };
  } catch(e) { return { ok: false, err: e.message }; }
}

function updateRecord(rowNum, data) {
  try {
    var sheet = getOrCreateSheet().getSheetByName(SHEET_NAME);
    var n = parseInt(rowNum);
    sheet.getRange(n, 2).setValue(data.date);
    sheet.getRange(n, 5).setValue(data.operator);
    sheet.getRange(n, 6).setValue(data.prod);
    sheet.getRange(n, 7).setValue(data.ng);
    sheet.getRange(n, 8).setValue(data.kanno);
    sheet.getRange(n, 9).setValue(data.zairyo);
    sheet.getRange(n, 10).setValue(data.memo);
    sheet.getRange(n, 18).setValue(data.hokyu || '0');
    sheet.getRange(n, 19).setValue(data.sonota || '0');
    sheet.getRange(n, 20).setValue(data.sonotaMemo || '');
    SpreadsheetApp.flush();
    return { ok: true };
  } catch(e) { return { ok: false, err: e.message }; }
}

function submitRecord(data) {
  try {
    var sheet = getOrCreateSheet().getSheetByName(SHEET_NAME);
    var now = new Date();
    var dateStr = Utilities.formatDate(now, 'Asia/Tokyo', 'yyyyMMdd_HHmm');
    var safeNo = data.partNo.replace(/[/\\:*?"<>|]/g, '_');
    var root = getOrCreateFolder();
    var partFolder = getOrCreateSubFolder(root, safeNo);
    var yearStr = Utilities.formatDate(now, 'Asia/Tokyo', 'yyyy年');
    var yearFolder = getOrCreateSubFolder(partFolder, yearStr);
    var fileIds = [];
    var fileNames = [];
    var images = data.images || [];
    for (var i = 0; i < images.length; i++) {
      var imgData = images[i];
      if (!imgData || imgData.length < 100) continue;
      var suffix = images.length > 1 ? ('_' + (i+1)) : '';
      var fileName = dateStr + '_' + safeNo + suffix + '.jpg';
      var base64 = imgData.split(',').pop();
      var blob = Utilities.newBlob(Utilities.base64Decode(base64), 'image/jpeg', fileName);
      fileIds.push(yearFolder.createFile(blob).getId());
      fileNames.push(fileName);
    }
    var urls = fileIds.map(function(id){ return 'https://drive.google.com/file/d/' + id; });
    sheet.appendRow([
      Utilities.formatDate(now, 'Asia/Tokyo', 'yyyy/MM/dd HH:mm'),
      data.date, data.partNo, data.partName, data.operator,
      data.prod, data.ng, data.kanno, data.zairyo, data.memo,
      urls.join('|'), fileNames.join('|'), '未',
      data.seizoNo || '', data.junjo || '', data.kosei || '', data.shiji || '',
      data.hokyu || '0', data.sonota || '0', data.sonotaMemo || ''
    ]);
    SpreadsheetApp.flush();
    return { ok: true, fileNames: fileNames.join(', ') };
  } catch(e) { return { ok: false, err: e.message }; }
}

function getOrCreateSheet() {
  var ss = SpreadsheetApp.openById(SS_ID);
  if (!ss.getSheetByName(SHEET_NAME)) {
    var s = ss.insertSheet(SHEET_NAME);
    s.appendRow(['送信日時','生産日','部品番号','部品名','作業者','良品数','不良数','実績区分','材料残','メモ','DriveURL','ファイル名','システム入力','製造番号','工順','工程','加工指示数','保留品','その他','その他メモ']);
    s.getRange(1,1,1,17).setFontWeight('bold').setBackground('#1F4E79').setFontColor('#ffffff');
    s.setFrozenRows(1);
  }
  return ss;
}

function getOrCreateFolder() {
  var f = DriveApp.getFoldersByName(FOLDER_NAME);
  return f.hasNext() ? f.next() : DriveApp.createFolder(FOLDER_NAME);
}

function getOrCreateSubFolder(parent, name) {
  var f = parent.getFoldersByName(name);
  return f.hasNext() ? f.next() : parent.createFolder(name);
}

// ===== kintone部品マスタ中継（CORS回避）=====
function getKintonePartData(params) {
  var domain = params.domain;
  var appId  = params.appId;
  var token  = params.token;
  var query  = params.query  || '';
  var fields = params.fields || [];
  if (!domain || !token) return { ok: false, error: 'params_missing' };
  var fieldParams = fields.map(function(f, i) {
    return 'fields[' + i + ']=' + encodeURIComponent(f);
  }).join('&');
  var url = 'https://' + domain + '.cybozu.com/k/v1/records.json'
    + '?app=' + encodeURIComponent(appId)
    + '&query=' + encodeURIComponent(query)
    + (fieldParams ? '&' + fieldParams : '');
  try {
    var response = UrlFetchApp.fetch(url, {
      headers: { 'X-Cybozu-API-Token': token },
      muteHttpExceptions: true
    });
    var code = response.getResponseCode();
    if (code === 200) {
      return { ok: true, records: JSON.parse(response.getContentText()).records || [] };
    }
    return { ok: false, error: 'HTTP ' + code };
  } catch(err) {
    return { ok: false, error: err.message };
  }
}
