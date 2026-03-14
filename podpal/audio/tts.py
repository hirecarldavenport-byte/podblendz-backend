import os
import edge_tts
import uuid
from datetime import datetime


def generate_audio(text: str, voice: str = "en-US-GuyNeural") -> str:
    """
    Generate an MP3 file from text using Edge-TTS.
    Returns the full path to the generated audio file.
    """

    # Ensure output directory exists
    output_dir = "media/clips"
    os.makedirs(output_dir, exist_ok=True)

    # Create unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    filename = f"blend_{timestamp}_{unique_id}.mp3"
    output_path = os.path.join(output_dir, filename)

    # Generate audio
    communicate = edge_tts.Communicate(text, voice)
    with open(output_path, "wb") as f:
        for chunk in communicate.stream_sync():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
                print("DEBUG — writing audio to:", output_path)

    return output_path