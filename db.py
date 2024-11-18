import sqlite3
from datetime import datetime
from typing import List, Dict

class Database:
    def __init__(self, db_path: str = "learning_records.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建用户会话表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建对话历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    section TEXT,
                    subsection TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            
            conn.commit()
    
    def save_chat(self, session_id: str, section: str, subsection: str, 
                  role: str, content: str):
        """保存单条对话记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_history 
                (session_id, section, subsection, role, content)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, section, subsection, role, content))
            conn.commit()
    
    def get_chat_history(self, session_id: str, section: str = None, 
                        subsection: str = None) -> List[Dict]:
        """获取对话历史"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM chat_history WHERE session_id = ?"
            params = [session_id]
            
            if section:
                query += " AND section = ?"
                params.append(section)
            if subsection:
                query += " AND subsection = ?"
                params.append(subsection)
                
            query += " ORDER BY timestamp"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                {
                    "role": row[4],
                    "content": row[5],
                    "timestamp": row[6]
                }
                for row in rows
            ] 