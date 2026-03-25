from fastapi import APIRouter, UploadFile, File
from podpal.services.s3 import S3Service
router = APIRouter(prefix="/s3", tags=["S3"])
s3 = S3Service()
