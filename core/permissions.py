import os
import asyncio
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

# 从环境变量获取机器人所有者ID
OWNER_ID = os.getenv("OWNER_ID")
if OWNER_ID:
    OWNER_ID = int(OWNER_ID)

def admin_required(func):
    """检查用户是否为群组管理员的装饰器"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # 检查是否在群组中
        if not update.effective_chat or not update.effective_chat.type in ["group", "supergroup"]:
            await update.effective_message.reply_text("此命令仅能在群组中使用！")
            return None
        
        # 检查用户是否为管理员
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # 获取管理员列表
        admins = await context.bot.get_chat_administrators(chat_id)
        admin_ids = [admin.user.id for admin in admins]
        
        if user_id in admin_ids or (OWNER_ID and user_id == OWNER_ID):
            return await func(update, context, *args, **kwargs)
        else:
            await update.effective_message.reply_text("你没有权限执行此操作！需要管理员权限。")
            return None
    return wrapper

def owner_required(func):
    """检查用户是否为机器人所有者的装饰器"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not OWNER_ID:
            await update.effective_message.reply_text("未配置机器人所有者！")
            return None
            
        user_id = update.effective_user.id
        if user_id == OWNER_ID:
            return await func(update, context, *args, **kwargs)
        else:
            await update.effective_message.reply_text("你没有权限执行此操作！仅所有者可使用。")
            return None
    return wrapper

async def is_chat_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """检查用户是否为当前聊天的管理员"""
    if not update.effective_chat or not update.effective_chat.type in ["group", "supergroup"]:
        return False
        
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    admins = await context.bot.get_chat_administrators(chat_id)
    admin_ids = [admin.user.id for admin in admins]
    
    return user_id in admin_ids or (OWNER_ID and user_id == OWNER_ID)

async def is_bot_owner(user_id: int) -> bool:
    """检查用户是否为机器人所有者"""
    if not OWNER_ID:
        return False
    return user_id == OWNER_ID
    