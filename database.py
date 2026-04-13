from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Database setup
engine = create_engine("sqlite:///ethio_video_saas.db", echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ====================== MODELS ======================

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)                    # ← Added for signup
    hashed_password = Column(String, nullable=False)             # ← Required for auth
    stripe_customer_id = Column(String, nullable=True)
    credits = Column(Float, default=10.0)                        # ← Better as Float
    is_active = Column(Boolean, default=True)
    subscription_plan = Column(String, default="free")           # ← Useful for future
    created_at = Column(DateTime, default=datetime.utcnow)       # ← Added
    
    jobs = relationship("Job", back_populates="user")


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True)                        # UUID as string
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="processing")                # processing, completed, failed
    video_url = Column(String, nullable=True)
    cost_credits = Column(Float, default=0.0)
    language = Column(String)
    platform_posted = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    views = Column(Integer, default=0)
    
    user = relationship("User", back_populates="jobs")


# Create tables
Base.metadata.create_all(bind=engine)
