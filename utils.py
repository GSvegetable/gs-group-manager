from telegram import InlineKeyboardMarkup
from lang import UI_LANGUAGES

def get_text(user_id, key, user_ui_lang):
    lang_code = user_ui_lang.get(user_id, 'zh')
    return UI_LANGUAGES[lang_code].get(key, key)

# 返回 None，首页将不再显示任何按钮
def get_main_keyboard(user_id, user_ui_lang):
    return None
