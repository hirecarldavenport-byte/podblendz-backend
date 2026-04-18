from pathlib import Path
from typing import Optional, List, Any

from .schema import Transcript, Segment


class TranscriptionError(Exception):
    """Raised when transcription fails."""


class Transcriber:
    def __init__(self, model_name: str = "large-v3"):
        self.model_name = model_name
        self._model: Optional[Any] = None  # Whisper model, loaded lazily

    def _load_model(self) -> None:
        """
        Lazy-load the Whisper ASR model.
        """
        if self._model is not None:
            return

        try:
            import whisper  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Whisper is not installed. Install with: pip install openai-whisper"
            ) from exc

        self._model = whisper.load_model(self.model_name)

    def transcribe_file(self, audio_path: Path, episode_id: str) -> Transcript:
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        self._load_model()

        # ✅ Type narrowing for Pylance
        assert self._model is not None, "ASR model failed to load"

        try:
            result = self._model.transcribe(
                str(audio_path),
                verbose=False,
            )
        except Exception as exc:
            raise TranscriptionError(
                f"Failed to transcribe {audio_path.name}"
            ) from exc

        segments: List[Segment] = []
        for seg in result.get("segments", []):
            segments.append(
                Segment(
                    start=float(seg["start"]),
                    end=float(seg["end"]),
                    speaker=None,
                    text=seg["text"].strip(),
                )
            )

        return Transcript(
            episode_id=episode_id,
            duration=float(result.get("duration", 0.0)),
            segments=segments,
        )