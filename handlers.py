import asyncio
import httpx
import random
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes

from config import BOT_TOKEN, REQUIRED_CHANNEL, SUPER_ADMIN_IDS, AI_API_KEY, AI_BASE_URL, AI_MODEL
from lang import UI_LANGUAGES
import utils
from database import get_db_connection, init_db, get_verified_status, set_verified_status, get_all_authorized_groups

init_db()
application = None
user_conversations = {}
user_ui_lang = {}
user_math_state = {}
user_nav_state = {}

async def update_bottom_keyboard(context, chat_id, state, user_id):
    # 底部键盘逻辑保持不变
    pass

async def is_verified_bot_owner_admin(bot, chat_id):
    if chat_id > 0: return True
    cached_status = get_verified_status(chat_id)
    if cached_status:
        for uid in SUPER_ADMIN_IDS:
            try:
                member = await bot.get_chat_member(chat_id=chat_id, user_id=uid)
                if member.status in ['creator', 'administrator']: return True
            except Exception: pass
        set_verified_status(chat_id, False); return False
    for uid in SUPER_ADMIN_IDS:
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=uid)
            if member.status in ['creator', 'administrator']:
                set_verified_status(chat_id, True); return True
        except Exception: pass
    return False

async def is_user_group_admin(bot, chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ['creator', 'administrator']
    except Exception: return False

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
        if chat_id < 0:
            if not await is_user_group_admin(context.bot, chat_id, user_id): return
            if not await is_verified_bot_owner_admin(context.bot, chat_id):
                await update.message.reply_text("该群权限不足 联系 <a href=\"https://t.me/gsyxyc\">宫水</a>", parse_mode='HTML', disable_web_page_preview=True)
                return
        
        user_nav_state[chat_id] = 'home'
        
        # ===== 【第一层逻辑】 =====
        authorized_groups = get_all_authorized_groups()
        
        if authorized_groups:
            # 1. 如果有已授权的群，正常显示群组列表
            reply_text = utils.get_text(user_id, 'main_msg', user_ui_lang) + utils.get_text(user_id, 'select_group_msg', user_ui_lang)
            reply_markup = utils.get_group_selection_keyboard(user_id, user_ui_lang, authorized_groups)
        else:
            # 2. 如果没有已授权的群，显示提示，并且不显示按钮
            reply_text = utils.get_text(user_id, 'main_msg', user_ui_lang) + utils.get_text(user_id, 'no_groups_msg', user_ui_lang)
            reply_markup = None
            
        await update.message.reply_text(reply_text, reply_markup=reply_markup, parse_mode='HTML', disable_web_page_preview=True)
        await update_bottom_keyboard(context, chat_id, 'home', user_id)
    except Exception: pass

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query; await query.answer(); user_id = query.from_user.id; chat_id = query.message.chat_id
        if chat_id < 0:
            if not await is_user_group_admin(context.bot, chat_id, user_id): return
            if not await is_verified_bot_owner_admin(context.bot, chat_id):
                await query.edit_message_text("该群权限不足 联系 <a href=\"https://t.me/gsyxyc\">宫水</a>", parse_mode='HTML', disable_web_page_preview=True)
                return

        # 1. 点击了某个具体的群组（进入【第二层】）
        if query.data.startswith('group_'):
            current_gid = query.data.replace('group_', '')
            user_nav_state[chat_id] = 'level2'
            await query.edit_message_text(
                text=utils.get_text(user_id, 'group_panel_title', user_ui_lang) + f" {current_gid}",
                reply_markup=utils.get_level2_keyboard(user_id, user_ui_lang)
            )
            return

        # 2. 第二层功能按钮（目前只是占位，提示开发中）
        if query.data in ['welcome_btn', 'timed_msg_btn', 'keyword_btn', 'captcha_btn']:
            await query.edit_message_text("⚙️ 功能开发中，请期待后续更新。")
            return

        # 3. 点击返回主菜单
        if query.data == 'back_home':
            await show_menu(update, context)
            
    except Exception: pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id; chat_id = update.message.chat_id; user_text = update.message.text
        if chat_id < 0:
            if not await is_user_group_admin(context.bot, chat_id, user_id): return
            if not await is_verified_bot_owner_admin(context.bot, chat_id):
                await update.message.reply_text("该群权限不足 联系 <a href=\"https://t.me/gsyxyc\">宫水</a>", parse_mode='HTML', disable_web_page_preview=True)
                return
        if user_text == '主菜单': await show_menu(update, context); return
    except Exception: pass
