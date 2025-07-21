import random
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from core.database import Database
from core.permissions import PermissionChecker

class LotteryHandlers:
    """抽奖功能的命令处理器，依赖数据库和权限模块"""
    def __init__(self, db: Database):
        self.db = db  # 注入数据库实例（依赖注入，降低耦合）

    # ------------------------------
    # 命令处理器：配置相关（仅管理员）
    # ------------------------------
    async def show_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """显示当前抽奖配置"""
        group_id = update.effective_chat.id
        config = self.db.get_lottery_config(group_id)
        
        await update.message.reply_text(
            f"🎲 抽奖配置\n"
            f"状态：{'开启' if config['enabled'] else '关闭'}\n"
            f"奖品：{config['prize']}\n\n"
            "管理员命令：\n"
            "/lottery_toggle - 开关抽奖\n"
            "/lottery_set_prize [奖品] - 修改奖品\n"
            "/lottery_start - 开奖\n\n"
            "成员命令：\n"
            "/lottery_join - 参与抽奖"
        )

    async def toggle_lottery(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """开关抽奖功能（需管理员权限）"""
        if not await PermissionChecker.is_admin(update, context):
            return await update.message.reply_text("⚠️ 仅管理员可操作")
            
        group_id = update.effective_chat.id
        current = self.db.get_lottery_config(group_id)
        new_state = not current["enabled"]
        
        self.db.update_lottery_config(group_id, enabled=new_state)
        await update.message.reply_text(f"抽奖已{'开启' if new_state else '关闭'}")

    async def set_prize(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """修改奖品（需管理员权限）"""
        if not await PermissionChecker.is_admin(update, context):
            return await update.message.reply_text("⚠️ 仅管理员可操作")
            
        if not context.args:
            return await update.message.reply_text("用法：/lottery_set_prize [奖品名称]")
            
        group_id = update.effective_chat.id
        new_prize = " ".join(context.args)
        
        self.db.update_lottery_config(group_id, prize=new_prize)
        await update.message.reply_text(f"奖品已更新为：{new_prize}")

    # ------------------------------
    # 命令处理器：参与和开奖（混合权限）
    # ------------------------------
    async def join_lottery(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """用户参与抽奖（全员可用）"""
        group_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        # 检查抽奖是否开启
        if not self.db.get_lottery_config(group_id)["enabled"]:
            return await update.message.reply_text("❌ 抽奖未开启，无法参与")
            
        # 添加参与者
        if self.db.add_lottery_participant(group_id, user_id):
            await update.message.reply_text("🎉 成功参与抽奖！等待开奖...")
        else:
            await update.message.reply_text("⚠️ 你已参与过本次抽奖")

    async def start_lottery(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """开奖（需管理员权限）"""
        if not await PermissionChecker.is_admin(update, context):
            return await update.message.reply_text("⚠️ 仅管理员可开奖")
            
        group_id = update.effective_chat.id
        participants = self.db.get_lottery_participants(group_id)
        
        if not participants:
            return await update.message.reply_text("❌ 暂无参与者，无法开奖")
            
        # 随机抽奖
        winner_id = random.choice(participants)
        winner = await context.bot.get_chat_member(group_id, winner_id)
        prize = self.db.get_lottery_config(group_id)["prize"]
        
        # 重置抽奖
        self.db.clear_lottery_participants(group_id)
        
        await update.message.reply_text(
            f"🎊 抽奖结果揭晓！\n"
            f"奖品：{prize}\n"
            f"获奖者：{winner.user.mention_html()}",
            parse_mode="HTML"
        )

    # ------------------------------
    # 注册命令处理器（对外提供的接口）
    # ------------------------------
    def register(self, application):
        """将命令处理器注册到应用，与主程序解耦"""
        application.add_handler(CommandHandler("lottery", self.show_config))
        application.add_handler(CommandHandler("lottery_toggle", self.toggle_lottery))
        application.add_handler(CommandHandler("lottery_set_prize", self.set_prize))
        application.add_handler(CommandHandler("lottery_join", self.join_lottery))
        application.add_handler(CommandHandler("lottery_start", self.start_lottery))
