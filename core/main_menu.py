from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_chat = context.bot_data.get("current_chat", "未选择")
    keyboard = [
        [InlineKeyboardButton("抽奖", callback_data="menu_lottery")],
        [InlineKeyboardButton("统计", callback_data="menu_stats")],
        [InlineKeyboardButton("自动回复", callback_data="menu_auto_reply")],
        [InlineKeyboardButton("定时消息", callback_data="menu_cron")],
        [InlineKeyboardButton("验证", callback_data="menu_verification")],
        [InlineKeyboardButton("进群欢迎", callback_data="menu_welcome")],
        [InlineKeyboardButton("违禁词", callback_data="menu_ban_words")],
        [InlineKeyboardButton("检查", callback_data="menu_check")],
        [InlineKeyboardButton("积分", callback_data="menu_score")],
        [InlineKeyboardButton("新成员限制", callback_data="menu_new_member_limit")],
        [InlineKeyboardButton("切换群", callback_data="menu_switch")],
    ]
    await update.message.reply_text(
        f"当前操作群：{current_chat}\n选择功能进行配置",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    if query.data == "menu_lottery":
        await context.bot.send_message(chat_id=chat_id, text="发送 /lottery_setup 配置抽奖，/start_lottery 开奖")
    elif query.data == "menu_stats":
        await context.bot.send_message(chat_id=chat_id, text="发送 /stats 查看群统计数据")
    elif query.data == "menu_auto_reply":
        await context.bot.send_message(chat_id=chat_id, text="发送 /auto_reply_add 关键词 回复内容 添加规则，/auto_reply_list 查看规则")
    # 其他功能的 callback 逻辑类似，按需补充引导命令
    elif query.data == "menu_switch":
        await context.bot.send_message(chat_id=chat_id, text="发送 /switch_chat 切换管理的群组")

def register_main_menu(application):
    application.add_handler(CommandHandler("menu", show_main_menu))
    application.add_handler(CallbackQueryHandler(menu_callback))