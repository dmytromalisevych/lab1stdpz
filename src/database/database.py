from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_NAME = "voting_system.db"  
DB_PATH = os.path.join(BASE_DIR, DB_NAME)  

logger.info(f"Using database at: {DB_PATH}")

if not os.path.exists(DB_PATH):
    raise FileNotFoundError(f"Database file not found at: {DB_PATH}")

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection():
    """Перевіряємо з'єднання з існуючою базою даних"""
    try:
        with engine.connect() as connection:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            logger.info(f"Connected to existing database. Found tables: {tables}")
            
            for table in tables:
                columns = [col['name'] for col in inspector.get_columns(table)]
                logger.info(f"Table {table} structure: {columns}")
                
        return True
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return False

def init_db():
    """Ініціалізуємо з'єднання з існуючою базою даних"""
    if not check_db_connection():
        raise Exception("Failed to connect to existing database")
    logger.info("Successfully connected to existing database")