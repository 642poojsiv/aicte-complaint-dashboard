import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "development-only-change-me")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def hash_password(password): return pwd_context.hash(password)
def verify_password(password, hashed): return pwd_context.verify(password, hashed)
def create_token(user):
    exp = datetime.now(timezone.utc) + timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480")))
    return jwt.encode({"sub": str(user.id), "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)

def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    error = HTTPException(status_code=401, detail="Invalid or expired authentication token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise error
    user = db.get(User, user_id)
    if not user: raise error
    return user

def require_roles(*roles):
    def checker(user: User = Depends(current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="You do not have permission to perform this action")
        return user
    return checker
