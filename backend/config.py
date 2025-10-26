from dotenv import load_dotenv
import os
from supabase import create_client

load_dotenv()

FMP_API_KEY = os.getenv("FMP_API_KEY")
BALANCE_SHEET_API_URL = os.getenv("BALANCE_SHEET_API_URL")
INCOME_STATEMENT_API_URL = os.getenv("INCOME_STATEMENT_API_URL")
KEY_METRICS_API_URL = os.getenv("KEY_METRICS_API_URL")
EMPLOYEE_COUNT_API_URL = os.getenv("EMPLOYEE_COUNT_API_URL")
COMPANY_SEARCH_API_URL = os.getenv("COMPANY_SEARCH_API_URL")
LAVA_FORWARD_TOKEN = os.getenv("LAVA_FORWARD_TOKEN")
LAVA_BASE_URL = os.getenv("LAVA_BASE_URL")
LLM_API_URL = os.getenv("LLM_API_URL")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5-nano")
LAVA_API_URL = f"{LAVA_BASE_URL}/forward?u={LLM_API_URL}"

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
if LAVA_FORWARD_TOKEN is None:
    raise ValueError("LAVA_FORWARD_TOKEN not found in environment variables")
if LAVA_BASE_URL is None:
    raise ValueError("LAVA_BASE_URL not found in environment variables")
if LLM_API_URL is None:
    raise ValueError("LLM_API_URL not found in environment variables")
if LLM_MODEL is None:
    raise ValueError("LLM_MODEL not found in environment variables")

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)