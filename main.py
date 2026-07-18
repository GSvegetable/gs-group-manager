import os
import threading
import asyncio
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ChatMemberHandler

import handlers
from config import BOT_TOKEN

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================= 纯同步保活服务（完全避开 asyncio 和线程冲突） =================
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

# ================= 机器人主程序（只在主线程运行 asyncio） =================
async def run_bot():
    print("🧹 正在清理残留的 Webhook 连接...")
    try:
        await handlers.application.bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass
    
    print("🚀 装载核心功能...")
    handlers.application.add_handler(CommandHandler("start", handlers.show_menu))
    handlers.application.add_handler(CallbackQueryHandler(handlers.button_click))
    handlers.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
    handlers.application.add_handler(ChatMemberHandler(handlers.chat_member_update))
    
    print("✅ 机器人已上线，稳定监听中...")
    await handlers.application.run_polling()

if __name__ == "__main__":
    # 1. 启动纯同步的 HTTP 保活线程（绝不会触发 set_wakeup_fd 错误）
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # 2. 主线程运行 asyncio 机器人
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("停止机器人...")
