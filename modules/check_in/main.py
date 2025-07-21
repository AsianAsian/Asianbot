from telegram.ext import CommandHandler, filters, ContextTypes
from telegram import Update
from core.database import Database
import time

def register(application):
    """注册签到相关命令"""
    application.add_handler(CommandHandler(
        "check_in", 
        check_in_command, 
        filters=~filters.UpdateType.EDITED_MESSAGE
    ))
    application.add_handler(CommandHandler(
        "points", 
        points_command, 
        filters=~filters.UpdateType.EDITED_MESSAGE
    ))
    application.add_handler(CommandHandler(
        "leaderboard", 
        leaderboard_command, 
        filters=~filters.UpdateType.EDITED_MESSAGE
    ))
    print("✅ 签到模块已加载，命令: ['check_in', 'points', 'leaderboard']")

async def check_in_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """每日签到获取积分"""
    if not update.effective_message or not update.effective_user or not update.effective_chat:
        return
    
    user = update.effective_user
    chat = update.effective_chat
    db: Database = context.bot_data.get("db")
    if not db:
        await update.effective_message.reply_text("❌ 数据库未初始化，无法签到")
        return
    
    # 检查今日是否已签到
    today = time.strftime("%Y-%m-%d")
    check_in_record = await db.fetchone(
        "SELECT * FROM check_ins WHERE user_id = ? AND chat_id = ? AND date = ?",
        (user.id, chat.id, today)
    )
    
    if check_in_record:
        await update.effective_message.reply_text("你今天已经签过到啦！明天再来吧～")
        return
    
    # 计算连续签到天数
    yesterday = time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400))
    last_check_in = await db.fetchone(
        "SELECT streak FROM check_ins WHERE user_id = ? AND chat_id = ? AND date = ?",
        (user.id, chat.id, yesterday)
    )
    streak = last_check_in["streak"] + 1 if last_check_in else 1
    streak = min(streak, 7)  # 最大连续签到奖励为7天
    
    # 计算积分（基础10分+连续奖励）
    base_points = 10
    bonus = 5 * (streak - 1)
    total_points = base_points + bonus
    
    # 保存签到记录
    await db.execute(
        "INSERT INTO check_ins (user_id, chat_id, date, points, streak) VALUES (?, ?, ?, ?, ?)",
        (user.id, chat.id, today, total_points, streak)
    )
    
    # 更新用户总积分
    await db.execute(
        "INSERT OR IGNORE INTO user_points (user_id, chat_id, points) VALUES (?, ?, 0)",
        (user.id, chat.id)
    )
    await db.execute(
        "UPDATE user_points SET points = points + ? WHERE user_id = ? AND chat_id = ?",
        (total_points, user.id, chat.id)
    )
    
    await update.effective_message.reply_text(
        f"✅ 签到成功！\n"
        f"获得 {total_points} 积分（基础 {base_points} + 连续签到奖励 {bonus}）\n"
        f"当前连续签到 {streak} 天"
    )

async def points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看我的积分"""
    if not update.effective_message or not update.effective_user or not update.effective_chat:
        return
    
    user = update.effective_user
    chat = update.effective_chat
    db: Database = context.bot_data.get("db")
    if not db:
        await update.effective_message.reply_text("❌ 数据库未初始化")
        return
    
    user_points = await db.fetchone(
        "SELECT points FROM user_points WHERE user_id = ? AND chat_id = ?",
        (user.id, chat.id)
    )
    
    if not user_points or user_points["points"] == 0:
        await update.effective_message.reply_text("你当前的积分为 0，赶紧签到获取吧～")
    else:
        await update.effective_message.reply_text(f"你的当前积分为：{user_points['points']}")

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看积分排行榜"""
    if not update.effective_message or not update.effective_chat:
        return
    
    chat = update.effective_chat
    db: Database = context.bot_data.get("db")
    if not db:
        await update.effective_message.reply_text("❌ 数据库未初始化")
        return
    
    top_users = await db.fetchall(
        "SELECT user_id, points FROM user_points WHERE chat_id = ? ORDER BY points DESC LIMIT 10",
        (chat.id,)
    )
    
    if not top_users:
        await update.effective_message.reply_text("暂无积分记录，大家快来签到吧～")
        return
    
    leaderboard = "🏆 积分排行榜（前10名）\n\n"
    for i, record in enumerate(top_users, 1):
        try:
            user = await context.bot.get_chat(record["user_id"])
            leaderboard += f"{i}. {user.mention_html()} - {record['points']} 积分\n"
        except Exception:
            leaderboard += f"{i}. [未知用户] - {record['points']} 积分\n"
    
    await update.effective_message.reply_text(leaderboard, parse_mode="HTML")
