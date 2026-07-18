from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from lang import UI_LANGUAGES

def get_text(user_id, key, user_ui_lang):
    lang_code = user_ui_lang.get(user_id, 'zh')
    return UI_LANGUAGES[lang_code].get(key, key)

# ===== 【第一层】群组选择列表 =====
def get_group_selection_keyboard(user_id, user_ui_lang, group_ids):
    if not group_ids:
        return None
    keyboard = []
    for gid in group_ids:
        # 给每个群组做一个按钮，callback 前缀为 group_
        keyboard.append([InlineKeyboardButton(f"群组 {gid}", callback_data=f"group_{gid}")])
    return InlineKeyboardMarkup(keyboard)

# ===== 【第二层】四个功能按钮面板 =====
def get_level2_keyboard(user_id, user_ui_lang):
    keyboard = [
        [InlineKeyboardButton(get_text(user_id, 'welcome_btn', user_ui_lang), callback_data='welcome_btn')],
        [InlineKeyboardButton(get_text(user_id, 'timed_msg_btn', user_ui_lang), callback_data='timed_msg_btn')],
        [InlineKeyboardButton(get_text(user_id, 'keyword_btn', user_ui_lang), callback_data='keyword_btn')],
        [InlineKeyboardButton(get_text(user_id, 'captcha_btn', user_ui_lang), callback_data='captcha_btn')],
        [InlineKeyboardButton(get_text(user_id, 'back_home', user_ui_lang), callback_data='back_home')]
    ]
    return InlineKeyboardMarkup(keyboard)
