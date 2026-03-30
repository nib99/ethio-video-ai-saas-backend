from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

engine = create_engine("sqlite:///ethio_video_saas.db", echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    stripe_customer_id = Column(String)
    credits = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)
    jobs = relationship("Job", back_populates="user")

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String)  # processing, completed, failed
    video_url = Column(String)
    cost_credits = Column(Integer)
    language = Column(String)
    platform_posted = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    views = Column(Integer, default=0)
    user = relationship("User", back_populates="jobs")

Base.metadata.create_all(bind=engine)
