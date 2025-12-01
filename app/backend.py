from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# temporary in-memory storage
messages = []

# allow webpage & unreal to access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.post("/messages")
async def add_message(request: Request):
    # Debug: print what we're receiving
    content_type = request.headers.get("content-type")
    body = await request.body()
    print(f"Content-Type: {content_type}")
    print(f"Raw body: {body}")
    
    try:
        json_data = await request.json()
        print(f"Parsed JSON: {json_data}")
        messages.append(json_data.get("message", json_data))
        return {"status": "ok"}
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/messages")
def list_messages():
    return messages
