from telegram.ext import CommandHandler, filters, ContextTypes
from telegram import Update
from core.permissions import is_bot_owner, is_chat_admin

# 帮助信息字典，供其他模块（如admin）导入
HELP_MESSAGES = {
    "general": [
        "/help - 显示帮助菜单",
        "/start - 启动机器人",
        "/group_settings - 查看本群功能设置（仅群组）"
    ],
    "check_in": [
        "/check_in - 每日签到获取积分",
        "/points - 查看我的积分",
        "/leaderboard - 查看积分排行榜"
    ],
    "lottery": [
        "/lottery - 查看抽奖状态",
        "/lottery start [奖品] - 开始抽奖（管理员）",
        "/lottery stop - 停止抽奖（管理员）",
        "/lottery draw - 抽取获奖者（管理员）"
    ],
    "admin": [
        "/kick [用户] - 踢出用户",
        "/ban [用户] - 封禁用户",
        "/mute [用户] [时长] - 禁言用户",
        "/unmute [用户] - 解除禁言"
    ],
    "owner": [
        "/list_chats - 查看机器人加入的所有群组",
        "/broadcast [消息] - 向所有群组发送广播",
        "/stats - 查看机器人统计信息"
    ]
}

def register(application):
    """注册帮助命令"""
    application.add_handler(CommandHandler(
        "help", 
        help_command, 
        filters=~filters.UpdateType.EDITED_MESSAGE
    ))
    print("✅ 已加载模块: help")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """显示帮助菜单，根据权限展示不同命令"""
    if not update.effective_message:
        return
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return
    
    is_owner = is_bot_owner(user.id)
    is_admin = await is_chat_admin(update, context)
    
    # 构建帮助文本
    help_text = "📋 帮助菜单\n\n"
    
    # 通用命令
    help_text += "🔸 通用命令：\n"
    help_text += "/help - 显示此帮助菜单\n"
    help_text += "/start - 启动机器人\n"
    if chat.type in ["group", "supergroup"]:
        help_text += "/group_settings - 查看本群功能设置（仅群组）\n"
    
    # 积分命令
    help_text += "\n🔸 积分命令：\n"
    help_text += "/check_in - 每日签到获取积分\n"
    help_text += "/points - 查看我的积分\n"
    help_text += "/leaderboard - 查看积分排行榜\n"
    
    # 抽奖命令
    help_text += "\n🔸 抽奖命令：\n"
    help_text += "/lottery - 查看抽奖状态\n"
    if is_admin:
        help_text += "/lottery start [奖品] - 开始抽奖（管理员）\n"
        help_text += "/lottery stop - 停止抽奖（管理员）\n"
        help_text += "/lottery draw - 抽取获奖者（管理员）\n"
    
    # 管理员命令
    if is_admin:
        help_text += "\n🔸 管理员命令：\n"
        help_text += "/kick [用户] - 踢出用户（回复用户消息或@用户）\n"
        help_text += "/ban [用户] - 封禁用户（回复用户消息或@用户）\n"
        help_text += "/mute [用户] [时长] - 禁言用户（例如：/mute @user 60代表禁言60分钟）\n"
        help_text += "/unmute [用户] - 解除禁言（回复用户消息或@用户）\n"
    
    # 所有者命令
    if is_owner:
        help_text += "\n🔸 所有者命令：\n"
        help_text += "/list_chats - 查看机器人加入的所有群组\n"
        help_text += "/broadcast [消息] - 向所有群组发送广播\n"
        help_text += "/stats - 查看机器人统计信息\n"
    
    await update.effective_message.reply_text(help_text)
