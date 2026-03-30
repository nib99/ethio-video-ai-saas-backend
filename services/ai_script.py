from openai import AsyncOpenAI
import json
import logging
from typing import List, Dict

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = logging.getLogger(__name__)

async def generate_cinematic_scenes(text: str, language: str) -> List[Dict]:
    prompt = f"""
    VIRAL HOOK ENGINE v2 for {language} (Amharic/Afaan Oromo/Tigrinya/Somali).
    First scene: 2-second emotional/cultural hook.
    Build escalation. Final scene: strong CTA.
    Return ONLY JSON array of objects.
    """
    try:
        resp = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt + f"\nText: {text}"}],
            temperature=0.85,
            response_format={"type": "json_object"}
        )
        data = json.loads(resp.choices[0].message.content)
        return data if isinstance(data, list) else data.get("scenes", [])
    except Exception as e:
        logger.error(f"Hook engine failed: {e}")
        return [{"scene_number": 1, "spoken_text": text, "visual_prompt": "Cinematic Ethiopian scene", "emotion": "inspirational", "duration_seconds": 5}]
