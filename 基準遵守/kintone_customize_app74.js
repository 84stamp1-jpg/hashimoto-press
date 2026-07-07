// ================================================================
// 橋本工業　基準遵守手当　kintoneカスタマイズ v3
// App74：週次チェック・減点記録
// ================================================================
(function() {
  'use strict';

  var GAS_URL = 'https://script.google.com/macros/s/AKfycbxBJH2HIGJDCB_RMRTsDLktXsWLkJKV2ROWTmrbyaG2mbrd8jVT6yvLyVdheQmUjPNq2Q/exec';

  kintone.events.on([
    'app.record.create.submit.success',
    'app.record.edit.submit.success'
  ], function(event) {
    var record = event.record;

    var params = {
      action:     'deduct',
      appId:      '74',
      recordId:   record['レコード番号']['value'],
      memberName: record['ルックアップ']   ? record['ルックアップ']['value']   : '',
      deductItem: record['ルックアップ_0'] ? record['ルックアップ_0']['value'] : '',
      deductPt:   record['数値']           ? record['数値']['value']           : '0',
      pattern:    record['文字列__1行_']   ? record['文字列__1行_']['value']   : '',
      occurDate:  record['日付_0']         ? record['日付_0']['value']         : '',
    };

    console.log('App74 送信パラメータ:', JSON.stringify(params));

    var query = Object.keys(params).map(function(k) {
      return encodeURIComponent(k) + '=' + encodeURIComponent(params[k]);
    }).join('&');

    fetch(GAS_URL + '?' + query, { method: 'GET' })
      .then(function(res) {
        console.log('App74 GAS呼び出し成功 status:', res.status);
        return res.text();
      })
      .then(function(text) {
        console.log('App74 GASレスポンス:', text);
      })
      .catch(function(err) {
        console.error('App74 GAS呼び出しエラー:', err);
      });

    return event;
  });

})();
