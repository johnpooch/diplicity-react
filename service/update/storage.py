import boto3
from django.conf import settings


def bundle_storage_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )


def upload_bundle(path, object_key):
    bundle_storage_client().upload_file(
        str(path),
        settings.R2_BUCKET_NAME,
        object_key,
        ExtraArgs={"ContentType": "application/zip"},
    )
