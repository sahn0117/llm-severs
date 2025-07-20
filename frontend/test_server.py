# C:\llm_service\frontend\test_server.py
import http.server
import socketserver
import os
from pathlib import Path
# 設定端口
PORT = 8080
# 切換到前端目錄
os.chdir(Path(__file__).parent)
# 建立 HTTP 伺服器
Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"前端測試伺服器啟動在 http://localhost:{PORT}")
    print("按 Ctrl+C 停止伺服器")
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    print("\n伺服器已停止")
