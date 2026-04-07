import os
from typing import Optional, cast

USE_POLLY = os.getenv("USE_POLLY", "false").lower() == "true"
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


def synthesize_narration(text: str, filename: str) -> str:
    """
    Generate an audio narration file.

    Safe, production-grade:
    - Polly disabled by default
    - Never raises
    - Falls back automatically on failure
    """

    output_path = f"/audio/{filename}"

    # ---------------------------------------------------------
    # Polly disabled → stub
    # ---------------------------------------------------------
    if not USE_POLLY:
        print("[Polly] Disabled — returning stub audio path")
        return output_path

    # ---------------------------------------------------------
    # Polly enabled → attempt synthesis
    # ---------------------------------------------------------
    try:
        import boto3
        from botocore.response import StreamingBody

        polly = boto3.client("polly", region_name=AWS_REGION)

        response = polly.synthesize_speech(
            Text=text,
            OutputFormat="mp3",
            VoiceId="Matthew",
        )

        audio_stream = cast(StreamingBody, response.get("AudioStream"))

        if audio_stream is None:
            raise RuntimeError("AWS Polly returned no AudioStream")

        os.makedirs("audio", exist_ok=True)

        with open(f"audio/{filename}", "wb") as f:
            f.write(audio_stream.read())

        print("[Polly] Audio synthesized successfully")
        return output_path

    except Exception as exc:
        print("[Polly] ERROR — falling back to stub:", exc)
        return output_path

