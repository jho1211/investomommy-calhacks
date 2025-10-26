# dcf/server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .router import router  # ← keep as-is (since you run it from inside /dcf)

import os

app = FastAPI(
    title="DCF Microservice",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- CORS ---
# Use an environment variable FRONTEND_ORIGIN to tighten later
frontend_origin = os.getenv("FRONTEND_ORIGIN")
allow_origins = ["*"] if not frontend_origin else [frontend_origin]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Health Routes ---
@app.get("/", tags=["Meta"])
def root():
    return {
        "ok": True,
        "service": "DCF Microservice",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": ["/api/dcf/{ticker}"],
    }

@app.get("/health", tags=["Meta"])
def health():
    return {"status": "healthy"}

# --- Include DCF Routes ---
app.include_router(router)

# --- Optional local run ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
