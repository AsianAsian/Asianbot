from telegram.ext import CommandHandler, ContextTypes
from telegram import Update
from core.permissions import is_bot_owner
from core.database import Database

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_bot_owner(update, context):
        await update.message.reply_text("❌ 你不是机器人所有者")
        return
    db = context.bot_data["db"]
    total_chats = db.fetchone("SELECT COUNT(*) FROM chats WHERE bot_token = ?", (context.bot.token,))[0]
    # 后续可扩展统计用户数、消息数等，这里先简单示例
    await update.message.reply_text(f"📊 统计信息：\n- 群组总数：{total_chats}")

def register(application):
    application.add_handler(CommandHandler("stats", stats_command))