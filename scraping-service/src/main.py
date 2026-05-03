from dotenv import load_dotenv
from fastapi import FastAPI

from ai.router import router as ai_router

load_dotenv()

app = FastAPI(title="PathWeave AI", version="0.1.0")
app.include_router(ai_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "python-ai"}
