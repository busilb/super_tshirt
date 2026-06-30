#!/usr/bin/env python3
"""SuperMe T-shirt order relay server.
Receives order POSTs from the static site and forwards to DingTalk via am CLI.
"""
import json
import subprocess
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

NOTIFY_STAFF = "067660"  # 布斯
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "orders.log")

class OrderHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        self.send_response(200)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

        try:
            data = json.loads(body)
            self._log(data)
            self._forward(data)
        except Exception as e:
            print(f"Error: {e}")

    def _log(self, data):
        try:
            with open(LOG_FILE, "a") as f:
                entry = {"time": datetime.now().isoformat(), "data": data}
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _forward(self, data):
        t = data.get('type', 'unknown')
        if t in ('order', 'checkout', 'sync'):
            msg = self._format_order(data)
        elif t == 'paid':
            msg = f"【SuperMe T恤付款通知】\n{data.get('n', '-')} 点击了「我已付款」\n尺码: {data.get('sz', '-')}\n订单号: {data.get('id', '-')}\n时间: {data.get('tm', '-')}\n\n请确认收款后安排发货"
        elif t == 'bulk':
            msg = f"【团购订单】{data.get('count', 0)}条订单，时间：{data.get('tm', '-')}"
        else:
            msg = f"【T恤通知】{json.dumps(data, ensure_ascii=False)}"

        subprocess.Popen(
            ['am', 'chat', NOTIFY_STAFF, msg],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    def _format_order(self, d):
        is_sync = d.get('type') == 'sync'
        lines = ["【SuperMe T恤" + ("历史订单同步" if is_sync else "新订单") + "】"]
        lines.append(f"订单号: {d.get('id', '-')}")
        lines.append(f"姓名: {d.get('n', '-')}")
        lines.append(f"手机: {d.get('p', '-')}")
        lines.append(f"尺码: {d.get('sz', '-')}")
        lines.append(f"颜色: {d.get('cl', '经典白')}")
        lines.append(f"数量: {d.get('qty', 1)}")
        if d.get('fab'):
            lines.append(f"面料: {d.get('fab')}")
        if d.get('addr'):
            lines.append(f"地址: {d.get('addr')}")
        if d.get('note'):
            lines.append(f"备注: {d.get('note')}")
        lines.append(f"时间: {d.get('tm', '-')}")
        return "\n".join(lines)

    def log_message(self, fmt, *args):
        print(f"[relay] {args[0]}")

if __name__ == '__main__':
    port = 9001
    print(f"Order relay listening on :{port}")
    HTTPServer(('0.0.0.0', port), OrderHandler).serve_forever()
