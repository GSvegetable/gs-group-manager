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
    # 读取 handlers 里已经实例化好的 bot
    update = Update.de_json(request.get_json(force=True), handlers.application.bot)
    handlers.application.process_update(update)
    return "OK", 200

def main():
    # 自动获取 Railway 域名
    domain = os.getenv('RAILWAY_PUBLIC_DOMAIN')
    if not domain:
        domain = os.getenv('WEBHOOK_URL', 'https://gs-group-manager.up.railway.app')
    
    webhook_url = f"{domain}/telegram/{BOT_TOKEN}"
    # 使用 asyncio.run 正确注册 Webhook，解决各种冲突
    asyncio.run(handlers.application.bot.set_webhook(url=webhook_url))

    # 注册所有的控制器
    handlers.application.add_handler(CommandHandler("start", handlers.show_menu))
    handlers.application.add_handler(CallbackQueryHandler(handlers.button_click))
    handlers.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
    handlers.application.add_handler(ChatMemberHandler(handlers.chat_member_update))

    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
