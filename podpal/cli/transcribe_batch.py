from pathlib import Path
import logging

from podpal.transcription.transcriber import Transcriber, TranscriptionError
from podpal.transcription.normalizer import TranscriptNormalizer
from podpal.io.transcripts import TranscriptWriter


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def transcribe_batch(episodes_dir: Path, model_name: str = "medium") -> None:
    if not episodes_dir.exists():
        raise FileNotFoundError(episodes_dir)

    transcriber = Transcriber(model_name=model_name)
    normalizer = TranscriptNormalizer()

    episode_dirs = sorted(d for d in episodes_dir.iterdir() if d.is_dir())
    logger.info("Found %d episode folders", len(episode_dirs))

    for episode_dir in episode_dirs:
        episode_id = episode_dir.name
        audio = _find_audio(episode_dir)
        if audio is None:
            logger.warning("[%s] No audio found, skipping", episode_id)
            continue

        json_path = episode_dir / "transcript.json"
        txt_path = episode_dir / "transcript.txt"

        if json_path.exists():
            logger.info("[%s] Transcript exists, skipping", episode_id)
            continue

        logger.info("[%s] Transcribing: %s", episode_id, audio.name)

        try:
            raw = transcriber.transcribe_file(audio, episode_id)
        except TranscriptionError as exc:
            logger.error("[%s] Failed: %s", episode_id, exc)
            continue

        logger.info("[%s] Normalizing transcript", episode_id)
        clean = normalizer.normalize(raw)

        TranscriptWriter.write_all(clean, json_path, txt_path)
        logger.info("[%s] Transcription + normalization complete", episode_id)

    logger.info("Batch transcription finished")


def _find_audio(folder: Path) -> Path | None:
    for ext in (".mp3", ".wav", ".m4a", ".flac"):
        files = list(folder.glob(f"*{ext}"))
        if files:
            return files[0]
    return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("episodes_dir", type=Path)
    parser.add_argument("--model", default="medium")
    args = parser.parse_args()

    transcribe_batch(args.episodes_dir, args.model)
