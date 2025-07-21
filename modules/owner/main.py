from telegram.ext import CommandHandler, ContextTypes
from telegram import Update
from core.permissions import is_bot_owner
import time

# 查看机器人加入的所有群组
async def list_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_bot_owner(update, context):
        await update.message.reply_text("❌ 仅机器人所有者可使用此命令")
        return
    
    db = context.bot_data.get("db")
    if not db:
        await update.message.reply_text("❌ 数据库连接失败")
        return
    
    try:
        chats = db.fetchall("""
            SELECT chat_id, chat_title, added_at 
            FROM chats 
            ORDER BY added_at DESC
        """)
        
        if not chats:
            await update.message.reply_text("🤖 机器人尚未加入任何群组")
            return
        
        message = ["📋 机器人已加入的群组："]
        for i, chat in enumerate(chats, 1):
            message.append(
                f"{i}. {chat['chat_title'] or '未知群组'}\n"
                f"   ID: {chat['chat_id']}\n"
                f"   加入时间: {chat['added_at'].split('.')[0]}"
            )
        
        # 处理长消息
        if len("\n".join(message)) > 4000:
            for i in range(0, len(message), 5):
                await update.message.reply_text("\n".join(message[i:i+5]))
                time.sleep(1)
        else:
            await update.message.reply_text("\n".join(message))
            
    except Exception as e:
        await update.message.reply_text(f"❌ 操作失败: {str(e)}")
        print(f"list_chats 错误: {e}")

# 向所有群组广播消息
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_bot_owner(update, context):
        await update.message.reply_text("❌ 仅机器人所有者可使用此命令")
        return
    
    if not context.args:
        await update.message.reply_text("用法: /broadcast 要发送的消息")
        return
    
    db = context.bot_data.get("db")
    if not db:
        await update.message.reply_text("❌ 数据库连接失败")
        return
    
    try:
        broadcast_msg = " ".join(context.args)
        chats = db.fetchall("SELECT chat_id FROM chats")
        
        if not chats:
            await update.message.reply_text("🤖 没有可发送的群组")
            return
        
        success = 0
        failed = 0
        progress_msg = await update.message.reply_text(f"正在向 {len(chats)} 个群组发送...")
        
        for chat in chats:
            try:
                await context.bot.send_message(
                    chat_id=chat["chat_id"],
                    text=f"📢 系统通知:\n{broadcast_msg}"
                )
                success += 1
            except:
                failed += 1
            time.sleep(0.5)
        
        await progress_msg.edit_text(
            f"广播完成!\n"
            f"✅ 成功: {success} 个群组\n"
            f"❌ 失败: {failed} 个群组"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ 操作失败: {str(e)}")
        print(f"broadcast 错误: {e}")

# 查看机器人统计信息
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_bot_owner(update, context):
        await update.message.reply_text("❌ 仅机器人所有者可使用此命令")
        return
    
    db = context.bot_data.get("db")
    if not db:
        await update.message.reply_text("❌ 数据库连接失败")
        return
    
    try:
        # 统计数据
        total_chats = len(db.fetchall("SELECT chat_id FROM chats"))
        total_users = len(db.fetchall("SELECT DISTINCT user_id FROM group_user_points"))
        total_checkins = sum(
            row["total_check_ins"] 
            for row in db.fetchall("SELECT total_check_ins FROM group_user_points")
        )
        
        await update.message.reply_text(
            f"📊 机器人统计信息\n"
            f"• 总群组数: {total_chats}\n"
            f"• 总用户数: {total_users}\n"
            f"• 总签到次数: {total_checkins}"
        )
        
    except Exception as e:
        await update.message.replyply_text(f"❌ 操作失败: {str(e)}")
        print(f"stats 错误: {e}")

# 注册所有者命令
def register(application):
    application.add_handler(CommandHandler("list_chats", list_chats))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("stats", stats))
