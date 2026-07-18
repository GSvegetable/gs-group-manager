from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from lang import UI_LANGUAGES

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
