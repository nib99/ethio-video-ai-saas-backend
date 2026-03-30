from database import SessionLocal, Job

def track_views(job_id: str, platform: str, count: int = 1):
    db = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    if job:
        job.views += count
        if not job.platform_posted:
            job.platform_posted = platform
        db.commit()
    db.close()
