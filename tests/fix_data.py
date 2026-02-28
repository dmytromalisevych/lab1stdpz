import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database_structure():
    db_path = Path(__file__).parent.parent / "voting_system.db"
    
    logger.info(f"Fixing database at: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        logger.info("Creating backup of existing data...")
        
        cursor.execute("SELECT * FROM users")
        users_data = cursor.fetchall()
        
        cursor.execute("SELECT * FROM polls")
        polls_data = cursor.fetchall()
        
        cursor.execute("SELECT * FROM poll_options")
        options_data = cursor.fetchall()
        
        logger.info("Updating database structure...")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            is_admin BOOLEAN NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS polls_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ends_at TIMESTAMP,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            allow_multiple BOOLEAN NOT NULL DEFAULT 0,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS poll_options_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poll_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            FOREIGN KEY (poll_id) REFERENCES polls (id) ON DELETE CASCADE
        )
        """)
        
        logger.info("Migrating data to new tables...")
        
        for user in users_data:
            cursor.execute("""
            INSERT INTO users_new (username, email, password_hash, is_active, is_admin)
            VALUES (?, ?, ?, ?, ?)
            """, (user[1], user[2], user[3], user[4], user[5]))
        
        for poll in polls_data:
            cursor.execute("""
            INSERT INTO polls_new (title, description, created_at, ends_at, is_active, allow_multiple, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (poll[1], poll[2], poll[3], poll[4], poll[5], poll[6], 1))  
        
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("ALTER TABLE users_new RENAME TO users")
        
        cursor.execute("DROP TABLE IF EXISTS polls")
        cursor.execute("ALTER TABLE polls_new RENAME TO polls")
        
        cursor.execute("DROP TABLE IF EXISTS poll_options")
        cursor.execute("ALTER TABLE poll_options_new RENAME TO poll_options")
        
        conn.commit()
        
        logger.info("\nChecking fixed database structure:")
        
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        logger.info(f"Users count: {len(users)}")
        for user in users:
            logger.info(f"User ID: {user[0]}, Username: {user[1]}, Email: {user[2]}")
        
        cursor.execute("SELECT * FROM polls")
        polls = cursor.fetchall()
        logger.info(f"\nPolls count: {len(polls)}")
        for poll in polls:
            logger.info(f"Poll ID: {poll[0]}, Title: {poll[1]}, Active: {poll[5]}")
        
        logger.info("Database structure fixed successfully")
        
    except Exception as e:
        logger.error(f"Error fixing database: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database_structure()