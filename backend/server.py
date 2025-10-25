from fastapi import FastAPI
from model import calculate_stock_multiples

app = FastAPI()

@app.get("/multiples/{ticker}")
def get_multiples_for_stock(ticker: str):
    return calculate_stock_multiples(ticker)