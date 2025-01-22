import sqlite3
from contextlib import contextmanager
from config import DATABASE_PATH, logger
from datetime import datetime, timedelta
import json

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_db()

    def init_db(self):
        """Initialize the database with required tables."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Drop and recreate user_streaks table with proper schema
                cursor.execute('''DROP TABLE IF EXISTS user_streaks''')
                cursor.execute('''
                    CREATE TABLE user_streaks (
                        user_id INTEGER PRIMARY KEY,
                        streak_count INTEGER DEFAULT 0,
                        highest_streak INTEGER DEFAULT 0,
                        last_use TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        unlocked_rewards TEXT DEFAULT '[]'
                    )
                ''')

                # Drop and recreate user_preferences table with proper schema
                cursor.execute('''DROP TABLE IF EXISTS user_preferences''')
                cursor.execute('''
                    CREATE TABLE user_preferences (
                        user_id INTEGER PRIMARY KEY,
                        default_persona TEXT,
                        custom_settings TEXT DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                conn.commit()
                logger.info("Database tables created successfully")
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

    def update_user_streak(self, user_id: int) -> tuple:
        """Update user streak and return current streak and any new rewards."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_time = datetime.now()

                # Get user's current streak info
                cursor.execute('''
                    SELECT streak_count, last_use, highest_streak, unlocked_rewards 
                    FROM user_streaks 
                    WHERE user_id = ?
                ''', (user_id,))
                result = cursor.fetchone()

                new_streak = 1
                highest_streak = 1
                unlocked_rewards = []

                if result:
                    streak_count, last_use, current_highest, rewards_json = result
                    last_use = datetime.strptime(last_use, '%Y-%m-%d %H:%M:%S.%f')
                    time_diff = current_time - last_use
                    unlocked_rewards = json.loads(rewards_json)

                    # If last use was within 24 hours, increment streak
                    if time_diff <= timedelta(hours=24):
                        new_streak = streak_count + 1
                        highest_streak = max(new_streak, current_highest)

                        # Check for new rewards
                        new_rewards = self._check_rewards(new_streak, unlocked_rewards)
                        if new_rewards:
                            unlocked_rewards.extend(new_rewards)
                    else:
                        highest_streak = current_highest or 1

                # Update streak in database
                cursor.execute('''
                    INSERT INTO user_streaks (
                        user_id, streak_count, highest_streak, last_use, unlocked_rewards
                    ) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET 
                        streak_count = excluded.streak_count,
                        highest_streak = excluded.highest_streak,
                        last_use = excluded.last_use,
                        unlocked_rewards = excluded.unlocked_rewards
                ''', (
                    user_id, new_streak, highest_streak, current_time,
                    json.dumps(unlocked_rewards)
                ))
                conn.commit()

                return new_streak, highest_streak, unlocked_rewards

        except Exception as e:
            logger.error(f"Error updating user streak: {e}")
            return 0, 0, []

    def _check_rewards(self, streak: int, current_rewards: list) -> list:
        """Check and return any new rewards based on streak count."""
        new_rewards = []
        reward_tiers = {
            5: "meme_lord",      # Unlocks special meme responses
            10: "dank_memer",    # Original dank_memer persona
            25: "chaos_agent",   # Unlocks more chaotic responses
            50: "elite_status",  # Special status and custom response formats
            100: "legendary"     # Ultimate tier with all features
        }

        for tier, reward in reward_tiers.items():
            if streak >= tier and reward not in current_rewards:
                new_rewards.append(reward)
                logger.info(f"New reward unlocked: {reward} at streak {streak}")

        return new_rewards

    def get_user_streak(self, user_id: int) -> tuple:
        """Get current streak info for a user."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT streak_count, highest_streak, unlocked_rewards 
                    FROM user_streaks 
                    WHERE user_id = ?
                ''', (user_id,))
                result = cursor.fetchone()

                if result:
                    streak, highest, rewards = result
                    return streak, highest, json.loads(rewards)
                return 0, 0, []

        except Exception as e:
            logger.error(f"Error getting user streak: {e}")
            return 0, 0, []

    def save_user_preference(self, user_id: int, default_persona: str = None, custom_settings: dict = None) -> bool:
        """Save user preferences."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_time = datetime.now()

                if custom_settings is None:
                    custom_settings = {}

                # Use parameterized query to prevent SQL injection
                cursor.execute('''
                    INSERT INTO user_preferences (
                        user_id, default_persona, custom_settings, updated_at
                    ) VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        default_persona = COALESCE(?, default_persona),
                        custom_settings = ?,
                        updated_at = ?
                ''', (
                    user_id, default_persona, json.dumps(custom_settings), current_time,
                    default_persona, json.dumps(custom_settings), current_time
                ))
                conn.commit()
                return True

        except Exception as e:
            logger.error(f"Error saving user preferences: {e}")
            return False

    def get_user_preferences(self, user_id: int) -> tuple:
        """Get user preferences."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT default_persona, custom_settings 
                    FROM user_preferences 
                    WHERE user_id = ?
                ''', (user_id,))
                result = cursor.fetchone()

                if result:
                    persona, settings = result
                    return persona, json.loads(settings)
                return None, {}

        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return None, {}