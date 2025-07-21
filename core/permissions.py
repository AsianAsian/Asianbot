from telegram.ext import ContextTypes
from telegram import Update
import os

async def is_bot_owner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """验证用户是否为机器人所有者"""
    if not update.effective_user:
        return False
        
    # 从环境变量获取所有者ID
    owner_id = os.getenv("OWNER_ID")
    if not owner_id:
        return False
        
    try:
        return update.effective_user.id == int(owner_id)
    except ValueError:
        return False

async def is_chat_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """验证用户是否为群组管理员"""
    if update.effective_chat.type == "private":
        return False
        
    try:
        admin = await update.effective_chat.get_member(update.effective_user.id)
        return admin.status in ["administrator", "creator"]
    except Exception:
        return False
