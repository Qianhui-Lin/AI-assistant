import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

AWS_BUCKET = os.getenv("AWS_BUCKET_NAME", "bucket-name")
AWS_KEY = os.getenv("AWS_S3_KEY", "key")


def load_text_from_s3() -> str:
    """Downloads the handbook text file from S3 and returns it as a string."""

    s3 = boto3.client("s3")

    try:
        response = s3.get_object(Bucket=AWS_BUCKET, Key=AWS_KEY)
        text = response["Body"].read().decode("utf-8")
        print(f"Loaded handbook text from s3://{AWS_BUCKET}/{AWS_KEY}")
        return text

    except NoCredentialsError:
        raise RuntimeError("AWS credentials not found. Configure via environment variables.")

    except ClientError as e:
        raise RuntimeError(f"Failed to load from S3: {e}")
