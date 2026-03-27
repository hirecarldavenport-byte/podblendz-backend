from fastapi import APIRouter, UploadFile, File
from podpal.services.s3_service import S3Service

router = APIRouter(prefix="/s3", tags=["S3"])
s3 = S3Service()

@router.get("/test-upload")
def test_upload():
    return s3.test_upload()

@router.get("/presign-url")
def presign_url(key: str):
    return s3.get_presigned_url(key)

@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    return await s3.upload_file(file)