from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

async def show_switch_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """展示切换群菜单，引导用户选择或输入要管理的群"""
    keyboard = [
        [InlineKeyboardButton("输入群 ID 切换", callback_data="switch_manual")]
    ]
    await update.message.reply_text(
        "选择要管理的群组（输入群 ID 即可）",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def switch_manual_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理“输入群 ID 切换”的回调，让用户手动输入群 ID"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("请发送目标群组的 ID（纯数字，为 Telegram 群组的实际 ID）")
    context.user_data["waiting_chat_id"] = "switch"  # 标记等待用户输入群 ID

async def handle_chat_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理用户输入的群 ID，暂存到 bot_data 中，用于后续功能的多群隔离"""
    if "waiting_chat_id" in context.user_data:
        try:
            chat_id = int(update.message.text)
            # 将当前操作的群 ID 暂存，后续功能基于此 chat_id 操作对应群组的配置
            context.bot_data["current_chat"] = chat_id  
            await update.message.reply_text(f"已切换至群组 {chat_id}，可开始配置该群组功能！")
        except ValueError:
            await update.message.reply_text("无效的群 ID，请输入纯数字的 Telegram 群组 ID 重新尝试")
        finally:
            del context.user_data["waiting_chat_id"]

def register_switch_chat(application):
    """注册切换群相关的处理器到应用中"""
    application.add_handler(CommandHandler("switch_chat", show_switch_menu))
    application.add_handler(CallbackQueryHandler(switch_manual_callback, pattern="switch_manual"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat_id_input))