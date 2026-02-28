import sqlite3
import bcrypt
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_user_passwords():
    db_path = Path(__file__).parent.parent / "voting_system.db"
    
    logger.info(f"Updating user passwords in database at: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        passwords = {
            'admin': 'admin123',  
            'dmytromalisevych': 'password123'  
        }
        
        for username, password in passwords.items():
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            
            cursor.execute("""
                UPDATE users 
                SET password_hash = ? 
                WHERE username = ?
            """, (hashed.decode('utf-8'), username))
            
            logger.info(f"Updated password for user: {username}")
        
        conn.commit()
        
        cursor.execute("SELECT id, username, email, is_active, is_admin FROM users")
        users = cursor.fetchall()
        
        logger.info("\nUpdated users:")
        for user in users:
            logger.info(f"User ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Active: {user[3]}, Admin: {user[4]}")
        
        conn.close()
        logger.info("User passwords updated successfully")
        
        logger.info("\nLogin credentials:")
        for username, password in passwords.items():
            logger.info(f"Username: {username}")
            logger.info(f"Password: {password}")
            logger.info("---")
        
    except Exception as e:
        logger.error(f"Error updating user passwords: {str(e)}")
        conn.rollback()

if __name__ == "__main__":
    update_user_passwords()