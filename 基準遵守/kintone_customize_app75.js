// ================================================================
// 橋本工業　基準遵守手当　kintoneカスタマイズ v3
// App75：5S巡回チェック
// ================================================================
(function() {
  'use strict';

  var GAS_URL = 'https://script.google.com/macros/s/AKfycbxBJH2HIGJDCB_RMRTsDLktXsWLkJKV2ROWTmrbyaG2mbrd8jVT6yvLyVdheQmUjPNq2Q/exec';

  // ----------------------------------------------------------------
  // ① レコード保存時：基準遵守手当のペンディングリストに蓄積
  // ----------------------------------------------------------------
  kintone.events.on([
    'app.record.create.submit.success',
    'app.record.edit.submit.success'
  ], function(event) {
    var record = event.record;

    // テーブルから指摘内容を取得
    var tableRows = record['テーブル'] ? record['テーブル']['value'] : [];
    var issues = [];
    tableRows.forEach(function(row) {
      var content = row['value']['ドロップダウン_0']
        ? row['value']['ドロップダウン_0']['value'] : '';
      if (content && content !== '-----') {
        issues.push(content);
      }
    });

    if (issues.length === 0) {
      console.log('App75 指摘なし・スキップ');
      return event;
    }

    var params = {
      action:    'get5S',
      appId:     '75',
      recordId:  record['レコード番号']['value'],
      area:      record['ドロップダウン'] ? record['ドロップダウン']['value'] : '',
      inspector: record['ルックアップ']   ? record['ルックアップ']['value']   : '',
      date:      record['日付']          ? record['日付']['value']          : '',
      issues:    issues.join('|'),
    };

    console.log('App75 保存イベント送信:', JSON.stringify(params));
    gasCall(params);
    return event;
  });

  // ----------------------------------------------------------------
  // ② プロセスボタン押下時：即時Slack通知
  //    「指摘」ボタン  → 指摘あり通知（本番チャンネル）
  //    「報告する」ボタン → 改善完了通知（本番チャンネル）
  // ----------------------------------------------------------------
  kintone.events.on('app.record.detail.process.proceed', function(event) {
    var action = event.action.value;
    var record = event.record;

    // 「確認完了」はSlack通知しない
    if (action !== '指摘' && action !== '報告する') {
      return event;
    }

    var area      = record['ドロップダウン'] ? record['ドロップダウン']['value'] : '';
    var inspector = record['ルックアップ']   ? record['ルックアップ']['value']   : '';
    var date      = record['日付']          ? record['日付']['value']          : '';
    var recordId  = record['レコード番号']['value'];
    var tableRows = record['テーブル'] ? record['テーブル']['value'] : [];

    // ログインユーザー名（報告者として使用）
    var currentUser = kintone.getLoginUser();
    var userName    = currentUser ? currentUser.name : '';

    var params = {
      action:   '5sNotify',
      recordId: recordId,
      area:     area,
    };

    if (action === '指摘') {
      // 指摘内容をテーブルから収集
      var issues = [];
      tableRows.forEach(function(row) {
        var content = row['value']['ドロップダウン_0']
          ? row['value']['ドロップダウン_0']['value'] : '';
        if (content && content !== '-----') issues.push(content);
      });
      params.type      = 'report';
      params.inspector = inspector;
      params.date      = date;
      params.issues    = issues.join('|');

    } else if (action === '報告する') {
      // 対応日をテーブルから取得（最初に見つかった日付を使用）
      var responseDate = '';
      for (var i = 0; i < tableRows.length; i++) {
        var d = tableRows[i]['value']['日付_0']
          ? tableRows[i]['value']['日付_0']['value'] : '';
        if (d) { responseDate = d; break; }
      }
      params.type         = 'complete';
      params.reporter     = userName;
      params.responseDate = responseDate;
    }

    console.log('App75 プロセス通知送信:', JSON.stringify(params));
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
