import sqlite3
import bcrypt
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_password_hashes():
    db_path = Path(__file__).parent.parent / "voting_system.db"
    
    logger.info(f"Checking password hashes in database at: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, username, password_hash FROM users")
        users = cursor.fetchall()
        
        test_passwords = {
            'admin': 'admin123',
            'dmytromalisevych': 'password123'
        }
        
        for user_id, username, password_hash in users:
            logger.info(f"\nChecking user: {username}")
            logger.info(f"Stored hash: {password_hash}")
            
            if username in test_passwords:
                try:
                    is_valid = bcrypt.checkpw(
                        test_passwords[username].encode('utf-8'),
                        password_hash.encode('utf-8')
                    )
                    logger.info(f"Password check result: {is_valid}")
                except Exception as e:
                    logger.error(f"Error checking password: {str(e)}")
                
                new_hash = bcrypt.hashpw(
                    test_passwords[username].encode('utf-8'),
                    bcrypt.gensalt()
                )
                logger.info(f"New hash format: {new_hash.decode('utf-8')}")
                
                cursor.execute(
                    "UPDATE users SET password_hash = ? WHERE username = ?",
                    (new_hash.decode('utf-8'), username)
                )
        
        conn.commit()
        conn.close()
        
        logger.info("\nPassword hashes updated successfully")
        
    except Exception as e:
        logger.error(f"Error checking password hashes: {str(e)}")
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    check_password_hashes()