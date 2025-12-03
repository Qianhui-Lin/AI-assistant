import os
import pdfplumber
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME", "bucket-name")
AWS_UG_KEY = os.getenv("AWS_UG_KEY")
AWS_PGT_KEY = os.getenv("AWS_PGT_KEY")
AWS_PGR_KEY = os.getenv("AWS_PGR_KEY") 
AWS_ACADEMIC_KEY = os.getenv("AWS_ACADEMIC_KEY") 

def get_path_name(type:str,level:str|None=None):
    if type.lower() == "handbook":
        if level is None:
            raise ValueError("level is required when type is 'handbook'")
        pdf_path = os.path.join(BASE_DIR, f"data/original_pdf/{type}-{level}.pdf")
        local_text_path = os.path.join(BASE_DIR, f"data/extracted/{type}-{level}.txt")
    else:
        pdf_path = os.path.join(BASE_DIR, f"data/original_pdf/{type}.pdf")
        local_text_path = os.path.join(BASE_DIR, f"data/extracted/{type}.txt")
    return pdf_path, local_text_path

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
def save_text_locally(text: str, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Saved extracted text locally to: {output_path}")

# Upload to AWS S3
def upload_to_s3(text_path: str, key: str, bucket_name: str = AWS_BUCKET_NAME):
    s3 = boto3.client("s3")

    try:
        s3.upload_file(Filename = text_path, Bucket=bucket_name,Key=key)
        print(f"Uploaded extracted text to s3://{bucket_name}/{key}")
    except FileNotFoundError:
        print("ERROR: Local text file not found.")
    except NoCredentialsError:
        print("ERROR: AWS credentials not found. Configure via environment variables.")
    except ClientError as e:
        print("AWS client error:", e)

def process_and_upload_pdf_for_other_document(pdf_path: str, local_text_path: str,s3_key: str):
    """Full pipeline: PDF → extract text → save locally → upload to S3."""
    text = extract_pdf_text(pdf_path)
    save_text_locally(text,local_text_path)
    upload_to_s3(text_path=local_text_path,key=s3_key,bucket_name=AWS_BUCKET_NAME)
    return text

def process_and_upload_pdf_for_level(
    pdf_path: str,
    local_text_path: str,
    level: str,
):
    """
    Full pipeline for a specific level:
    PDF → extract text → save locally → upload to the correct S3 key.
    """
    # Extract
    text = extract_pdf_text(pdf_path)

    # Save locally
    save_text_locally(text, local_text_path)

    # Find correct S3 key for this level
    level_lower = level.lower()
    if level_lower == "ug":
        s3_key = AWS_UG_KEY
    elif level_lower == "pgt":
        s3_key = AWS_PGT_KEY
    elif level_lower == "pgr":
        s3_key = AWS_PGR_KEY
    else:
        raise ValueError(f"Unsupported level '{level}'. Must be ug/pgt/pgr.")

    if not s3_key:
        raise RuntimeError(
            f"No S3 key configured for level '{level}'. "
            f"Please set AWS_{level.upper()}_KEY in your .env"
        )

    # Upload
    upload_to_s3(text_path=local_text_path,key=s3_key,bucket_name=AWS_BUCKET_NAME)

    return text

def process_all_handbooks(levels=None):
    """
    Process and upload handbook PDFs for one or more levels.

    Parameters
    ----------
    levels : None | str | list[str]
        - None       → process ["UG", "PGT", "PGR"]
        - "UG"       → process only UG
        - ["UG","PGT"] → process UG and PGT
    """
    # Default: all levels
    if levels is None:
        levels = ["ug", "pgt", "pgr"]

    # Allow a single string as input
    if isinstance(levels, str):
        levels = [levels]

    # Normalise and validate
    valid_levels = {"ug", "pgt", "pgr"}
    norm_levels = []
    for lvl in levels:
        lvl_norm = lvl.strip().upper()
        if lvl_norm.lower() not in valid_levels:
            raise ValueError(f"Unsupported level '{lvl}'. Must be one of ug/pgt/pgr.")
        norm_levels.append(lvl_norm)

    # Process each requested level
    for level in norm_levels:
        pdf_path, local_text_path = get_path_name("handbook", level)
        print(f"\n=== Processing {level} handbook ===")
        process_and_upload_pdf_for_level(
            pdf_path=pdf_path,
            local_text_path=local_text_path,
            level=level,
        )

def process_other_document(type: str):
    """
    Process and upload other document types (e.g., academic integrity).

    """
    # Default: all levels
    if type=="handbook":
        raise ValueError("For handbook, please use process_all_handbooks() instead.")
    pdf_path, local_text_path = get_path_name(type)
    print(f"\n=== Processing {type} document ===")
    if type=="academic-integrity":
        s3_key = AWS_ACADEMIC_KEY
        if not s3_key:
            raise RuntimeError(
                f"No S3 key configured for academic integrity document. "
                f"Please set AWS_ACADEMIC_KEY in your .env"
            )
        process_and_upload_pdf_for_other_document(
            pdf_path=pdf_path,
            local_text_path=local_text_path,
            s3_key=s3_key,
        )
    else:
        raise ValueError(f"Unsupported document type '{type}'.")
