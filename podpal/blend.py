# podpal/blend.py

def blend_transcript(text: str) -> str:
    """
    Minimal blending function.
    """
    if not text:
        return ""
    cleaned = " ".join(text.split())
    return f"Blended version:\n\n{cleaned}"

class BlendEngine:
    """
    Minimal engine wrapper around blend_transcript.
    Extend with steps: load transcript, clean, summarize, TTS, etc.
    """
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path

    def blend(self, text: str) -> str:
        return blend_transcript(text)