from fastapi import APIRouter, HTTPException, Query
import os
import math
import requests
import yfinance as yf
import numpy as np
from typing import Any, Dict, Tuple, List, Optional

from dcf_calc import dcf_valuation

router = APIRouter(tags=["DCF"])

# ----------------------------------------------------------------------------
# COMPANY-SPECIFIC DATA STORE
# ----------------------------------------------------------------------------
COMPANY_DATA = {
    "AAPL": {
        "company_name": "Apple Inc.",
        "beta": 1.25,
        "risk_free_rate": 0.045,
        "equity_risk_premium": 0.055,
        "cost_of_debt_pretax": 0.035,
        "tax_rate": 0.15,
        "debt_to_equity": 1.57,
        "terminal_growth": 0.035,
        "market_cap": 3.5e12,
        "total_debt": 1.1e11,
        "profile": "mature, low-risk, stable cash flows"
    },
    "TSLA": {
        "company_name": "Tesla Inc.",
        "beta": 2.05,
        "risk_free_rate": 0.045,
        "equity_risk_premium": 0.055,
        "cost_of_debt_pretax": 0.065,
        "tax_rate": 0.21,
        "debt_to_equity": 0.15,
        "terminal_growth": 0.045,
        "market_cap": 8e11,
        "total_debt": 1.2e10,
        "profile": "high-growth, high-risk, volatile"
    },
    "KO": {
        "company_name": "The Coca-Cola Company",
        "beta": 0.65,
        "risk_free_rate": 0.045,
        "equity_risk_premium": 0.055,
        "cost_of_debt_pretax": 0.030,
        "tax_rate": 0.21,
        "debt_to_equity": 1.85,
        "terminal_growth": 0.025,
        "market_cap": 2.5e11,
        "total_debt": 4.0e10,
        "profile": "defensive, very low-risk, saturated market"
    },
    "MSFT": {
        "company_name": "Microsoft Corporation",
        "beta": 1.15,
        "risk_free_rate": 0.045,
        "equity_risk_premium": 0.055,
        "cost_of_debt_pretax": 0.032,
        "tax_rate": 0.16,
        "debt_to_equity": 0.45,
        "terminal_growth": 0.035,
        "market_cap": 3.1e12,
        "total_debt": 7.5e10,
        "profile": "mature tech, moderate-risk, steady growth"
    },
    "GOOGL": {
        "company_name": "Alphabet Inc.",
        "beta": 1.10,
        "risk_free_rate": 0.045,
        "equity_risk_premium": 0.055,
        "cost_of_debt_pretax": 0.028,
        "tax_rate": 0.15,
        "debt_to_equity": 0.08,
        "terminal_growth": 0.040,
        "market_cap": 2.0e12,
        "total_debt": 1.3e10,
        "profile": "tech giant, low debt, moderate growth"
    }
}

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def safe(val, default=0.0) -> float:
    try:
        return float(val) if val is not None else float(default)
    except Exception:
        return float(default)

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def nz(x, alt):
    return x if x is not None else alt

def _row(df, name: str):
    try:
        if df is not None and not df.empty and isinstance(name, str) and (name in df.index):
            return df.loc[name]
    except Exception:
        pass
    return None

def _first(row) -> float:
    try:
        if row is not None and hasattr(row, "iloc") and len(row) > 0:
            return float(row.iloc[0])
    except Exception:
        pass
    return np.nan

def _series_vals(row, max_n=5) -> List[float]:
    try:
        if row is not None and hasattr(row, "dropna"):
            vals = row.dropna().astype(float).values
            return [float(v) for v in vals[:max_n]]
    except Exception:
        pass
    return []

def _clean_num(x):
    try:
        xf = float(x)
        if math.isfinite(xf):
            return xf
    except Exception:
        pass
    return None

def _clean(obj):
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, (int, float, np.floating, np.integer)):
        return _clean_num(obj)
    return obj

def _qsum(row, n=4):
    try:
        if row is not None and hasattr(row, "dropna"):
            vals = row.dropna().astype(float).values[:n]
            return float(np.nansum(vals))
    except Exception:
        pass
    return np.nan

FMP_API_KEY = os.environ.get("FMP_API_KEY")

def _fmp_get(path: str) -> Optional[Any]:
    if not FMP_API_KEY:
        return None
    base = "https://financialmodelingprep.com/api/v3"
    url = f"{base}/{path}{'&' if ('?' in path) else '?'}apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=15)
        if r.ok:
            return r.json()
    except Exception:
        pass
    return None

def enrich_with_fmp(info: Dict[str, Any], ticker: str) -> Dict[str, Any]:
    out = dict(info or {})
    prof = _fmp_get(f"profile/{ticker.upper()}")
    if isinstance(prof, list) and prof:
        p = prof[0]
        out.setdefault("marketCap", p.get("mktCap"))
        out.setdefault("sharesOutstanding", p.get("sharesOutstanding"))
        out.setdefault("impliedSharesOutstanding", p.get("sharesOutstanding"))

    quote = _fmp_get(f"quote/{ticker.upper()}")
    if isinstance(quote, list) and quote:
        q = quote[0]
        out.setdefault("currentPrice", q.get("price"))
        out.setdefault("regularMarketPrice", q.get("price"))

    bsq = _fmp_get(f"balance-sheet-statement/{ticker.upper()}?period=quarter&limit=2")
    if isinstance(bsq, list) and bsq:
        bs0 = bsq[0]
        total_debt = bs0.get("totalDebt") or ((bs0.get("shortTermDebt") or 0) + (bs0.get("longTermDebt") or 0))
        out.setdefault("totalDebt", total_debt)
        cash_like = (bs0.get("cashAndCashEquivalents") or 0) + (bs0.get("shortTermInvestments") or 0)
        out.setdefault("totalCash", cash_like if cash_like else None)
    return out

def compute_cash_like(info: dict, bs) -> float:
    cash = safe(info.get("totalCash"), 0.0)
    if bs is not None and not bs.empty:
        cs_row = _row(bs, "Cash And Short Term Investments")
        sti_row = _row(bs, "Short Term Investments")
        ms_row = _row(bs, "Marketable Securities")
        extras = 0.0
        for r in [cs_row, sti_row, ms_row]:
            try:
                if r is not None:
                    v = _first(r)
                    if np.isfinite(v):
                        extras += float(v)
            except Exception:
                pass
        cash = max(cash, extras)
    return cash

def compute_delta_nwc_quarterly(bs_q) -> float:
    if bs_q is None or bs_q.empty:
        return 0.0

    def series_vals(name):
        return _series_vals(_row(bs_q, name), max_n=2)

    tca = series_vals("Total Current Assets")
    tcl = series_vals("Total Current Liabilities")
    cash = series_vals("Cash And Cash Equivalents") or series_vals("Cash")
    std = series_vals("Short Long Term Debt") or series_vals("Short/Current Long Term Debt")

    def v(a, i):
        try:
            return float(a[i])
        except Exception:
            return 0.0

    ca0, ca1 = v(tca, 0), v(tca, 1)
    cl0, cl1 = v(tcl, 0), v(tcl, 1)
    c0, c1 = v(cash, 0), v(cash, 1)
    sd0, sd1 = v(std, 0), v(std, 1)

    nwc0 = (ca0 - c0) - (cl0 - sd0)
    nwc1 = (ca1 - c1) - (cl1 - sd1)
    return nwc0 - nwc1

def calculate_cost_of_equity(beta: float, rf: float, erp: float) -> float:
    return rf + (beta * erp)

def calculate_wacc_from_company_data(company_data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    beta = company_data["beta"]
    rf = company_data["risk_free_rate"]
    erp = company_data["equity_risk_premium"]
    rd_pretax = company_data["cost_of_debt_pretax"]
    tax_rate = company_data["tax_rate"]
    de_ratio = company_data["debt_to_equity"]

    re = calculate_cost_of_equity(beta, rf, erp)
    rd_after_tax = rd_pretax * (1 - tax_rate)

    total_capital = 1 + de_ratio
    equity_weight = 1 / total_capital
    debt_weight = de_ratio / total_capital

    wacc = (equity_weight * re) + (debt_weight * rd_after_tax)
    wacc = clamp(wacc, 0.05, 0.15)

    details = {
        "cost_of_equity": re,
        "cost_of_debt_pretax": rd_pretax,
        "cost_of_debt_after_tax": rd_after_tax,
        "equity_weight": equity_weight,
        "debt_weight": debt_weight,
        "beta": beta,
        "risk_free_rate": rf,
        "equity_risk_premium": erp,
        "tax_rate": tax_rate,
        "debt_to_equity_ratio": de_ratio,
        "source": "company_specific_database"
    }
    return wacc, details

def compute_effective_tax_rate(tkr: yf.Ticker, company_data: Dict[str, Any]) -> float:
    try:
        fin = tkr.financials
        if fin is not None and not fin.empty:
            tax = safe(_first(_row(fin, "Income Tax Expense")), np.nan)
            pre = safe(_first(_row(fin, "Income Before Tax")), np.nan)
            if np.isfinite(tax) and np.isfinite(pre) and pre != 0.0:
                return clamp(tax / pre, 0.00, 0.35)
    except Exception:
        pass
    if company_data and "tax_rate" in company_data:
        return company_data["tax_rate"]
    return 0.21

def fcff_from_statements(tkr: yf.Ticker, eff_tax: float) -> Tuple[float, Dict[str, Any]]:
    fin_q = tkr.quarterly_financials
    cf_q = tkr.quarterly_cashflow
    bs_q = tkr.quarterly_balance_sheet
    diag = {"components": {}, "source_quality": "ok"}

    ebit_ttm = np.nan
    for lab in ["Ebit", "Operating Income"]:
        if fin_q is not None and not fin_q.empty and lab in fin_q.index:
            ebit_ttm = _qsum(_row(fin_q, lab), 4)
            if np.isfinite(ebit_ttm):
                break
    diag["components"]["EBIT_TTM"] = ebit_ttm

    da_ttm = np.nan
    if cf_q is not None and not cf_q.empty:
        for lab in ["Depreciation", "Depreciation & Amortization", "Depreciation Amortization Depletion", "DepreciationAndAmortization"]:
            if lab in cf_q.index:
                da_ttm = _qsum(_row(cf_q, lab), 4)
                if np.isfinite(da_ttm):
                    break
    diag["components"]["D&A_TTM"] = da_ttm

    capex_ttm = np.nan
    if cf_q is not None and not cf_q.empty and "Capital Expenditures" in cf_q.index:
        capex_ttm = abs(_qsum(_row(cf_q, "Capital Expenditures"), 4))
    diag["components"]["CapEx_TTM"] = capex_ttm

    delta_nwc_ttm = compute_delta_nwc_quarterly(bs_q)
    diag["components"]["ΔNWC_TTM"] = delta_nwc_ttm

    if all(np.isfinite(v) for v in [ebit_ttm, da_ttm, capex_ttm]) and np.isfinite(delta_nwc_ttm):
        fcff0 = ebit_ttm * (1.0 - eff_tax) + da_ttm - capex_ttm - delta_nwc_ttm
        diag["method"] = "EBIT(1-T)+DA-CapEx-ΔNWC (TTM, quarterly)"
        return float(fcff0), diag

    cf = tkr.cashflow
    if cf is not None and not cf.empty and ("Free Cash Flow" in cf.index):
        vals = _series_vals(_row(cf, "Free Cash Flow"), max_n=1)
        if vals:
            diag["method"] = "Fallback annual Free Cash Flow"
            return float(vals[0]), diag

    ocf = _first(_row(cf, "Total Cash From Operating Activities")) if (cf is not None and not cf.empty) else np.nan
    if np.isfinite(ocf) and np.isfinite(capex_ttm):
        diag["method"] = "Fallback OCF - CapEx"
        return float(ocf - capex_ttm), diag

    info = tkr.info or {}
    fcff0 = safe(info.get("freeCashflow") or info.get("operatingCashflow"), 0.0)
    diag["method"] = "Fallback info.freeCashflow/operatingCashflow"
    return float(fcff0), diag

def estimate_growths(tkr: yf.Ticker, horizon: int, company_data: Dict[str, Any]) -> dict:
    info, fin, cf = tkr.info or {}, tkr.financials, tkr.cashflow

    fcff_hist = []
    if cf is not None and not cf.empty:
        if "Free Cash Flow" in cf.index:
            vals = _series_vals(_row(cf, "Free Cash Flow"), max_n=5)
            fcff_hist = [v for v in vals if np.isfinite(v)]

    g_fcff_hist = 0.06
    if len(fcff_hist) >= 2 and fcff_hist[-1] > 0:
        recent = float(fcff_hist[0])
        oldest = float(fcff_hist[-1])
        n = len(fcff_hist) - 1
        if oldest > 0 and n > 0:
            g_fcff_hist = clamp((recent / oldest) ** (1.0 / n) - 1.0, 0.0, 0.25)

    g_rev_cagr = np.nan
    if fin is not None and not fin.empty and ("Total Revenue" in fin.index):
        rev = _series_vals(_row(fin, "Total Revenue"), max_n=5)
        if len(rev) >= 2 and rev[-1] > 0:
            recent, oldest = float(rev[0]), float(rev[-1])
            n = len(rev) - 1
            g_rev_cagr = clamp((recent / oldest) ** (1.0 / n) - 1.0, -0.2, 0.25)

    if np.isfinite(g_rev_cagr):
        g_used = clamp(0.7 * g_fcff_hist + 0.3 * g_rev_cagr, -0.05, 0.20)
    else:
        g_used = g_fcff_hist

    growth_path = []
    for i in range(1, horizon + 1):
        decayed = g_used * (0.8 ** (i / horizon))
        growth_path.append(decayed)

    return {
        "g_fcff_hist": g_fcff_hist,
        "g_rev_cagr": g_rev_cagr if np.isfinite(g_rev_cagr) else None,
        "g_used": g_used,
        "growth_path": growth_path,
    }

def estimate_roic_and_reinvestment(tkr: yf.Ticker) -> dict:
    fin_q, bs_q = tkr.quarterly_financials, tkr.quarterly_balance_sheet

    ebit_ttm = np.nan
    if fin_q is not None and not fin_q.empty:
        for lab in ["Ebit", "Operating Income"]:
            if lab in fin_q.index:
                ebit_ttm = _qsum(_row(fin_q, lab), 4)
                if np.isfinite(ebit_ttm):
                    break

    ic = np.nan
    if bs_q is not None and not bs_q.empty:
        ta = _first(_row(bs_q, "Total Assets")) or np.nan
        tcl = _first(_row(bs_q, "Total Current Liabilities")) or 0.0
        cash_like = compute_cash_like(tkr.info or {}, bs_q)
        if np.isfinite(ta):
            ic = max(ta - tcl - cash_like, 1.0)

    return {"nopat_ttm": ebit_ttm, "invested_capital": ic}

def build_fcff_path_via_roic(fcff0: float, tax_rate: float, years: int, growth_path: List[float], tkr: yf.Ticker):
    est = estimate_roic_and_reinvestment(tkr)
    nopat0_raw = safe(est.get("nopat_ttm"), np.nan)
    ic = safe(est.get("invested_capital"), np.nan)

    if not (np.isfinite(nopat0_raw) and np.isfinite(ic) and ic > 0):
        fcff, lvl = [], fcff0
        for g in growth_path:
            lvl *= (1.0 + g)
            fcff.append(lvl)
        return fcff

    nopat = nopat0_raw * (1.0 - tax_rate)
    roic = clamp(nopat / max(ic, 1.0), 0.08, 0.40)

    fcff = []
    for g in growth_path:
        nopat = nopat * (1.0 + g)
        reinvest = clamp((g / max(roic, 1e-6)) * nopat, 0.0, nopat * 0.9)
        fcff_t = nopat - reinvest
        fcff.append(float(fcff_t))

    if len(fcff) > 0 and fcff0 > 0:
        adj = fcff0 / max(fcff[0], 1e-6)
        fcff = [f * adj for f in fcff]
    return fcff

def compute_financials_snapshot(tkr: yf.Ticker, info: dict) -> dict:
    fin, bs, cf = tkr.financials, tkr.balance_sheet, tkr.cashflow

    total_revenue = _first(_row(fin, "Total Revenue")) if (fin is not None and not fin.empty) else np.nan
    ebitda = _first(_row(fin, "Ebitda")) if (fin is not None and not fin.empty) else np.nan
    ebit = _first(_row(fin, "Ebit")) if (fin is not None and not fin.empty) else np.nan
    if (not np.isfinite(ebit)) and (fin is not None and not fin.empty):
        ebit = _first(_row(fin, "Operating Income"))
    net_income = _first(_row(fin, "Net Income")) if (fin is not None and not fin.empty) else np.nan

    capex = _first(_row(cf, "Capital Expenditures")) if (cf is not None and not cf.empty) else np.nan

    cash_like = compute_cash_like(info, bs)
    debt = safe(info.get("totalDebt"), np.nan)
    mktcap = safe(info.get("marketCap"), np.nan)
    shares = safe(info.get("impliedSharesOutstanding") or info.get("sharesOutstanding"), np.nan)

    price = nz(info.get("currentPrice"), info.get("regularMarketPrice"))
    price = safe(price, np.nan)
    eps = safe(info.get("trailingEps"), np.nan)

    tev = np.nan
    if np.isfinite(mktcap) and np.isfinite(cash_like) and np.isfinite(debt):
        tev = mktcap + debt - cash_like

    tev_rev = (tev / total_revenue) if (np.isfinite(tev) and np.isfinite(total_revenue) and total_revenue != 0.0) else np.nan
    tev_ebitda = (tev / ebitda) if (np.isfinite(tev) and np.isfinite(ebitda) and ebitda != 0.0) else np.nan
    pe = (price / eps) if (np.isfinite(price) and np.isfinite(eps) and eps != 0.0) else np.nan

    rev_cagr = None
    if fin is not None and not fin.empty and ("Total Revenue" in fin.index):
        rev = _series_vals(_row(fin, "Total Revenue"), max_n=5)
        if len(rev) >= 2 and rev[-1] > 0:
            recent, oldest = float(rev[0]), float(rev[-1])
            n = len(rev) - 1
            rev_cagr = clamp((recent / oldest) ** (1.0 / n) - 1.0, -0.2, 0.25)

    return {
        "currency": info.get("financialCurrency", "USD"),
        "units": "USD",
        "totals": {
            "total_revenue": total_revenue,
            "ebitda": ebitda,
            "ebit": ebit,
            "net_income": net_income,
            "capex": capex,
            "cash_and_st_invest": cash_like,
            "total_debt": debt,
            "total_assets": _first(_row(bs, "Total Assets")) if (bs is not None and not bs.empty) else np.nan,
            "market_cap": mktcap,
            "shares_out": shares,
            "price": price,
            "trailing_eps": eps,
        },
        "tev": tev,
        "multiples": {
            "tev_to_revenue": tev_rev,
            "tev_to_ebitda": tev_ebitda,
            "price_to_eps": pe
        },
        "revenue_cagr": rev_cagr
    }

def sensitivity_grid(
    fcff: List[float], wacc_base: float, tg_base: float, cash: float, debt: float, shares: float,
    midyear: bool, step_wacc=0.015, step_tg=0.005
) -> List[List[Optional[float]]]:
    rows = []
    for tg in [clamp(tg_base - step_tg, 0.01, 0.06), tg_base, clamp(tg_base + step_tg, 0.01, 0.06)]:
        row = []
        for w in [clamp(wacc_base - step_wacc, 0.03, 0.20), wacc_base, clamp(wacc_base + step_wacc, 0.03, 0.20)]:
            tg_adj = min(tg, w - 0.001) if (w - tg) <= 0.001 else tg
            try:
                res = dcf_valuation(
                    fcff=fcff, wacc=w, terminal_growth=tg_adj, midyear=midyear,
                    cash=cash, debt=debt, shares_out=shares, extras=None
                )
                row.append(_clean_num(res.get("intrinsic_value_per_share")))
            except Exception:
                row.append(None)
        row = row
        rows.append(row)
    return rows

# ----------------------------------------------------------------------------
# Dynamic assumptions
# ----------------------------------------------------------------------------
def fetch_company_assumptions(ticker: str) -> Dict[str, Any]:
    t = yf.Ticker(ticker)
    info = t.info or {}

    rf_env = os.getenv("RF_RATE")
    if rf_env is not None:
        rf = safe(rf_env, 0.04)
    else:
        try:
            tnx = yf.Ticker("^TNX").info or {}
            rf = safe(tnx.get("regularMarketPrice"), 40.0) / 100.0
        except Exception:
            rf = 0.04
    erp = safe(os.getenv("EQUITY_RISK_PREMIUM"), 0.055)

    beta = safe(info.get("beta"), np.nan)
    if not np.isfinite(beta):
        try:
            px = t.history(period="2y", interval="1wk")["Close"].pct_change().dropna()
            mkt = yf.Ticker("SPY").history(period="2y", interval="1wk")["Close"].pct_change().dropna()
            ri, rm = px.align(mkt, join="inner")
            var_m = float(np.var(rm, ddof=1)) or 1e-8
            cov_im = float(np.cov(ri, rm, ddof=1)[0, 1])
            beta = clamp(cov_im / var_m, -1.0, 5.0)
        except Exception:
            beta = 1.0

    fin = t.financials
    cf  = t.cashflow
    bs  = t.balance_sheet

    interest_exp = None
    if fin is not None and not fin.empty:
        for k in ["Interest Expense", "InterestExpense", "Interest Expense Non Operating"]:
            r = _row(fin, k)
            if r is not None:
                v = _qsum(r, 4)
                if np.isfinite(v):
                    interest_exp = abs(v)
                    break

    total_debt = safe(info.get("totalDebt"), np.nan)
    avg_debt = safe(total_debt, 0.0)
    if bs is not None and not bs.empty:
        td_row = _row(bs, "Total Debt")
        if td_row is not None:
            vals = _series_vals(td_row, max_n=2)
            if vals:
                if len(vals) > 1:
                    avg_debt = (safe(vals[0], 0.0) + safe(vals[1], 0.0)) / 2.0
                else:
                    avg_debt = safe(vals[0], 0.0)

    rd_pretax = np.nan
    if np.isfinite(interest_exp) and avg_debt > 1.0:
        rd_pretax = clamp(interest_exp / avg_debt, 0.01, 0.12)
    if not np.isfinite(rd_pretax):
        rd_pretax = 0.04

    eff_tax = compute_effective_tax_rate(t, {})

    mktcap = safe(info.get("marketCap"), np.nan)
    if np.isnan(mktcap) and FMP_API_KEY:
        filled = enrich_with_fmp(info, ticker)
        mktcap = safe(filled.get("marketCap"), mktcap)
        info = filled

    de_ratio = 0.3
    if mktcap > 0:
        de_ratio = clamp(safe(info.get("totalDebt"), 0.0) / mktcap, 0.0, 5.0)

    sector = (info.get("sector") or "").lower()
    if any(s in sector for s in ["utilities", "consumer defensive", "staples", "telecom"]):
        tg = 0.025
    elif any(s in sector for s in ["technology", "it", "semiconductor", "software"]):
        tg = 0.035
    else:
        tg = 0.03
    tg = clamp(tg, 0.01, 0.06)

    return {
        "company_name": info.get("longName") or info.get("shortName") or ticker.upper(),
        "beta": beta,
        "risk_free_rate": rf,
        "equity_risk_premium": erp,
        "cost_of_debt_pretax": rd_pretax,
        "tax_rate": eff_tax,
        "debt_to_equity": de_ratio,
        "terminal_growth": tg,
        "market_cap": mktcap if np.isfinite(mktcap) else None,
        "total_debt": safe(info.get("totalDebt"), None),
        "profile": f"{info.get('sector', 'Unknown')} / {info.get('industry', 'Unknown')}"
    }

def get_company_data(ticker: str) -> Dict[str, Any]:
    ticker = ticker.upper()
    dynamic_only = os.getenv("DCF_DYNAMIC_ONLY", "0") == "1"
    if not dynamic_only and ticker in COMPANY_DATA:
        return COMPANY_DATA[ticker]
    return fetch_company_assumptions(ticker)

# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------

@router.get("/health")
def dcf_health():
    return {"ok": True}

@router.get("/company-data/{ticker}")
async def get_company_parameters(ticker: str):
    try:
        data = get_company_data(ticker)
        wacc, wacc_details = calculate_wacc_from_company_data(data)
        return {
            "ticker": ticker.upper(),
            "company_name": data["company_name"],
            "profile": data["profile"],
            "wacc_calculated": round(wacc * 100, 2),
            "parameters": data,
            "wacc_breakdown": wacc_details
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/available-tickers")
async def list_available_tickers():
    return {
        "available_tickers": list(COMPANY_DATA.keys()),
        "count": len(COMPANY_DATA),
        "companies": [
            {
                "ticker": ticker,
                "name": data["company_name"],
                "profile": data["profile"],
                "beta": data["beta"],
                "terminal_growth": data["terminal_growth"]
            }
            for ticker, data in COMPANY_DATA.items()
        ]
    }

@router.get("/compare-assumptions")
async def compare_company_assumptions(tickers: List[str] = Query(default=["AAPL", "TSLA", "KO"])):
    try:
        comparison = {}
        for ticker in tickers:
            data = get_company_data(ticker)
            wacc, wacc_details = calculate_wacc_from_company_data(data)
            comparison[ticker] = {
                "company_name": data["company_name"],
                "beta": data["beta"],
                "wacc": round(wacc * 100, 2),
                "cost_of_equity": round(wacc_details["cost_of_equity"] * 100, 2),
                "terminal_growth": round(data["terminal_growth"] * 100, 2),
                "debt_to_equity": data["debt_to_equity"],
                "tax_rate": round(data["tax_rate"] * 100, 2),
                "profile": data["profile"]
            }
        return {
            "comparison": comparison,
            "note": "WACC, Cost of Equity, Terminal Growth, and Tax Rate shown as percentages"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{ticker}")
def get_dcf(
    ticker: str,
    years: int = Query(10, ge=3, le=20),
    midyear: bool = Query(True),
    terminal_growth_override: Optional[float] = Query(default=None),
    wacc_override: Optional[float] = Query(default=None),
    debug: bool = Query(False)
):
    try:
        company_data = get_company_data(ticker)

        y = yf.Ticker(ticker)
        info = y.info or {}

        if FMP_API_KEY:
            info = enrich_with_fmp(info, ticker)

        if wacc_override is not None:
            wacc_base = clamp(float(wacc_override), 0.03, 0.20)
            wacc_details = {"source": "manual_override", "value": wacc_base}
        else:
            wacc_base, wacc_details = calculate_wacc_from_company_data(company_data)

        if terminal_growth_override is not None:
            tg_used = clamp(float(terminal_growth_override), 0.01, 0.06)
            tg_source = "manual_override"
        else:
            tg_used = clamp(float(company_data["terminal_growth"]), 0.01, 0.06)
            tg_source = "company_specific_database"

        eff_tax = compute_effective_tax_rate(y, company_data)
        fcff0, fcff_diag = fcff_from_statements(y, eff_tax)

        gr = estimate_growths(y, years, company_data)
        fcff = build_fcff_path_via_roic(fcff0, eff_tax, years, gr["growth_path"], y)

        cash = compute_cash_like(info, y.balance_sheet)
        debt = safe(info.get("totalDebt"), 0.0)
        shares = safe(info.get("impliedSharesOutstanding") or info.get("sharesOutstanding"), 0.0)
        shares = max(shares, 1e-6)

        result = dcf_valuation(
            fcff=fcff,
            wacc=wacc_base,
            terminal_growth=tg_used,
            midyear=midyear,
            cash=cash,
            debt=debt,
            shares_out=shares,
            extras=None
        )

        grid = sensitivity_grid(fcff, wacc_base, tg_used, cash, debt, shares, midyear)
        snapshot = compute_financials_snapshot(y, info)

        out = {
            "ticker": ticker.upper(),
            "company_name": company_data["company_name"],
            "profile": company_data["profile"],
            "inputs": {
                "years": years,
                "midyear": midyear,
                "wacc": wacc_base,
                "terminal_growth": tg_used,
                "wacc_details": wacc_details,
                "tg_source": tg_source,
                "effective_tax_rate": eff_tax,
                "cash": cash,
                "debt": debt,
                "shares_out": shares
            },
            "growth_estimates": gr,
            "fcff_projection": fcff,
            "dcf_result": _clean(result),
            "sensitivity_grid": grid,
            "financials_snapshot": _clean(snapshot),
        }

        if debug:
            out["diagnostics"] = {"fcff": fcff_diag}

        return out

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DCF computation failed: {str(e)}")
