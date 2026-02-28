from database.database import SessionLocal
from database.models import Poll, PollOption, User
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

def seed_database():
    db = SessionLocal()
    try:
       
        db.query(PollOption).delete()
        db.query(Poll).delete()

       
        poll1 = Poll(
            title="Найкраща мова програмування 2025",
            description="Яка мова програмування, на вашу думку, найкраща для вивчення у 2025 році?",
            is_active=True,
            created_by=1,  
            ends_at=datetime.utcnow() + timedelta(days=7)
        )
        db.add(poll1)
        db.flush()

       
        options1 = [
            "Python",
            "JavaScript",
            "Java",
            "C++",
            "Go",
            "Rust"
        ]
        
        for text in options1:
            option = PollOption(
                poll_id=poll1.id,
                text=text
            )
            db.add(option)

      
        poll2 = Poll(
            title="Вибір фреймворка для веб-розробки",
            description="Який фреймворк ви використовуєте для веб-розробки?",
            is_active=True,
            created_by=1,
            ends_at=datetime.utcnow() + timedelta(days=7)
        )
        db.add(poll2)
        db.flush()


        options2 = [
            "Django",
            "Flask",
            "FastAPI",
            "Express.js",
            "React",
            "Vue.js"
        ]
        
        for text in options2:
            option = PollOption(
                poll_id=poll2.id,
                text=text
            )
            db.add(option)

        db.commit()
        print("Тестові дані успішно додано!")
        
    except Exception as e:
        db.rollback()
        print(f"Помилка при додаванні тестових даних: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()