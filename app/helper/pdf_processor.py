import os
import pdfplumber
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
PDF_PATH = os.path.join(BASE_DIR, "data/original_pdf/PGR-Regs.pdf")
LOCAL_TEXT_PATH = os.path.join(BASE_DIR, "data/extracted/handbook.txt")

AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME", "bucket-name")
AWS_S3_KEY = os.getenv("AWS_S3_KEY", "key")

def extract_pdf_text(pdf_path: str) -> str:
    """Extract clean text from a PDF file."""
    print(f"Extracting text from: {pdf_path}")

    text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text.append(extracted)

    full_text = "\n\n".join(text)
    cleaned = "\n".join([line.strip() for line in full_text.splitlines() if line.strip()])

    print(f"Extracted {len(cleaned)} characters of text.")
    return cleaned

# Save text locally
def save_text_locally(text: str, output_path: str = LOCAL_TEXT_PATH):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Saved extracted text locally to: {output_path}")

# Upload to AWS S3
def upload_to_s3(text_path: str, bucket_name: str = AWS_BUCKET_NAME, key: str = AWS_S3_KEY):
    s3 = boto3.client("s3")

    try:
        s3.upload_file(text_path, bucket_name, key)
        print(f"Uploaded extracted text to s3://{bucket_name}/{key}")
    except FileNotFoundError:
        print("ERROR: Local text file not found.")
    except NoCredentialsError:
        print("ERROR: AWS credentials not found. Configure via environment variables.")
    except ClientError as e:
        print("AWS client error:", e)

def process_and_upload_pdf():
    """Full pipeline: PDF → extract text → save locally → upload to S3."""
    text = extract_pdf_text(PDF_PATH)
    save_text_locally(text)
    upload_to_s3(LOCAL_TEXT_PATH)
    return text

if __name__ == "__main__":
    process_and_upload_pdf()