import os
import uuid
import subprocess
from moviepy.editor import (ImageClip, concatenate_videoclips, AudioFileClip,
                            TextClip, CompositeVideoClip, CompositeAudioClip)
from moviepy.video.fx.all import fadein, fadeout
from services.scene_generator import generate_scene_image
from services.tts import tts_service
import logging

logger = logging.getLogger(__name__)

async def create_cinematic_video(scenes: list, language: str, tier: str) -> str:
    output_path = f"outputs/{uuid.uuid4()}_main.mp4"
    os.makedirs("outputs", exist_ok=True)

    scene_audios = []
    scene_durations = []
    image_paths = []

    for scene in scenes:
        audio_path = await tts_service.generate_audio(scene["spoken_text"], language)
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration

        scene_audios.append(audio_path)
        scene_durations.append(duration)
        image_paths.append(await generate_scene_image(scene, tier))

    clips = []
    for i, (img_path, dur, aud_path) in enumerate(zip(image_paths, scene_durations, scene_audios)):
        clip = ImageClip(img_path).set_duration(dur)
        clip = clip.resize(lambda t: 1 + 0.07 * (t / dur))  # Ken Burns zoom
        clip = clip.set_position(("center", "center"))

        if i > 0:
            clip = fadein(clip, 0.7)
        if i < len(scenes) - 1:
            clip = fadeout(clip, 0.7)

        # Layer music
        voice = AudioFileClip(aud_path)
        try:
            music = AudioFileClip("assets/background_music.mp3").volumex(0.12).subclip(0, dur)
            final_audio = CompositeAudioClip([voice, music])
        except:
            final_audio = voice
        clip = clip.set_audio(final_audio)
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")

    # Burn subtitles
    subtitle_clips = []
    current_time = 0.0
    font = "Noto-Sans-Ethiopic" if "am" in language.lower() else "Arial"
    for scene, dur in zip(scenes, scene_durations):
        txt_clip = TextClip(
            txt=scene["spoken_text"],
            fontsize=28,
            color="white",
            font=font,
            stroke_color="black",
            stroke_width=2,
            size=video.size
        ).set_position(("center", "bottom")).set_duration(dur).set_start(current_time)
        subtitle_clips.append(txt_clip)
        current_time += dur

    final = CompositeVideoClip([video] + subtitle_clips)
    final.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", preset="medium", threads=4)

    # Multi-format export
    formats = {
        "tiktok": "scale=1080:1920",
        "youtube": "scale=1280:720",
        "reels": "scale=1080:1080",
        "instagram": "scale=1080:1080"
    }
    base_name = output_path.replace("_main.mp4", "")
    for fmt_name, vf in formats.items():
        out_path = f"{base_name}_{fmt_name}.mp4"
        cmd = ["ffmpeg", "-i", output_path, "-vf", vf, "-c:v", "libx264", "-preset", "fast", "-crf", "23", out_path]
        subprocess.run(cmd, check=True)

    return output_path  # return main path; formats are side-by-side
