"""SQLite 消息存储：按群持久化聊天记录，供总结时取上下文。"""

import sqlite3
import threading
import time

_SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    roomid   TEXT NOT NULL,
    sender   TEXT NOT NULL,
    nickname TEXT NOT NULL,
    ts       INTEGER NOT NULL,
    type     TEXT NOT NULL,   -- text / image / other
    content  TEXT NOT NULL    -- 文本原文；图片则是视觉模型生成的描述
);
CREATE INDEX IF NOT EXISTS idx_room_ts ON messages (roomid, ts);
"""


class MessageStore:
    def __init__(self, path: str = "messages.db"):
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()
        self._conn.executescript(_SCHEMA)

    def add(self, roomid: str, sender: str, nickname: str, msg_type: str, content: str):
        with self._lock:
            self._conn.execute(
                "INSERT INTO messages (roomid, sender, nickname, ts, type, content) VALUES (?, ?, ?, ?, ?, ?)",
                (roomid, sender, nickname, int(time.time()), msg_type, content),
            )
            self._conn.commit()

    def recent(self, roomid: str, limit: int = 200) -> list[dict]:
        """返回某群最近 limit 条消息，按时间正序。"""
        with self._lock:
            rows = self._conn.execute(
                "SELECT nickname, ts, type, content FROM messages"
                " WHERE roomid = ? ORDER BY ts DESC, id DESC LIMIT ?",
                (roomid, limit),
            ).fetchall()
        rows.reverse()
        return [
            {"nickname": r[0], "ts": r[1], "type": r[2], "content": r[3]}
            for r in rows
        ]
