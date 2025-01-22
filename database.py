import sqlite3
from contextlib import contextmanager
from config import DATABASE_PATH, logger

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_db()

    def init_db(self):
        """Initialize the database with required tables."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_streaks (
                        user_id INTEGER PRIMARY KEY,
                        streak_count INTEGER DEFAULT 0,
                        last_use TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def update_user_streak(self, user_id: int) -> int:
        """Update user streak and return current streak count."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Update or insert user streak
                cursor.execute('''
                    INSERT INTO user_streaks (user_id, streak_count)
                    VALUES (?, 1)
                    ON CONFLICT(user_id) DO UPDATE SET 
                    streak_count = streak_count + 1,
                    last_use = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (user_id, user_id))
                conn.commit()
                
                # Get current streak
                cursor.execute('SELECT streak_count FROM user_streaks WHERE user_id = ?', 
                             (user_id,))
                result = cursor.fetchone()
                return result[0] if result else 1
        except Exception as e:
            logger.error(f"Error updating user streak: {e}")
            return 0

    def get_user_streak(self, user_id: int) -> int:
        """Get current streak count for a user."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT streak_count FROM user_streaks WHERE user_id = ?', 
                             (user_id,))
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error getting user streak: {e}")
            return 0
