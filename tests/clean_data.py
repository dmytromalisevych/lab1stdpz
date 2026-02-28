import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_duplicate_polls():
    db_path = Path(__file__).parent.parent / "voting_system.db"
    
    logger.info(f"Cleaning duplicate polls in database at: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, COUNT(*) as count
            FROM polls
            GROUP BY title
            HAVING count > 1
        """)
        duplicates = cursor.fetchall()
        
        for title, count in duplicates:
            logger.info(f"Found {count} duplicates for poll: {title}")
            
            cursor.execute("""
                DELETE FROM polls 
                WHERE title = ? 
                AND id NOT IN (
                    SELECT MIN(id) 
                    FROM polls 
                    WHERE title = ?
                )
            """, (title, title))
        
        conn.commit()
        
        # Перевіряємо результат
        cursor.execute("SELECT id, title, is_active, created_by FROM polls ORDER BY id")
        polls = cursor.fetchall()
        
        logger.info("\nRemaining polls after cleanup:")
        for poll in polls:
            logger.info(f"Poll ID: {poll[0]}, Title: {poll[1]}, Active: {poll[2]}, Created by: {poll[3]}")
        
        conn.close()
        logger.info("Duplicate polls cleaned successfully")
        
    except Exception as e:
        logger.error(f"Error cleaning duplicate polls: {str(e)}")
        conn.rollback()

if __name__ == "__main__":
    clean_duplicate_polls()