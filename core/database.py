import sqlite3
import json  # 引入json模块，替代不安全的eval
from typing import Dict, Any, List
import os

class Database:
    def __init__(self, db_path: str):
        db_dir = os.path.dirname(db_path)
        os.makedirs(db_dir, exist_ok=True)
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # 支持按列名访问
        self._create_tables()  # 初始化表结构

    def _create_tables(self):
        """创建基础表 + 新功能扩展表"""
        cursor = self.conn.cursor()
        
        # 1. 基础关联表（机器人-群组）
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bots (
            token TEXT PRIMARY KEY,
            owner_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_token TEXT NOT NULL,
            chat_id INTEGER NOT NULL,  -- 群组ID
            chat_title TEXT,           -- 群组名称
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bot_token) REFERENCES bots(token),
            UNIQUE(bot_token, chat_id)  -- 确保机器人-群组唯一关联
        )
        """)
        
        # 2. 群组独立设置表（核心扩展：新增所有功能的配置字段）
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_settings (
            group_id INTEGER PRIMARY KEY,  -- 群组唯一ID（核心隔离标识）
            -- 基础功能（原）
            welcome_enabled BOOLEAN DEFAULT 1,  
            welcome_message TEXT DEFAULT "🎉 欢迎 {user} 加入群组！请遵守群规～",
            filter_enabled BOOLEAN DEFAULT 1,
            filter_words TEXT DEFAULT "广告,违规,测试",  
            checkin_enabled BOOLEAN DEFAULT 1,
            checkin_base_reward INTEGER DEFAULT 5,
            checkin_consecutive_bonus INTEGER DEFAULT 2,
            checkin_max_bonus INTEGER DEFAULT 10,
            checkin_special_rewards TEXT DEFAULT "7:30,14:80,30:200",  
            -- 新功能扩展（抽奖、统计等）
            lottery_enabled BOOLEAN DEFAULT 1,    -- 抽奖功能开关
            lottery_config TEXT DEFAULT '{"prize": "神秘大奖", "participants": []}',  -- JSON 存规则
            stats_enabled BOOLEAN DEFAULT 1,      -- 统计功能开关
            stats_config TEXT DEFAULT '{"message_count": 0, "active_hours": {}}',     -- JSON 存统计数据
            auto_reply_enabled BOOLEAN DEFAULT 1, -- 自动回复开关
            auto_reply_rules TEXT DEFAULT '{}',   -- JSON 存关键词-回复映射
            cron_enabled BOOLEAN DEFAULT 1,       -- 定时消息开关
            cron_jobs TEXT DEFAULT '[]',          -- JSON 存定时任务
            verification_enabled BOOLEAN DEFAULT 1, -- 验证开关
            verification_rules TEXT DEFAULT '{"questions": ["验证问题1"]}', -- JSON 存验证规则
            ban_words_enabled BOOLEAN DEFAULT 1,  -- 违禁词开关
            ban_words_list TEXT DEFAULT '["广告","违规"]', -- JSON 存违禁词
            check_enabled BOOLEAN DEFAULT 1,      -- 检查功能开关
            score_enabled BOOLEAN DEFAULT 1,      -- 积分功能开关（原积分逻辑保留，新增开关）
            new_member_limit_enabled BOOLEAN DEFAULT 1, -- 新成员限制开关
            new_member_limit_config TEXT DEFAULT '{"mute_duration": 600}', -- JSON 存限制规则
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 3. 按群组隔离的积分表（原逻辑保留，新增功能不影响）
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_user_points (
            group_id INTEGER NOT NULL,  -- 关联群组
            user_id INTEGER NOT NULL,   -- 关联用户
            points INTEGER DEFAULT 0,
            last_check_in DATE,
            consecutive_days INTEGER DEFAULT 0,
            total_check_ins INTEGER DEFAULT 0,
            PRIMARY KEY (group_id, user_id)  -- 联合主键确保群内用户独立
        )
        """)
        
        # 4. 按群组隔离的积分日志表（原逻辑保留）
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_points_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,  -- 关联群组
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            points INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 5. 新功能专属表（可选：复杂功能可拆表，示例抽奖参与记录表）
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_lottery_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,  -- 关联群组
            user_id INTEGER NOT NULL,   -- 参与用户
            lottery_id TEXT NOT NULL,   -- 抽奖唯一标识（如批次ID）
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(group_id, user_id, lottery_id)
        )
        """)
        
        self.conn.commit()

    # ------------------------------
    # 通用执行方法（原逻辑保留）
    # ------------------------------
    def execute(self, query: str, params=None) -> sqlite3.Cursor:
        cursor = self.conn.cursor()
        cursor.execute(query, params or ())
        self.conn.commit()
        return cursor

    def fetchone(self, query: str, params=None) -> Dict[str, Any]:
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    def fetchall(self, query: str, params=None) -> List[Dict[str, Any]]:
        cursor = self.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        self.conn.close()


    # ------------------------------
    # 群组设置管理（核心扩展：支持新功能配置）
    # ------------------------------
    def init_group_settings(self, group_id: int):
        """新群组加入时，自动创建默认设置（含新功能）"""
        if not self.fetchone("SELECT group_id FROM group_settings WHERE group_id = ?", (group_id,)):
            self.execute("INSERT INTO group_settings (group_id) VALUES (?)", (group_id,))
            print(f"✅ 为新群组 {group_id} 初始化默认设置（含新功能）")

    def get_group_settings(self, group_id: int) -> dict:
        """获取当前群组的所有设置（自动初始化新群）"""
        self.init_group_settings(group_id)  # 确保设置存在
        settings = self.fetchone("SELECT * FROM group_settings WHERE group_id = ?", (group_id,))
        # 将 JSON 字段转为字典，使用json.loads替代eval，增强安全性
        for field in [
            "lottery_config", "stats_config", "auto_reply_rules", 
            "cron_jobs", "verification_rules", "ban_words_list", 
            "new_member_limit_config"
        ]:
            if settings[field]:
                try:
                    settings[field] = json.loads(settings[field])
                except json.JSONDecodeError:
                    # 解析失败时返回空字典，避免程序崩溃
                    settings[field] = {}
        return settings

    def update_group_settings(self, group_id: int, **kwargs):
        """更新当前群组的设置（支持新功能参数，自动处理 JSON 字段）"""
        # 预处理 JSON 字段，使用json.dumps转为字符串，确保格式正确
        for field in [
            "lottery_config", "stats_config", "auto_reply_rules", 
            "cron_jobs", "verification_rules", "ban_words_list", 
            "new_member_limit_config"
        ]:
            if field in kwargs:
                kwargs[field] = json.dumps(kwargs[field])
        
        if not kwargs:
            return
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        params = list(kwargs.values()) + [group_id]
        self.execute(f"UPDATE group_settings SET {set_clause} WHERE group_id = ?", params)
        print(f"🔧 群组 {group_id} 更新设置：{kwargs}")


    # ------------------------------
    # 群组积分管理（原逻辑保留，新增功能不影响）
    # ------------------------------
    def get_group_user_points(self, group_id: int, user_id: int) -> dict:
        """获取用户在当前群组的积分数据"""
        self.init_group_settings(group_id)  # 确保群组已初始化
        row = self.fetchone("""
            SELECT * FROM group_user_points 
            WHERE group_id = ? AND user_id = ?
        """, (group_id, user_id))
        return dict(row) if row else {
            "group_id": group_id,
            "user_id": user_id,
            "points": 0,
            "last_check_in": None,
            "consecutive_days": 0,
            "total_check_ins": 0
        }

    def update_group_user_points(self, group_id: int, user_id: int, points: int, action: str):
        """更新用户在当前群组的积分（自动处理连续签到）"""
        user_data = self.get_group_user_points(group_id, user_id)
        new_points = user_data["points"] + points  # 计算新积分
        
        # 插入或更新积分记录（按群组+用户联合主键）
        self.execute("""
            INSERT INTO group_user_points 
            (group_id, user_id, points, last_check_in, consecutive_days, total_check_ins)
            VALUES (?, ?, ?, CURRENT_DATE, ?, ?)
            ON CONFLICT(group_id, user_id) DO UPDATE SET 
                points = ?,  -- 更新积分
                consecutive_days = CASE 
                    WHEN last_check_in = DATE('now', '-1 day') THEN consecutive_days + 1
                    WHEN last_check_in = DATE('now') THEN consecutive_days
                    ELSE 1
                END,
                total_check_ins = total_check_ins + CASE 
                    WHEN last_check_in != DATE('now') THEN 1 
                    ELSE 0 
                END
        """, (
            group_id, user_id, new_points,
            user_data["consecutive_days"], user_data["total_check_ins"],
            new_points  # 冲突时更新的积分值
        ))
        
        # 记录积分变动日志（关联群组）
        self.execute("""
            INSERT INTO group_points_log 
            (group_id, user_id, action, points) 
            VALUES (?, ?, ?, ?)
        """, (group_id, user_id, action, points))

    def get_group_top_users(self, group_id: int, limit: int = 10) -> list:
        """获取当前群组的积分排行榜（仅本群用户）"""
        return self.fetchall("""
            SELECT user_id, points FROM group_user_points 
            WHERE group_id = ? 
            ORDER BY points DESC LIMIT ?
        """, (group_id, limit))


    # ------------------------------
    # 新功能专属方法（以抽奖为例，其他功能同理扩展）
    # ------------------------------
    def add_lottery_participant(self, group_id: int, user_id: int, lottery_id: str):
        """记录用户参与某群组的抽奖"""
        self.execute("""
            INSERT INTO group_lottery_participants 
            (group_id, user_id, lottery_id) 
            VALUES (?, ?, ?)
            ON CONFLICT DO NOTHING  -- 避免重复参与
        """, (group_id, user_id, lottery_id))

    def get_lottery_participants(self, group_id: int, lottery_id: str) -> List[Dict[str, Any]]:
        """获取某群组某抽奖的参与者"""
        return self.fetchall("""
            SELECT user_id FROM group_lottery_participants 
            WHERE group_id = ? AND lottery_id = ?
        """, (group_id, lottery_id))

    def clear_lottery_participants(self, group_id: int, lottery_id: str):
        """清空某群组某抽奖的参与者（开奖后调用）"""
        self.execute("""
            DELETE FROM group_lottery_participants 
            WHERE group_id = ? AND lottery_id = ?
        """, (group_id, lottery_id))