import os
import asyncio
from threading import Thread
from flask import Flask
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import handlers
from config import BOT_TOKEN

# ===== 修复点：使用 Railway 的 PORT 环境变量 =====
PORT = int(os.getenv('PORT', 10000))
app = Flask(__name__)

@app.route('/')
def home():
    return "机器人运行中..."

def run_web():
    app.run(host="0.0.0.0", port=PORT) 

def main():
    Thread(target=run_web).start()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", handlers.show_menu))
    application.add_handler(CommandHandler("auth", handlers.auth_group))
    application.add_handler(CallbackQueryHandler(handlers.button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
    
    # 启动定时任务
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(handlers.start_scheduler(application.bot))
    
    print("✅ 群管机器人已上线！")
    application.run_polling()

if __name__ == "__main__":
    main()
