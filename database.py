# database.py
import aiosqlite
import os
from pathlib import Path


DB_PATH = os.getenv("DATABASE_URL", "chatbot.db")


async def init_db():
    """Инициализация базы данных: создаёт таблицу messages, если её нет."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message_text TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def save_message(user_id: int, message_text: str):
    """Сохраняет сообщение от пользователя в базу."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (user_id, message_text) VALUES (?, ?)",
            (user_id, message_text)
        )
        await db.commit()


async def get_messages(user_id: int, limit: int = 100):
    """Возвращает последние N сообщений пользователя (по умолчанию 100)."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT message_text, timestamp
            FROM messages
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (user_id, limit)
        )
        rows = await cursor.fetchall()
        return [{"text": row[0], "timestamp": row[1]} for row in rows]
