import os
import threading
import logging
from flask import Flask
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ChatMemberHandler

import handlers
from config import BOT_TOKEN

# 开启实时日志打印
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 1. 启动 Flask 保活网页
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# 2. 主程序启动
if __name__ == "__main__":
    try:
        # 启动保活网页线程
        web_thread = threading.Thread(target=run_web)
        web_thread.daemon = True
        web_thread.start()
        
        print("🚀 正在装载机器人核心功能...")
        
        # 绑定处理函数
        handlers.application.add_handler(CommandHandler("start", handlers.show_menu))
        handlers.application.add_handler(CallbackQueryHandler(handlers.button_click))
        handlers.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
        handlers.application.add_handler(ChatMemberHandler(handlers.chat_member_update))

        print("✅ 机器人已成功上线，正在监听您的消息！")
        # 直接启动长轮询，让它自己解决连接冲突
        handlers.application.run_polling()

    except Exception as e:
        print(f"❌ 机器人遭遇严重错误，崩溃详情如下：")
        print(e)
