from telegram.ext import CommandHandler, ContextTypes
from telegram import Update, User, ChatPermissions
from core.permissions import is_chat_admin
from telegram.error import BadRequest

async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        await update.message.reply_text("❌ 你没有权限执行此操作")
        return
    
    chat_id = update.effective_chat.id
    message = update.effective_message
    
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    else:
        args = context.args
        if not args:
            await update.message.reply_text("用法：/kick @用户名 或 回复消息使用 /kick")
            return
        
        arg = args[0]
        try:
            user_id = int(arg)
            chat_member = await context.bot.get_chat_member(chat_id, user_id)
            target_user = chat_member.user
        except ValueError:
            if not arg.startswith('@'):
                await update.message.reply_text("请使用 @用户名 或 回复消息")
                return
            username = arg[1:]
            try:
                chat_member = await context.bot.get_chat_member(chat_id, username)
                target_user = chat_member.user
            except Exception as e:
                await update.message.reply_text(f"未找到用户：{arg}")
                return
    
    if target_user.id == update.effective_user.id:
        await update.message.reply_text("❌ 你不能踢自己")
        return
    
    if target_user.id == context.bot.id:
        await update.message.reply_text("❌ 我不能踢自己")
        return
    
    try:
        target_status = (await context.bot.get_chat_member(chat_id, target_user.id)).status
        if target_status in ['administrator', 'creator']:
            await update.message.reply_text("❌ 无法踢管理员")
            return
    except Exception as e:
        await update.message.reply_text(f"检查用户权限失败：{str(e)}")
        return
    
    try:
        await context.bot.ban_chat_member(chat_id, target_user.id)
        await update.message.reply_text(f"✅ 已踢出用户：{target_user.first_name}")
    except Exception as e:
        await update.message.reply_text(f"踢人失败：{str(e)}")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        await update.message.reply_text("❌ 你没有权限执行此操作")
        return
    
    chat_id = update.effective_chat.id
    message = update.effective_message
    
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    else:
        args = context.args
        if not args:
            await update.message.reply_text("用法：/ban @用户名 或 回复消息使用 /ban")
            return
        
        arg = args[0]
        try:
            user_id = int(arg)
            chat_member = await context.bot.get_chat_member(chat_id, user_id)
            target_user = chat_member.user
        except ValueError:
            if not arg.startswith('@'):
                await update.message.reply_text("请使用 @用户名 或 回复消息")
                return
            username = arg[1:]
            try:
                chat_member = await context.bot.get_chat_member(chat_id, username)
                target_user = chat_member.user
            except Exception as e:
                await update.message.reply_text(f"未找到用户：{arg}")
                return
    
    if target_user.id == update.effective_user.id:
        await update.message.reply_text("❌ 你不能封禁自己")
        return
    
    if target_user.id == context.bot.id:
        await update.message.reply_text("❌ 我不能封禁自己")
        return
    
    try:
        target_status = (await context.bot.get_chat_member(chat_id, target_user.id)).status
        if target_status in ['administrator', 'creator']:
            await update.message.reply_text("❌ 无法封禁管理员")
            return
    except Exception as e:
        await update.message.reply_text(f"检查用户权限失败：{str(e)}")
        return
    
    try:
        await context.bot.ban_chat_member(chat_id, target_user.id)
        await update.message.reply_text(f"✅ 已封禁用户：{target_user.first_name}")
    except Exception as e:
        await update.message.reply_text(f"封禁失败：{str(e)}")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        await update.message.reply_text("❌ 你没有权限执行此操作")
        return
    
    chat_id = update.effective_chat.id
    message = update.effective_message
    
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    else:
        args = context.args
        if not args:
            await update.message.reply_text("用法：/unban @用户名 或 回复消息使用 /unban")
            return
        
        arg = args[0]
        try:
            user_id = int(arg)
            target_user = User(user_id, "用户", False)
        except ValueError:
            if not arg.startswith('@'):
                await update.message.reply_text("请使用 @用户名 或 回复消息")
                return
            username = arg[1:]
            try:
                user_id = await get_user_id_by_username(context, chat_id, username)
                if not user_id:
                    await update.message.reply_text(f"未找到用户：{arg}")
                    return
                target_user = User(user_id, "用户", False)
            except Exception as e:
                await update.message.reply_text(f"处理用户名失败：{str(e)}")
                return
    
    try:
        await context.bot.unban_chat_member(chat_id, target_user.id)
        await update.message.reply_text(f"✅ 已解除对用户的封禁")
    except Exception as e:
        await update.message.reply_text(f"解封失败：{str(e)}")

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        await update.message.reply_text("❌ 你没有权限执行此操作")
        return
    
    chat_id = update.effective_chat.id
    message = update.effective_message
    
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        args = context.args
        if not args:
            duration = 60  # 默认1小时
        else:
            duration_str = args[0]
            duration, unit = parse_duration(duration_str)
            if not duration:
                await update.message.reply_text("无效的时间格式，示例：/mute @user 1h")
                return
    else:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("用法：/mute @用户名 [时间] 或 回复消息使用 /mute [时间]")
            return
        
        user_arg = args[0]
        duration_str = args[1]
        
        try:
            user_id = int(user_arg)
            chat_member = await context.bot.get_chat_member(chat_id, user_id)
            target_user = chat_member.user
        except ValueError:
            if not user_arg.startswith('@'):
                await update.message.reply_text("请使用 @用户名 或 回复消息")
                return
            username = user_arg[1:]
            try:
                chat_member = await context.bot.get_chat_member(chat_id, username)
                target_user = chat_member.user
            except Exception as e:
                await update.message.reply_text(f"未找到用户：{user_arg}")
                return
        
        duration, unit = parse_duration(duration_str)
        if not duration:
            await update.message.reply_text("无效的时间格式，支持：数字+单位（如1h、30m、2d）")
            return
    
    if target_user.id == update.effective_user.id:
        await update.message.reply_text("❌ 你不能禁言自己")
        return
    
    if target_user.id == context.bot.id:
        await update.message.reply_text("❌ 我不能禁言自己")
        return
    
    try:
        target_status = (await context.bot.get_chat_member(chat_id, target_user.id)).status
        if target_status in ['administrator', 'creator']:
            await update.message.reply_text("❌ 无法禁言管理员")
            return
    except Exception as e:
        await update.message.reply_text(f"检查用户权限失败：{str(e)}")
        return
    
    duration_seconds = int(duration * 60)
    
    try:
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False
        )
        
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target_user.id,
            permissions=permissions,
            until_date=duration_seconds
        )
        
        unit_text = {
            's': '秒', 'm': '分钟', 'h': '小时', 'd': '天', 'w': '周'
        }.get(unit, '分钟')
        
        await update.message.reply_text(
            f"✅ 已禁言用户：{target_user.first_name}，时长：{duration} {unit_text}"
        )
    except Exception as e:
        await update.message.reply_text(f"禁言失败：{str(e)}")

def parse_duration(duration_str):
    import re
    match = re.match(r'^(\d+)([smhdw]?)$', duration_str)
    if not match:
        return None, None
    
    value = int(match.group(1))
    unit = match.group(2) or 'm'
    
    time_units = {
        's': 1/60,
        'm': 1,
        'h': 60,
        'd': 60 * 24,
        'w': 60 * 24 * 7
    }
    
    if unit not in time_units:
        return None, None
    
    return value * time_units[unit], unit

async def get_user_id_by_username(context, chat_id, username):
    try:
        chat_member = await context.bot.get_chat_member(chat_id, username)
        return chat_member.user.id
    except Exception:
        members = await context.bot.get_chat_administrators(chat_id)
        for member in members:
            if member.user.username and member.user.username.lower() == username.lower():
                return member.user.id
        return None

# 帮助文本
HELP_TEXT = """
🔸 管理员命令（需管理员权限）：
/kick [@用户名|用户ID] - 踢出用户（可回复消息使用）
/ban [@用户名|用户ID] - 封禁用户
/unban [@用户名|用户ID] - 解除封禁
/mute [@用户名|用户ID] [时间] - 禁言用户（如：/mute @user 1h）
"""

def register(application):
    from modules.help.main import HELP_MESSAGES
    HELP_MESSAGES["admin"] = HELP_TEXT
    
    application.add_handler(CommandHandler("kick", kick_command))
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("mute", mute_command))