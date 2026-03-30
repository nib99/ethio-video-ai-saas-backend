import os, uuid, httpx, logging
from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)

class TTSService:
    async def generate_audio(self, text: str, language: str) -> str:
        lang = language.lower().strip()
        try:
            if lang in ["amharic", "am", "አማርኛ"]:
                return await self._addis_ai(text, "am")
            elif lang in ["afaan oromo", "oromo", "om"]:
                return await self._addis_ai(text, "om")
            else:
                return await self._elevenlabs(text)
        except Exception:
            return await self._elevenlabs(text)

    async def _addis_ai(self, text: str, code: str) -> str:
        api_key = os.getenv("ADDIS_AI_API_KEY")
        url = "https://api.addisassistant.com/api/v1/audio"
        headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
        payload = {"text": text, "language": code}
        async with httpx.AsyncClient(timeout=40) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            audio_data = resp.content
        path = f"outputs/{uuid.uuid4()}.mp3"
        os.makedirs("outputs", exist_ok=True)
        with open(path, "wb") as f:
            f.write(audio_data)
        return path

    async def _elevenlabs(self, text: str) -> str:
        client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        audio = client.text_to_speech.convert(
            text=text,
            voice_id="21m00Tcm4TlvDq8ikWAM",
            model_id="eleven_multilingual_v2"
        )
        path = f"outputs/{uuid.uuid4()}.mp3"
        os.makedirs("outputs", exist_ok=True)
        with open(path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        return path

tts_service = TTSService()
