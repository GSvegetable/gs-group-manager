import os
import threading
import asyncio
import logging
from flask import Flask
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ChatMemberHandler, Application

import handlers
from config import BOT_TOKEN

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.getenv("PORT", 8080))
    # 🟢 关键修复：关闭调试模式和重载器，彻底避开 set_wakeup_fd 底层报错
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)

async def run_bot_loop():
    while True:
        try:
            print("🚀 正在启动机器人核心（单进程模式，极省内存）...")
            bot_app = Application.builder().token(BOT_TOKEN).build()
            handlers.application = bot_app

            bot_app.add_handler(CommandHandler("start", handlers.show_menu))
            bot_app.add_handler(CallbackQueryHandler(handlers.button_click))
            bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
            bot_app.add_handler(ChatMemberHandler(handlers.chat_member_update))

            # 清理残留的 Webhook 连接
            await bot_app.bot.delete_webhook(drop_pending_updates=True)

            print("✅ 机器人已上线，开始监听消息...")
            # 这是一个会一直阻塞的命令，只要它不报错，就一直在这里挂机
            await bot_app.run_polling()

        except Exception as e:
            print(f"❌ 机器人遭遇意外崩溃：{e}")
            print("🔄 正在等待 5 秒后自动重启...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_bot_loop())
    except KeyboardInterrupt:
        print("手动停止机器人...")
    finally:
        loop.close()
