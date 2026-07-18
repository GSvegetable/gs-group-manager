import os
import asyncio
import threading
import logging
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
    try:
        web_thread = threading.Thread(target=run_web)
        web_thread.daemon = True
        web_thread.start()
        
        print("🚀 正在尝试终止旧连接...")
        # 【关键绝杀】强制清理 Webhook 残留，防止 Polling 冲突
        asyncio.run(handlers.application.bot.delete_webhook(drop_pending_updates=True))
        
        print("🚀 机器人正在加载核心功能...")
        handlers.application.add_handler(CommandHandler("start", handlers.show_menu))
        handlers.application.add_handler(CallbackQueryHandler(handlers.button_click))
        handlers.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
        handlers.application.add_handler(ChatMemberHandler(handlers.chat_member_update))

        print("✅ 机器人已成功上线，正在监听您的消息！")
        handlers.application.run_polling()

    except Exception as e:
        print(f"❌ 机器人遭遇严重错误，崩溃详情如下：")
        print(e)
