from config import supabase

def fetch_multiples(ticker: str):
    response = supabase.table("stockmultiples").select("*").eq("ticker", ticker).execute()
    data = response.data
    if data:
        return data[0]
    return None

def fetch_userlist(uid: str):
    response = supabase.table("userticker").select("ticker").eq("uid", uid).execute()
    data = response.data
    if data:
        return [item['ticker'] for item in data]
    return []