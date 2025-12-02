import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

AWS_BUCKET = os.getenv("AWS_BUCKET_NAME", "bucket-name")
AWS_UG_KEY = os.getenv("AWS_UG_KEY")
AWS_PGT_KEY = os.getenv("AWS_PGT_KEY")
AWS_PGR_KEY = os.getenv("AWS_PGR_KEY") 


def load_text_from_s3(key: str) -> str:
    """Downloads the handbook text file from S3 and returns it as a string."""

    s3 = boto3.client("s3")
    s3_key = key

    try:
        response = s3.get_object(Bucket=AWS_BUCKET, Key=s3_key)
        text = response["Body"].read().decode("utf-8")
        print(f"Loaded handbook text from s3://{AWS_BUCKET}/{s3_key}")
        return text

    except NoCredentialsError:
        raise RuntimeError("AWS credentials not found. Configure via environment variables.")

    except ClientError as e:
        raise RuntimeError(f"Failed to load from S3: {e}")

def load_text_from_s3_for_level(level: str) -> str:

    l = level.strip().lower()

    if l == "ug":
        key = AWS_UG_KEY
    elif l == "pgt":
        key = AWS_PGT_KEY
    elif l == "pgr":
        key = AWS_PGR_KEY
    else:
        raise ValueError(f"Unsupported level '{level}' for S3 load.")

    if not key:
        
        raise RuntimeError(
            f"No S3 key configured for level '{level}'. "
            f"Set AWS_{level.upper()}_KEY in your environment."
        )

    return load_text_from_s3(key)
