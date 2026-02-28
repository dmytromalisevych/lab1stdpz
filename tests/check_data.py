import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_data():
    db_path = Path(__file__).parent.parent / "voting_system.db"
    
    logger.info(f"Checking database at: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        logger.info("\nChecking database structure:")
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            if table[0]: 
                logger.info(f"\n{table[0]}")
        
        logger.info("\nChecking users table:")
        cursor.execute("SELECT id, username, email, is_active, is_admin FROM users")
        users = cursor.fetchall()
        logger.info(f"Found {len(users)} users:")
        for user in users:
            logger.info(f"User ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Active: {user[3]}, Admin: {user[4]}")
        
        logger.info("\nChecking polls table:")
        cursor.execute("SELECT id, title, is_active, created_by FROM polls")
        polls = cursor.fetchall()
        logger.info(f"Found {len(polls)} polls:")
        for poll in polls:
            logger.info(f"Poll ID: {poll[0]}, Title: {poll[1]}, Active: {poll[2]}, Created by: {poll[3]}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error checking database: {str(e)}")

if __name__ == "__main__":
    check_database_data()