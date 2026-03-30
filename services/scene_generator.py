import hashlib
import os
import httpx
from openai import AsyncOpenAI
from typing import Dict

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
PEXELS_KEY = os.getenv("PEXELS_API_KEY")

async def generate_scene_image(scene: Dict, tier: str = "premium") -> str:
    prompt = scene.get("visual_prompt", "Cinematic scene")
    cache_key = hashlib.md5(prompt.encode()).hexdigest()
    cache_path = f"cache/{cache_key}.png"
    if os.path.exists(cache_path):
        return cache_path

    # Stock fallback for non-premium
    if tier != "premium" and PEXELS_KEY:
        try:
            async with httpx.AsyncClient() as http:
                r = await http.get(
                    "https://api.pexels.com/v1/search",
                    headers={"Authorization": PEXELS_KEY},
                    params={"query": prompt[:100], "per_page": 1}
                )
                data = r.json()
                if data.get("photos"):
                    url = data["photos"][0]["src"]["large"]
                    img_resp = await http.get(url)
                    with open(cache_path, "wb") as f:
                        f.write(img_resp.content)
                    return cache_path
        except:
            pass

    # Premium: GPT Image 1.5 (2026 flagship)
    try:
        resp = await client.images.generate(
            model="gpt-image-1.5",
            prompt=f"{prompt}, cinematic, filmic style, 16:9 aspect ratio, high detail",
            size="1792x1024",
            quality="hd",
            n=1
        )
        url = resp.data[0].url
        async with httpx.AsyncClient() as http:
            img_resp = await http.get(url)
        with open(cache_path, "wb") as f:
            f.write(img_resp.content)
        return cache_path
    except Exception as e:
        print(f"Image generation failed: {e}")
        return "https://picsum.photos/1280/720"  # ultimate fallback
