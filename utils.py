from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from lang import UI_LANGUAGES

def get_text(user_id, key, user_ui_lang):
    lang_code = user_ui_lang.get(user_id, 'zh')
    return UI_LANGUAGES[lang_code].get(key, key)

# 第一层主页的按钮（竖直排列）
def get_main_keyboard(user_id, user_ui_lang):
    keyboard = [
        [InlineKeyboardButton(get_text(user_id, 'welcome_btn', user_ui_lang), callback_data='welcome_btn')],
        [InlineKeyboardButton(get_text(user_id, 'timed_msg_btn', user_ui_lang), callback_data='timed_msg_btn')],
        [InlineKeyboardButton(get_text(user_id, 'keyword_btn', user_ui_lang), callback_data='keyword_btn')],
        [InlineKeyboardButton(get_text(user_id, 'captcha_btn', user_ui_lang), callback_data='captcha_btn')]
    ]
    return InlineKeyboardMarkup(keyboard)
