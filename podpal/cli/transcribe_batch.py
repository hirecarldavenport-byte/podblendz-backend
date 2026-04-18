from pathlib import Path
import logging

from podpal.transcription.transcriber import Transcriber, TranscriptionError
from podpal.io.transcripts import TranscriptWriter


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)


def transcribe_batch(
    episodes_dir: Path,
    model_name: str = "medium",
) -> None:
    """
    Batch-transcribe podcast episodes.

    Expects structure:
    episodes/
      ep_001/
        audio.mp3
      ep_002/
        audio.mp3

    Writes:
      transcript.json
      transcript.txt

    Safe to re-run: skips episodes with existing transcripts.
    """
    if not episodes_dir.exists():
        raise FileNotFoundError(f"Episodes directory not found: {episodes_dir}")

    transcriber = Transcriber(model_name=model_name)

    episode_dirs = sorted(
        d for d in episodes_dir.iterdir()
        if d.is_dir()
    )

    if not episode_dirs:
        logger.warning("No episode folders found.")
        return

    logger.info("Found %d episode folders", len(episode_dirs))

    for episode_dir in episode_dirs:
        episode_id = episode_dir.name
        audio_path = _find_audio_file(episode_dir)

        if audio_path is None:
            logger.warning("[%s] No audio file found, skipping", episode_id)
            continue

        json_path = episode_dir / "transcript.json"
        txt_path = episode_dir / "transcript.txt"

        if json_path.exists():
            logger.info("[%s] Transcript already exists, skipping", episode_id)
            continue

        logger.info("[%s] Transcribing: %s", episode_id, audio_path.name)

        try:
            transcript = transcriber.transcribe_file(
                audio_path=audio_path,
                episode_id=episode_id,
            )
        except TranscriptionError as exc:
            logger.error("[%s] Transcription failed: %s", episode_id, exc)
            continue

        TranscriptWriter.write_all(
            transcript,
            json_path=json_path,
            txt_path=txt_path,
        )

        logger.info("[%s] Transcription complete", episode_id)

    logger.info("Batch transcription finished")


def _find_audio_file(episode_dir: Path) -> Path | None:
    """
    Find the first supported audio file in an episode directory.
    """
    for ext in (".mp3", ".wav", ".m4a", ".flac"):
        files = list(episode_dir.glob(f"*{ext}"))
        if files:
            return files[0]
    return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Batch transcribe podcast episodes")
    parser.add_argument(
        "episodes_dir",
        type=Path,
        help="Directory containing episode folders",
    )
    parser.add_argument(
        "--model",
        default="medium",
        help="Whisper model name (base, small, medium, large-v3)",
    )

    args = parser.parse_args()
    transcribe_batch(args.episodes_dir, model_name=args.model)
