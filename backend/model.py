import requests
from config import FMP_API_KEY, BALANCE_SHEET_API_URL, INCOME_STATEMENT_API_URL, KEY_METRICS_API_URL, EMPLOYEE_COUNT_API_URL, supabase
from query import fetch_multiples
import io
import base64
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

def calculate_stock_multiples(ticker):
    existing_multiples = fetch_multiples(ticker)
    
    if existing_multiples is not None:
        return existing_multiples
    
    balance_sheet = requests.get(BALANCE_SHEET_API_URL.format(ticker, FMP_API_KEY)).json()[0]
    income_statement = requests.get(INCOME_STATEMENT_API_URL.format(ticker, FMP_API_KEY)).json()[0]
    key_metrics = requests.get(KEY_METRICS_API_URL.format(ticker, FMP_API_KEY)).json()[0]
    employee_count = requests.get(EMPLOYEE_COUNT_API_URL.format(ticker, FMP_API_KEY)).json()[0]

    evToEbitda = key_metrics.get("evToEBITDA")
    evToFreeCashFlow = key_metrics.get("evToFreeCashFlow")
    evToSales = key_metrics.get("evToSales")
    ev = key_metrics.get("enterpriseValue")
    employeeCount = employee_count.get("employeeCount")
    evToRevenuePerEmployee = ev / employeeCount
    marketCap = key_metrics.get("marketCap")
    evToOperatingCashFlow = key_metrics.get("evToOperatingCashFlow")
    priceToCashFlow = marketCap / (ev / evToOperatingCashFlow)
    priceToBook = marketCap / key_metrics.get("tangibleAssetValue")
    debtToEquity = balance_sheet.get("totalDebt") / balance_sheet.get("totalStockholdersEquity")
    evToInvestedCapital = ev / key_metrics.get("investedCapital")
    price_to_earnings = marketCap / income_statement.get("netIncome")
    evToEbit = ev / income_statement.get("ebit")

    multiples_data = {
        "ticker": ticker,
        "price_to_earnings": price_to_earnings,
        "ev_to_ebitda": evToEbitda,
        "ev_to_ebit": evToEbit,
        "price_to_book": priceToBook,
        "debt_to_equity": debtToEquity,
        "ev_to_invested_capital": evToInvestedCapital,
        "ev_to_fcf": evToFreeCashFlow,
        "price_to_cash_flow": priceToCashFlow,
        "ev_to_sales": evToSales,
        "ev_to_revenue_per_employee": evToRevenuePerEmployee,
    }
    
    supabase.table("stockmultiples").insert(multiples_data).execute()
    return multiples_data

def _fig_to_data_url(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    return f"data:image/png;base64,{b64}"

def run_monte_carlo(
    ticker: str,
    years_history: int = 5,
    horizon_years: float = 1.0,
    steps_per_year: int = 252,
    n_paths: int = 1000,
):
    data = yf.download(ticker, period=f"{years_history}y", progress=False, auto_adjust=False)
    if data.empty or "Adj Close" not in data:
        raise ValueError("No historical data found for that ticker.")

    prices = data["Adj Close"].dropna()
    if len(prices) < 2:
        raise ValueError("Not enough price history to compute returns.")

    # log returns -> annualized drift and vol
    returns = np.log(prices / prices.shift(1)).dropna()
    mu_annual = float(returns.mean() * 252)
    sigma_annual = float(returns.std() * np.sqrt(252))

    S0 = float(prices.iloc[-1])
    T = float(horizon_years)
    N = int(steps_per_year * T)
    if N <= 0:
        raise ValueError("steps_per_year * horizon_years must be positive.")
    dt = T / N

    rng = np.random.default_rng(42)
    paths = np.zeros((N + 1, n_paths), dtype=np.float64)
    paths[0] = S0

    drift = (mu_annual - 0.5 * sigma_annual**2) * dt
    vol_step = sigma_annual * np.sqrt(dt)

    for t in range(1, N + 1):
        z = rng.standard_normal(n_paths)
        paths[t] = paths[t - 1] * np.exp(drift + vol_step * z)

    terminal_returns = (paths[-1] - S0) / S0
    pnl = paths[-1] - S0

    # risk stats
    VaR95_ret = float(np.percentile(terminal_returns, 5))
    ES95_ret = float(terminal_returns[terminal_returns <= VaR95_ret].mean())
    VaR95_pnl = float(np.percentile(pnl, 5))
    ES95_pnl = float(pnl[pnl <= VaR95_pnl].mean())

    # plots
    fig1, ax1 = plt.subplots()
    ax1.hist(terminal_returns, bins=50, alpha=0.7)
    ax1.set_title(f"{ticker.upper()} Monte Carlo Return Distribution")
    ax1.set_xlabel("Return")
    ax1.set_ylabel("Frequency")
    hist_url = _fig_to_data_url(fig1)
    plt.close(fig1)

    fig2, ax2 = plt.subplots(figsize=(8, 4))
    ax2.plot(paths[:, :10])
    ax2.set_title(f"{ticker.upper()} Monte Carlo Simulated Price Paths")
    ax2.set_xlabel("Days")
    ax2.set_ylabel("Price")
    paths_url = _fig_to_data_url(fig2)
    plt.close(fig2)

    return {
        "ticker": ticker.upper(),
        "spot_price": round(S0, 2),
        "mu_annual": round(mu_annual, 6),
        "sigma_annual": round(sigma_annual, 6),
        "mean_return": round(float(terminal_returns.mean()), 6),
        "std_return": round(float(terminal_returns.std()), 6),
        "var95_return": round(VaR95_ret, 6),
        "es95_return": round(ES95_ret, 6),
        "mean_pnl": round(float(pnl.mean()), 2),
        "std_pnl": round(float(pnl.std()), 2),
        "var95_pnl": round(VaR95_pnl, 2),
        "es95_pnl": round(ES95_pnl, 2),
        "histogram_url": hist_url,
        "paths_url": paths_url,
        "params": {
            "years_history": years_history,
            "horizon_years": horizon_years,
            "steps_per_year": steps_per_year,
            "n_paths": n_paths,
        },
    }