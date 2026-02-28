from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .database import engine, Base, SessionLocal
from .models import User, Role, Poll, PollOption, Vote
import bcrypt

def seed_database():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        
        admin_role = Role(name="admin", description="Адміністратор системи")
        user_role = Role(name="user", description="Звичайний користувач")
        db.add_all([admin_role, user_role])
        db.commit()

        
        admin_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
        admin = User(
            username="admin",
            email="admin@example.com",
            hashed_password=admin_password,
            roles=[admin_role]
        )
        
        user_password = bcrypt.hashpw("user123".encode('utf-8'), bcrypt.gensalt())
        user1 = User(
            username="dmytromalisevych",
            email="dmytro@example.com",
            hashed_password=user_password,
            roles=[user_role]
        )
        
        db.add_all([admin, user1])
        db.commit()

        polls = [
            Poll(
                title="Найкраща мова програмування",
                description="Яка мова програмування вам подобається найбільше?",
                created_at=datetime.utcnow(),
                ends_at=datetime.utcnow() + timedelta(days=7),
                is_active=True,
                allow_multiple=True,
                creator=admin,
                options=[
                    PollOption(text="Python"),
                    PollOption(text="JavaScript"),
                    PollOption(text="Java"),
                    PollOption(text="C++")
                ]
            ),
            Poll(
                title="Улюблений фреймворк",
                description="Який веб-фреймворк ви використовуєте найчастіше?",
                created_at=datetime.utcnow(),
                ends_at=datetime.utcnow() + timedelta(days=5),
                is_active=True,
                creator=user1,
                options=[
                    PollOption(text="FastAPI"),
                    PollOption(text="Django"),
                    PollOption(text="Flask"),
                    PollOption(text="Express.js")
                ]
            )
        ]
        
        db.add_all(polls)
        db.commit()

        print("База даних успішно заповнена тестовими даними!")
        
    except Exception as e:
        print(f"Помилка при заповненні бази даних: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()