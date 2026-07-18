import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from lang import UI_LANGUAGES
from config import SUPER_ADMIN_IDS
from database import get_db_connection

def get_text(user_id, key, user_ui_lang):
    """获取多语言文本"""
    lang = user_ui_lang.get(user_id, 'zh')
    texts = UI_LANGUAGES.get(lang, UI_LANGUAGES['zh'])
    return texts.get(key, f"[缺失文本: {key}]")

def get_main_keyboard(user_id, user_ui_lang):
    keyboard = [[InlineKeyboardButton("群管面板", callback_data='panel')]]
    return InlineKeyboardMarkup(keyboard)

def get_panel_keyboard(user_id, user_ui_lang):
    keyboard = [
        [InlineKeyboardButton("欢迎语设置", callback_data='welcome'), InlineKeyboardButton("广告触发词", callback_data='triggers')],
        [InlineKeyboardButton("定时群发", callback_data='tasks'), InlineKeyboardButton("管理员设置", callback_data='admins')],
        [InlineKeyboardButton("返回主菜单", callback_data='back_home')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_panel_keyboard(user_id, user_ui_lang):
    keyboard = [[InlineKeyboardButton("返回上一级", callback_data='back_level')]]
    return InlineKeyboardMarkup(keyboard)

def get_dev_keyboard(user_id, user_ui_lang):
    keyboard = [
        [InlineKeyboardButton("验证码设置", callback_data='dev_captcha')],
        [InlineKeyboardButton("返回上一级", callback_data='back_level')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_captcha_keyboard(user_id, user_ui_lang):
    keyboard = [
        [InlineKeyboardButton("数学验证码", callback_data='captcha_math')],
        [InlineKeyboardButton("返回上一级", callback_data='back_level')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_setting_keyboard(user_id, user_ui_lang):
    keyboard = [
        [InlineKeyboardButton("语言设置", callback_data='setting_lang')],
        [InlineKeyboardButton("返回主菜单", callback_data='back_home')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_lang_keyboard(user_id, user_ui_lang):
    keyboard = [
        [InlineKeyboardButton("中文 🇨🇳", callback_data='lang_zh'), InlineKeyboardButton("English 🇺🇸", callback_data='lang_en')],
        [InlineKeyboardButton("返回上一级", callback_data='lang_back')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_channel_keyboard(user_id, user_ui_lang, channel_url):
    keyboard = [[InlineKeyboardButton("加入频道", url=channel_url)]]
    return InlineKeyboardMarkup(keyboard)

def get_bottom_keyboard(state, user_id, user_ui_lang):
    """获取底部键盘"""
    if state == 'ai':
        keyboard = [[InlineKeyboardButton("退出 AI 对话", callback_data='exit_ai')]]
    elif state == 'math':
        keyboard = [[InlineKeyboardButton("重新回答", callback_data='restart_math'), InlineKeyboardButton("返回上一级", callback_data='back_level')]]
    else:
        keyboard = [[InlineKeyboardButton("返回主菜单", callback_data='back_home')]]
    return InlineKeyboardMarkup(keyboard)

async def is_channel_member(bot, user_id, channel):
    """检查用户是否加入频道"""
    try:
        member = await bot.get_chat_member(chat_id=f"@{channel}", user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def get_triggers_keyboard(user_id, user_ui_lang):
    keyboard = [
        [InlineKeyboardButton("新增触发词", callback_data='add_trigger')],
        [InlineKeyboardButton("删除触发词", callback_data='del_trigger')],
        [InlineKeyboardButton("返回上一级", callback_data='back_level')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_tasks_keyboard(user_id, user_ui_lang):
    keyboard = [
        [InlineKeyboardButton("新增定时任务", callback_data='add_task')],
        [InlineKeyboardButton("返回上一级", callback_data='back_level')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admins_keyboard(user_id, user_ui_lang):
    keyboard = [
        [InlineKeyboardButton("新增管理员", callback_data='add_admin')],
        [InlineKeyboardButton("删除管理员", callback_data='del_admin')],
        [InlineKeyboardButton("返回上一级", callback_data='back_level')]
    ]
    return InlineKeyboardMarkup(keyboard)

# 权限检查核心函数
async def check_permission(user_id, group_id, db_pool):
    if user_id in SUPER_ADMIN_IDS:
        return True
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT admin_ids FROM groups WHERE group_id = %s", (group_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if row:
        admins = json.loads(row[0])
        return str(user_id) in admins
    return False
