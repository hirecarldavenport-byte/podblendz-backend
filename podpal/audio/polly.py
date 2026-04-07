def synthesize_narration(text: str, filename: str) -> str:
    """
    Temporary stub for audio synthesis.

    This bypasses AWS Polly so the API can operate
    without external credentials during development.
    """
    print("Polly stub active — returning placeholder audio path")
    return f"/audio/{filename}"
