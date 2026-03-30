import os
import logging
import requests
from services.ai_script import generate_cinematic_scenes
from services.video_engine import create_cinematic_video
from database import Job, SessionLocal

logger = logging.getLogger(__name__)

async def run_pipeline(job_id: str, text: str, language: str, tier: str, user_id: int):
    db = SessionLocal()
    try:
        scenes = await generate_cinematic_scenes(text, language)
        video_path = await create_cinematic_video(scenes, language, tier)

        job = Job(
            id=job_id,
            user_id=user_id,
            status="completed",
            video_url=video_path,
            cost_credits=2,
            language=language
        )
        db.add(job)
        db.commit()

        # Auto-post to Telegram
        await post_to_telegram(video_path)

        logger.info(f"Job {job_id} completed successfully")
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        job = Job(id=job_id, user_id=user_id, status="failed", cost_credits=0, language=language)
        db.add(job)
        db.commit()
    finally:
        db.close()

async def post_to_telegram(video_path: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID")
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendVideo"
    with open(video_path, "rb") as f:
        requests.post(url, data={"chat_id": chat_id}, files={"video": f})
