import os
import logging
import asyncio
from platform import system
from telegram.ext import ApplicationBuilder
from core.database import Database
from core.module_manager import load_modules
from core.switch_chat import register_switch_chat
from core.main_menu import register_main_menu
from dotenv import load_dotenv
from pathlib import Path

# 针对Windows系统设置事件循环策略，解决循环关闭问题
if system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def init_bot():
    project_root = Path(__file__).parent
    load_dotenv(dotenv_path=project_root / "config" / ".env")
    
    # 配置日志
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN 未设置！")
    
    application = ApplicationBuilder().token(token).build()
    
    # 数据库路径处理（确保目录存在）
    db_path = os.getenv("DATABASE_PATH", "data/bot.db")
    db_dir = os.path.dirname(db_path)
    os.makedirs(db_dir, exist_ok=True)  # 自动创建数据库目录
    db = Database(db_path)
    application.bot_data["db"] = db
    
    # 动态加载模块
    load_modules(application)
    
    register_switch_chat(application)
    register_main_menu(application)
    
    # 输出机器人信息
    try:
        bot_info = await application.bot.get_me()
        print(f"📌 机器人信息：{bot_info.first_name}（@{bot_info.username}，ID: {bot_info.id}）")
    except Exception as e:
        print(f"⚠️ 获取机器人信息失败：{str(e)}")
    
    return application

async def main():
    app = await init_bot()
    print("🤖 机器人启动成功！正在运行中...（按 Ctrl+C 停止）")
    try:
        # 显式管理应用生命周期
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        # 保持运行直到被中断
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n⏹️ 正在停止机器人...")
    finally:
        # 确保资源正确释放
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ 机器人启动失败：{str(e)}")
        exit(1)
    