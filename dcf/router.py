# dcf/router.py
from fastapi import APIRouter, HTTPException, Query
import yfinance as yf
import numpy as np
import math
from calc import dcf_valuation  # keep this import

router = APIRouter(prefix="/api/dcf", tags=["DCF"])

# ----------------- utils -----------------
def safe(val, default=0.0):
    try:
        return float(val) if val is not None else float(default)
    except Exception:
        return float(default)

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def nz(x, alt):
    return x if x is not None else alt

def _row(df, name):
    """Safe row getter by index label."""
    try:
        if df is not None and not df.empty and isinstance(name, str) and (name in df.index):
            return df.loc[name]
    except Exception:
        pass
    return None

def _first(row):
    """First (most recent) column value of a row Series (yfinance quarterly/annual are most-recent at iloc[0])."""
    try:
        if row is not None and hasattr(row, "iloc") and len(row) > 0:
            return float(row.iloc[0])
    except Exception:
        pass
    return np.nan

def _series_vals(row, max_n=5):
    """Return up to max_n numeric values from a row (most recent first)."""
    try:
        if row is not None and hasattr(row, "dropna"):
            vals = row.dropna().astype(float).values
            return [float(v) for v in vals[:max_n]]
    except Exception:
        pass
    return []

def _clean_num(x):
    """Return a finite float or None."""
    try:
        xf = float(x)
        if math.isfinite(xf):
            return xf
    except Exception:
        pass
    return None

def _clean(obj):
    """Recursively replace NaN/Inf with None for JSON."""
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, (int, float, np.floating, np.integer)):
        return _clean_num(obj)
    return obj

def _qsum(row, n=4):
    """Sum last n quarterly values for a TTM approximation."""
    try:
        if row is not None and hasattr(row, "dropna"):
            vals = row.dropna().astype(float).values[:n]
            return float(np.nansum(vals))
    except Exception:
        pass
    return np.nan

# ----------------- market & risk inputs -----------------
def fetch_risk_free_rate() -> float:
    """U.S. 10Y (^TNX), yfinance returns percent*10; divide by 100."""
    try:
        tnx = yf.Ticker("^TNX").history(period="10d")
        if tnx is not None and not tnx.empty and "Close" in tnx:
            close = tnx["Close"].dropna()
            if len(close) > 0:
                rf = float(close.iloc[-1]) / 100.0
                return clamp(rf, 0.02, 0.07)
    except Exception:
        pass
    return 0.04

def compute_effective_tax_rate(tkr: yf.Ticker) -> float:
    """Effective tax = Income Tax Expense / Income Before Tax (fallback 21%)."""
    try:
        fin = tkr.financials
        if fin is not None and not fin.empty:
            tax = safe(_first(_row(fin, "Income Tax Expense")), np.nan)
            pre = safe(_first(_row(fin, "Income Before Tax")), np.nan)
            if np.isfinite(tax) and np.isfinite(pre) and pre != 0.0:
                return clamp(tax / pre, 0.00, 0.35)
    except Exception:
        pass
    return 0.21

# --------- beta / costs ----------
def compute_beta_historical(ticker: str, market: str = "^GSPC"):
    """Weekly beta over ~2 years vs S&P500 (^GSPC)."""
    diag = {"points": 0, "period": "2y", "freq": "1wk", "method": "cov/var"}
    try:
        s_hist = yf.Ticker(ticker).history(period="2y", interval="1wk")
        m_hist = yf.Ticker(market).history(period="2y", interval="1wk")
        if s_hist is not None and not s_hist.empty and m_hist is not None and not m_hist.empty:
            if "Close" in s_hist and "Close" in m_hist:
                s = s_hist["Close"].dropna()
                m = m_hist["Close"].dropna()
                idx = s.index.intersection(m.index)
                s, m = s.loc[idx], m.loc[idx]
                if len(s) >= 26 and len(m) >= 26:
                    rs = np.diff(np.log(s.values))
                    rm = np.diff(np.log(m.values))
                    diag["points"] = int(len(rs))
                    vm = np.var(rm, ddof=1)
                    if vm > 0:
                        cov = np.cov(rs, rm, ddof=1)[0, 1]
                        beta = cov / vm
                        return clamp(float(beta), 0.2, 3.0), diag
    except Exception:
        pass
    return float("nan"), diag

def compute_beta(info: dict, ticker: str):
    """Blend historical beta (70%) with Yahoo info beta (30%)."""
    b_info_raw = info.get("beta")
    b_info = None
    try:
        if b_info_raw is not None:
            b_info = clamp(float(b_info_raw), 0.2, 3.0)
    except Exception:
        b_info = None

    b_hist, diag_hist = compute_beta_historical(ticker)
    has_hist, has_info = np.isfinite(b_hist), (b_info is not None)

    if has_hist and has_info:
        b = 0.7 * b_hist + 0.3 * b_info
        src = "blend(70% hist, 30% info)"
    elif has_hist:
        b, src = b_hist, "historical"
    elif has_info:
        b, src = b_info, "info"
    else:
        b, src = 1.0, "fallback"

    return clamp(b, 0.2, 3.0), {"source": src, "hist_diag": diag_hist, "info_beta": b_info_raw}

def market_risk_premium_with_size(info: dict, base_mrp: float = 0.0475) -> float:
    """Size tilt: mega-caps slightly lower, small-caps slightly higher."""
    mc = safe(info.get("marketCap"), 0.0)
    adj = -0.005 if mc >= 5e11 else (0.01 if (mc and mc <= 1e10) else 0.0)
    return clamp(base_mrp + adj, 0.035, 0.07)

def compute_cost_of_equity(rf: float, beta: float, mrp: float) -> float:
    return clamp(rf + beta * mrp, 0.05, 0.16)

def compute_cost_of_debt_after_tax(tkr: yf.Ticker, tax_rate: float, rf: float):
    """
    After-tax CoD:
      1) avg(Interest Expense TTM)/avg(Debt last 4Q)  -> * (1 - tax)
      2) If missing: map Interest Coverage to spread (pre-tax = rf + spread)
      3) Fallback: rf + 1.5% (pre-tax)
    """
    diag = {"method": None}
    try:
        # Route 1: average quarterly interest / average total debt (more stable)
        fin_q, bs_q = tkr.quarterly_financials, tkr.quarterly_balance_sheet
        if fin_q is not None and not fin_q.empty and bs_q is not None and not bs_q.empty:
            int_row = _row(fin_q, "Interest Expense")
            debt_row = _row(bs_q, "Total Debt")
            if int_row is not None and debt_row is not None:
                interest_4q = _qsum(int_row, 4)
                debt_vals = _series_vals(debt_row, max_n=4)
                avg_debt = float(np.nanmean(debt_vals)) if len(debt_vals) > 0 else np.nan
                if np.isfinite(interest_4q) and np.isfinite(avg_debt) and avg_debt > 0:
                    pretax = clamp(abs(interest_4q) / avg_debt, 0.01, 0.12)
                    diag.update({"method": "avg(Interest_TTM)/avg(Debt_4Q)", "pretax_cod": pretax})
                    return pretax * (1.0 - tax_rate), diag

        # Route 2: coverage -> spread (annual)
        fin = tkr.financials
        ebit = _first(_row(fin, "Ebit")) if (fin is not None and not fin.empty) else np.nan
        if not np.isfinite(ebit) and (fin is not None and not fin.empty):
            ebit = _first(_row(fin, "Operating Income"))
        interest_exp = _first(_row(fin, "Interest Expense")) if (fin is not None and not fin.empty) else np.nan

        if np.isfinite(ebit) and np.isfinite(interest_exp) and interest_exp != 0.0:
            coverage = abs(ebit / interest_exp)
            if coverage >= 12: spread = 0.010
            elif coverage >= 8: spread = 0.015
            elif coverage >= 6: spread = 0.020
            elif coverage >= 4: spread = 0.025
            elif coverage >= 3: spread = 0.030
            elif coverage >= 2: spread = 0.040
            elif coverage >= 1: spread = 0.060
            else:               spread = 0.080
            pretax = clamp(rf + spread, 0.03, 0.16)
            diag.update({"method": "coverage->spread", "coverage": coverage, "pretax_cod": pretax})
            return pretax * (1.0 - tax_rate), diag
    except Exception:
        pass

    # Fallback
    pretax = clamp(rf + 0.015, 0.03, 0.12)
    diag.update({"method": "fallback", "pretax_cod": pretax})
    return pretax * (1.0 - tax_rate), diag

def compute_wacc(info: dict, coe: float, cod_after_tax: float) -> float:
    E = max(safe(info.get("marketCap"), 0.0), 0.0)
    D = max(safe(info.get("totalDebt"), 0.0), 0.0)
    V = E + D
    if V <= 0.0:
        return coe
    we, wd = E / V, D / V
    return clamp(we * coe + wd * cod_after_tax, 0.05, 0.15)

# ----------------- cash-like assets -----------------
def compute_cash_like(info: dict, bs) -> float:
    """
    Use cash + short-term investments + marketable securities if available.
    Yahoo 'totalCash' can understate cash-like assets.
    """
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
                    if np.isfinite(v): extras += float(v)
            except Exception:
                pass
        cash = max(cash, extras)

    return cash

# ----------------- ΔNWC & FCFF (TTM, quarterly) -----------------
def compute_delta_nwc_quarterly(bs_q) -> float:
    """
    ΔNWC_TTM = NWC(t) - NWC(t-1),
    with NWC ≈ (Current Assets - Cash) - (Current Liabilities - Short-term Debt).
    """
    if bs_q is None or bs_q.empty:
        return 0.0

    def series_vals(name):
        return _series_vals(_row(bs_q, name), max_n=2)

    tca  = series_vals("Total Current Assets")
    tcl  = series_vals("Total Current Liabilities")
    cash = series_vals("Cash And Cash Equivalents") or series_vals("Cash")
    std  = series_vals("Short Long Term Debt") or series_vals("Short/Current Long Term Debt")

    def v(a, i):
        try:
            return float(a[i])
        except Exception:
            return 0.0

    ca0, ca1 = v(tca, 0), v(tca, 1)
    cl0, cl1 = v(tcl, 0), v(tcl, 1)
    c0,  c1  = v(cash, 0), v(cash, 1)
    sd0, sd1 = v(std, 0),  v(std, 1)

    nwc0 = (ca0 - c0) - (cl0 - sd0)
    nwc1 = (ca1 - c1) - (cl1 - sd1)
    return nwc0 - nwc1

def fcff_from_statements(tkr: yf.Ticker, eff_tax: float) -> tuple[float, dict]:
    """
    FCFF_TTM = EBIT_TTM*(1-T) + D&A_TTM - CapEx_TTM - ΔNWC_TTM
    Derived from most recent quarterly data (TTM) with fallbacks.
    """
    fin_q = tkr.quarterly_financials
    cf_q  = tkr.quarterly_cashflow
    bs_q  = tkr.quarterly_balance_sheet
    diag = {"components": {}, "source_quality": "ok"}

    # EBIT TTM
    ebit_ttm = np.nan
    for lab in ["Ebit", "Operating Income"]:
        if fin_q is not None and not fin_q.empty and lab in fin_q.index:
            ebit_ttm = _qsum(_row(fin_q, lab), 4)
            if np.isfinite(ebit_ttm): break
    diag["components"]["EBIT_TTM"] = ebit_ttm

    # D&A TTM
    da_ttm = np.nan
    if cf_q is not None and not cf_q.empty:
        for lab in ["Depreciation", "Depreciation & Amortization", "Depreciation Amortization Depletion", "DepreciationAndAmortization"]:
            if lab in cf_q.index:
                da_ttm = _qsum(_row(cf_q, lab), 4)
                if np.isfinite(da_ttm): break
    diag["components"]["D&A_TTM"] = da_ttm

    # CapEx TTM (absolute value of cash outflow)
    capex_ttm = np.nan
    if cf_q is not None and not cf_q.empty and "Capital Expenditures" in cf_q.index:
        capex_ttm = abs(_qsum(_row(cf_q, "Capital Expenditures"), 4))
    diag["components"]["CapEx_TTM"] = capex_ttm

    # ΔNWC TTM
    delta_nwc_ttm = compute_delta_nwc_quarterly(bs_q)
    diag["components"]["ΔNWC_TTM"] = delta_nwc_ttm

    # FCFF_TTM
    if all(np.isfinite(v) for v in [ebit_ttm, da_ttm, capex_ttm]) and np.isfinite(delta_nwc_ttm):
        fcff0 = ebit_ttm * (1.0 - eff_tax) + da_ttm - capex_ttm - delta_nwc_ttm
        diag["method"] = "EBIT(1-T)+DA-CapEx-ΔNWC (TTM, quarterly)"
        return float(fcff0), diag

    # Fallbacks
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

    diag["method"] = "Fallback info.freeCashflow/operatingCashflow"
    info = tkr.info or {}
    fcff0 = safe(info.get("freeCashflow") or info.get("operatingCashflow"), 0.0)
    return float(fcff0), diag

# ----------------- growths -----------------
def estimate_growths(tkr: yf.Ticker, horizon: int) -> dict:
    info, fin, cf = tkr.info or {}, tkr.financials, tkr.cashflow

    # FCFF history for CAGR (if available)
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

    # Revenue CAGR (3–5 points)
    g_rev_cagr = np.nan
    if fin is not None and not fin.empty and ("Total Revenue" in fin.index):
        rev = _series_vals(_row(fin, "Total Revenue"), max_n=5)
        if len(rev) >= 2 and rev[-1] > 0:
            recent, oldest = float(rev[0]), float(rev[-1])
            n = len(rev) - 1
            g_rev_cagr = clamp((recent / oldest) ** (1.0 / n) - 1.0, -0.2, 0.25)

    # Blend: FCFF has more weight
    if np.isfinite(g_rev_cagr):
        g_used = clamp(0.7 * g_fcff_hist + 0.3 * g_rev_cagr, -0.05, 0.20)
    else:
        g_used = g_fcff_hist

    # Decaying path
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

# ----------------- terminal growth -----------------
def compute_terminal_growth_enhanced(rf: float, g_hist: float, rev_cagr: float | None, margins: float | None) -> float:
    """
    TG anchored to nominal growth and rf, tempered by firm specifics.
      base_nominal ≈ 4.0%
      tg = 0.4*base_nominal + 0.4*rf + 0.2*max(g_hist, rev_cagr)
      margin nudge: +30bps if op margin >25%, -30bps if <10%
      guardrails: 2.0%–5.0%
    """
    base_nominal = 0.04
    growth_signal = g_hist
    if rev_cagr is not None and np.isfinite(rev_cagr):
        growth_signal = max(g_hist, rev_cagr)
    tg = 0.4 * base_nominal + 0.4 * clamp(rf, 0.02, 0.05) + 0.2 * clamp(growth_signal, 0.0, 0.08)

    if margins is not None and np.isfinite(margins):
        if margins > 0.25: tg += 0.003
        elif margins < 0.10: tg -= 0.003

    return clamp(tg, 0.02, 0.05)

# ----------------- WACC path -----------------
def build_wacc_path(base_beta: float, rf: float, mrp: float, cod_after_tax: float, info: dict, years: int):
    E = max(safe(info.get("marketCap"), 0.0), 0.0)
    D = max(safe(info.get("totalDebt"), 0.0), 0.0)
    V0 = E + D if (E + D) > 0 else 1.0
    wd0 = D / V0

    is_mega = E >= 5e11
    wd_target = clamp(wd0 * (0.90 if is_mega else 1.00), 0.0, 0.95)

    waccs, coes, weights = [], [], []
    for t in range(1, years + 1):
        decay = 0.85 ** t
        beta_t = 1.0 + (base_beta - 1.0) * decay
        coe_t = clamp(rf + beta_t * mrp, 0.05, 0.16)

        wd_t = clamp(wd0 + (wd_target - wd0) * (t / years), 0.0, 0.95)
        we_t = clamp(1.0 - wd_t, 0.05, 0.99)

        wacc_t = clamp(we_t * coe_t + wd_t * cod_after_tax, 0.05, 0.15)

        waccs.append(wacc_t)
        coes.append(coe_t)
        weights.append({"we": we_t, "wd": wd_t, "beta_t": beta_t})

    return waccs, coes, weights

def discount_factors_varying_wacc(waccs: list[float], midyear: bool) -> list[float]:
    dfs, cum = [], 1.0
    for i, r in enumerate(waccs, start=1):
        if i > 1:
            cum *= 1.0 / (1.0 + waccs[i-2])
        df = cum / ((1.0 + r) ** (0.5 if midyear else 1.0))
        dfs.append(df)
    return dfs

def pv_with_varying_wacc(fcff: list[float], waccs: list[float], midyear: bool, terminal_growth: float):
    dfs = discount_factors_varying_wacc(waccs, midyear)
    pv_explicit = sum((fcff[i] * dfs[i]) for i in range(len(fcff)))
    rN = waccs[-1]
    tv = (fcff[-1] * (1.0 + terminal_growth)) / max(rN - terminal_growth, 1e-6)
    disc_tv = 1.0
    for r in waccs:
        disc_tv *= 1.0 / (1.0 + r)
    pv_tv = tv * disc_tv
    return float(pv_explicit), float(pv_tv), float(tv), dfs

# ----------------- ROIC-based FCFF path -----------------
def estimate_roic_and_reinvestment(tkr: yf.Ticker) -> dict:
    fin_q, bs_q = tkr.quarterly_financials, tkr.quarterly_balance_sheet

    ebit_ttm = np.nan
    if fin_q is not None and not fin_q.empty:
        for lab in ["Ebit", "Operating Income"]:
            if lab in fin_q.index:
                ebit_ttm = _qsum(_row(fin_q, lab), 4)
                if np.isfinite(ebit_ttm): break

    ic = np.nan
    if bs_q is not None and not bs_q.empty:
        ta = _first(_row(bs_q, "Total Assets")) or np.nan
        tcl = _first(_row(bs_q, "Total Current Liabilities")) or 0.0
        cash_like = compute_cash_like(tkr.info or {}, bs_q)
        if np.isfinite(ta):
            ic = max(ta - tcl - cash_like, 1.0)

    return {"nopat_ttm": ebit_ttm, "invested_capital": ic}

def build_fcff_path_via_roic(fcff0: float, tax_rate: float, years: int, growth_path: list[float], tkr: yf.Ticker):
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

# ----------------- snapshot / multiples ----------
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

# ----------------- sensitivity grid -----------------
def sensitivity_grid(fcff, wacc_base, tg_base, cash, debt, shares, midyear, step_wacc=0.015, step_tg=0.005):
    rows = []
    for tg in [clamp(tg_base - step_tg, 0.01, 0.06), tg_base, clamp(tg_base + step_tg, 0.01, 0.06)]:
        row = []
        for w in [clamp(wacc_base - step_wacc, 0.03, 0.20), wacc_base, clamp(wacc_base + step_wacc, 0.03, 0.20)]:
            res = dcf_valuation(
                fcff=fcff, wacc=w, terminal_growth=tg, midyear=midyear,
                cash=cash, debt=debt, shares_out=shares, extras=None
            )
            row.append(_clean_num(res.get("intrinsic_value_per_share")))
        rows.append(row)
    return rows

# ----------------- API -----------------
@router.get("/{ticker}")
def get_dcf(
    ticker: str,
    years: int = Query(10, ge=3, le=20, description="Forecast horizon (years)"),
    midyear: bool = True,
    terminal_growth: float | None = Query(None, description="Optional override, e.g. 0.035"),
    debug: bool = False
):
    try:
        y = yf.Ticker(ticker)
        info = y.info or {}

        # Capital inputs (base)
        rf = fetch_risk_free_rate()
        tax_rate = compute_effective_tax_rate(y)
        beta, beta_diag = compute_beta(info, ticker)
        mrp = market_risk_premium_with_size(info, base_mrp=0.0475)
        coe = compute_cost_of_equity(rf, beta, mrp)
        cod_after, cod_diag = compute_cost_of_debt_after_tax(y, tax_rate, rf)
        wacc_base = compute_wacc(info, coe, cod_after)

        # FCFF starting level from statements (TTM)
        fcff0, fcff_diag = fcff_from_statements(y, tax_rate)

        # Growths
        g = estimate_growths(y, years)
        margins = safe(info.get("operatingMargins"), np.nan)
        tg_auto = compute_terminal_growth_enhanced(rf, g["g_fcff_hist"], g["g_rev_cagr"], margins)
        tg_used = clamp(float(terminal_growth), 0.01, 0.06) if terminal_growth is not None else tg_auto

        # Build FCFF path via ROIC model with smoothing
        fcff = build_fcff_path_via_roic(fcff0, tax_rate, years, g["growth_path"], y)

        # Equity bridge
        shares = safe(info.get("impliedSharesOutstanding") or info.get("sharesOutstanding"), 0.0)
        debt = safe(info.get("totalDebt"), 0.0)
        cash = compute_cash_like(info, y.balance_sheet)
        if len(fcff) == 0 or fcff[0] == 0.0:
            raise HTTPException(status_code=400, detail="Unable to build FCFF projections for this ticker.")

        # -------- BASE valuation
        base = dcf_valuation(
            fcff=fcff, wacc=wacc_base, terminal_growth=tg_used, midyear=midyear,
            cash=cash, debt=debt, shares_out=shares,
            extras={
                "tax_rate": tax_rate,
                "growth_rates": g["growth_path"],
                "data_sources": [
                    {"name": "Yahoo Finance (yfinance)", "fields": [
                        "financials", "balance_sheet", "cashflow", "quarterly_financials",
                        "quarterly_balance_sheet", "quarterly_cashflow",
                        "marketCap", "totalDebt", "totalCash", "sharesOutstanding", "impliedSharesOutstanding",
                        "beta", "operatingMargins", "trailingEps", "financialCurrency"
                    ]},
                    {"name": "Yahoo Finance ^TNX", "fields": ["10Y Treasury yield (risk-free rate)"]},
                    {"name": "^GSPC", "fields": ["Market return series for historical beta"]},
                ],
                "disclaimer": "Educational DCF with automatic, ticker-specific assumptions derived from public data."
            }
        )

        # -------- DYNAMIC valuation (time-dependent WACC)
        waccs, coes_path, weights_path = build_wacc_path(beta, rf, mrp, cod_after, info, years)
        pv_exp_dyn, pv_tv_dyn, tv_dyn, dfs_dyn = pv_with_varying_wacc(fcff, waccs, midyear, tg_used)
        ev_dyn = pv_exp_dyn + pv_tv_dyn
        eq_dyn = ev_dyn + cash - debt
        ivps_dyn = (eq_dyn / shares) if shares else None

        # -------- Sensitivity
        sens_grid = sensitivity_grid(
            fcff=fcff, wacc_base=wacc_base, tg_base=tg_used,
            cash=cash, debt=debt, shares=shares, midyear=midyear,
            step_wacc=0.015, step_tg=0.005
        )

        # Financials snapshot
        snapshot = compute_financials_snapshot(y, info)

        # Compose response
        out = {
            "ticker": ticker.upper(),
            "valuation": {
                "base_constant_wacc": {
                    "enterprise_value": base["enterprise_value"],
                    "equity_value": base["equity_value"],
                    "intrinsic_value_per_share": base["intrinsic_value_per_share"],
                    "pv_of_explicit_fcff": base["pv_of_explicit_fcff"],
                    "pv_of_terminal_value": base["pv_of_terminal_value"],
                    "terminal_value_at_horizon": base["terminal_value_at_horizon"],
                    "discount_factors": base["discount_factors"],
                },
                "dynamic_wacc": {
                    "enterprise_value": ev_dyn,
                    "equity_value": eq_dyn,
                    "intrinsic_value_per_share": ivps_dyn,
                    "pv_of_explicit_fcff": pv_exp_dyn,
                    "pv_of_terminal_value": pv_tv_dyn,
                    "terminal_value_at_horizon": tv_dyn,
                    "discount_factors": dfs_dyn,
                    "wacc_path": waccs,
                    "coe_path": coes_path,
                    "weights_path": weights_path,
                },
                "sensitivity": {
                    "grid_wacc_rows_tg_cols": sens_grid,
                    "wacc_axis": [clamp(wacc_base - 0.015, 0.03, 0.2), wacc_base, clamp(wacc_base + 0.015, 0.03, 0.2)],
                    "tg_axis": [clamp(tg_used - 0.005, 0.01, 0.06), tg_used, clamp(tg_used + 0.005, 0.01, 0.06)],
                }
            },
            "assumptions": {
                "risk_free_rate": rf,
                "beta": beta,
                "beta_details": beta_diag,
                "market_risk_premium_used": mrp,
                "cost_of_equity": coe,
                "cost_of_debt_after_tax": cod_after,
                "wacc_base": wacc_base,
                "terminal_growth_used": tg_used,
                "years_forecasted": years,
                "operating_margins": safe(info.get("operatingMargins"), np.nan),
                "effective_tax_rate": tax_rate,  # <— added for verification/UI
                "growths": {
                    "fcff_cagr_hist": g["g_fcff_hist"],
                    "revenue_cagr": g["g_rev_cagr"],
                    "projection_growth_path": g["growth_path"],
                },
                "fcff_start_method": fcff_diag,
            },
            "fcff_projection": fcff,
            "financials_snapshot": snapshot,
        }

        if debug:
            out["diagnostics"] = {
                "cost_of_debt_method": cod_diag,
                "wacc_weights_now": {
                    "marketCap": safe(info.get("marketCap"), 0.0),
                    "totalDebt": safe(info.get("totalDebt"), 0.0),
                },
            }

        return _clean(out)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
