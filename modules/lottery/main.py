import asyncio
import random
import time
from telegram.ext import CommandHandler, CallbackQueryHandler, filters, ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.constants import ParseMode
from core.permissions import admin_required, is_chat_admin

# 存储当前正在进行的抽奖
active_lotteries = {}

def register(application):
    """注册抽奖模块的命令和处理器"""
    application.add_handler(CommandHandler(
        "lottery", 
        lottery_command, 
        filters=~filters.UpdateType.EDITED_MESSAGE
    ))
    application.add_handler(CallbackQueryHandler(
        handle_lottery_actions, 
        pattern=r"^lottery:"
    ))
    print("✅ 已加载模块: lottery")

async def lottery_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """抽奖主命令，处理所有抽奖相关操作"""
    if not update.effective_message or not update.effective_chat:
        return
    
    chat_id = update.effective_chat.id
    user = update.effective_user
    args = context.args or []
    
    # 检查是否有正在进行的抽奖
    has_active = chat_id in active_lotteries
    
    # 管理员命令处理
    if args and args[0] in ["start", "stop", "draw"]:
        if not await is_chat_admin(update, context):
            await update.effective_message.reply_text("❌ 只有管理员可以执行此操作")
            return
            
        if args[0] == "start":
            await start_lottery(update, context, args[1:])
        elif args[0] == "stop":
            await stop_lottery(update, context)
        elif args[0] == "draw":
            await draw_winner(update, context)
    else:
        # 普通用户查看抽奖状态或参与
        if has_active:
            await show_lottery_status(update, context)
        else:
            await update.effective_message.reply_text(
                "当前没有正在进行的抽奖！\n"
                "管理员可以使用 /lottery start [奖品名称] 开始新抽奖"
            )

@admin_required
async def start_lottery(update: Update, context: ContextTypes.DEFAULT_TYPE, args):
    """管理员：开始新的抽奖"""
    if not update.effective_message or not update.effective_chat:
        return
    
    chat_id = update.effective_chat.id
    
    if chat_id in active_lotteries:
        await update.effective_message.reply_text("⚠️ 当前已有正在进行的抽奖，请先结束它！")
        return
    
    if not args:
        await update.effective_message.reply_text("❌ 请指定奖品名称！使用格式: /lottery start [奖品名称]")
        return
    
    prize_name = " ".join(args)
    
    # 初始化抽奖数据
    active_lotteries[chat_id] = {
        "start_time": time.time(),
        "participants": [],
        "prize": prize_name,
        "status": "active"  # active, drawing, ended
    }
    
    # 创建操作键盘
    keyboard = [
        [InlineKeyboardButton("🎲 参与抽奖", callback_data=f"lottery:join:{chat_id}")],
        [InlineKeyboardButton("📊 查看参与者", callback_data=f"lottery:list:{chat_id}")],
        [InlineKeyboardButton("🎁 抽取获奖者", callback_data=f"lottery:draw:{chat_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.effective_message.reply_text(
        f"🎉 抽奖活动开始啦！\n\n"
        f"🏆 奖品: {prize_name}\n"
        f"⏰ 开始时间: {time.strftime('%Y-%m-%d %H:%M', time.localtime())}\n\n"
        f"点击下方按钮参与抽奖吧！",
        reply_markup=reply_markup
    )

@admin_required
async def stop_lottery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理员：停止当前抽奖"""
    if not update.effective_message or not update.effective_chat:
        return
    
    chat_id = update.effective_chat.id
    
    if chat_id not in active_lotteries:
        await update.effective_message.reply_text("⚠️ 当前没有正在进行的抽奖！")
        return
    
    # 移除抽奖
    del active_lotteries[chat_id]
    await update.effective_message.reply_text("🔴 抽奖已提前结束！")

async def show_lottery_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """显示当前抽奖状态"""
    if not update.effective_message or not update.effective_chat:
        return
    
    chat_id = update.effective_chat.id
    lottery = active_lotteries.get(chat_id)
    
    if not lottery:
        await update.effective_message.reply_text("当前没有正在进行的抽奖！")
        return
    
    # 计算抽奖持续时间
    duration = int(time.time() - lottery["start_time"])
    hours, remainder = divmod(duration, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # 创建操作键盘
    keyboard = [
        [InlineKeyboardButton("🎲 参与抽奖", callback_data=f"lottery:join:{chat_id}")],
        [InlineKeyboardButton("📊 查看参与者", callback_data=f"lottery:list:{chat_id}")],
        [InlineKeyboardButton("🎁 抽取获奖者", callback_data=f"lottery:draw:{chat_id}")] if await is_chat_admin(update, context) else []
    ]
    keyboard = [row for row in keyboard if row]  # 过滤空行
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.effective_message.reply_text(
        f"🎰 当前正在进行的抽奖\n\n"
        f"🏆 奖品: {lottery['prize']}\n"
        f"⏳ 已持续: {hours}时{minutes}分{seconds}秒\n"
        f"👥 参与人数: {len(lottery['participants'])}\n\n"
        f"点击按钮参与或查看详情",
        reply_markup=reply_markup
    )

async def handle_lottery_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理抽奖相关的按钮点击"""
    query = update.callback_query
    if not query:
        return
    await query.answer()
    
    # 解析回调数据
    parts = query.data.split(":")
    if len(parts) < 3:
        await query.edit_message_text("❌ 无效操作")
        return
    
    action = parts[1]
    chat_id = int(parts[2])
    
    # 检查抽奖是否存在
    if chat_id not in active_lotteries:
        await query.edit_message_text("❌ 抽奖已结束或不存在！")
        return
    
    lottery = active_lotteries[chat_id]
    
    if action == "join":
        await handle_join_lottery(query, lottery, chat_id, context)
    elif action == "list":
        await handle_show_participants(query, lottery, context)
    elif action == "draw":
        if await is_chat_admin(update, context):
            await draw_winner(update, context, chat_id, is_query=True)
        else:
            await query.answer("你没有权限执行此操作", show_alert=True)

async def handle_join_lottery(query: CallbackQuery, lottery, chat_id, context: ContextTypes.DEFAULT_TYPE):
    """处理用户参与抽奖"""
    user = query.from_user
    if not user:
        return
    
    # 检查是否已参与
    if user.id in [p["id"] for p in lottery["participants"]]:
        await query.answer("你已经参与过抽奖啦！", show_alert=True)
        return
    
    # 添加参与者
    lottery["participants"].append({
        "id": user.id,
        "name": user.mention_html(),
        "join_time": time.time()
    })
    
    # 更新消息
    keyboard = [
        [InlineKeyboardButton("🎲 参与抽奖", callback_data=f"lottery:join:{chat_id}")],
        [InlineKeyboardButton("📊 查看参与者", callback_data=f"lottery:list:{chat_id}")],
        [InlineKeyboardButton("🎁 抽取获奖者", callback_data=f"lottery:draw:{chat_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🎉 你已成功参与抽奖！\n\n"
        f"🏆 奖品: {lottery['prize']}\n"
        f"👥 当前参与人数: {len(lottery['participants'])}\n"
        f"⏰ 参与时间: {time.strftime('%H:%M:%S', time.localtime())}",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def handle_show_participants(query: CallbackQuery, lottery, context: ContextTypes.DEFAULT_TYPE):
    """显示参与者列表"""
    if not lottery["participants"]:
        await query.edit_message_text("暂无参与者，请邀请好友参与吧！")
        return
    
    # 生成参与者列表
    participants_list = []
    for i, participant in enumerate(lottery["participants"], 1):
        participants_list.append(f"{i}. {participant['name']}")
    
    # 分页处理
    page_size = 15
    total_pages = (len(participants_list) + page_size - 1) // page_size
    current_page = 0
    start = current_page * page_size
    end = start + page_size
    page_content = participants_list[start:end]
    
    # 分页键盘
    pagination_keyboard = []
    if total_pages > 1:
        pagination_keyboard.append([
            InlineKeyboardButton("上一页", callback_data=f"lottery:prev:{query.message.chat.id}"),
            InlineKeyboardButton(f"{current_page+1}/{total_pages}", callback_data="lottery:page"),
            InlineKeyboardButton("下一页", callback_data=f"lottery:next:{query.message.chat.id}")
        ])
    
    pagination_keyboard.append([
        InlineKeyboardButton("返回抽奖主页", callback_data=f"lottery:home:{query.message.chat.id}")
    ])
    
    reply_markup = InlineKeyboardMarkup(pagination_keyboard)
    
    await query.edit_message_text(
        f"📊 抽奖参与者 ({len(lottery['participants'])}人)\n\n"
        f"{chr(10).join(page_content)}",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def draw_winner(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id=None, is_query=False):
    """抽取获奖者"""
    if is_query:
        query = update.callback_query
        if not query or not query.message:
            return
        message = query.message
        chat_id = chat_id or message.chat.id
    else:
        if not update.effective_message or not update.effective_chat:
            return
        message = update.effective_message
        chat_id = chat_id or update.effective_chat.id
    
    lottery = active_lotteries.get(chat_id)
    if not lottery:
        await message.edit_text("❌ 抽奖已结束或不存在！")
        return
    
    if len(lottery["participants"]) < 1:
        await message.edit_text("❌ 参与人数不足，无法抽奖！")
        return
    
    # 显示抽奖动画
    lottery["status"] = "drawing"
    await message.edit_text("🎲 正在抽取获奖者...")
    
    for _ in range(5):
        temp_winner = random.choice(lottery["participants"])
        await message.edit_text(
            f"🎲 正在抽取获奖者...\n"
            f"当前选中: {temp_winner['name']}",
            parse_mode=ParseMode.HTML
        )
        await asyncio.sleep(0.5)
    
    # 最终确定获奖者
    winner = random.choice(lottery["participants"])
    lottery["status"] = "ended"
    
    # 显示结果
    keyboard = [
        [InlineKeyboardButton("查看完整名单", callback_data=f"lottery:list:{chat_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    result_msg = (
        f"🏆 抽奖结果公布！\n\n"
        f"恭喜 {winner['name']} 获得 {lottery['prize']}！\n\n"
        f"🎊 感谢所有参与者的支持！"
    )
    
    await message.edit_text(result_msg, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    # 移除抽奖
    del active_lotteries[chat_id]
