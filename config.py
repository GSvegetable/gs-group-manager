import os

# 1. 你的机器人 Token
BOT_TOKEN = "8961214660:AAFK-0EN0ztZENLB08Q5vG_IDjTAk6cBMNo"

# 2. 你的开发者 ID（必须是这两个 ID 之一在群里当管理员）
SUPER_ADMIN_IDS = [7857605443, 7867520461]

# ==================================================
# 3. 下面这些是防止程序报错补全的变量，代码里用到了就得写上。
# （如果你不需要 AI 功能或者强制入群，填默认值占位即可，保证程序不崩就行）
# ==================================================

REQUIRED_CHANNEL = "gs0z1"    # 你的频道号，不用可以随便填
ADMIN_CHAT_ID = 7857605443    # 你的数字 ID
AI_API_KEY = "sk-258fd45a189545d6b0d2b383f14094a9" # AI 的 key，如果不用就放着
AI_BASE_URL = "https://api.deepseek.com/chat/completions"
AI_MODEL = "deepseek-chat"
