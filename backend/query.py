from config import supabase

def fetch_multiples(ticker: str):
    response = supabase.table("stockmultiples").select("*").eq("ticker", ticker).execute()
    data = response.data
    if data:
        return data[0]
    return None