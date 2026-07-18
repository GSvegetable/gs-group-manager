import os
import time
import asyncio
import logging
from multiprocessing import Process
from flask import Flask
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ChatMemberHandler

import handlers
from config import BOT_TOKEN

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================= 进程 1：保活网页 =================
def run_web():
    app = Flask(__name__)
    @app.route('/')
    def home():
        return "Bot is running!"
    port = int(os.getenv("PORT", 8080))
    # 在独立的进程里运行 Flask，彻底避开多线程冲突
    app.run(host="0.0.0.0", port=port)

# ================= 进程 2：机器人核心 =================
def run_bot():
    # 在自己独立的进程里创建全新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        print("🧹 正在清理残留的 Webhook...")
        loop.run_until_complete(handlers.application.bot.delete_webhook(drop_pending_updates=True))
        
        print("🚀 装载核心功能...")
        handlers.application.add_handler(CommandHandler("start", handlers.show_menu))
        handlers.application.add_handler(CallbackQueryHandler(handlers.button_click))
        handlers.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
        handlers.application.add_handler(ChatMemberHandler(handlers.chat_member_update))
        
        print("✅ 机器人已上线，稳定监听中...")
        # 在独立进程里跑 Polling，绝不干扰网页进程
        loop.run_until_complete(handlers.application.run_polling())
        
    except Exception as e:
        print(f"❌ 机器人异常停止：{e}")
    finally:
        loop.close()

if __name__ == "__main__":
    # ===== 真正的核心启动逻辑 =====
    while True:
        # 分别开启两个完全隔离的进程
        web_process = Process(target=run_web)
        bot_process = Process(target=run_bot)

        web_process.start()
        bot_process.start()

        # 等待两个进程结束（如果其中一个因为网络断了，会自动走到下面）
        web_process.join()
        bot_process.join()

        print("🔄 机器人进程已停止，正在 5 秒后重新拉起...")
        time.sleep(5)
