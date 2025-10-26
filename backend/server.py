# from fastapi import FastAPI, Query
# from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# from .model import (
#     calculate_stock_multiples, 
#         run_monte_carlo, 
#         insert_user_ticker, 
#     generate_research_brief,
# )
# from .query import (
#     fetch_userlist, 
#     fetch_news_sentiment, 
#     fetch_overall_news_sentiment
# )
# from dcf.router import router as dcf_router

# app = FastAPI()

# origins = [
#     "http://localhost:8080",
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.get("/multiples")
# def get_multiples_for_stock(
#     ticker: str = Query(..., description="Stock ticker, e.g., AAPL")
# ):
#     return calculate_stock_multiples(ticker)

# @app.get("/userlist")
# def get_user_list(
#     uid: str = Query(..., description="User ID")
# ):
#     return fetch_userlist(uid)

# @app.post("/userlist")
# def add_to_user_list(
#     uid: str = Query(..., description="User ID"),
#     ticker: str = Query(..., description="Stock ticker, e.g., AAPL")
# ):
#     try:
#         return insert_user_ticker(uid, ticker)
#     except Exception as e:
#         return {"error": str(e)}    

# @app.get("/montecarlo")
# async def montecarlo_endpoint(
#     ticker: str = Query(..., description="Stock ticker, e.g., AAPL"),
#     years_history: int = Query(5, ge=1, le=20),
#     horizon_years: float = Query(1.0, gt=0),
#     steps_per_year: int = Query(252, ge=50, le=2000),
#     n_paths: int = Query(1000, ge=100, le=20000),
# ):
#     try:
#         result = run_monte_carlo(
#             ticker=ticker,
#             years_history=years_history,
#             horizon_years=horizon_years,
#             steps_per_year=steps_per_year,
#             n_paths=n_paths,
#         )
#         return JSONResponse(content=result)
#     except Exception as e:
#         return JSONResponse(status_code=400, content={"error": str(e)})
    
# @app.get("/research")
# def research_endpoint(
#     ticker: str = Query(..., description="Stock ticker, e.g., AAPL")
# ):
#     try:
#         return generate_research_brief(ticker)
#     except Exception as e:
#         return {"error": str(e)}
    
# @app.get("/news-sentiment")
# def news_sentiment_endpoint(
#     ticker: str = Query(..., description="Stock ticker, e.g., AAPL")
# ):
#     return fetch_news_sentiment(ticker.upper())


# @app.get("/overall-news-sentiment")
# def overall_news_sentiment_endpoint(
#     ticker: str = Query(..., description="Stock ticker, e.g., AAPL")
# ):
#     return fetch_overall_news_sentiment(ticker.upper())

# app.include_router(dcf_router, prefix="")
# backend/server.py
import logging
import traceback
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# ---- your app code imports ----
from .model import (
    calculate_stock_multiples,
    run_monte_carlo,
    insert_user_ticker,
    generate_research_brief,
)
from .query import (
    fetch_userlist,
    fetch_news_sentiment,
    fetch_overall_news_sentiment,
)

# ---- DCF microservice router ----
from dcf.router import router as dcf_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("investomommy")

app = FastAPI(title="InvestoMommy API")

# Allow common local dev origins (add more if needed)
ALLOWED_ORIGINS = [
    "http://localhost:8080",   # your current front-end
    "http://127.0.0.1:8080",
    "http://localhost:5173",   # Vite default
    "http://127.0.0.1:5173",
    "http://localhost:3000",   # CRA/Next.js
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- Health + error handling --------
@app.get("/health")
def health():
    return {"ok": True}

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s %s\n%s",
                 request.method, request.url, traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )

# -------- Your existing endpoints --------
@app.get("/multiples")
def get_multiples_for_stock(
    ticker: str = Query(..., description="Stock ticker, e.g., AAPL")
):
    return calculate_stock_multiples(ticker)

@app.get("/userlist")
def get_user_list(uid: str = Query(..., description="User ID")):
    return fetch_userlist(uid)

@app.post("/userlist")
def add_to_user_list(
    uid: str = Query(..., description="User ID"),
    ticker: str = Query(..., description="Stock ticker, e.g., AAPL"),
):
    try:
        return insert_user_ticker(uid, ticker)
    except Exception as e:
        logger.exception("Insert user ticker failed")
        return {"error": str(e)}

@app.get("/montecarlo")
async def montecarlo_endpoint(
    ticker: str = Query(..., description="Stock ticker, e.g., AAPL"),
    years_history: int = Query(5, ge=1, le=20),
    horizon_years: float = Query(1.0, gt=0),
    steps_per_year: int = Query(252, ge=50, le=2000),
    n_paths: int = Query(1000, ge=100, le=20000),
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

@app.get("/research")
def research_endpoint(
    ticker: str = Query(..., description="Stock ticker, e.g., AAPL")
):
    try:
        return generate_research_brief(ticker)
    except Exception as e:
        logger.exception("Research generation failed")
        return {"error": str(e)}

@app.get("/news-sentiment")
def news_sentiment_endpoint(
    ticker: str = Query(..., description="Stock ticker, e.g., AAPL")
):
    return fetch_news_sentiment(ticker.upper())

@app.get("/overall-news-sentiment")
def overall_news_sentiment_endpoint(
    ticker: str = Query(..., description="Stock ticker, e.g., AAPL")
):
    return fetch_overall_news_sentiment(ticker.upper())

# -------- Mount the DCF microservice under a clear prefix --------
# Your frontend should call `${API_BASE_URL}/api/dcf/...`
app.include_router(dcf_router, prefix="/api/dcf", tags=["DCF"])

# Optional: microservice health
@app.get("/api/dcf/health")
def dcf_health():
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
