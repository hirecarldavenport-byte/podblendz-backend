import boto3
import os
from botocore.exceptions import BotoCoreError, ClientError

AWS_REGION = "us-east-1"
OUTPUT_DIR = "media/audio"

def synthesize_narration(text: str, filename: str) -> str:
    """
    Generate narration audio via AWS Polly and save as MP3.
    Returns the path to the generated audio file.
    """
    polly = boto3.client("polly", region_name=AWS_REGION)

    try:
        response = polly.synthesize_speech(
            Text=text,
            OutputFormat="mp3",
            VoiceId="Joanna",
            Engine="neural"
        )
    except (BotoCoreError, ClientError) as error:
        raise RuntimeError(f"AWS Polly error: {error}")

    if "AudioStream" not in response:
        raise RuntimeError("No AudioStream returned from Polly")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, filename)

    with open(output_path, "wb") as f:
        f.write(response["AudioStream"].read())

    return output_path
