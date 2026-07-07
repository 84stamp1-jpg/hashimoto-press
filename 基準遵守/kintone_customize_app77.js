// ================================================================
// 橋本工業　期限管理アプリ　kintoneカスタマイズ v1
// App77：期限管理アプリ
// ================================================================
(function() {
  'use strict';

  var GAS_URL = 'https://script.google.com/macros/s/AKfycbxBJH2HIGJDCB_RMRTsDLktXsWLkJKV2ROWTmrbyaG2mbrd8jVT6yvLyVdheQmUjPNq2Q/exec';

  // 3日自動設定の対象種別
  var AUTO_DEADLINE_TYPE = '不良/保留品処置';
  var AUTO_DEADLINE_DAYS = 3;

  // ----------------------------------------------------------------
  // ① 対応期限の自動計算
  //    種別が「不良/保留品処置」かつ発生日が入力されたら
  //    対応期限 = 発生日 + 3日 を自動セット
  // ----------------------------------------------------------------
  kintone.events.on([
    'app.record.create.change.種別',
    'app.record.create.change.発生日',
    'app.record.edit.change.種別',
    'app.record.edit.change.発生日',
  ], function(event) {
    var record  = event.record;
    var type    = record['種別']['value'];
    var occDate = record['発生日']['value'];

    if (type === AUTO_DEADLINE_TYPE && occDate) {
      var d = new Date(occDate);
      d.setDate(d.getDate() + AUTO_DEADLINE_DAYS);
      var yyyy = d.getFullYear();
      var mm   = ('0' + (d.getMonth() + 1)).slice(-2);
      var dd   = ('0' + d.getDate()).slice(-2);
      record['対応期限']['value'] = yyyy + '-' + mm + '-' + dd;
    } else if (type !== AUTO_DEADLINE_TYPE) {
      // 他の種別に切り替えた場合は自動設定をクリアしない（手動入力を尊重）
    }

    return event;
  });

  // ----------------------------------------------------------------
  // ② 新規登録時：Slack通知（GAS経由）
  // ----------------------------------------------------------------
  kintone.events.on('app.record.create.submit.success', function(event) {
    var record = event.record;

    var params = {
      action:   'qualityNew',
      appId:    '77',
      recordId: record['レコード番号']['value'],
      type:     record['種別']['value']     || '',
      title:    record['件名']['value']     || '',
      occDate:  record['発生日']['value']   || '',
      deadline: record['対応期限']['value'] || '',
      person:   record['担当者']['value']   || '',
      detail:   (record['詳細']['value']    || '').slice(0, 100), // 長すぎる場合は先頭100文字
    };

    console.log('App77 新規登録通知:', JSON.stringify(params));
    gasCall(params);
    return event;
  });

  // ----------------------------------------------------------------
  // ③ プロセスボタン押下時：Slack通知
  //    「完了報告」ボタン → 完了通知
  //    「対応開始」「確認完了」は通知なし
  // ----------------------------------------------------------------
  kintone.events.on('app.record.detail.process.proceed', function(event) {
    var action = event.action.value;
    var record = event.record;

    if (action !== '完了報告') return event;

    var currentUser  = kintone.getLoginUser();
    var userName     = currentUser ? currentUser.name : '';
    var completeDate = record['完了日']['value']    || '';
    var comment      = record['完了報告']['value']  || '';

    var params = {
      action:       'qualityComplete',
      recordId:     record['レコード番号']['value'],
      type:         record['種別']['value'] || '',
      title:        record['件名']['value'] || '',
      reporter:     userName,
      completeDate: completeDate,
      comment:      (comment || '').slice(0, 100),
    };

    console.log('App77 完了報告通知:', JSON.stringify(params));
    gasCall(params);
    return event;
  });

  // ----------------------------------------------------------------
  // 共通：GAS呼び出しヘルパー
  // ----------------------------------------------------------------
  function gasCall(params) {
    var query = Object.keys(params).map(function(k) {
      return encodeURIComponent(k) + '=' + encodeURIComponent(params[k]);
    }).join('&');

    fetch(GAS_URL + '?' + query, { method: 'GET' })
      .then(function(res) {
        console.log('GAS呼び出し成功 status:', res.status);
        return res.text();
      })
      .then(function(text) {
        console.log('GASレスポンス:', text);
      })
      .catch(function(err) {
        console.error('GAS呼び出しエラー:', err);
      });
  }

})();
