import os
import threading
import asyncio
import time
import logging
from flask import Flask
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ChatMemberHandler

import handlers
from config import BOT_TOKEN

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 1. 启动保活网页
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.getenv("PORT", 8080))
    # 禁用 reloader，防止重复启动
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# 2. 机器人的核心运行线程
def run_bot_thread():
    while True:
        # 手动创建一个新的事件循环，避免 "No current event loop"
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            print("🚀 正在装载机器人核心功能...")
            
            # 强制清理老旧的 Webhook 冲突
            try:
                loop.run_until_complete(handlers.application.bot.delete_webhook(drop_pending_updates=True))
            except Exception:
                pass
            
            # 注册控制器
            handlers.application.add_handler(CommandHandler("start", handlers.show_menu))
            handlers.application.add_handler(CallbackQueryHandler(handlers.button_click))
            handlers.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
            handlers.application.add_handler(ChatMemberHandler(handlers.chat_member_update))
            
            print("✅ 机器人已上线并开始监听消息...")
            
            # 启动 Polling（这会永久阻塞这个线程，除非报错）
            loop.run_until_complete(handlers.application.run_polling())
            
        except Exception as e:
            # 只要有任何异常导致机器人停止，就会进到这里
            print(f"❌ 机器人遭遇连接中断：{e}")
            print("🔄 正在等待 5 秒后自动重启机器人...")
            time.sleep(5)
        finally:
            # 重置、关闭旧的事件循环，为下一次循环做准备
            loop.close()

if __name__ == "__main__":
    # 1. 独立线程运行 Flask 网页
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    
    # 2. 独立线程运行机器人核心（自带无限自动重启）
    bot_thread = threading.Thread(target=run_bot_thread, daemon=True)
    bot_thread.start()

    # 3. 主线程直接进入死循环待命，保持容器不退出
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("停止机器人...")
