import time
from fastapi import HTTPException, status

RATE_LIMIT_STORE = {}

# Config
MAX_REQUESTS = 20 
WINDOW_SECONDS = 60 

def check_rate_limit(token: str):
    now = time.time()

    if token not in RATE_LIMIT_STORE:
        RATE_LIMIT_STORE[token] = {"count": 1, "start": now}
        return

    record = RATE_LIMIT_STORE[token]
    elapsed = now - record["start"]

    # Reset window if expired
    if elapsed > WINDOW_SECONDS:
        RATE_LIMIT_STORE[token] = {"count": 1, "start": now}
        return

    # Still in same window
    if record["count"] >= MAX_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later."
        )

    record["count"] += 1