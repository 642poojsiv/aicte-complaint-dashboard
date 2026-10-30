import os

from app.database import Base, engine, SessionLocal
from app.models import User
from app.security import hash_password

Base.metadata.create_all(bind=engine)

password = os.getenv("SEED_PASSWORD")

if not password:
    raise RuntimeError("SEED_PASSWORD environment variable is required.")

db = SessionLocal()

try:
    users = [
        ("System Administrator", "admin@example.com", "Admin"),
        ("Bureau Officer", "officer@example.com", "Officer"),
        ("Read Only Viewer", "viewer@example.com", "Viewer"),
    ]

    for name, email, role in users:
        existing_user = db.query(User).filter_by(email=email).first()

        if not existing_user:
            db.add(
                User(
                    name=name,
                    email=email,
                    password_hash=hash_password(password),
                    role=role,
                )
            )

    db.commit()
    print("Seed complete. Demo accounts created or already exist.")

finally:
    db.close()