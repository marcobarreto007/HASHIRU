import sqlite3
from typing import List, Tuple

class DialogMemoryManager:
    """Manages persistent conversation memory using SQLite."""

    def __init__(self, db_path: str = "dialog_memory.db", max_messages: int = 50):
        self.db_path = db_path
        self.max_messages = max_messages
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_table()

    def _create_table(self):
        """Creates the conversation history table if it doesn't exist."""
        try:
            with self.conn:
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def add_message(self, role: str, content: str):
        """
        Adds a message to the conversation history.

        :param role: The role of the speaker ('user' or 'assistant').
        :param content: The message content.
        """
        try:
            with self.conn:
                self.conn.execute(
                    "INSERT INTO conversation_history (role, content) VALUES (?, ?)",
                    (role, content)
                )
            self._prune_history()
        except sqlite3.Error as e:
            print(f"Database error on insert: {e}")

    def get_history(self, limit: int = 20) -> List[Tuple[str, str]]:
        """
        Retrieves the most recent conversation history.

        :param limit: The maximum number of messages to retrieve.
        :return: A list of (role, content) tuples.
        """
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT role, content FROM conversation_history ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
                # Fetched in descending order, so we reverse to get chronological order
                return list(reversed(cursor.fetchall()))
        except sqlite3.Error as e:
            print(f"Database error on select: {e}")
            return []

    def _prune_history(self):
        """Removes the oldest messages if the history exceeds the max limit."""
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM conversation_history")
                count = cursor.fetchone()[0]

                if count > self.max_messages:
                    num_to_delete = count - self.max_messages
                    cursor.execute("""
                        DELETE FROM conversation_history
                        WHERE id IN (
                            SELECT id FROM conversation_history
                            ORDER BY timestamp ASC
                            LIMIT ?
                        )
                    """, (num_to_delete,))
        except sqlite3.Error as e:
            print(f"Database error on prune: {e}")

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
