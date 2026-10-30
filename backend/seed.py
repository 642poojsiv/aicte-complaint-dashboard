from app.database import Base, engine, SessionLocal
from app.models import User
from app.security import hash_password
Base.metadata.create_all(bind=engine)
db=SessionLocal()
for name,email,role in [
    ("System Administrator","admin@aicte.local","Admin"),
    ("Bureau Officer","officer@aicte.local","Officer"),
    ("Read Only Viewer","viewer@aicte.local","Viewer")]:
    if not db.query(User).filter_by(email=email).first():
        db.add(User(name=name,email=email,password_hash=hash_password("Password@123"),role=role))
db.commit(); db.close()
print("Seed complete. Demo password: Password@123")
