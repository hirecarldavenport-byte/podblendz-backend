# podpal/audio/tts.py

from __future__ import annotations

import os
import uuid
import asyncio
from datetime import datetime
from typing import Optional

import edge_tts
import logging

# Silence edge-tts and aiohttp debug chatter
logging.getLogger("edge_tts").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)


def generate_audio(
    text: str,
    voice: str = "en-US-GuyNeural",
    output_dir: str = "media",
    filename_prefix: str = "blend",
) -> str:
    """
    Generate TTS audio using Microsoft Edge TTS and return the written file path.

    This implementation uses edge_tts.Communicate(...).save(path) which is async.
    We call it from a sync function via asyncio.run(...).

    Args:
        text: The text to synthesize.
        voice: TTS voice (e.g., 'en-US-GuyNeural').
        output_dir: Output directory for the generated mp3.
        filename_prefix: Prefix for the generated filename.

    Returns:
        Absolute path to the generated MP3 file.

    Raises:
        RuntimeError: If the file could not be written or is empty.
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{filename_prefix}_{timestamp}_{unique_id}.mp3"
    output_path = os.path.abspath(os.path.join(output_dir, filename))

    # Use edge-tts to synthesize and save directly
    communicate = edge_tts.Communicate(text=text, voice=voice)

    async def _run_save() -> None:
        await communicate.save(output_path)

    # Run the async save from this sync function
    asyncio.run(_run_save())

    # Sanity check: ensure non-empty file
    try:
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError("TTS produced no audio; output file is missing or empty.")
    except Exception:
        # Clean up if a zero-byte file was created
        if os.path.exists(output_path) and os.path.getsize(output_path) == 0:
            try:
                os.remove(output_path)
            except Exception:
                pass
        raise

    print(f"🟢 TTS — wrote audio to: {output_path}")
    return output_path