import os
from threading import Thread
from flask import Flask
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ChatMemberHandler

import handlers
from config import BOT_TOKEN

# ===== 启动 Flask 保活网页 =====
app = Flask(__name__)
@app.route('/')
def home():
    return "机器人运行中..."

def run_web():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ===== 主程序 =====
def main():
    # 1. 在后台启动保活网页
    Thread(target=run_web).start()
    
    # 2. 启动 Polling（长轮询）模式，彻底绕过 Webhook
    print("🚀 正在通过 Polling 启动机器人...")
    try:
        handlers.application.add_handler(CommandHandler("start", handlers.show_menu))
        handlers.application.add_handler(CallbackQueryHandler(handlers.button_click))
        handlers.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
        handlers.application.add_handler(ChatMemberHandler(handlers.chat_member_update))
        
        # 3. 开始轮询监听（如果有报错，这里会直接打印在控制台）
        handlers.application.run_polling()
    except Exception as e:
        print(f"❌ 机器人启动失败，错误信息：{e}")

if __name__ == "__main__":
    main()
