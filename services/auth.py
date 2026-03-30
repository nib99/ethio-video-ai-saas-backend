from fastapi import HTTPException
from database import SessionLocal, User

def get_current_user(user_id: int = 1):  # Demo – use real auth in production
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    db.close()
    if not user:
        raise HTTPException(401, "User not found")
    return user
