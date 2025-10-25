from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from model import calculate_stock_multiples, run_monte_carlo

app = FastAPI()

@app.get("/multiples/{ticker}")
def get_multiples_for_stock(ticker: str):
    return calculate_stock_multiples(ticker)

@app.get("/montecarlo")
def run_monte_carlo_simulation(ticker: str, num_simulations: int = 1000, years: int = 5):
    return run_monte_carlo(ticker, n_paths=num_simulations, horizon_years=years)

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