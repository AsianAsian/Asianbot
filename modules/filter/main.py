from telegram.ext import MessageHandler, filters, ContextTypes
from telegram import Update
from core.permissions import is_chat_admin
import yaml

async def filter_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_chat_admin(update, context):
        return
    if not update.effective_message.text:
        return
    with open("../config/config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    sensitive_words = config.get("module_settings", {}).get("filter", {}).get("sensitive_words", [])
    for word in sensitive_words:
        if word in update.effective_message.text:
            await update.effective_message.delete()
            await update.message.reply_text("❌ 消息包含敏感内容，已删除")
            break

def register(application):
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_message))