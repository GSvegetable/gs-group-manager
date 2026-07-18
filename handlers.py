import os
import sys
import time
import subprocess
import threading
import asyncio
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ChatMemberHandler

import handlers
from config import BOT_TOKEN

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================= 保活服务 =================
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

# ================= 机器人核心进程 =================
async def run_bot_process():
    while True:
        try:
            print("🚀 正在装载机器人的核心功能...")
            app = Application.builder().token(BOT_TOKEN).build()
            handlers.application = app
            
            # 清理残留连接
            await app.bot.delete_webhook(drop_pending_updates=True)

            app.add_handler(CommandHandler("start", handlers.show_menu))
            app.add_handler(CallbackQueryHandler(handlers.button_click))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
            app.add_handler(ChatMemberHandler(handlers.chat_member_update))

            print("✅ 机器人已稳定上线，开始监听消息...")
            await app.run_polling()
        except Exception as e:
            print(f"❌ 机器人遭遇意外崩溃：{e}")
            print("🔄 正在等待 5 秒后自动重启...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    # ✅ 核心修复：判断当前是父进程还是子进程
    if "--run-bot" in sys.argv:
        # ===== 子进程：只跑机器人，绝对不碰端口 =====
        try:
            asyncio.run(run_bot_process())
        except KeyboardInterrupt:
            print("子进程手动停止")
    else:
        # ===== 父进程：负责保活页面 + 拉起子进程 =====
        http_thread = threading.Thread(target=run_http_server, daemon=True)
        http_thread.start()
        
        print("👶 主进程已启动。正在为机器人开启纯净进程守护...")
        
        while True:
            try:
                print("🚀 启动全新的机器人子进程...")
                bot_process = subprocess.Popen(
                    [sys.executable, "main.py", "--run-bot"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                for line in bot_process.stdout:
                    print(line.strip())
                    
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
