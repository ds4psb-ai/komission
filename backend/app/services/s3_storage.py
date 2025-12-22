import boto3
from botocore.exceptions import NoCredentialsError
import uuid
import os
from app.config import settings

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME

    async def upload_file(self, file_content: bytes, file_name: str, content_type: str = None) -> str:
        """
        Uploads a file to S3 and returns the public URL.
        """
        try:
            # Generate a unique filename to prevent collisions
            ext = os.path.splitext(file_name)[1]
            unique_filename = f"{uuid.uuid4()}{ext}"
            
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=unique_filename,
                Body=file_content,
                **extra_args
            )

            # Construct the URL based on the region and bucket
            url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{unique_filename}"
            return url

        except NoCredentialsError:
            print("Credentials not available")
            return None
        except Exception as e:
            print(f"Error uploading to S3: {e}")
            raise e

s3_service = S3Service()
