import os
import asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ChatMemberHandler

import handlers
from config import BOT_TOKEN

app = Flask(__name__)

@app.route(f"/telegram/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    handlers.application.process_update(update)
    return "OK", 200

def main():
    bot = Bot(token=BOT_TOKEN)
    # 尝试获取外部域名，如果获取不到，使用你之前在 Variables 里配置的 WEBHOOK_URL
    domain = os.getenv('RAILWAY_PUBLIC_DOMAIN')
    if not domain:
        # 如果没自动获取到，fallback 到环境变量你手动填的
        domain = os.getenv('WEBHOOK_URL', 'https://gs-group-manager.up.railway.app')
    
    webhook_url = f"{domain}/telegram/{BOT_TOKEN}"
    
    # ======= 关键修复：加上 await =======
    asyncio.run(bot.set_webhook(url=webhook_url))
    # =====================================

    # 注册处理器
    handlers.application.add_handler(CommandHandler("start", handlers.show_menu))
    handlers.application.add_handler(CallbackQueryHandler(handlers.button_click))
    handlers.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
    handlers.application.add_handler(ChatMemberHandler(handlers.chat_member_update))

    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
