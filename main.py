import os
import asyncio
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ChatMemberHandler

import handlers
from config import BOT_TOKEN

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 极简保活页面（替代臃肿的 Flask）
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run_health():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"🟢 保活已启动 (端口 {port})")
    server.serve_forever()

if __name__ == "__main__":
    # 开启纯线程保活
    threading.Thread(target=run_health, daemon=True).start()

    while True:
        try:
            print("🚀 装载核心...")
            app = Application.builder().token(BOT_TOKEN).build()
            handlers.application = app

            app.add_handler(CommandHandler("start", handlers.show_menu))
            app.add_handler(CallbackQueryHandler(handlers.button_click))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
            app.add_handler(ChatMemberHandler(handlers.chat_member_update))

            print("✅ 上线，监听中...")
            asyncio.run(app.run_polling()) # 直接单线程跑，绝不溢出

        except Exception as e:
            print(f"❌ 崩溃：{e}，5秒后重启...")
            import time
            time.sleep(5)
