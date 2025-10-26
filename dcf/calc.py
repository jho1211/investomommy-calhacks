#dcf_calc.py
from typing import List, Optional, Dict, Any
import math

# ===========================
# Company-specific assumptions
# (Optional – router does not depend on these; kept for convenience)
# ===========================
COMPANY_DATA: Dict[str, Dict[str, Any]] = {
    "AAPL": {
        "beta": 1.25,
        "risk_free_rate": 0.045,
        "equity_risk_premium": 0.055,
        "cost_of_debt": 0.035,
        "tax_rate": 0.15,
        "debt_to_equity": 1.57,
        "terminal_growth": 0.035,
        "company_name": "Apple Inc.",
    },
    "TSLA": {
        "beta": 2.05,
        "risk_free_rate": 0.045,
        "equity_risk_premium": 0.055,
        "cost_of_debt": 0.065,
        "tax_rate": 0.21,
        "debt_to_equity": 0.15,
        "terminal_growth": 0.045,
        "company_name": "Tesla Inc.",
    },
    "KO": {
        "beta": 0.65,
        "risk_free_rate": 0.045,
        "equity_risk_premium": 0.055,
        "cost_of_debt": 0.030,
        "tax_rate": 0.21,
        "debt_to_equity": 1.85,
        "terminal_growth": 0.025,
        "company_name": "The Coca-Cola Company",
    },
    "MSFT": {
        "beta": 1.15,
        "risk_free_rate": 0.045,
        "equity_risk_premium": 0.055,
        "cost_of_debt": 0.032,
        "tax_rate": 0.16,
        "debt_to_equity": 0.45,
        "terminal_growth": 0.035,
        "company_name": "Microsoft Corporation",
    },
    "GOOGL": {
        "beta": 1.10,
        "risk_free_rate": 0.045,
        "equity_risk_premium": 0.055,
        "cost_of_debt": 0.028,
        "tax_rate": 0.15,
        "debt_to_equity": 0.08,
        "terminal_growth": 0.040,
        "company_name": "Alphabet Inc.",
    },
}


def get_company_data(ticker: str) -> Dict[str, Any]:
    t = (ticker or "").upper()
    if t not in COMPANY_DATA:
        raise ValueError(
            f"Ticker '{t}' not found. Available: {', '.join(COMPANY_DATA.keys())}"
        )
    return COMPANY_DATA[t]


def calculate_cost_of_equity(beta: float, rf: float, erp: float) -> float:
    """CAPM: re = rf + β × ERP"""
    return float(rf) + float(beta) * float(erp)


def calculate_wacc(
    *,
    beta: float,
    rf: float,
    erp: float,
    rd_pretax: float,
    tax_rate: float,
    debt_to_equity: float,
) -> float:
    """WACC = (E/V)·re + (D/V)·rd·(1−t), with E=1, D=D/E"""
    re = calculate_cost_of_equity(beta, rf, erp)
    de = float(debt_to_equity)
    total_cap = 1.0 + de
    ew = 1.0 / total_cap
    dw = de / total_cap
    rd_after = float(rd_pretax) * (1.0 - float(tax_rate))
    return ew * re + dw * rd_after


# ===========================
# Core DCF math (adapter the router expects)
# ===========================
def _discount_factor(rate: float, t: float) -> float:
    return (1.0 + rate) ** (-t)


def _terminal_value(last_fcff: float, rate: float, growth: float) -> float:
    # Guard against r <= g
    if rate <= growth:
        # back off growth slightly to avoid divide-by-zero or negative denom
        growth = rate - 0.001
    return float(last_fcff) * (1.0 + growth) / (rate - growth)


def dcf_valuation(
    *,
    fcff: List[float],
    # names used by the router
    wacc: Optional[float] = None,
    terminal_growth: Optional[float] = None,
    midyear: bool = True,
    cash: float = 0.0,
    debt: float = 0.0,
    shares_out: Optional[float] = None,
    extras: Optional[Dict[str, Any]] = None,
    # aliases for flexibility (won't be used by your router but harmless)
    discount_rate: Optional[float] = None,
    r: Optional[float] = None,
    g: Optional[float] = None,
    shares: Optional[float] = None,
    shares_outstanding: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Adapter-style DCF that matches the router's call signature.
    Computes PV of explicit FCFF (with optional midyear) + Gordon terminal,
    then EV → Equity → per-share.
    """
    if not isinstance(fcff, list) or len(fcff) == 0:
        raise ValueError("fcff must be a non-empty list of numbers")

    # normalize inputs / aliases
    rate = next((x for x in (wacc, discount_rate, r) if x is not None), None)
    growth = next((x for x in (terminal_growth, g) if x is not None), None)
    shares_norm = next((x for x in (shares_out, shares, shares_outstanding) if x is not None), None)

    if rate is None:
        raise ValueError("wacc/discount_rate/r must be provided")
    if growth is None:
        raise ValueError("terminal_growth/g must be provided")

    rate = float(rate)
    growth = float(growth)
    cash = float(cash or 0.0)
    debt = float(debt or 0.0)
    n = len(fcff)

    if shares_norm is None or shares_norm <= 0:
        shares_norm = 1e-6  # avoid divide-by-zero; caller should supply a real value

    # PV of explicit period
    pv_explicit = 0.0
    for idx, cf in enumerate(fcff, start=1):
        expo = (idx - 0.5) if midyear else idx
        pv_explicit += float(cf) * _discount_factor(rate, expo)

    # Terminal value at horizon N, then discounted back
    tv = _terminal_value(float(fcff[-1]), rate, growth)
    tv_expo = (n - 0.5) if midyear else n
    pv_tv = tv * _discount_factor(rate, tv_expo)

    # Enterprise → Equity → Per-share
    enterprise_value = pv_explicit + pv_tv
    equity_value = enterprise_value + cash - debt
    intrinsic_value_per_share = equity_value / float(shares_norm)

    out = {
        "intrinsic_value_per_share": float(intrinsic_value_per_share),
        "enterprise_value": float(enterprise_value),
        "equity_value": float(equity_value),
        "pv_explicit": float(pv_explicit),
        "pv_terminal": float(pv_tv),
        "terminal_value": float(tv),
        "assumptions": {
            "wacc": rate,
            "terminal_growth": growth,
            "midyear": bool(midyear),
            "cash": cash,
            "debt": debt,
            "shares_out": float(shares_norm),
            **(extras or {}),
        },
    }
    return out


# ===========================
# Optional convenience wrapper (not used by the router)
# ===========================
def dcf_valuation_with_company(
    *,
    ticker: str,
    fcff: List[float],
    cash: float,
    debt: float,
    shares_out: float,
    midyear: bool = True,
    wacc_override: Optional[float] = None,
    terminal_growth_override: Optional[float] = None,
    extras: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Convenience wrapper if you ever want to compute using the
    hardcoded COMPANY_DATA. The router does not need this.
    """
    cd = get_company_data(ticker)
    rate = (
        float(wacc_override)
        if wacc_override is not None
        else calculate_wacc(
            beta=cd["beta"],
            rf=cd["risk_free_rate"],
            erp=cd["equity_risk_premium"],
            rd_pretax=cd["cost_of_debt"],
            tax_rate=cd["tax_rate"],
            debt_to_equity=cd["debt_to_equity"],
        )
    )
    growth = (
        float(terminal_growth_override)
        if terminal_growth_override is not None
        else float(cd["terminal_growth"])
    )

    result = dcf_valuation(
        fcff=fcff,
        wacc=rate,
        terminal_growth=growth,
        midyear=midyear,
        cash=cash,
        debt=debt,
        shares_out=shares_out,
        extras={"ticker": ticker, "company_name": cd.get("company_name", ""), **(extras or {})},
    )
    return result
