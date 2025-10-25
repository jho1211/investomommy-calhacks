from config import supabase

def fetch_multiples(ticker: str):
    response = supabase.table("stockmultiples").select("*").eq("ticker", ticker).execute()
    data = response.data
    if data:
        return data[0]
    return None

def fetch_userlist(uid: str):
    response = supabase.table("userticker").select("ticker(ticker, company_name)").eq("uid", uid).execute()
    data = response.data
    if data:
        return [{"ticker": item['ticker']['ticker'], "company_name": item['ticker']['company_name']} for item in data]
    return []

def check_ticker_exists(ticker: str) -> bool:
    response = supabase.table("ticker").select("ticker").eq("ticker", ticker).execute()
    data = response.data
    return len(data) > 0

def add_ticker(ticker: str, company_name: str):
    if not check_ticker_exists(ticker):
        supabase.table("ticker").insert({"ticker": ticker, "company_name": company_name}).execute()

def add_user_ticker(uid: str, ticker: str):
    supabase.table("userticker").insert({"uid": uid, "ticker": ticker}).execute()

def insert_research_data(ticker: str, research_data: dict):
    supabase.table("researchanalysis").insert({"ticker": ticker, "analysis_data": research_data}).execute()

def get_research_data(ticker):
    response = supabase.table("researchanalysis").select("analysis_data", "analysis_date", "created_at").eq("ticker", ticker).order("analysis_date", desc=True).execute()
    data = response.data
    if data:
        return data[0]
    return None

# --- News Sentiment Queries ---
def fetch_news_sentiment(ticker: str):
    """Fetch detailed sentiment rows for a given ticker from 'newssentiment'."""
    res = supabase.table("newssentiment").select("*").eq("ticker", ticker).execute()
    return res.data if res.data else []


def fetch_overall_news_sentiment(ticker: str):
    """Fetch overall aggregated sentiment for a given ticker from 'overallnewssentiment'."""
    res = supabase.table("overallnewssentiment").select("*").eq("ticker", ticker).execute()
    return res.data if res.data else []
