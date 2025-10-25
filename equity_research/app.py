from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from anthropic import Anthropic
import os, json, re

# --- Load environment variables ---
load_dotenv()

app = FastAPI()

# --- Allow frontend access ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest")

@app.get("/")
def root():
    return {"ok": True, "message": "Structured backend running successfully"}

@app.get("/api/research/{ticker}")
async def research(ticker: str, view: str = "json"):
    # --- Claude prompt (keeps your tone exactly) ---
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

    # --- Generate from Claude ---
    msg = anthropic_client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1600,
        temperature=0.2,  # tighter for structure
        messages=[{"role": "user", "content": prompt}],
    )
    raw = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()

    # --- Parse tagged blocks robustly ---
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
        # match content between <<key>> and <<end>> (non-greedy, DOTALL)
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

    # ---------- Views ----------
    if view == "text":
        from fastapi.responses import PlainTextResponse
        TITLE = {
            "company_overview": "Company Overview",
            "business_segments": "Business Segments",
            "revenue_characteristics": "Revenue Characteristics",
            "geographic_breakdown": "Geographic Breakdown",
            "stakeholders": "Stakeholders",
            "key_performance_indicators": "Key Performance Indicators (KPIs)",
            "valuation": "Valuation",
            "recent_news": "Recent News",
            "forensic_red_flags": "Forensic Red Flags",
        }
        def block(title, paras):
            return f"{title}\n{('='*len(title))}\n" + "\n\n".join(paras) + "\n\n" if paras else ""
        text = "".join(block(TITLE[k], sections[k]) for k in KEYS).strip()
        return PlainTextResponse(text)

    if view == "html":
        from fastapi.responses import HTMLResponse
        TITLE = {
            "company_overview": "Company Overview",
            "business_segments": "Business Segments",
            "revenue_characteristics": "Revenue Characteristics",
            "geographic_breakdown": "Geographic Breakdown",
            "stakeholders": "Stakeholders",
            "key_performance_indicators": "Key Performance Indicators (KPIs)",
            "valuation": "Valuation",
            "recent_news": "Recent News",
            "forensic_red_flags": "Forensic Red Flags",
        }
        def sec_id(t): return t.lower().replace(" ", "-").replace("(", "").replace(")", "")
        def section_html(k):
            ps = sections.get(k, [])
            if not ps: return ""
            body = "".join(f"<p>{_html.escape(p)}</p>" for p in ps)
            return f'<section id="{sec_id(TITLE[k])}" class="card"><h2 class="section-title">{_html.escape(TITLE[k])}</h2>{body}</section>'

        total_words = sum(len(" ".join(ps).split()) for ps in sections.values())
        minutes = max(1, round(total_words/200))

        html = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{_html.escape(ticker.upper())} Research Brief</title>
<style>
:root{{--paper:#f7f3e8;--ink:#1b1b1b;--muted:#5c5c5c;--accent:#0f5132;--accent-2:#0b5ed7;--card:#fff;--rule:#e6dfcf;--shadow:0 10px 20px rgba(0,0,0,.06);}}
*{{box-sizing:border-box}} html,body{{margin:0;padding:0}}
body{{background:var(--paper);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Inter,Arial;line-height:1.65}}
.wrap{{max-width:940px;margin:0 auto;padding:28px 20px 48px;display:grid;grid-template-columns:230px 1fr;gap:28px}}
header.hero{{grid-column:1/-1;background:linear-gradient(180deg,#fff 0%,#faf7f0 100%);border:1px solid var(--rule);border-radius:14px;padding:22px;box-shadow:var(--shadow)}}
.kicker{{text-transform:uppercase;letter-spacing:.12em;font-weight:600;color:var(--accent);font-size:12px}}
.title{{margin:6px 0 8px;font-family:Georgia,"Times New Roman",Times,serif;font-size:30px;line-height:1.2}}
.meta{{color:var(--muted);font-size:13px}}
.badge{{display:inline-block;padding:4px 10px;border-radius:999px;border:1px solid var(--rule);background:#fff;font-weight:600;font-family:ui-monospace,Menlo,Consolas;margin-left:8px}}
nav.toc{{position:sticky;top:12px;align-self:start;border:1px solid var(--rule);background:#fff;border-radius:12px;padding:16px;box-shadow:var(--shadow)}}
nav.toc h3{{margin:0 0 10px;font-size:14px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}}
nav.toc a{{display:block;padding:6px 8px;border-radius:8px;color:var(--ink);text-decoration:none;font-size:14px}}
nav.toc a:hover{{background:#f2ecdf}}
.card{{background:var(--card);border:1px solid var(--rule);border-radius:12px;padding:18px;margin-bottom:16px;box-shadow:var(--shadow)}}
.section-title {{
  font-family: Georgia, "Times New Roman", Times, serif;
  font-size: 20px;
  margin: 6px 0 10px;
  line-height: 1.25;
  border-bottom: 1px solid var(--rule);
  padding-bottom: 6px;
}}
p {{ margin: 10px 0; }}
footer.footer{{grid-column:1/-1;text-align:center;color:var(--muted);font-size:12px;margin-top:8px}}
.top-link{{position:fixed;right:16px;bottom:16px;background:var(--accent-2);color:#fff;border:none;padding:10px 12px;border-radius:10px;cursor:pointer;box-shadow:var(--shadow)}}
@media (max-width:900px){{.wrap{{grid-template-columns:1fr}} nav.toc{{position:relative;top:0}}}}
@media print{{nav.toc,.top-link{{display:none}} body{{background:#fff}} .card{{box-shadow:none}}}}
</style>
</head>
<body>
<div class="wrap">
  <header class="hero">
    <div class="kicker">Equity Research</div>
    <div class="title">{_html.escape(ticker.upper())} — Company Research Brief <span class="badge">{_html.escape(ticker.upper())}</span></div>
    <div class="meta">Approx. {minutes} min read · Generated by Claude</div>
  </header>

  <nav class="toc">
    <h3>Sections</h3>
    <a href="#company-overview">Company Overview</a>
    <a href="#business-segments">Business Segments</a>
    <a href="#revenue-characteristics">Revenue Characteristics</a>
    <a href="#geographic-breakdown">Geographic Breakdown</a>
    <a href="#stakeholders">Stakeholders</a>
    <a href="#key-performance-indicators">KPIs</a>
    <a href="#valuation">Valuation</a>
    <a href="#recent-news">Recent News</a>
    <a href="#forensic-red-flags">Forensic Red Flags</a>
  </nav>

  <main class="content">
    {section_html("company_overview")}
    {section_html("business_segments")}
    {section_html("revenue_characteristics")}
    {section_html("geographic_breakdown")}
    {section_html("stakeholders")}
    {section_html("key_performance_indicators")}
    {section_html("valuation")}
    {section_html("recent_news")}
    {section_html("forensic_red_flags")}
  </main>

  <footer class="footer">Educational content only. Not investment advice.</footer>
</div>
<button class="top-link" onclick="window.scrollTo({{top:0, behavior:'smooth'}})">Back to top</button>
</body></html>
"""
        return HTMLResponse(html)

    # default: structured JSON
    return {"ok": True, "ticker": ticker.upper(), "data": sections}
