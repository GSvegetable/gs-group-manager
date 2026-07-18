import os
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ChatMemberHandler

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
    # 自动获取 Railway 的域名，如果没有就手动读你配置的 WEBHOOK_URL
    webhook_url = f"{os.getenv('RAILWAY_PUBLIC_DOMAIN', 'https://gs-group-manager.up.railway.app')}/telegram/{BOT_TOKEN}"
    bot.set_webhook(url=webhook_url)

    # 初始化处理器
    handlers.application.bot = bot
    handlers.application.add_handler(CommandHandler("start", handlers.show_menu))
    handlers.application.add_handler(CallbackQueryHandler(handlers.button_click))
    handlers.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
    # ✅ 新增：监听你的账号在群内身份变化的处理器（退群/降权会自动通知机器人）
    handlers.application.add_handler(ChatMemberHandler(handlers.chat_member_update))

    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
