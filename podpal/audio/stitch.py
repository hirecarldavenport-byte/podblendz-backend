"""
Audio stitching utilities for PodBlendz.

Purpose:
- Concatenate real podcast audio clips and narration audio
- Preserve original audio quality (no re-encoding)
- Create a single, listenable Blendz audio artifact

Implementation:
- Uses FFmpeg concat demuxer (industry standard)
"""

from pathlib import Path
import subprocess
import imageio_ffmpeg
from typing import List


def create_concat_file(
    audio_files: List[str],
    concat_file: str,
) -> None:
    """
    Create a FFmpeg-compatible concat file.

    Each line must be in the form:
        file 'path/to/audio.ext'
    """

    lines = []
    for audio in audio_files:
        path = Path(audio).resolve()
        lines.append(f"file '{path.as_posix()}'")

    Path(concat_file).write_text("\n".join(lines), encoding="utf-8")


def stitch_blendz(
    audio_files: List[str],
    output_file: str,
    temp_concat_file: str = "blendz_concat.txt",
) -> None:
    """
    Stitch multiple audio files into a single Blendz output.

    Parameters:
    - audio_files: ordered list of audio file paths
                   (e.g. clip, narration, clip, narration)
    - output_file: final Blendz audio file
    """

    create_concat_file(audio_files, temp_concat_file)

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", temp_concat_file,
            "-c", "copy",
            output_file,
        ],
        check=True,
    )

    print(f"✅ Blendz audio created → {output_file}")