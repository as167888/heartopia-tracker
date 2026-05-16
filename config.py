import os

INVITE_CODE = "heartopia"
PROXY = os.environ.get("DISCORD_PROXY")  # 本地设置 http://127.0.0.1:7993，CI 不设
DATA_DIR = "data"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

API_URL = f"https://discord.com/api/v9/invites/{INVITE_CODE}?with_counts=true"

REQUEST_TIMEOUT = 15
