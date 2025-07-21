from telegram.ext import ChatMemberHandler, ContextTypes
from telegram import Update, ChatMember
from core.permissions import is_chat_admin
import yaml

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return
    new_member = update.effective_message.new_chat_members[0]
    with open("../config/config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    welcome_msg = config.get("module_settings", {}).get("welcome", {}).get("message", "欢迎 {user} 加入群组！")
    await update.effective_chat.send_message(welcome_msg.format(user=new_member.mention_html()), parse_mode="HTML")

def register(application):
    application.add_handler(ChatMemberHandler(welcome_new_member, ChatMemberHandler.CHAT_MEMBER))