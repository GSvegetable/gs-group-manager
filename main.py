import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ChatMemberHandler

import handlers
from config import BOT_TOKEN

app = Flask(__name__)

@app.route(f"/telegram/{BOT_TOKEN}", methods=["POST"])
def webhook():
    # 1. 解析 Telegram 推送来的更新
    update = Update.de_json(request.get_json(force=True), handlers.application.bot)
    
    # 2. 使用 asyncio.create_task 在后台异步处理更新
    #    这样能完美避免 "coroutine ... was never awaited" 的黄色警告
    asyncio.create_task(handlers.application.process_update(update))
    
    return "OK", 200

def main():
    # 获取 Railway 的公开域名
    domain = os.getenv('RAILWAY_PUBLIC_DOMAIN')
    if not domain:
        # 如果环境变量没取到，退一步使用你手动配置的 WEBHOOK_URL
        domain = os.getenv('WEBHOOK_URL', 'https://gs-group-manager.up.railway.app')
    
    webhook_url = f"{domain}/telegram/{BOT_TOKEN}"
    
    # 设置 Webhook（依然是绝对没问题的 async 注册方式）
    asyncio.run(handlers.application.bot.set_webhook(url=webhook_url))

    # 注册所有处理器
    handlers.application.add_handler(CommandHandler("start", handlers.show_menu))
    handlers.application.add_handler(CallbackQueryHandler(handlers.button_click))
    handlers.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
    handlers.application.add_handler(ChatMemberHandler(handlers.chat_member_update))

    # 启动 Flask 页面，保持 Railway 服务不自动休眠
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
