import src.database.database as db

print("Testing database connection...")
print("Engine:", db.engine)
print("Base:", db.Base)

try:
    db.Base.metadata.create_all(bind=db.engine)
    print("Database tables created successfully!")
except Exception as e:
    print("Error creating database:", e)