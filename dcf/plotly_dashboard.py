# dcf/plotly_dashboard.py
import argparse
import requests
from typing import Any, Dict

from dash import Dash, html, dcc, Input, Output, State
import plotly.graph_objects as go

# --------- helpers ----------
def pct(x):
    try:
        return f"{x*100:.2f}%"
    except Exception:
        return "—"

def fmt_usd(x, short=False):
    try:
        x = float(x)
    except Exception:
        return "—"
    if short:
        return f"${x/1e9:,.1f}B"
    return f"${x:,.0f}"

def fmt_num(x):
    try:
        return f"{float(x):,.0f}"
    except Exception:
        return "—"

def get(d, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

def fetch(api_base: str, ticker: str, years: int = 10, midyear: bool = True) -> Dict[str, Any]:
    url = f"{api_base.rstrip('/')}/api/dcf/{ticker.upper()}?years={years}&midyear={'true' if midyear else 'false'}&debug=true"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

def make_heatmap(grid, wacc_axis, tg_axis):
    # axis labels can be numeric or strings; format if numeric
    if wacc_axis and isinstance(wacc_axis[0], (int, float)):
        wacc_labels = [f"{w*100:.2f}%" for w in wacc_axis]
    else:
        wacc_labels = wacc_axis or ["WACC"]
    if tg_axis and isinstance(tg_axis[0], (int, float)):
        tg_labels = [f"{g*100:.2f}%" for g in tg_axis]
    else:
        tg_labels = tg_axis or ["g"]

    fig = go.Figure(data=go.Heatmap(
        z=grid or [[None]], x=tg_labels, y=wacc_labels,
        colorscale="Viridis",
        colorbar=dict(title="IV / Share (USD)"),
        hovertemplate="WACC %{y}<br>g %{x}<br>IV $%{z:.0f}<extra></extra>"
    ))
    fig.update_layout(
        template="plotly_dark",
        xaxis_title="Terminal Growth (g)",
        yaxis_title="WACC",
        margin=dict(l=70, r=20, t=10, b=60),
        height=520
    )
    return fig

# --------- app factory ----------
def create_app(api_base: str, default_ticker: str = "AAPL") -> Dash:
    app = Dash(__name__, title="DCF Dev Dashboard")

    app.layout = html.Div(
        style={"background": "#0f1115", "color": "#e8edf2", "minHeight": "100vh", "padding": "18px"},
        children=[
            html.Div([
                html.H2("DCF — Dev Dashboard", style={"margin":"0 0 6px 0"}),
                html.Div("Quick sanity-check of your FastAPI numbers. KPIs + WACC×g heatmap + FCFF components.", style={"color":"#aab2bf"})
            ], style={"marginBottom":"12px"}),

            html.Div([
                dcc.Input(id="ticker", type="text", value=default_ticker, debounce=True,
                          style={"background":"#151a1f","color":"#e8edf2","border":"1px solid #232b35",
                                 "borderRadius":"8px","padding":"8px","width":"160px","marginRight":"8px"}),
                html.Button("Fetch", id="fetch", n_clicks=0,
                            style={"background":"#26323f","color":"#fff","border":"0","borderRadius":"8px","padding":"8px 12px"}),
                dcc.Store(id="api-base", data=api_base),
                html.Span(id="status", style={"marginLeft":"12px","color":"#aab2bf"})
            ], style={"marginBottom":"14px"}),

            # KPIs
            html.Div(id="kpis", style={"display":"grid","gridTemplateColumns":"repeat(1,1fr)","gap":"12px","marginBottom":"12px"}),

            # Heatmap
            html.Div([
                html.H4("DCF Sensitivity (WACC × Terminal Growth)", style={"margin":"6px 0"}),
                dcc.Graph(id="heat", style={"height":"520px"})
            ], style={"background":"#151a1f","borderRadius":"12px","padding":"12px","boxShadow":"0 6px 18px rgba(0,0,0,.35)","marginBottom":"12px"}),

            # FCFF components table
            html.Div([
                html.H4("Unlevered Free Cash Flow — What’s Included", style={"margin":"6px 0"}),
                html.P([
                    "FCFF is cash available to all investors before debt service. ",
                    "Include: Revenue, COGS & Operating Expenses (inside EBIT), Taxes, D&A, ΔNWC, CapEx. ",
                    "Ignore: Net Interest, Other Income/Expense, most non-cash one-offs, most of Cash Flow from Investing, and all of Cash Flow from Financing."
                ], style={"color":"#aab2bf"}),
                html.Div(id="fcf-table")
            ], style={"background":"#151a1f","borderRadius":"12px","padding":"12px","boxShadow":"0 6px 18px rgba(0,0,0,.35)"}),
        ]
    )

    @app.callback(
        Output("kpis", "children"),
        Output("heat", "figure"),
        Output("fcf-table", "children"),
        Output("status", "children"),
        Input("fetch", "n_clicks"),
        State("ticker", "value"),
        State("api-base", "data"),
        prevent_initial_call=True
    )
    def on_fetch(_n, tkr, api):
        try:
            d = fetch(api, tkr, years=10, midyear=True)
        except Exception as e:
            return [], go.Figure(), html.Div(f"Error: {e}", style={"color":"#ef4444"}), "Fetch failed."

        price    = get(d, "financials_snapshot", "totals", "price")
        iv_base  = get(d, "valuation", "base_constant_wacc", "intrinsic_value_per_share")
        iv_dyn   = get(d, "valuation", "dynamic_wacc", "intrinsic_value_per_share")
        ev_base  = get(d, "valuation", "base_constant_wacc", "enterprise_value")
        pv_tv    = get(d, "valuation", "base_constant_wacc", "pv_of_terminal_value")

        wacc     = get(d, "assumptions", "wacc_base")
        g_used   = get(d, "assumptions", "terminal_growth_used")
        tv_share = (pv_tv / ev_base) if (pv_tv and ev_base) else None

        base_up  = ((iv_base - price) / price) if (iv_base and price) else None
        dyn_up   = ((iv_dyn  - price) / price) if (iv_dyn  and price) else None

        market_cap = get(d, "financials_snapshot", "totals", "market_cap")
        shares     = get(d, "financials_snapshot", "totals", "shares_out")

        # KPIs
        kpi_style = {"background":"#0f141a","border":"1px solid #232b35","borderRadius":"12px","padding":"12px"}
        kpis = [
            html.Div([
                html.Div("Intrinsic Value / Share (Base)", style={"color":"#96a0ac","fontSize":"12px"}),
                html.Div(fmt_usd(iv_base), style={"fontSize":"20px","fontWeight":"700"}),
                html.Div(["vs Price ", fmt_usd(price), " → ",
                          html.Span(f"{base_up*100:.1f}%" if base_up is not None else "—",
                                    style={"color":"#10b981" if (base_up or 0)>=0 else "#ef4444"})],
                         style={"fontSize":"12px","marginTop":"4px"})
            ], style=kpi_style),
            html.Div([
                html.Div("Intrinsic Value / Share (Dynamic)", style={"color":"#96a0ac","fontSize":"12px"}),
                html.Div(fmt_usd(iv_dyn), style={"fontSize":"20px","fontWeight":"700"}),
                html.Div(["vs Price ", fmt_usd(price), " → ",
                          html.Span(f"{dyn_up*100:.1f}%" if dyn_up is not None else "—",
                                    style={"color":"#10b981" if (dyn_up or 0)>=0 else "#ef4444"})],
                         style={"fontSize":"12px","marginTop":"4px"})
            ], style=kpi_style),
            html.Div([
                html.Div("WACC / Terminal g", style={"color":"#96a0ac","fontSize":"12px"}),
                html.Div(f"{pct(wacc)} / {pct(g_used)}", style={"fontSize":"20px","fontWeight":"700"}),
                html.Div(["TV share of EV: ", html.B(pct(tv_share))], style={"fontSize":"12px","marginTop":"4px"})
            ], style=kpi_style),
            html.Div([
                html.Div("Market Snapshot", style={"color":"#96a0ac","fontSize":"12px"}),
                html.Div(fmt_usd(market_cap, True), style={"fontSize":"20px","fontWeight":"700"}),
                html.Div(f"Shares: {fmt_num(shares)}", style={"fontSize":"12px","marginTop":"4px"})
            ], style=kpi_style),
        ]

        # Heatmap
        grid      = get(d, "valuation", "sensitivity", "grid_wacc_rows_tg_cols", default=[])
        wacc_axis = get(d, "valuation", "sensitivity", "wacc_axis", default=[])
        tg_axis   = get(d, "valuation", "sensitivity", "tg_axis", default=[])
        fig_heat  = make_heatmap(grid, wacc_axis, tg_axis)

        # FCFF components table
        comps     = get(d, "assumptions", "fcff_start_method", "components", default={})
        ebit_ttm  = comps.get("EBIT_TTM")
        da_ttm    = comps.get("D&A_TTM")
        capex_ttm = comps.get("CapEx_TTM")
        dnwc_ttm  = comps.get("ΔNWC_TTM")
        eff_tax   = get(d, "assumptions", "effective_tax_rate")

        taxes_est = (ebit_ttm * eff_tax) if (isinstance(ebit_ttm,(int,float)) and isinstance(eff_tax,(int,float))) else None

        rows = [
            ("Revenue (last annual)", fmt_usd(get(d,"financials_snapshot","totals","total_revenue"), True), "Top-line sales for the last reported fiscal year."),
            ("EBIT (TTM)",            fmt_usd(ebit_ttm, True), "Operating profit before interest & taxes (TTM)."),
            ("Taxes (est.)",          fmt_usd(taxes_est, True) if taxes_est is not None else "—", "EBIT × effective tax rate."),
            ("Depreciation & Amortization (TTM)", fmt_usd(da_ttm, True), "Non-cash add-back."),
            ("Change in Working Capital (ΔNWC, TTM)", fmt_usd(dnwc_ttm, True), "Increase = cash outflow; decrease = cash inflow."),
            ("Capital Expenditures (TTM)", fmt_usd(capex_ttm, True), "Investments in PP&E and similar long-lived assets."),
        ]
        table = html.Table([
            html.Thead(html.Tr([html.Th("Line Item"), html.Th("Figure", style={"textAlign":"right"}), html.Th("Explanation")])),
            html.Tbody([html.Tr([html.Td(a), html.Td(b, style={"textAlign":"right"}), html.Td(c, style={"color":"#aab2bf"})]) for a,b,c in rows])
        ], style={"width":"100%","borderCollapse":"collapse"})

        return kpis, fig_heat, table, "OK"

    return app

# --------- entrypoint ----------
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Run the lean DCF dev dashboard.")
    ap.add_argument("--api", default="http://127.0.0.1:8000", help="FastAPI base URL")
    ap.add_argument("--ticker", default="AAPL", help="Default ticker")
    args = ap.parse_args()

    app = create_app(args.api, args.ticker)
    app.run(host="127.0.0.1", port=8050, debug=True)