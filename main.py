import os
import threading
import logging
import time
from flask import Flask
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ChatMemberHandler

import handlers
from config import BOT_TOKEN

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # 启动保活网页
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()
    
    print("🚀 正在装载机器人核心功能...")
    handlers.application.add_handler(CommandHandler("start", handlers.show_menu))
    handlers.application.add_handler(CallbackQueryHandler(handlers.button_click))
    handlers.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
    handlers.application.add_handler(ChatMemberHandler(handlers.chat_member_update))

    # ===== 核心不死逻辑 =====
    while True:
        try:
            print("✅ 机器人已上线并开始监听消息...")
            handlers.application.run_polling()
        except Exception as e:
            # 任何导致机器人退出的错误都会进入这里
            print(f"❌ 机器人遭遇连接中断 (可能是 TimedOut 超时): {e}")
            print("🔄 正在等待 5 秒后自动重启机器人...")
            time.sleep(5) # 暂停5秒后再试，防止无限快速崩溃
            # 注意：由于 run_polling 停止后，add_handler 已存在，循环即可
