from telegram.ext import CommandHandler, filters, ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from core.permissions import is_chat_admin

def register_main_menu(application):
    """注册启动命令和主菜单"""
    application.add_handler(CommandHandler(
        "start", 
        start_command, 
        filters=~filters.UpdateType.EDITED_MESSAGE
    ))
    application.add_handler(CommandHandler(
        "group_settings", 
        group_settings_command, 
        filters=filters.ChatType.GROUPS & ~filters.UpdateType.EDITED_MESSAGE
    ))

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """启动机器人，显示欢迎消息"""
    user = update.effective_user
    chat = update.effective_chat
    
    # 私人聊天显示欢迎消息，群组显示简短提示
    if chat.type == "private":
        keyboard = [
            [InlineKeyboardButton("帮助菜单", callback_data="menu:help")],
            [InlineKeyboardButton("关于机器人", callback_data="menu:about")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"你好呀，{user.mention_html()}！我是你的机器人助手～\n"
            "发送 /help 查看所有可用命令",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text("机器人已启动！发送 /help 查看可用命令～")

async def group_settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看群组功能设置（仅群组）"""
    chat = update.effective_chat
    db = context.bot_data.get("db")
    if not db:
        await update.message.reply_text("❌ 数据库未初始化")
        return
    
    # 获取群组设置
    settings = await db.fetchone(
        "SELECT welcome_enabled, check_in_enabled FROM group_settings WHERE chat_id = ?",
        (chat.id,)
    )
    if not settings:
        # 初始化默认设置
        settings = {"welcome_enabled": True, "check_in_enabled": True}
        await db.execute(
            "INSERT INTO group_settings (chat_id, welcome_enabled, check_in_enabled) VALUES (?, ?, ?)",
            (chat.id, True, True)
        )
    
    settings_text = "⚙️ 本群功能设置\n\n"
    settings_text += f"欢迎消息：{'开启' if settings['welcome_enabled'] else '关闭'}\n"
    settings_text += f"签到功能：{'开启' if settings['check_in_enabled'] else '关闭'}\n"
    
    # 管理员可看到设置按钮
    if await is_chat_admin(update, context):
        keyboard = [[InlineKeyboardButton("修改设置", callback_data="settings:edit")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(settings_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(settings_text)
    