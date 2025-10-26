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
    """Enhanced heatmap with better color scale and styling"""
    if wacc_axis and isinstance(wacc_axis[0], (int, float)):
        wacc_labels = [f"{w*100:.2f}%" for w in wacc_axis]
    else:
        wacc_labels = wacc_axis or ["WACC"]
    if tg_axis and isinstance(tg_axis[0], (int, float)):
        tg_labels = [f"{g*100:.2f}%" for g in tg_axis]
    else:
        tg_labels = tg_axis or ["g"]

    fig = go.Figure(data=go.Heatmap(
        z=grid or [[None]], 
        x=tg_labels, 
        y=wacc_labels,
        colorscale="Cividis",  # More impactful color scale
        colorbar=dict(
            title=dict(
                text="Intrinsic Value<br>per Share",
                font=dict(size=12, color="#e8edf2")
            ),
            tickfont=dict(size=11, color="#aab2bf"),
            thickness=15,
            len=0.7
        ),
        hovertemplate="<b>WACC:</b> %{y}<br><b>Terminal Growth:</b> %{x}<br><b>Intrinsic Value:</b> $%{z:.2f}<extra></extra>",
        texttemplate="%{z:.0f}",
        textfont={"size": 11, "color": "#ffffff"},
        showscale=True
    ))
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0f141a",
        plot_bgcolor="#0f141a",
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif", color="#e8edf2"),
        xaxis=dict(
            title=dict(text="Terminal Growth Rate (g)", font=dict(size=13, color="#e8edf2")),
            tickfont=dict(size=11, color="#aab2bf"),
            showgrid=False
        ),
        yaxis=dict(
            title=dict(text="Weighted Average Cost of Capital (WACC)", font=dict(size=13, color="#e8edf2")),
            tickfont=dict(size=11, color="#aab2bf"),
            showgrid=False
        ),
        margin=dict(l=100, r=40, t=20, b=70),
        height=540,
        hoverlabel=dict(
            bgcolor="#1a1f26",
            font_size=12,
            font_family="Inter, sans-serif"
        )
    )
    
    return fig

# --------- app factory ----------
def create_app(api_base: str, default_ticker: str = "AAPL") -> Dash:
    app = Dash(__name__, title="DCF Valuation Dashboard")
    
    # Enhanced CSS styling
    app.index_string = '''
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                body {
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    -webkit-font-smoothing: antialiased;
                    -moz-osx-font-smoothing: grayscale;
                }
                /* Responsive KPI Grid */
                .kpi-grid {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 16px;
                    margin-bottom: 20px;
                }
                @media (min-width: 1024px) {
                    .kpi-grid {
                        grid-template-columns: repeat(4, 1fr);
                    }
                }
                /* KPI Card Styling */
                .kpi-card {
                    background: linear-gradient(135deg, #0f141a 0%, #151b22 100%);
                    border: 1px solid #232b35;
                    border-radius: 16px;
                    padding: 20px;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
                }
                .kpi-card:hover {
                    transform: translateY(-4px);
                    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
                    border-color: #3a4556;
                }
                /* Input and Button Styling */
                .input-group {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    flex-wrap: wrap;
                }
                .ticker-input {
                    background: linear-gradient(135deg, #151a1f 0%, #1a2028 100%);
                    color: #e8edf2;
                    border: 2px solid #232b35;
                    border-radius: 12px;
                    padding: 12px 16px;
                    width: 180px;
                    font-size: 15px;
                    font-weight: 500;
                    transition: all 0.3s ease;
                    outline: none;
                    letter-spacing: 0.5px;
                }
                .ticker-input:focus {
                    border-color: #4a90e2;
                    box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.15);
                }
                .fetch-button {
                    background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
                    color: #ffffff;
                    border: none;
                    border-radius: 12px;
                    padding: 12px 28px;
                    font-size: 15px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 12px rgba(74, 144, 226, 0.25);
                }
                .fetch-button:hover {
                    background: linear-gradient(135deg, #357abd 0%, #2a5f8f 100%);
                    transform: translateY(-2px);
                    box-shadow: 0 6px 16px rgba(74, 144, 226, 0.35);
                }
                .fetch-button:active {
                    transform: translateY(0);
                }
                /* Status and Loading */
                .status-text {
                    margin-left: 16px;
                    color: #aab2bf;
                    font-size: 14px;
                    font-weight: 500;
                }
                /* Section Card */
                .section-card {
                    background: linear-gradient(135deg, #0f141a 0%, #151b22 100%);
                    border: 1px solid #232b35;
                    border-radius: 16px;
                    padding: 24px;
                    margin-bottom: 20px;
                    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
                }
                /* Table Styling */
                .fcf-table {
                    width: 100%;
                    border-collapse: separate;
                    border-spacing: 0;
                    font-size: 14px;
                }
                .fcf-table thead th {
                    background: #1a2028;
                    color: #e8edf2;
                    font-weight: 600;
                    text-align: left;
                    padding: 14px 16px;
                    border-bottom: 2px solid #232b35;
                }
                .fcf-table thead th:first-child {
                    border-top-left-radius: 12px;
                }
                .fcf-table thead th:last-child {
                    border-top-right-radius: 12px;
                }
                .fcf-table tbody tr {
                    transition: background-color 0.2s ease;
                }
                .fcf-table tbody tr:nth-child(odd) {
                    background: rgba(26, 32, 40, 0.3);
                }
                .fcf-table tbody tr:hover {
                    background: rgba(74, 144, 226, 0.08);
                }
                .fcf-table tbody td {
                    padding: 14px 16px;
                    border-bottom: 1px solid #232b35;
                    color: #e8edf2;
                }
                .fcf-table tbody tr:last-child td {
                    border-bottom: none;
                }
                .fcf-table tbody tr:last-child td:first-child {
                    border-bottom-left-radius: 12px;
                }
                .fcf-table tbody tr:last-child td:last-child {
                    border-bottom-right-radius: 12px;
                }
                /* Loading Spinner */
                .loading-overlay {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 40px;
                }
                .spinner {
                    border: 3px solid #232b35;
                    border-top: 3px solid #4a90e2;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    '''

    app.layout = html.Div(
        style={
            "background": "linear-gradient(135deg, #0a0e13 0%, #0f1115 100%)",
            "color": "#e8edf2",
            "minHeight": "100vh",
            "padding": "28px",
            "fontFamily": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
        },
        children=[
            # Header
            html.Div([
                html.H1(
                    "DCF Valuation Dashboard",
                    style={
                        "margin": "0 0 8px 0",
                        "fontSize": "32px",
                        "fontWeight": "700",
                        "background": "linear-gradient(135deg, #4a90e2 0%, #63b3ed 100%)",
                        "WebkitBackgroundClip": "text",
                        "WebkitTextFillColor": "transparent",
                        "backgroundClip": "text"
                    }
                ),
                html.P(
                    "Real-time company-specific DCF analysis with dynamic WACC and sensitivity modeling",
                    style={"color": "#aab2bf", "fontSize": "15px", "lineHeight": "1.6"}
                )
            ], style={"marginBottom": "28px"}),

            # Input Controls
            html.Div([
                html.Div(className="input-group", children=[
                    dcc.Input(
                        id="ticker",
                        type="text",
                        value=default_ticker,
                        debounce=True,
                        placeholder="Enter ticker...",
                        className="ticker-input"
                    ),
                    html.Button("Fetch Valuation", id="fetch", n_clicks=0, className="fetch-button"),
                    html.Span(id="status", className="status-text")
                ]),
                dcc.Store(id="api-base", data=api_base)
            ], style={"marginBottom": "28px"}),

            # Loading Wrapper
            dcc.Loading(
                id="loading",
                type="default",
                color="#4a90e2",
                children=[
                    # KPIs
                    html.Div(id="kpis", className="kpi-grid"),

                    # Heatmap
                    html.Div(className="section-card", children=[
                        html.H3(
                            "DCF Sensitivity Analysis",
                            style={
                                "margin": "0 0 8px 0",
                                "fontSize": "20px",
                                "fontWeight": "600",
                                "color": "#e8edf2"
                            }
                        ),
                        html.P(
                            "How intrinsic value changes across different WACC and terminal growth rate assumptions",
                            style={"color": "#aab2bf", "fontSize": "13px", "marginBottom": "16px"}
                        ),
                        dcc.Graph(id="heat", style={"height": "540px"}, config={"displayModeBar": False})
                    ]),

                    # FCFF Table
                    html.Div(className="section-card", children=[
                        html.H3(
                            "Free Cash Flow Components (TTM)",
                            style={
                                "margin": "0 0 8px 0",
                                "fontSize": "20px",
                                "fontWeight": "600",
                                "color": "#e8edf2"
                            }
                        ),
                        html.P(
                            "Unlevered free cash flow represents cash available to all investors before debt service. "
                            "Key components include operating profit (EBIT), taxes, depreciation & amortization, "
                            "changes in net working capital, and capital expenditures.",
                            style={"color": "#aab2bf", "fontSize": "13px", "lineHeight": "1.6", "marginBottom": "20px"}
                        ),
                        html.Div(id="fcf-table")
                    ])
                ]
            )
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
            error_msg = html.Div(
                f"⚠️ Error: {str(e)}",
                style={"color": "#ef4444", "fontWeight": "500"}
            )
            return [], go.Figure(), error_msg, "❌ Fetch failed"

        # Extract data
        price = get(d, "financials_snapshot", "totals", "price")
        iv_base = get(d, "valuation", "base_constant_wacc", "intrinsic_value_per_share")
        iv_dyn = get(d, "valuation", "dynamic_wacc", "intrinsic_value_per_share")
        ev_base = get(d, "valuation", "base_constant_wacc", "enterprise_value")
        pv_tv = get(d, "valuation", "base_constant_wacc", "pv_of_terminal_value")

        wacc = get(d, "assumptions", "wacc_base")
        g_used = get(d, "assumptions", "terminal_growth_used")
        tv_share = (pv_tv / ev_base) if (pv_tv and ev_base) else None

        base_up = ((iv_base - price) / price) if (iv_base and price) else None
        dyn_up = ((iv_dyn - price) / price) if (iv_dyn and price) else None

        market_cap = get(d, "financials_snapshot", "totals", "market_cap")
        shares = get(d, "financials_snapshot", "totals", "shares_out")
        company_name = get(d, "company_name", default=tkr.upper())

        # KPIs with enhanced styling
        kpis = [
            html.Div(className="kpi-card", children=[
                html.Div("Intrinsic Value (Constant WACC)", style={
                    "color": "#96a0ac",
                    "fontSize": "12px",
                    "fontWeight": "500",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.5px",
                    "marginBottom": "8px"
                }),
                html.Div(fmt_usd(iv_base), style={
                    "fontSize": "28px",
                    "fontWeight": "700",
                    "color": "#e8edf2",
                    "marginBottom": "8px"
                }),
                html.Div([
                    html.Span("Market: ", style={"color": "#96a0ac"}),
                    html.Span(fmt_usd(price), style={"color": "#e8edf2", "fontWeight": "500"}),
                    html.Span(" • ", style={"color": "#96a0ac", "margin": "0 6px"}),
                    html.Span(
                        f"{base_up*100:+.1f}%" if base_up is not None else "—",
                        style={
                            "color": "#10b981" if (base_up or 0) >= 0 else "#ef4444",
                            "fontWeight": "600"
                        }
                    )
                ], style={"fontSize": "13px"})
            ]),
            
            html.Div(className="kpi-card", children=[
                html.Div("Intrinsic Value (Dynamic WACC)", style={
                    "color": "#96a0ac",
                    "fontSize": "12px",
                    "fontWeight": "500",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.5px",
                    "marginBottom": "8px"
                }),
                html.Div(fmt_usd(iv_dyn), style={
                    "fontSize": "28px",
                    "fontWeight": "700",
                    "color": "#e8edf2",
                    "marginBottom": "8px"
                }),
                html.Div([
                    html.Span("Market: ", style={"color": "#96a0ac"}),
                    html.Span(fmt_usd(price), style={"color": "#e8edf2", "fontWeight": "500"}),
                    html.Span(" • ", style={"color": "#96a0ac", "margin": "0 6px"}),
                    html.Span(
                        f"{dyn_up*100:+.1f}%" if dyn_up is not None else "—",
                        style={
                            "color": "#10b981" if (dyn_up or 0) >= 0 else "#ef4444",
                            "fontWeight": "600"
                        }
                    )
                ], style={"fontSize": "13px"})
            ]),
            
            html.Div(className="kpi-card", children=[
                html.Div("WACC & Terminal Growth", style={
                    "color": "#96a0ac",
                    "fontSize": "12px",
                    "fontWeight": "500",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.5px",
                    "marginBottom": "8px"
                }),
                html.Div(f"{pct(wacc)} / {pct(g_used)}", style={
                    "fontSize": "28px",
                    "fontWeight": "700",
                    "color": "#e8edf2",
                    "marginBottom": "8px"
                }),
                html.Div([
                    html.Span("Terminal Value: ", style={"color": "#96a0ac"}),
                    html.Span(pct(tv_share), style={"color": "#4a90e2", "fontWeight": "600"}),
                    html.Span(" of EV", style={"color": "#96a0ac"})
                ], style={"fontSize": "13px"})
            ]),
            
            html.Div(className="kpi-card", children=[
                html.Div(company_name, style={
                    "color": "#96a0ac",
                    "fontSize": "12px",
                    "fontWeight": "500",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.5px",
                    "marginBottom": "8px"
                }),
                html.Div(fmt_usd(market_cap, True), style={
                    "fontSize": "28px",
                    "fontWeight": "700",
                    "color": "#e8edf2",
                    "marginBottom": "8px"
                }),
                html.Div([
                    html.Span("Shares: ", style={"color": "#96a0ac"}),
                    html.Span(fmt_num(shares), style={"color": "#e8edf2", "fontWeight": "500"})
                ], style={"fontSize": "13px"})
            ])
        ]

        # Heatmap
        grid = get(d, "valuation", "sensitivity", "grid_wacc_rows_tg_cols", default=[])
        wacc_axis = get(d, "valuation", "sensitivity", "wacc_axis", default=[])
        tg_axis = get(d, "valuation", "sensitivity", "tg_axis", default=[])
        fig_heat = make_heatmap(grid, wacc_axis, tg_axis)

        # FCFF Table
        comps = get(d, "assumptions", "fcff_start_method", "components", default={})
        ebit_ttm = comps.get("EBIT_TTM")
        da_ttm = comps.get("D&A_TTM")
        capex_ttm = comps.get("CapEx_TTM")
        dnwc_ttm = comps.get("ΔNWC_TTM")
        eff_tax = get(d, "assumptions", "effective_tax_rate")

        taxes_est = (ebit_ttm * eff_tax) if (isinstance(ebit_ttm, (int, float)) and isinstance(eff_tax, (int, float))) else None

        rows = [
            ("Revenue (Last Annual)", fmt_usd(get(d, "financials_snapshot", "totals", "total_revenue"), True), 
             "Top-line sales for the most recent fiscal year"),
            ("Operating Profit (EBIT, TTM)", fmt_usd(ebit_ttm, True), 
             "Earnings before interest and taxes over trailing twelve months"),
            ("Estimated Tax Expense", fmt_usd(taxes_est, True) if taxes_est is not None else "—", 
             "EBIT multiplied by effective tax rate"),
            ("Depreciation & Amortization (TTM)", fmt_usd(da_ttm, True), 
             "Non-cash expense added back to cash flow"),
            ("Change in Net Working Capital (TTM)", fmt_usd(dnwc_ttm, True), 
             "Increase in NWC is cash outflow; decrease is cash inflow"),
            ("Capital Expenditures (TTM)", fmt_usd(capex_ttm, True), 
             "Cash spent on property, plant, equipment, and other long-term assets")
        ]

        table = html.Table(className="fcf-table", children=[
            html.Thead(html.Tr([
                html.Th("Component", style={"width": "25%"}),
                html.Th("Amount", style={"width": "15%", "textAlign": "right"}),
                html.Th("Description", style={"width": "60%"})
            ])),
            html.Tbody([
                html.Tr([
                    html.Td(a, style={"fontWeight": "500"}),
                    html.Td(b, style={"textAlign": "right", "fontWeight": "600", "color": "#4a90e2"}),
                    html.Td(c, style={"color": "#aab2bf", "fontSize": "13px"})
                ]) for a, b, c in rows
            ])
        ])

        return kpis, fig_heat, table, f"✓ {company_name} loaded successfully"

    return app

# --------- entrypoint ----------
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Run the enhanced DCF valuation dashboard.")
    ap.add_argument("--api", default="http://127.0.0.1:8000", help="FastAPI base URL")
    ap.add_argument("--ticker", default="AAPL", help="Default ticker symbol")
    args = ap.parse_args()

    app = create_app(args.api, args.ticker)
    app.run(host="127.0.0.1", port=8050, debug=True)
    