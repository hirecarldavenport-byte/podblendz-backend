"""
Application configuration for PodBlendz.

This file intentionally contains only simple constants.
Sensitive values should come from environment variables.
"""

import os

# AWS / S3 configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

EPISODE_AUDIO_BUCKET = os.getenv(
    "EPISODE_AUDIO_BUCKET",
    "podblendz-episode-audio",
)