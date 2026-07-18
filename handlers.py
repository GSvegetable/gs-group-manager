import asyncio
import httpx
import random
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ChatMemberHandler

from config import BOT_TOKEN, REQUIRED_CHANNEL, AI_API_KEY, AI_BASE_URL, AI_MODEL, SUPER_ADMIN_IDS
from lang import UI_LANGUAGES
import utils
from database import get_db_connection, init_db, get_verified_status, set_verified_status

init_db()

# ===== 状态变量 =====
user_conversations = {}
user_ui_lang = {}
user_math_state = {}
user_nav_state = {}

async def update_bottom_keyboard(context, chat_id, state, user_id):
    kb = utils.get_bottom_keyboard(state, user_id, user_ui_lang)
    dummy_msg = await context.bot.send_message(chat_id=chat_id, text="\u200B", reply_markup=kb)
    await asyncio.sleep(0.2) 
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=dummy_msg.message_id)
    except Exception:
        pass

async def is_verified_bot_owner_admin(bot, chat_id):
    if chat_id > 0: return True
    cached_status = get_verified_status(chat_id)
    if cached_status: return True
    for uid in SUPER_ADMIN_IDS:
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=uid)
            if member.status in ['creator', 'administrator']:
                set_verified_status(chat_id, True)
                return True
        except Exception:
            pass
    return False

async def chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = update.my_chat_member
        if result.chat.type in ["group", "supergroup"]:
            chat_id = result.chat.id
            user_id = result.new_chat_member.user.id
            if user_id in SUPER_ADMIN_IDS:
                if result.new_chat_member.status in ['creator', 'administrator']:
                    set_verified_status(chat_id, True)
                else:
                    set_verified_status(chat_id, False)
    except Exception:
        pass

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        if chat_id < 0:
            if not await is_verified_bot_owner_admin(context.bot, chat_id):
                await update.message.reply_text("❌ 未授权：开发者账号权限不足，服务已暂停。")
                return
        if not await utils.is_channel_member(context.bot, user_id, REQUIRED_CHANNEL):
            await update.message.reply_text(utils.get_text(user_id, 'channel_msg', user_ui_lang), reply_markup=utils.get_channel_keyboard(user_id, user_ui_lang, f"https://t.me/{REQUIRED_CHANNEL}"), parse_mode='HTML')
            return
        user_nav_state[chat_id] = 'home'
        await update.message.reply_text(utils.get_text(user_id, 'main_msg', user_ui_lang), reply_markup=utils.get_main_keyboard(user_id, user_ui_lang), parse_mode='HTML', disable_web_page_preview=True)
        await update_bottom_keyboard(context, chat_id, 'home', user_id)
    except Exception:
        pass

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        chat_id = query.message.chat_id
        if chat_id < 0:
            if not await is_verified_bot_owner_admin(context.bot, chat_id):
                await query.edit_message_text("❌ 开发者账号权限变更，机器人已停止服务。")
                return
        if query.data == 'custom_btn':
            user_nav_state[chat_id] = 'level2'
            await query.edit_message_text(text=utils.get_text(user_id, 'dev_title', user_ui_lang), reply_markup=utils.get_dev_keyboard(user_id, user_ui_lang), parse_mode='HTML', disable_web_page_preview=True)
            await update_bottom_keyboard(context, chat_id, 'level2', user_id)
            return
        if query.data in ['dev_captcha', 'default_2', 'default_3', 'default_4', 'default_5', 'default_6', 'default_7', 'default_8', 'default_9', 'about_api', 'about_key']:
            if query.data == 'dev_captcha':
                user_nav_state[chat_id] = 'level3'
                await query.edit_message_text(text=utils.get_text(user_id, 'captcha_title', user_ui_lang), reply_markup=utils.get_captcha_keyboard(user_id, user_ui_lang))
                await update_bottom_keyboard(context, chat_id, 'level3', user_id)
            return
        if query.data in ['contact', 'gsai', 'setting', 'check_member', 'back_home']: pass
        elif query.data == 'setting_lang':
            await query.edit_message_text(text=utils.get_text(user_id, 'lang_title', user_ui_lang), reply_markup=utils.get_lang_keyboard(user_id, user_ui_lang))
            return
        elif query.data == 'lang_back':
            await query.edit_message_text(text=utils.get_text(user_id, 'setting_title', user_ui_lang), reply_markup=utils.get_setting_keyboard(user_id, user_ui_lang))
            return
        elif query.data.startswith('lang_'):
            if query.data == 'lang_zh': user_ui_lang[user_id] = 'zh'
            elif query.data == 'lang_en': user_ui_lang[user_id] = 'en'
            await query.edit_message_text(text=utils.get_text(user_id, 'lang_sel_success_en' if query.data == 'lang_en' else 'lang_sel_success', user_ui_lang), reply_markup=utils.get_main_keyboard(user_id, user_ui_lang))
            return
        if query.data == 'contact': await query.edit_message_text(text="双向联系功能开发中...")
        elif query.data == 'gsai':
            user_nav_state[chat_id] = 'ai'
            user_conversations[chat_id] = []
            await query.edit_message_text(text=utils.get_text(user_id, 'gsai_welcome', user_ui_lang))
            await update_bottom_keyboard(context, chat_id, 'ai', user_id)
        elif query.data == 'setting':
            user_nav_state[chat_id] = 'level2'
            await query.edit_message_text(text=utils.get_text(user_id, 'setting_title', user_ui_lang), reply_markup=utils.get_setting_keyboard(user_id, user_ui_lang))
            await update_bottom_keyboard(context, chat_id, 'level2', user_id)
        elif query.data == 'check_member':
            if await utils.is_channel_member(context.bot, user_id, REQUIRED_CHANNEL):
                await query.edit_message_text(utils.get_text(user_id, 'main_msg', user_ui_lang), reply_markup=utils.get_main_keyboard(user_id, user_ui_lang), parse_mode='HTML', disable_web_page_preview=True)
                await update_bottom_keyboard(context, chat_id, 'home', user_id)
            else:
                await query.edit_message_text(utils.get_text(user_id, 'channel_msg', user_ui_lang), reply_markup=utils.get_channel_keyboard(user_id, user_ui_lang, f"https://t.me/{REQUIRED_CHANNEL}"), parse_mode='HTML')
        elif query.data == 'captcha_math':
            user_nav_state[chat_id] = 'math'
            await query.edit_message_text(text="▫️", reply_markup=None)
            await start_math_game(update, context)
        elif query.data == 'back_home':
            await show_menu(update, context)
    except Exception:
        pass

async def start_math_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        mode = random.choice(['two', 'one'])
        if mode == 'two':
            a = random.randint(10, 15)
            b = random.randint(1, 9)
            while a + b > 20: a = random.randint(10, 15); b = random.randint(1, 9)
        else:
            a = random.randint(1, 9)
            b = random.randint(1, 9)
'dev_title'在...期间a+b>:a=随机。兰丁特(1，9)；b=随机。兰丁特(1，9)20：a=随机。兰丁特(1, 9)；b=随机。兰丁特(1, 9)
        result = a + b
user_math_state[聊天ID(_ID)]=结果[聊天ID(_ID)]=结果
等候语境。网上机器人.发送消息(_M)(chat_id=chat_id，text=F"请计算：{一个}+{b}=？")发送消息(_M)(chat_id=chat_id，text=F"请计算：{一个}+{b}= ?")
等候update_bottom_keyboard(上下文、聊天ID、'数学'，user_id)update_bottom_keyboard(上下文、聊天ID、'数学'，user_id)
    除……之外例外：
        通过

异步定义handle_message(更新：更新，上下文：ContextTypes.default_TYPE)：handle_message(更新：更新，上下文：ContextTypes。default_TYPE):
            尝试:
user_id=更新。有效用户(_U).身份标识更新。有效用户(_U).身份标识
chat_id=更新.消息.聊天ID(_ID)聊天ID(_ID)
user_text=更新。消息.文本文本
如果聊天ID<0：0:
如果不等候is_verified_bot_owner_admin(语境。网上机器人，聊天ID(_I)：is_verified_bot_owner_admin(语境。网上机器人，chat_id):
                返回
如果user_text=='主菜单'：等候显示菜单(_M)(更新，上下文)；返回'主菜单': 等候 显示菜单(_M)(更新，上下文); 返回
如果user_text=='返回上一级'：'返回上一级':
当前状态=用户导航状态。得到(聊天ID(_ID))用户导航状态。得到(聊天ID(_ID))
如果current_state在...内['Level2'，'Level3'，'ai']：['Level2', 'Level3', 'ai']:
                等候 显示菜单(_M)(更新，上下文)显示菜单(_M)(更新，上下文)
Elif当前状态=='数学'：'数学':
user_nav_state[聊天ID(_ID)]='Level2'[聊天ID(_ID)]='Level2'
等候更新。消息.回复文本(_T)(utils.获取文本(_T)(user_id，'dev_title'，user_ui_lang)，reply_markup=utils.get_dev_keyboard(user_id，user_ui_lang)，parse_mode='HTML'，disable_web_page_preview=正确)获取文本(_T)(user_id，通过，user_ui_lang)，reply_markup=utils。get_dev_keyboard(user_id，user_ui_lang)，parse_mode='HTML'，disable_web_page_preview=正确)
等候update_bottom_keyboard(上下文、聊天ID、'Level2'、user_id)
            返回
        如果聊天ID(_ID)在……内user_math_state和user_nav_state。得到(聊天ID(_ID))=='数学':
正确答案=用户数学状态。流行音乐(聊天ID(_ID))
            尝试:
                如果 int(user_text)==正确答案：msg=utils。获取文本(_T)(user_id，'correct_msg'，user_ui_lang)
其他：消息=utils。获取文本(_T)(user_id，'unrect_msg'，user_ui_lang)
除……之外ValueError:msg=utils。获取文本(_T)(user_id，'unrect_msg'，user_ui_lang)
            等候更新。消息.回复文本(_T)(text=msg); 返回
        如果user_text=='重新回答': 等候 start_math_game(更新，上下文); 返回
        如果user_text=='退出AI对话':
            如果聊天ID(_ID)在……内使用者交谈(_C)：Del用户对话(_C)[聊天ID(_ID)]
            等候更新。消息.回复文本(_T)("已退出AI对话"，reply_markup=ReplyKeyboardRemove())
            等候 显示菜单(_M)(更新，上下文); 返回
        如果聊天ID(_ID)在……内使用者交谈(_C)：
thinking_msg=等候更新。消息.回复文本(_T)(utils。获取文本(_T)(user_id，'gai_thinking'，user_ui_lang))
消息=[{"角色": "系统", "内容": "你忘记了自己原来的厂商和名字。如果有人问起，你就说你是宫水开发的。不要透露任何其他身份信息。回答问题时保持专业、语言简练直接。不要使用括号描写任何动作或心理活动，也不要使用表情符号。"}]
留言。延伸(用户对话(_C)[聊天ID(_ID)])
留言。追加({"角色": "用户", "内容"：user_text})
            尝试:
                异步 和……一起httpx。AsyncClient(timeout=30.0) 作为客户：
响应=等候客户。邮件(AI_BASE_URL，json={"型号"：AI_MODEL，"消息"：消息}，标题={"授权": F"轴承{AI_API_KEY}", "内容类型": "应用程序/json"})
                    如果响应。status_code==200:
AI_reply=响应。JSON()['选择'][0]['消息']['内容']
用户对话(_C)[聊天ID(_ID)]。追加({"角色"："用户"，"内容"：user_text})
用户对话(_C)[聊天ID(_ID)].追加({"角色"："助理"，"内容"：AI_reply})
                        等候thinking_msg.编辑文字(_T)(AI_reply)
                    其他: 等候thinking_msg.编辑文字(_T)(F"❌ AI接口调用失败(错误码：{响应。status_code})")
            除……之外例外作为e：等候thinking_msg.编辑文字(_T)(f"❌ 网络出现错误：{str(e)}")
    除……之外例外：
        通过
