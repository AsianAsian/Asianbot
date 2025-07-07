import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from config import BOT_TOKEN, ADMIN_IDS
from proxy import set_proxy_env, test_proxy

# 启用日志（记录到终端）
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 定义自定义键盘
def get_custom_keyboard():
    keyboard = [
        [KeyboardButton("南京"), KeyboardButton("上海")],
        [KeyboardButton("广州"), KeyboardButton("深圳")],
        [KeyboardButton("北京"), KeyboardButton("日本")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

# 命令处理函数
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "👋 欢迎使用群助手机器人！\n"
        "发送 /help 查看可用命令列表。",
        reply_markup=get_custom_keyboard()
    )

def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "📚 可用命令:\n"
        "/start - 启动机器人\n"
        "/help - 显示帮助菜单\n"
        "/hello - 测试机器人响应\n"
        "/admin - 管理员命令（需授权）"
    )

def hello(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("👋 你好！我是群助手机器人。")

def admin(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in ADMIN_IDS:
        update.message.reply_text(
            "🔧 管理员命令:\n"
            "/kick [用户ID] - 踢出用户\n"
            "/mute [用户ID] [时长] - 禁言用户\n"
            "/announce [消息] - 发布公告"
        )
    else:
        update.message.reply_text("🚀 你不是管理员，无法使用此命令。")

# 新增：仅监听消息，不自动回复
def listen_messages(update: Update, context: CallbackContext) -> None:
    """记录消息到终端，包含群组名称（如果是群组消息）"""
    message = update.message
    if message:
        user = message.from_user
        chat = message.chat  # 获取聊天对象（私聊/群聊）
        
        # 区分聊天类型
        if chat.type == "private":
            chat_info = f"私聊（用户: {user.id}）"
        else:
            # 群聊/超级群，显示群组名称和 ID
            chat_info = f"群组: {chat.title}（ID: {chat.id}）"
        
        # 记录详细日志到终端
        logger.info(
            f"收到消息 | 用户: {user.username}({user.id}) "
            f"| 聊天类型: {chat_info} "
            f"| 内容: {message.text}"
        )

# 错误处理
def error(update: Update, context: CallbackContext) -> None:
    logger.error(f'Update "{update}" 导致错误: "{context.error}"')

# 主函数
def main():
    # 设置代理
    set_proxy_env()
    test_proxy()
    
    # 启动机器人
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher
    
    # 注册命令处理器（保留自动回复）
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("hello", hello))
    dispatcher.add_handler(CommandHandler("admin", admin))
    
    # 注册消息处理器（仅记录，不回复）
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, listen_messages))
    
    # 注册错误处理器
    dispatcher.add_error_handler(error)
    
    # 启动机器人（接收所有更新）
    logging.info("🚀 机器人已启动，开始监听消息（仅终端记录）...")
    updater.start_polling(allowed_updates=Update.ALL_TYPES)
    updater.idle()

if __name__ == '__main__':
    main()