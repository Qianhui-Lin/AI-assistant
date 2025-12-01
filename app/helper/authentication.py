import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

# Load environment variables from a .env file (if running locally)
load_dotenv()

EXPECTED_TOKEN = os.getenv("API_SECRET_TOKEN")
if not EXPECTED_TOKEN:
    raise ValueError("API_SECRET_TOKEN environment variable not set. Cannot start service securely.")

# 1. Define the security scheme: HTTP Bearer
security_scheme = HTTPBearer()

def get_current_token(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    """
    Helper function to validate the incoming request token.
    Checks the 'Authorization: Bearer <token>' header.
    """
    
    # Check if the scheme is 'Bearer' (required by HTTPBearer)
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme. Must be Bearer.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 2. Compare the token with the expected secret
    if credentials.credentials != EXPECTED_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # If successful, return the token (though we don't strictly need it later)
    return credentials.credentials