import os
import threading
import logging
import time
import asyncio
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
    # 1. 启动保活网页
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()
    
    print("🚀 正在装载机器人核心功能...")
    handlers.application.add_handler(CommandHandler("start", handlers.show_menu))
    handlers.application.add_handler(CallbackQueryHandler(handlers.button_click))
    handlers.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
    handlers.application.add_handler(ChatMemberHandler(handlers.chat_member_update))

    # ===== ✨ 关键修复：强行删除 Telegram 端残留的 Webhook =====
    try:
        print("🧹 正在清理残留的 Webhook 连接，准备接管...")
        # 用 asyncio.run 发送删除指令
        asyncio.run(handlers.application.bot.delete_webhook(drop_pending_updates=True))
        print("✅ 连接清理成功，开始接管消息！")
    except Exception as e:
        print(f"⚠️ 清理 Webhook 时出现微小异常（可忽略）：{e}")

    # ===== 核心不死逻辑 =====
    while True:
        try:
            print("✅ 机器人已上线并开始监听消息...")
            # 开始长轮询
            handlers.application.run_polling()
        except Exception as e:
            print(f"❌ 机器人遭遇连接中断：{e}")
            print("🔄 正在等待 5 秒后自动重启机器人...")
            time.sleep(5)
