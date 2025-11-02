import logging
import traceback
from fastapi import FastAPI, Query, Request, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import os
import mimetypes
from auth import verify_token

from model import (
    calculate_stock_multiples,
    run_monte_carlo,
    insert_user_ticker,
    generate_research_brief,
)
from query import (
    fetch_userlist,
    fetch_news_sentiment,
    fetch_overall_news_sentiment,
)
from dcf import router as dcf_router
from config import supabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("investomommy")

app = FastAPI(
    title="InvestoMommy API",
    description="Investment analysis API with Supabase authentication",
    version="1.0.0"
)

origins = [
    "https://investomommy-calhacks.onrender.com",
    "http://localhost:8000",
    "http://localhost:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"ok": True}

@app.post("/api/auth/get-token")
def get_test_token(
        email: str = Query(..., description="User email"), 
        password: str = Query(..., description="User password")
    ):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.session:
            return {
                "access_token": response.session.access_token,
                "token_type": "bearer",
                "expires_at": response.session.expires_at,
                "user_id": response.user.id if response.user else None,
            }
        else:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid credentials"}
            )
    except Exception as e:
        logger.exception("Test token generation failed")
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s %s\n%s",
                 request.method, request.url, traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )

# -------- Your existing endpoints --------
@app.get("/api/multiples")
def get_multiples_for_stock(
    ticker: str = Query(..., description="Stock ticker, e.g., AAPL"),
    user: dict = Depends(verify_token)
):
    return calculate_stock_multiples(ticker)

@app.get("/api/userlist")
def get_user_list(
    uid: str = Query(..., description="User ID"),
    user: dict = Depends(verify_token)
):
    return fetch_userlist(uid)

@app.post("/api/userlist")
def add_to_user_list(
    uid: str = Query(..., description="User ID"),
    ticker: str = Query(..., description="Stock ticker, e.g., AAPL"),
    user: dict = Depends(verify_token)
):
    try:
        return insert_user_ticker(uid, ticker)
    except Exception as e:
        logger.exception("Insert user ticker failed")
        return {"error": str(e)}

@app.get("/api/montecarlo")
async def montecarlo_endpoint(
    ticker: str = Query(..., description="Stock ticker, e.g., AAPL"),
    years_history: int = Query(5, ge=1, le=20),
    horizon_years: float = Query(1.0, gt=0),
    steps_per_year: int = Query(252, ge=50, le=2000),
    n_paths: int = Query(1000, ge=100, le=20000),
    user: dict = Depends(verify_token)
):
    try:
        result = run_monte_carlo(
            ticker=ticker,
            years_history=years_history,
            horizon_years=horizon_years,
            steps_per_year=steps_per_year,
            n_paths=n_paths,
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.exception("Monte Carlo failed")
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.get("/api/research")
def research_endpoint(
    ticker: str = Query(..., description="Stock ticker, e.g., AAPL"),
    user: dict = Depends(verify_token)
):
    try:
        return generate_research_brief(ticker)
    except Exception as e:
        logger.exception("Research generation failed")
        return {"error": str(e)}

@app.get("/api/news-sentiment")
def news_sentiment_endpoint(
    ticker: str = Query(..., description="Stock ticker, e.g., AAPL"),
    user: dict = Depends(verify_token)
):
    return fetch_news_sentiment(ticker.upper())

@app.get("/api/overall-news-sentiment")
def overall_news_sentiment_endpoint(
    ticker: str = Query(..., description="Stock ticker, e.g., AAPL"),
    user: dict = Depends(verify_token)
):
    return fetch_overall_news_sentiment(ticker.upper())

app.include_router(dcf_router, prefix="/api", tags=["DCF"])

@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """
    Catch-all route to serve index.html for all non-API routes.
    This allows React Router to handle client-side routing.
    """
    file_path = os.path.join("build", full_path)
    
    if os.path.isfile(file_path):
        mime_type, _ = mimetypes.guess_type(file_path)
        return FileResponse(
            file_path,
            media_type=mime_type,
            headers={"Cache-Control": "public, max-age=3600"}
        )
    
    index_path = os.path.join("build", "index.html")
    if os.path.exists(index_path):
        return FileResponse(
            index_path,
            media_type="text/html",
            headers={"Cache-Control": "no-cache"}
        )
    
    return JSONResponse(status_code=404, content={"error": "Not found"})