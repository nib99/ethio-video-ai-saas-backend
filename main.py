import os
import uuid
import stripe
import logging

from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, Request, Body
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import SessionLocal, User, Job
from services.pipeline import run_pipeline
from services.webhooks import process_stripe_webhook

# ✅ Merge auth imports here
from services.auth import (
    get_current_user, 
    get_password_hash, 
    verify_password, 
    create_access_token
)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="EthioVideo AI – Full SaaS Cinematic Backend 2026 💰")

# Create directories
os.makedirs("outputs", exist_ok=True)
os.makedirs("cache", exist_ok=True)

# Mount static files for generated videos
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class GenerateRequest(BaseModel):
    text: str
    language: str = "Amharic"
    tier: str = "premium"

class CheckoutRequest(BaseModel):
    email: str
    plan: str = "pay_per_video"
    
# ====================== SIGNUP / LOGIN ======================
@app.post("/api/signup")
def signup(email: str = Body(...), password: str = Body(...), db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    hashed = get_password_hash(password)
    user = User(email=email, hashed_password=hashed, credits=10)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    token = create_access_token({"sub": str(user.id)})
    return {
        "user": {"id": user.id, "email": user.email, "credits": user.credits},
        "token": token
    }

@app.post("/api/login")
def login(email: str = Body(...), password: str = Body(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token({"sub": str(user.id)})
    return {
        "user": {"id": user.id, "email": user.email, "credits": user.credits},
        "token": token
    }
# ====================== STRIPE CHECKOUT ======================
@app.post("/api/create-checkout")
async def create_checkout(request: CheckoutRequest):
    if not request.email:
        raise HTTPException(status_code=400, detail="Email is required")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": os.getenv("STRIPE_PRICE_ID"),   # Make sure this is set in .env
                "quantity": 1
            }],
            mode="payment",
            success_url="https://your-frontend-domain.com/success?session_id={CHECKOUT_SESSION_ID}",  # ← CHANGE THIS
            cancel_url="https://your-frontend-domain.com/dashboard/credits",                        # ← CHANGE THIS
            customer_email=request.email,
            metadata={
                "email": request.email,
                "plan": request.plan
            }
        )

        return {"checkout_url": session.url}

    except stripe.error.StripeError as e:
        logging.error(f"Stripe error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create Stripe checkout session")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ====================== STRIPE WEBHOOK ======================
@app.post("/api/webhook/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig, os.getenv("STRIPE_WEBHOOK_SECRET")
        )
        await process_stripe_webhook(event, db)
    except Exception as e:
        logging.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    return {"status": "success"}

# ====================== VIDEO GENERATION ======================
@app.post("/api/generate-cinematic-video")
async def start_generation(
    req: GenerateRequest,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.credits < 2:
        raise HTTPException(status_code=402, detail="Insufficient credits. Please purchase more.")

    job_id = str(uuid.uuid4())
    
    # Start background job
    bg.add_task(run_pipeline, job_id, req.text, req.language, req.tier, user.id)
    
    # Deduct credits immediately
    user.credits -= 2
    db.commit()

    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Video generation started. Check status with /api/status/{job_id}"
    }

# ====================== JOB STATUS ======================
@app.get("/api/status/{job_id}")
async def get_status(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == user.id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job

# ====================== ANALYTICS ======================
@app.get("/api/analytics")
async def analytics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    total = db.query(Job).filter(Job.user_id == user.id).count()
    completed = db.query(Job).filter(
        Job.user_id == user.id,
        Job.status == "completed"
    ).count()
    spent = db.query(Job).filter(Job.user_id == user.id).count() * 2

    return {
        "total_videos": total,
        "completed": completed,
        "credits_spent": spent,
        "estimated_roi": f"\~{(completed * 0.15):.2f} USD (based on avg view value)",
        "recent_jobs": db.query(Job)
            .filter(Job.user_id == user.id)
            .order_by(Job.created_at.desc())
            .limit(5)
            .all()
    }

# ====================== HEALTH CHECK ======================
@app.get("/")
async def health():
    return {
        "status": "🚀 EthioVideo AI SaaS Backend – Live & Monetized",
        "version": "2026.1"
    }
