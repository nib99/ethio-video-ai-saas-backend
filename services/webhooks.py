async def process_stripe_webhook(event, db):
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        email = session.get("customer_email") or session.get("metadata", {}).get("email")
        
        if email:
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.credits += 20   # or read from metadata
                db.commit()
                logging.info(f"✅ Added 20 credits to {email}")
