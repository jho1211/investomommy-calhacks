import requests
from config import FMP_API_KEY, BALANCE_SHEET_API_URL, INCOME_STATEMENT_API_URL, KEY_METRICS_API_URL, EMPLOYEE_COUNT_API_URL, supabase
from query import fetch_multiples

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