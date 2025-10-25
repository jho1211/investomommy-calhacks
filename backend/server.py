from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from model import calculate_stock_multiples, run_monte_carlo, insert_user_ticker
from query import fetch_userlist

app = FastAPI()

@app.get("/multiples")
def get_multiples_for_stock(
    ticker: str = Query(..., description="Stock ticker, e.g., AAPL")
):
    return calculate_stock_multiples(ticker)

@app.get("/userlist")
def get_user_list(
    uid: str = Query(..., description="User ID")
):
    return fetch_userlist(uid)

@app.post("/userlist")
def add_to_user_list(
    uid: str = Query(..., description="User ID"),
    ticker: str = Query(..., description="Stock ticker, e.g., AAPL")
):
    try:
        return insert_user_ticker(uid, ticker)
    except Exception as e:
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
        return JSONResponse(status_code=400, content={"error": str(e)})