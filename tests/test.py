from src.database.database import engine, Base
from src.database.models import Poll, PollOption

print("Testing imports...")
print("Engine:", engine)
print("Base:", Base)

try:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
except Exception as e:
    print("Error:", e)