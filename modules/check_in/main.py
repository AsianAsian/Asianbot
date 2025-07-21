from telegram.ext import CommandHandler, ContextTypes
from telegram import Update
from datetime import datetime

# 1. 签到命令（必须在群组内，且用当前群的积分表）
async def check_in(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 禁止私聊使用
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ 签到只能在群组里玩哦！")
        return
    
    # 获取当前群组ID和用户ID（关键：绑定到当前群）
    group_id = update.effective_chat.id
    user_id = update.effective_user.id
    db = context.bot_data["db"]
    
    # 2. 检查当前群是否开启签到功能（读取群组独立设置）
    group_settings = db.get_group_settings(group_id)
    if not group_settings["checkin_enabled"]:
        await update.message.reply_text("❌ 本群未开启签到功能~")
        return
    
    # 3. 读取用户在【当前群】的积分数据（用新的数据库方法）
    user_data = db.get_group_user_points(group_id, user_id)
    
    # 4. 检查是否已签到（逻辑不变，但数据是当前群的）
    today = datetime.now().strftime("%Y-%m-%d")
    if user_data["last_check_in"] == today:
        await update.message.reply_text(
            f"你今天已经签到过啦！\n"
            f"当前积分：{user_data['points']}\n"
            f"连续签到：{user_data['consecutive_days']} 天"
        )
        return
    
    # 5. 计算奖励（用当前群的独立设置，比如基础积分、连续奖励）
    base_reward = group_settings["checkin_base_reward"]
    consecutive_bonus = group_settings["checkin_consecutive_bonus"]
    max_bonus = group_settings["checkin_max_bonus"]
    
    # 计算连续签到奖励
    current_consecutive = user_data["consecutive_days"]
    bonus = min(current_consecutive * consecutive_bonus, max_bonus)
    
    # 计算特殊奖励（比如连续7天额外奖励，从群设置读取）
    special_reward = 0
    special_rewards = group_settings["checkin_special_rewards"].split(",")
    for item in special_rewards:
        if ":" in item:
            days, reward = item.split(":")
            if current_consecutive + 1 == int(days):
                special_reward = int(reward)
                break
    
    total_reward = base_reward + bonus + special_reward
    
    # 6. 更新【当前群】的积分（用新的数据库方法）
    db.update_group_user_points(group_id, user_id, total_reward, "签到")
    
    # 7. 回复结果（显示当前群的积分）
    updated_data = db.get_group_user_points(group_id, user_id)
    await update.message.reply_text(
        f"签到成功！🎉\n"
        f"获得积分：{total_reward}\n"
        f"当前积分：{updated_data['points']}\n"
        f"连续签到：{updated_data['consecutive_days']} 天"
    )

# 2. 查看积分命令（只显示当前群的积分）
async def points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ 查积分只能在群组里哦！")
        return
    
    group_id = update.effective_chat.id
    user_id = update.effective_user.id
    db = context.bot_data["db"]
    
    # 读取当前群的积分数据
    user_data = db.get_group_user_points(group_id, user_id)
    await update.message.reply_text(
        f"你的积分情况📊\n"
        f"当前积分：{user_data['points']}\n"
        f"连续签到：{user_data['consecutive_days']} 天\n"
        f"总签到次数：{user_data['total_check_ins']}"
    )

# 3. 排行榜命令（只显示当前群的排名）
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ 排行榜只能在群组里看哦！")
        return
    
    group_id = update.effective_chat.id
    db = context.bot_data["db"]
    
    # 读取当前群的排行榜（只取本群数据）
    top_users = db.get_group_top_users(group_id, 10)
    if not top_users:
        await update.message.reply_text("本群还没人签到呢，快来抢第一！")
        return
    
    message = [f"🏆 {update.effective_chat.title} 积分排行榜"]
    for rank, user in enumerate(top_users, 1):
        # 显示当前群内的用户名
        try:
            member = await context.bot.get_chat_member(group_id, user["user_id"])
            username = member.user.mention_html()  # @用户
        except:
            username = f"用户{user['user_id']}"
        message.append(f"{rank}. {username}：{user['points']} 积分")
    
    await update.message.reply_text("\n".join(message), parse_mode="HTML")

# 4. 注册命令（保持不变）
def register(application):
    application.add_handler(CommandHandler("check_in", check_in))
    application.add_handler(CommandHandler("points", points))
    application.add_handler(CommandHandler("leaderboard", leaderboard))

# 帮助文本
HELP_TEXT = """
🔸 签到系统：
/check_in - 每日签到获取积分
/points - 查看我的积分
/leaderboard - 查看积分排行榜
"""

def register(application):
    from modules.help.main import HELP_MESSAGES
    HELP_MESSAGES["check_in"] = HELP_TEXT
    
    application.add_handler(CommandHandler("check_in", check_in))
    application.add_handler(CommandHandler("points", points))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    
    # 添加调试输出，确认模块加载
    print("✅ 签到模块已加载，命令:", ["check_in", "points", "leaderboard"])