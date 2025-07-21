import asyncio
from telegram.ext import CommandHandler, filters, ContextTypes
from telegram import Update
from core.permissions import owner_required
from core.database import Database
import time

def register(application):
    """注册所有者命令"""
    application.add_handler(CommandHandler(
        "list_chats", 
        list_chats_command, 
        filters=~filters.UpdateType.EDITED_MESSAGE
    ))
    application.add_handler(CommandHandler(
        "broadcast", 
        broadcast_command, 
        filters=~filters.UpdateType.EDITED_MESSAGE
    ))
    application.add_handler(CommandHandler(
        "stats", 
        stats_command, 
        filters=~filters.UpdateType.EDITED_MESSAGE
    ))
    print("✅ 已加载模块: owner")

@owner_required
async def list_chats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看机器人加入的所有群组"""
    if not update.effective_message:
        return
    
    db: Database = context.bot_data.get("db")
    if not db:
        await update.effective_message.reply_text("❌ 数据库未初始化")
        return
    
    chats = await db.fetchall("SELECT chat_id, chat_name FROM chats")
    if not chats:
        await update.effective_message.reply_text("🤖 尚未加入任何群组")
        return
    
    text = "📝 机器人加入的群组列表：\n\n"
    for chat in chats:
        text += f"• {chat['chat_name']}（ID: {chat['chat_id']}）\n"
    
    await update.effective_message.reply_text(text)

@owner_required
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """向所有群组发送广播"""
    if not update.effective_message or not context.args:
        await update.effective_message.reply_text("用法：/broadcast [消息内容]")
        return
    
    message = " ".join(context.args)
    db: Database = context.bot_data.get("db")
    if not db:
        await update.effective_message.reply_text("❌ 数据库未初始化")
        return
    
    chats = await db.fetchall("SELECT chat_id FROM chats")
    success = 0
    failed = 0
    
    for chat in chats:
        try:
            await context.bot.send_message(chat_id=chat["chat_id"], text=message)
            success += 1
            await asyncio.sleep(0.5)  # 避免触发频率限制
        except Exception:
            failed += 1
    
    await update.effective_message.reply_text(
        f"📢 广播完成：\n成功发送到 {success} 个群组\n失败 {failed} 个群组"
    )

@owner_required
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看机器人统计信息"""
    if not update.effective_message:
        return
    
    db: Database = context.bot_data.get("db")
    if not db:
        await update.effective_message.reply_text("❌ 数据库未初始化")
        return
    
    chat_count = await db.fetchone("SELECT COUNT(*) as cnt FROM chats") or {"cnt": 0}
    user_count = await db.fetchone("SELECT COUNT(*) as cnt FROM users") or {"cnt": 0}
    check_in_count = await db.fetchone("SELECT COUNT(*) as cnt FROM check_ins") or {"cnt": 0}
    
    # 计算运行时间
    start_time = context.bot_data.get("start_time", time.time())
    run_time = time.time() - start_time
    days, remainder = divmod(int(run_time), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60
    
    stats_text = "📊 机器人统计信息\n\n"
    stats_text += f"加入群组数：{chat_count['cnt']}\n"
    stats_text += f"用户总数：{user_count['cnt']}\n"
    stats_text += f"累计签到次数：{check_in_count['cnt']}\n"
    stats_text += f"运行时间：{days}天{hours}时{minutes}分"
    
    await update.effective_message.reply_text(stats_text)
