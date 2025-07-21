from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from telegram import Update
from core.database import Database

async def add_auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.bot_data.get("current_chat")
    if not chat_id:
        await update.message.reply_text("请先 /switch_chat 选择群组！")
        return
    if len(context.args) < 2:
        await update.message.reply_text("用法：/auto_reply_add 关键词 回复内容")
        return
    keyword = context.args[0]
    reply = " ".join(context.args[1:])
    db: Database = context.bot_data["db"]
    config = db.get_config(chat_id, "auto_reply")
    config["rules"][keyword] = reply
    db.save_config(chat_id, "auto_reply", config)
    await update.message.reply_text(f"已添加自动回复：{keyword} → {reply}")

async def list_auto_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.bot_data.get("current_chat")
    if not chat_id:
        await update.message.reply_text("请先 /switch_chat 选择群组！")
        return
    db: Database = context.bot_data["db"]
    config = db.get_config(chat_id, "auto_reply")
    if not config["rules"]:
        await update.message.reply_text("暂无自动回复规则")
        return
    reply_text = "自动回复规则：\n"
    for keyword, reply in config["rules"].items():
        reply_text += f"{keyword} → {reply}\n"
    await update.message.reply_text(reply_text)

async def auto_reply_listener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.bot_data.get("current_chat", update.effective_chat.id)
    db: Database = context.bot_data["db"]
    config = db.get_config(chat_id, "auto_reply")
    message_text = update.message.text
    for keyword, reply in config["rules"].items():
        if keyword in message_text:
            await update.message.reply_text(reply)
            break

def register(application):
    application.add_handler(CommandHandler("auto_reply_add", add_auto_reply))
    application.add_handler(CommandHandler("auto_reply_list", list_auto_replies))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply_listener))