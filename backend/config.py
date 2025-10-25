from dotenv import load_dotenv
import os
from supabase import create_client
from anthropic import Anthropic

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")
FMP_API_KEY = os.getenv("FMP_API_KEY")
BALANCE_SHEET_API_URL = os.getenv("BALANCE_SHEET_API_URL")
INCOME_STATEMENT_API_URL = os.getenv("INCOME_STATEMENT_API_URL")
KEY_METRICS_API_URL = os.getenv("KEY_METRICS_API_URL")
EMPLOYEE_COUNT_API_URL = os.getenv("EMPLOYEE_COUNT_API_URL")
COMPANY_SEARCH_API_URL = os.getenv("COMPANY_SEARCH_API_URL")

if ANTHROPIC_API_KEY is None:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
if CLAUDE_MODEL is None:
    raise ValueError("CLAUDE_MODEL not found in environment variables")
if FMP_API_KEY is None:
    raise ValueError("FMP_API_KEY not found in environment variables")
if BALANCE_SHEET_API_URL is None:
    raise ValueError("BALANCE_SHEET_API_URL not found in environment variables")
if INCOME_STATEMENT_API_URL is None:
    raise ValueError("INCOME_STATEMENT_API_URL not found in environment variables")
if KEY_METRICS_API_URL is None:
    raise ValueError("KEY_METRICS_API_URL not found in environment variables")
if EMPLOYEE_COUNT_API_URL is None:
    raise ValueError("EMPLOYEE_COUNT_API_URL not found in environment variables")
if COMPANY_SEARCH_API_URL is None:
    raise ValueError("COMPANY_SEARCH_API_URL not found in environment variables")

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)