import os
from telegram.ext import ApplicationBuilder
from core.database import Database
from core.module_manager import load_modules
from core.switch_chat import register_switch_chat
from core.main_menu import register_main_menu
from dotenv import load_dotenv
from pathlib import Path

def init_bot():
    project_root = Path(__file__).parent
    load_dotenv(dotenv_path=project_root / "config" / ".env")
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN 未设置！")
    application = ApplicationBuilder().token(token).build()
    db_path = os.getenv("DATABASE_PATH", "data/bot.db")
    db = Database(db_path)
    application.bot_data["db"] = db
    load_modules(application)  # 动态加载 modules/ 下的功能模块
    register_switch_chat(application)
    register_main_menu(application)
    return application

if __name__ == "__main__":
    app = init_bot()
    app.run_polling()