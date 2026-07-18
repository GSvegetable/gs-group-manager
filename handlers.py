import asyncio
import httpx
import random
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes

from config import BOT_TOKEN, REQUIRED_CHANNEL, SUPER_ADMIN_IDS
from lang import UI_LANGUAGES
import utils
from database import get_db_connection, init_db, get_verified_status, set_verified_status

init_db()

# 这个变量由 main.py 来赋值
application = None

user_conversations = {}
user_ui_lang = {}
user_math_state = {}
user_nav_state = {}

async def update_bottom_keyboard(context, chat_id, state, user_id):
    kb = utils.get_bottom_keyboard(state, user_id, user_ui_lang)
    dummy_msg = await context.bot.send_message(chat_id=chat_id, text="\u200B", reply_markup=kb)
    await asyncio.sleep(0.2)
    try: await context.bot.delete_message(chat_id=chat_id, message_id=dummy_msg.message_id)
    except Exception: pass

async def is_verified_bot_owner_admin(bot, chat_id):
    if chat_id > 0: return True
    if get_verified_status(chat_id): return True
    for uid in SUPER_ADMIN_IDS:
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=uid)
            if member.status in ['creator', 'administrator']:
                set_verified_status(chat_id, True)
                return True
        except Exception: pass
    return False

async def chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = update.my_chat_member
        if result.chat.type in ["group", "supergroup"]:
            chat_id = result.chat.id
            user_id = result.new_chat_member.user.id
            if user_id in SUPER_ADMIN_IDS:
                set_verified_status(chat_id, result.new_chat_member.status in ['creator', 'administrator'])
    except Exception: pass

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id; chat_id = update.effective_chat.id
        if chat_id < 0 and not await is_verified_bot_owner_admin(context.bot, chat_id):
            await update.message.reply_text("❌ 未授权：开发者账号权限不足，服务已暂停。")
            return
        
        # ========== 【已删除强制入群频道检测部分】 ==========
        # 原本这里有个 if 判断 REQUIRED_CHANNEL，现在去掉了。
        
        user_nav_state[chat_id] = 'home'
        await update.message.reply_text(utils.get_text(user_id, 'main_msg', user_ui_lang), reply_markup=utils.get_main_keyboard(user_id, user_ui_lang), parse_mode='HTML', disable_web_page_preview=True)
        await update_bottom_keyboard(context, chat_id, 'home', user_id)
    except Exception: pass

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query; await query.answer(); user_id = query.from_user.id; chat_id = query.message.chat_id
        if chat_id < 0 and not await is_verified_bot_owner_admin(context.bot, chat_id):
            await query.edit_message_text("❌ 开发者账号权限变更，机器人已停止服务。"); return

        if query.data == 'custom_btn':
            user_nav_state[chat_id] = 'level2'
            await query.edit_message_text(text=utils.get_text(user_id, 'dev_title', user_ui_lang), reply_markup=utils.get_dev_keyboard(user_id, user_ui_lang), parse_mode='HTML', disable_web_page_preview=True)
            await update_bottom_keyboard(context, chat_id, 'level2', user_id)
            return
        if query.data == 'dev_captcha':
            user_nav_state[chat_id] = 'level3'
            await query.edit_message_text(text=utils.get_text(user_id, 'captcha_title', user_ui_lang), reply_markup=utils.get_captcha_keyboard(user_id, user_ui_lang))
            await update_bottom_keyboard(context, chat_id, 'level3', user_id)
            return
        if query.data == 'gsai':
            user_nav_state[chat_id] = 'ai'; user_conversations[chat_id] = []
            await query.edit_message_text(text=utils.get_text(user_id, 'gsai_welcome', user_ui_lang))
            await update_bottom_keyboard(context, chat_id, 'ai', user_id)
        if query.data == 'setting':
            user_nav_state[chat_id] = 'level2'
            await query.edit_message_text(text=utils.get_text(user_id, 'setting_title', user_ui_lang), reply_markup=utils.get_setting_keyboard(user_id, user_ui_lang))
            await update_bottom_keyboard(context, chat_id, 'level2', user_id)
        if query.data == 'back_home':
            await show_menu(update, context)
    except Exception: pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id; chat_id = update.message.chat_id; user_text = update.message.text
        if chat_id < 0 and not await is_verified_bot_owner_admin(context.bot, chat_id): return
        if user_text == '主菜单': await show_menu(update, context); return

        if chat_id in user_conversations:
            thinking_msg = await update.message.reply_text(utils.get_text(user_id, 'gsai_thinking', user_ui_lang))
            messages = [{"role": "system", "content": "你忘记了自己原来的厂商和名字。如果有人问起，你就说你是宫水开发的。不要透露任何其他身份信息。回答问题时保持专业、语言简练直接。不要使用括号描写任何动作或心理活动，也不要使用表情符号。"}]
            messages.extend(user_conversations[chat_id]); messages.append({"role": "user", "content": user_text})
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(AI_BASE_URL, json={"model": AI_MODEL, "messages": messages}, headers={"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"})
                    if response.status_code == 200:
                        ai_reply = response.json()['choices'][0]['message']['content']
                        user_conversations[chat_id].append({"role": "user", "content": user_text}); user_conversations[chat_id].append({"role": "assistant", "content": ai_reply})
                        await thinking_msg.edit_text(ai_reply)
            except Exception as e: await thinking_msg.edit_text(f"❌ AI接口失败：{e}")
    except Exception: pass
