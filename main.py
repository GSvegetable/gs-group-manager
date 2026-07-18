import os
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ChatMemberHandler

import handlers
from config import BOT_TOKEN

app = Flask(__name__)

@app.route(f"/telegram/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    # 使用 handlers 里的 application 处理更新
    handlers.application.process_update(update)
    return "OK", 200

def main():
    bot = Bot(token=BOT_TOKEN)
    # 自动获取 Railway 的域名
    webhook_url = f"{os.getenv('RAILWAY_PUBLIC_DOMAIN', 'https://gs-group-manager.up.railway.app')}/telegram/{BOT_TOKEN}"
    # 注册 Webhook
    bot.set_webhook(url=webhook_url)

    # 将处理器添加到 handlers 内部的 application 中
    handlers.application.add_handler(CommandHandler("start", handlers.show_menu))
    handlers.application.add_handler(CallbackQueryHandler(handlers.button_click))
    handlers.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
    handlers.application.add_handler(ChatMemberHandler(handlers.chat_member_update))

    # 启动 Flask 网页保活
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
