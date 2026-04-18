from pathlib import Path
from typing import Optional, Any, List

from .schema import Transcript, Segment


class TranscriptionError(Exception):
    pass


class Transcriber:
    def __init__(self, model_name: str = "medium"):
        self.model_name = model_name
        self._model: Optional[Any] = None

    def _load_model(self) -> None:
        if self._model is not None:
            return

        try:
            import whisper  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Whisper not installed. Run: pip install openai-whisper"
            ) from exc

        self._model = whisper.load_model(self.model_name)

    def transcribe_file(self, audio_path: Path, episode_id: str) -> Transcript:
        if not audio_path.exists():
            raise FileNotFoundError(audio_path)

        self._load_model()
        assert self._model is not None

        try:
            result = self._model.transcribe(
                str(audio_path),
                verbose=False,
                temperature=0.0,
                condition_on_previous_text=False,
                no_speech_threshold=0.6,
                logprob_threshold=-1.0,
                compression_ratio_threshold=2.4,
            )
        except Exception as exc:
            raise TranscriptionError(str(exc)) from exc

        segments: List[Segment] = []
        for seg in result.get("segments", []):
            text = seg["text"].strip()
            if not text:
                continue
            segments.append(
                Segment(
                    start=float(seg["start"]),
                    end=float(seg["end"]),
                    speaker=None,
                    text=text,
                )
            )

        duration = (
            float(result.get("duration"))
            if result.get("duration") is not None
            else (max((s.end for s in segments), default=0.0))
        )

        return Transcript(
            episode_id=episode_id,
            duration=duration,
            segments=segments,
        )