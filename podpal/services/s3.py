import os
import boto3
from fastapi import UploadFile

class S3Service:
    def __init__(self,
                 region: str | None = None,
                 narrator_bucket: str = "a-narrator-audio",
                 blendz_bucket: str = "b-blendz-audio"):

        self.region = region or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        self.narrator_bucket = narrator_bucket
        self.blendz_bucket = blendz_bucket
        self.client = boto3.client("s3", region_name=self.region)

