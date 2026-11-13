# -*- coding: utf-8 -*-
"""カメラ一覧ページを社内へ配る（8080番）。2026-11-11

   ふだんは `python -m http.server 8080` と同じで、このフォルダのファイルを配るだけ。
   違うのは1か所だけ：**/api/streams を聞かれたら go2rtc(127.0.0.1:1984) に代わりに聞いて返す**。

   なぜ要るか：
     カメラの枠は go2rtc の画面を埋め込んでいるだけで、一度つながり損ねると自分では直らない。
     どの枠が切れているかは go2rtc の /api/streams を見れば分かるが、ページは8080・go2rtcは1984で
     ブラウザから見ると「別のサイト」あつかいになり、直には読めない（ブラウザが止める）。
     go2rtc 側で「どのサイトからでも読んでよい」と緩める手もあるが、それはやらずに、
     **ページを配っているこちら側で、この1本だけ・読むだけ**を中継する。
     go2rtc の設定は何も変えていない（再起動も不要）。

   止め方・直し方：
     タスク `camera_page_server`（ログオン時）が start_camera_page_server.vbs を呼び、
     そこからこのファイルが起動する。入れ替えたいときは python を落としてから vbs を実行。
"""
import http.server
import json
import os
import urllib.request

PORT = 8080
HERE = os.path.dirname(os.path.abspath(__file__))
GO2RTC = 'http://127.0.0.1:1984/api/streams'


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=HERE, **kw)

    def do_GET(self):
        if self.path.split('?')[0] == '/api/streams':
            self.relay()
            return
        super().do_GET()

    def relay(self):
        """go2rtc に代わりに聞いて、そのまま返す（読むだけ）"""
        try:
            with urllib.request.urlopen(GO2RTC, timeout=5) as r:
                body = r.read()
            code = 200
        except Exception as e:
            body = json.dumps({'error': str(e)}, ensure_ascii=False).encode('utf-8')
            code = 502
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        # ★ページを直しても古いまま表示される件（2026-11-13）
        #   ブラウザは Cache-Control が無いと「しばらく聞き直さなくていい」と勝手に判断し、
        #   Ctrl+Shift+R しないと新しい版にならなかった。no-cache＝毎回サーバに確かめる。
        #   変わっていなければ 304 を返すだけなので、重くはならない。
        if self.path.split('?')[0].endswith('.html'):
            self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def log_message(self, *a):
        pass                      # 裏で動くので画面には何も出さない


if __name__ == '__main__':
    http.server.ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
