from telegram import Update, ChatMember
from telegram.ext import ChatMemberHandler, ContextTypes
from core.permissions import is_bot_owner

async def handle_bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.my_chat_member:
        return
    new_status = update.my_chat_member.new_chat_member.status
    if new_status == ChatMember.MEMBER:
        chat = update.effective_chat
        if not chat:
            return
        db = context.bot_data["db"]
        # 插入或忽略已存在的群组信息
        db.execute(
            "INSERT OR IGNORE INTO chats (bot_token, chat_id, chat_title) VALUES (?, ?, ?)",
            (context.bot.token, chat.id, chat.title)
        )
        owner_id = context.bot_data["owner_id"]
        await context.bot.send_message(
            chat_id=owner_id,
            text=f"🚨 机器人被添加到新群组：\n名称：{chat.title}\nID：{chat.id}"
        )

def register_events(application):
    application.add_handler(
        ChatMemberHandler(handle_bot_added, ChatMemberHandler.MY_CHAT_MEMBER)
    )