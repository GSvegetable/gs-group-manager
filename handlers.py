import asyncio
import httpx
from telegram import Update
from telegram.ext import ContextTypes

from config import BOT_TOKEN, REQUIRED_CHANNEL, SUPER_ADMIN_IDS
from lang import UI_LANGUAGES
import utils
from database import get_db_connection, init_db, get_verified_status, set_verified_status

init_db()
application = None
user_conversations = {}
user_ui_lang = {}
user_nav_state = {}

async def update_bottom_keyboard(context, chat_id, state, user_id):
    # 所有键盘已删除，此函数保留但不影响任何执行
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
        set_verified_status(chat_id, False)
        return False
    for uid in SUPER_ADMIN_IDS:
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=uid)
            if member.status in ['creator', 'administrator']:
                set_verified_status(chat_id, True)
                return True
        except Exception: pass
    return False

async def is_user_group_admin(bot, chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ['creator', 'administrator']
    except Exception:
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

# ===== 彻底解决拉群即崩溃的入口 =====
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        if chat_id < 0:
            # 1. 如果不是群管理，直接静默返回，绝不报错
            if not await is_user_group_admin(context.bot, chat_id, user_id):
                return
            # 2. 如果是群管理，但没有授权人在群，回复提示后返回
            if not await is_verified_bot_owner_admin(context.bot, chat_id):
                await update.message.reply_text("该群权限不足 联系 <a href=\"https://t.me/gsyxyc\">宫水</a>", parse_mode='HTML', disable_web_page_preview=True)
                return

        # 私聊或授权群，仅发送纯文本，不带任何按钮
        await update.message.reply_text(
            utils.get_text(user_id, 'main_msg', user_ui_lang),
            parse_mode='HTML',
            disable_web_page_preview=True
        )
    except Exception:
        # 极端情况下的终极兜底，防止任何意外抛出导致崩溃
        pass

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass # 按钮全部移除，此函数留空

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        chat_id = update.message.chat_id
        user_text = update.message.text
        
        if chat_id < 0:
            # 普通群员在群里发任何话，直接静默无视
            if not await is_user_group_admin(context.bot, chat_id, user_id):
                return
            # 群管在群里发指令，但没有授权人，直接静默无视
            if not await is_verified_bot_owner_admin(context.bot, chat_id):
                return
        
        if user_text == '主菜单':
            await show_menu(update, context)
            return
    except Exception:
        pass
