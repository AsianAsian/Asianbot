from telegram.ext import CommandHandler, ContextTypes
from telegram import Update
from core.permissions import is_bot_owner, is_chat_admin

HELP_MESSAGES = {
    "general": """
🤖 <b>机器人命令列表</b> 🤖

🔸 基础命令：
/help - 显示此帮助菜单
/start - 启动机器人
/group_settings - 查看本群功能设置（仅群组）
""",
    "admin": """
🔸 管理员命令（需管理员权限，仅群组可用）：
/kick [@用户名|用户ID] - 踢出用户
/ban [@用户名|用户ID] - 封禁用户
/unban [@用户名|用户ID] - 解除封禁
/mute [@用户名|用户ID] [时间] - 禁言用户（如：/mute @user 1h）
/set_welcome [消息] - 修改欢迎语（{user}代表新成员）
/toggle_welcome - 开关欢迎消息
/set_filter [词1 词2] - 设置敏感词
/toggle_filter - 开关敏感词过滤
/set_checkin_base [数字] - 设置签到基础积分
""",
    "owner": """
🔸 所有者命令（仅机器人所有者可用）：
/list_chats - 查看机器人加入的所有群组
/broadcast [消息] - 向所有群组发送广播
/stats - 查看机器人统计信息
""",
    "welcome": """
🔸 欢迎消息（仅群组）：
自动向新成员发送欢迎语，管理员可自定义
""",
    "filter": """
🔸 敏感词过滤（仅群组）：
自动检测并删除含敏感词的消息
""",
    "check_in": """
🔸 签到系统（仅群组可用）：
/check_in - 每日签到领积分
/points - 查看个人积分
/leaderboard - 查看本群积分排行
"""
}

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        private_msg = "⚠️ 提示：部分功能仅在群组中可用\n\n"
    else:
        private_msg = ""
    
    message = private_msg + HELP_MESSAGES["general"]
    
    if update.effective_chat.type != "private" and await is_chat_admin(update, context):
        message += HELP_MESSAGES["admin"]
    
    if await is_bot_owner(update, context):
        message += HELP_MESSAGES["owner"]
    
    message += HELP_MESSAGES["welcome"]
    message += HELP_MESSAGES["filter"]
    message += HELP_MESSAGES["check_in"]
    
    await update.message.reply_text(message, parse_mode="HTML")

def register(application):
    application.add_handler(CommandHandler("help", help_command))
