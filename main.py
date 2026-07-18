import os
import sys
import time
import subprocess
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================= 纯同步保活服务（主进程） =================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Bot is running!')

def run_http_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"🟢 保活服务已启动 (端口 {port})")
    server.serve_forever()

# ================= 主进程守护（保证机器人永不僵死） =================
if __name__ == "__main__":
    # 1. 启动保活服务
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    print("👶 主进程已启动。正在为机器人开启纯净进程守护...")
    
    # 2. 主循环：永远让机器人以纯净的子进程运行
    while True:
        try:
            # 启动一个全新的、干净的 Python 子进程来跑机器人
            print("🚀 启动全新的机器人子进程...")
            # 传入参数 `--run-bot` 告诉子进程它是机器人
            bot_process = subprocess.Popen(
                [sys.executable, "main.py", "--run-bot"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # 实时打印子进程的日志
            for line in bot_process.stdout:
                print(line.strip())
                
            # 等待子进程结束（如果是因为超时死掉，会走到这里）
            bot_process.wait()
            
            print(f"⚠️ 机器人子进程已退出 (退出码: {bot_process.returncode})")
            print("🔄 机器人即将在 5 秒后由父进程重新拉起...")
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("手动停止父进程...")
            break
        except Exception as e:
            print(f"❌ 守护进程出现错误: {e}")
            time.sleep(5)
