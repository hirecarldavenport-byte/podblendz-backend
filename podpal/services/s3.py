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

    def test_upload(self):
        key = "render-test-upload.txt"
        content = b"Render to S3 connection works!"

        try:
            self.client.put_object(
                Bucket=self.narrator_bucket,
                Key=key,
                Body=content
            )
            return {
                "status": "success",
                "file": f"s3://{self.narrator_bucket}/{key}"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_presigned_url(self, key: str, expires_in: int = 3600):
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.narrator_bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return {"url": url}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def upload_file(self, file: UploadFile):
        key = file.filename
        data = await file.read()
        try:
            self.client.put_object(Bucket=self.narrator_bucket, Key=key, Body=data)
            return {"status": "success", "file": f"s3://{self.narrator_bucket}/{key}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

