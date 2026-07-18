import os
import threading
import asyncio
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ChatMemberHandler, Application

import handlers
from config import BOT_TOKEN

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================= 纯同步保活服务 =================
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

# ================= 无限重生机器人核心 =================
async def run_bot_loop():
    while True:
        try:
            print("🚀 正在重新装载机器人的核心功能...")
            # 每次重启都建一个全新的实例，把之前卡死的痕迹彻底抹掉
            app = Application.builder().token(BOT_TOKEN).build()
            handlers.application = app

            print("🧹 正在清理残留的 Webhook 连接...")
            await app.bot.delete_webhook(drop_pending_updates=True)

            app.add_handler(CommandHandler("start", handlers.show_menu))
            app.add_handler(CallbackQueryHandler(handlers.button_click))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
            app.add_handler(ChatMemberHandler(handlers.chat_member_update))

            print("✅ 机器人已稳定上线，开始监听消息...")
            await app.run_polling()

        except Exception as e:
            # 只要发生任何崩溃，都只会进这里，绝对不会导致程序死亡
            print(f"❌ 机器人遭遇意外崩溃：{e}")
            print("🔄 正在等待 5 秒后自动重启...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    # 1. 启动保活线程
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # 2. 主线程跑无限重生逻辑
    try:
        asyncio.run(run_bot_loop())
    except KeyboardInterrupt:
        print("手动停止机器人...")
