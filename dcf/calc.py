# dcf/dcf_calc.py
from typing import List, Optional, Dict, Any
import numpy as np

def _dfs(r: float, n: int, midyear: bool):
    t = np.arange(1, n + 1, dtype=float)
    if midyear:
        t -= 0.5
    return (1 + r) ** (-t)

def _terminal(last_fcff: float, r: float, g: float):
    return (last_fcff * (1 + g)) / (r - g)

def dcf_valuation(
    fcff: List[float],
    wacc: float,
    terminal_growth: float,
    midyear: bool,
    cash: float,
    debt: float,
    shares_out: Optional[float],
    extras: Optional[Dict[str, Any]] = None,
):
    n = len(fcff)
    dfs = _dfs(wacc, n, midyear)
    pv_explicit = float(np.dot(np.array(fcff), dfs))
    tv = _terminal(fcff[-1], wacc, terminal_growth)
    tv_df = (1 + wacc) ** (-(n - (0.5 if midyear else 0.0)))
    pv_tv = float(tv * tv_df)
    ev = pv_explicit + pv_tv
    eq = ev + cash - debt
    per_share = (eq / shares_out) if shares_out else None

    out = {
        "enterprise_value": ev,
        "equity_value": eq,
        "intrinsic_value_per_share": per_share,
        "pv_of_explicit_fcff": pv_explicit,
        "pv_of_terminal_value": pv_tv,
        "terminal_value_at_horizon": tv,
        "fcff_projection": fcff,
        "discount_factors": list(map(float, dfs)),
        "assumptions": {
            "wacc": wacc,
            "terminal_growth": terminal_growth,
            "midyear": midyear,
        },
    }
    if extras:
        if "tax_rate" in extras: out["assumptions"]["tax_rate"] = extras["tax_rate"]
        if "growth_rates" in extras: out["assumptions"]["growth_rates"] = extras["growth_rates"]
        if "data_sources" in extras: out["data_sources"] = extras["data_sources"]
        if "disclaimer" in extras: out["disclaimer"] = extras["disclaimer"]
    return out
