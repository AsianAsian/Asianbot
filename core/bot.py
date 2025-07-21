from telegram.ext import ApplicationBuilder
from core.module_manager import load_modules
# 删除不存在的 setup_owner_permissions 导入
from core.database import Database
from core.events import register_events
from dotenv import load_dotenv
from pathlib import Path
import os

def init_bot():
    # 获取项目根目录（core目录的上一级）
    project_root = Path(__file__).parent.parent
    
    # 构建.env文件的绝对路径
    env_path = project_root / "config" / ".env"
    
    # 加载环境变量
    load_dotenv(dotenv_path=env_path)
    
    # 添加调试输出
    print("加载的环境变量:")
    print(f"TELEGRAM_BOT_TOKEN: {os.getenv('TELEGRAM_BOT_TOKEN')}")
    print(f"OWNER_ID: {os.getenv('OWNER_ID')}")
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN 环境变量未设置")
    
    application = ApplicationBuilder().token(token).build()
    
    # 处理数据库路径（如果未设置则使用默认路径）
    db_path = os.getenv("DATABASE_PATH") or str(project_root / "data" / "bot.db")
    db = Database(db_path)
    application.bot_data["db"] = db
    
    # 存储所有者ID（转换为整数，方便后续权限判断）
    try:
        owner_id = int(os.getenv("OWNER_ID", ""))
        application.bot_data["owner_id"] = owner_id
    except ValueError:
        print("⚠️ OWNER_ID 格式错误，所有者功能可能无法使用")
        application.bot_data["owner_id"] = None
    
    # 加载模块和事件（删除 setup_owner_permissions 调用）
    load_modules(application)
    register_events(application)
    
    return application