// ================================================================
// 橋本工業　苦情・不適合報告書　kintoneカスタマイズ v1
// App45：苦情・不適合報告書
//
// ★2026-11-21 新設。これまでApp45からのSlack通知は一切なく、
//   報告書が起票されても対策担当者本人に伝わっていなかった。
//   「対策担当者」または「提出期限」が入った時点で、
//   Slackのチャンネル投稿＋本人へのDMを出す（GAS経由）。
//
// ★通知するのは次のときだけ（何度も保存しても鳴り続けないように）
//   ・新規登録で、対策担当者が入っているとき
//   ・編集で、対策担当者または提出期限が「前と変わった」とき
//
// ⚠このアプリは表示名とフィールドコードが食い違う。コードで書くこと。
//     提出期限   → 不具合発生日_0
//     対策担当者 → ルックアップ_0
//     報告区分   → ラジオボタン
//     部品番号   → ルックアップ_2 ／ 部品名称 → 文字列__1行__1
//     不具合内容 → 文字列__複数行_
// ================================================================
(function() {
  'use strict';

  var GAS_URL = 'https://script.google.com/macros/s/AKfycbxBJH2HIGJDCB_RMRTsDLktXsWLkJKV2ROWTmrbyaG2mbrd8jVT6yvLyVdheQmUjPNq2Q/exec';

  // フィールドコード（表示名ではない）
  var F = {
    person:   'ルックアップ_0',    // 対策担当者
    deadline: '不具合発生日_0',    // 提出期限
    kubun:    'ラジオボタン',      // 報告区分（苦情/不適合/改善/異常）
    part:     'ルックアップ_2',    // 部品番号
    partName: '文字列__1行__1',    // 部品名称
    content:  '文字列__複数行_',   // 不具合内容
  };

  // 開いたときの値を覚えておく（変わったかどうかを見るため）
  var before = { person: '', deadline: '' };

  function val(record, code) {
    return (record[code] && record[code].value) ? String(record[code].value) : '';
  }

  // ----------------------------------------------------------------
  // ① 画面を開いたときの値を控える
  // ----------------------------------------------------------------
  kintone.events.on(['app.record.edit.show', 'app.record.detail.show'], function(event) {
    before.person   = val(event.record, F.person);
    before.deadline = val(event.record, F.deadline);
    return event;
  });

  kintone.events.on('app.record.create.show', function(event) {
    before.person   = '';
    before.deadline = '';
    return event;
  });

  // ----------------------------------------------------------------
  // ② 保存できたら、担当者・期限が入った／変わったときだけ通知
  // ----------------------------------------------------------------
  kintone.events.on([
    'app.record.create.submit.success',
    'app.record.edit.submit.success',
  ], function(event) {
    var record   = event.record;
    var person   = val(record, F.person);
    var deadline = val(record, F.deadline);

    if (!person) return event;                     // 担当者がまだ決まっていない
    if (person === before.person && deadline === before.deadline) return event;  // 変わっていない

    var params = {
      action:   'houkokushoAssign',
      appId:    '45',
      recordId: record['レコード番号']['value'],
      kubun:    val(record, F.kubun),
      part:     val(record, F.part),
      partName: val(record, F.partName),
      content:  val(record, F.content).slice(0, 100),  // 長すぎる場合は先頭100文字
      person:   person,
      deadline: deadline,
    };

    console.log('App45 担当者通知:', JSON.stringify(params));
    gasCall(params);

    before.person   = person;
    before.deadline = deadline;
    return event;
  });

  // ----------------------------------------------------------------
  // 共通：GAS呼び出しヘルパー（App77と同じ作り）
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
