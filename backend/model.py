import requests
from config import (
    anthropic_client,
    CLAUDE_MODEL,
    FMP_API_KEY, 
    BALANCE_SHEET_API_URL, 
    INCOME_STATEMENT_API_URL, 
    KEY_METRICS_API_URL, 
    EMPLOYEE_COUNT_API_URL, 
    COMPANY_SEARCH_API_URL,
    supabase
)
from query import (
    fetch_multiples, 
    fetch_userlist, 
    check_ticker_exists, 
    add_ticker, 
    add_user_ticker, 
    insert_research_data,
    get_research_data
)
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

def insert_user_ticker(uid: str, ticker: str):
    userlist = fetch_userlist(uid)
    if ticker not in userlist:
        if not check_ticker_exists(ticker):
            company_info = requests.get(COMPANY_SEARCH_API_URL.format(ticker, FMP_API_KEY)).json()[0]
            add_ticker(ticker, company_info.get("name", "Unknown Company"))
        add_user_ticker(uid, ticker)
        return {"message": "Ticker added to user list"}
    else:
        return {"message": "Ticker already in user list"}
    
def generate_research_brief(ticker: str) -> str:
    cur_research_data = get_research_data(ticker)
    if cur_research_data is not None:
        return cur_research_data

    prompt = f"""
    You are a financial writer for beginners, similar in tone to the Wall Street Journal or Investopedia.
    Write a structured, beginner-friendly equity research report for the company with ticker symbol ({ticker}).

    Return the content ONLY using the following tagged blocks (no JSON, no markdown, no extra text):
    <<company_overview>>
    ...1–3 sentence paragraphs, separated by a blank line.
    <<end>>

    <<business_segments>>
    ...1–3 sentence paragraphs, separated by a blank line.
    <<end>>

    <<revenue_characteristics>>
    ...1–3 sentence paragraphs, separated by a blank line.
    <<end>>

    <<geographic_breakdown>>
    ...1–3 sentence paragraphs, separated by a blank line.
    <<end>>

    <<stakeholders>>
    ...1–3 sentence paragraphs, separated by a blank line.
    <<end>>

    <<key_performance_indicators>>
    ...1–3 sentence paragraphs, separated by a blank line.
    <<end>>

    <<valuation>>
    ...1–3 sentence paragraphs, separated by a blank line.
    <<end>>

    <<recent_news>>
    ...1–3 sentence paragraphs, separated by a blank line.
    <<end>>

    <<forensic_red_flags>>
    ...1–3 sentence paragraphs, separated by a blank line.
    <<end>>

    Rules:
    - Plain English for beginners; no jargon unless briefly explained.
    - No bullets, tables, or special symbols.
    - Output ONLY those tagged sections in the exact order above.
    """
    msg = anthropic_client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1600,
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()

    import re, html as _html
    KEYS = [
        "company_overview",
        "business_segments",
        "revenue_characteristics",
        "geographic_breakdown",
        "stakeholders",
        "key_performance_indicators",
        "valuation",
        "recent_news",
        "forensic_red_flags",
    ]

    def extract_block(key: str, s: str) -> str:
        m = re.search(rf"<<{key}>>\s*(.*?)\s*<<end>>", s, flags=re.DOTALL | re.IGNORECASE)
        return m.group(1).strip() if m else ""

    def to_paragraphs(txt: str) -> list[str]:
        # split on blank lines; clean up whitespace
        parts = [p.strip() for p in re.split(r"\n\s*\n", txt) if p.strip()]
        # fallback: if no blank lines, split every 2–3 sentences
        if len(parts) <= 1:
            sentences = re.split(r"(?<=\.)\s+", txt)
            parts = [" ".join(sentences[i:i+3]).strip() for i in range(0, len(sentences), 3)]
            parts = [p for p in parts if p]
        return parts

    sections = {k: to_paragraphs(extract_block(k, raw)) for k in KEYS}
    insert_research_data(ticker, sections)
    return get_research_data(ticker)