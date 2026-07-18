import os
import asyncio
from threading import Thread
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import handlers
from config import BOT_TOKEN

# ===== 修复点：使用 Railway 的 PORT 环境变量 =====
PORT = int(os.getenv('PORT', 10000))

# ===== 使用 Railway 分配的公网域名拼接 webhook 地址 =====
RAILWAY_DOMAIN = os.getenv('RAILWAY_PUBLIC_DOMAIN') or os.getenv('RAILWAY_STATIC_URL')
WEBHOOK_PATH = f"/telegram/{BOT_TOKEN}"
WEBHOOK_URL = f"https://{RAILWAY_DOMAIN}{WEBHOOK_PATH}" if RAILWAY_DOMAIN else None

app = Flask(__name__)

application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", handlers.show_menu))
application.add_handler(CommandHandler("auth", handlers.auth_group))
application.add_handler(CallbackQueryHandler(handlers.button_click))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))

# ===== 单独的事件循环线程，专门用来跑 telegram Application 和定时任务 =====
bot_loop = asyncio.new_event_loop()


@app.route('/')
def home():
    return "机器人运行中..."


@app.route(WEBHOOK_PATH, methods=['POST'])
def telegram_webhook():
    """接收 Telegram 的 webhook 回调，并交给 bot 的事件循环处理"""
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run_coroutine_threadsafe(application.process_update(update), bot_loop)
    return "ok"


def run_bot_loop():
    """在后台线程里持续运行事件循环"""
    asyncio.set_event_loop(bot_loop)
    bot_loop.run_forever()


async def setup_bot():
    """初始化 application、注册 webhook、启动定时任务"""
    await application.initialize()
    await application.start()

    if WEBHOOK_URL:
        await application.bot.set_webhook(url=WEBHOOK_URL)
        print(f"✅ Webhook 已设置: {WEBHOOK_URL}")
    else:
        print("⚠️ 未检测到 RAILWAY_PUBLIC_DOMAIN/RAILWAY_STATIC_URL，请手动设置 webhook 地址")

    # 启动定时任务
    await handlers.start_scheduler(application.bot)


def main():
    # 后台线程运行 bot 的事件循环（webhook 处理 + 定时任务）
    Thread(target=run_bot_loop, daemon=True).start()

    # 把初始化协程扔进上面的事件循环里执行，并等待完成
    asyncio.run_coroutine_threadsafe(setup_bot(), bot_loop).result(timeout=30)

    print("✅ 群管机器人已上线！")
    # Flask 放在主线程运行，接收 Railway 的 HTTP 请求（包括 webhook 回调）
    app.run(host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
