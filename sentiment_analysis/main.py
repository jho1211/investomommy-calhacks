import os
import json
import requests
import torch
from datetime import date, timedelta
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch.nn.functional as F
from dotenv import load_dotenv

# --- Load API key ---
load_dotenv()
API_KEY = os.getenv("FINNHUB_API_KEY")
if not API_KEY:
    raise ValueError("⚠️ Please set FINNHUB_API_KEY in your .env file")

# --- FinBERT model setup ---
MODEL_NAME = "yiyanghkust/finbert-tone"
print("🔍 Loading FinBERT model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
labels = ["positive", "neutral", "negative"]
print("✅ Model loaded successfully.")

# --- Predefined ticker list (you can expand this) ---
AVAILABLE_TICKERS = {
    "TSLA": "Tesla Inc.",
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corp.",
    "AMZN": "Amazon.com Inc.",
    "GOOGL": "Alphabet Inc.",
    "META": "Meta Platforms Inc.",
    "NVDA": "NVIDIA Corp.",
    "JPM": "JPMorgan Chase & Co.",
    "BAC": "Bank of America Corp.",
    "DIS": "Walt Disney Co."
}

# --- Function to fetch company news ---
def fetch_news(symbol, days=5, limit=10):
    today = date.today()
    from_date = (today - timedelta(days=days)).isoformat()
    to_date = today.isoformat()

    url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from={from_date}&to={to_date}&token={API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"❌ Error fetching news for {symbol}: {response.status_code}")
        return []

    data = response.json()
    news = [{"headline": item["headline"], "datetime": item.get("datetime")} for item in data[:limit]]
    return news

# --- Function to analyze sentiment with FinBERT ---
def analyze_sentiment(news_list):
    results = []
    if not news_list:
        return results

    texts = [item["headline"] for item in news_list]
    inputs = tokenizer(texts, return_tensors="pt", truncation=True, padding=True)
    outputs = model(**inputs)
    probs = F.softmax(outputs.logits, dim=-1)

    for i, item in enumerate(news_list):
        sentiment = labels[probs[i].argmax()]
        confidence = round(probs[i].max().item(), 4)
        results.append({
            "headline": item["headline"],
            "datetime": item.get("datetime"),
            "sentiment": sentiment,
            "confidence": confidence
        })
    return results

# --- MAIN ---
if __name__ == "__main__":
    print("\n📈 Available Tickers:")
    for i, (symbol, name) in enumerate(AVAILABLE_TICKERS.items(), 1):
        print(f"  {i}. {symbol} - {name}")

    # User selects tickers by typing numbers or symbols
    choice = input("\nEnter tickers (comma separated or numbers, e.g. 'AAPL, TSLA' or '1,3,5'): ").strip()

    selected = []
    parts = [c.strip().upper() for c in choice.split(",")]

    for p in parts:
        if p.isdigit() and 1 <= int(p) <= len(AVAILABLE_TICKERS):
            symbol = list(AVAILABLE_TICKERS.keys())[int(p)-1]
            selected.append(symbol)
        elif p in AVAILABLE_TICKERS:
            selected.append(p)

    if not selected:
        print("⚠️ No valid tickers selected. Exiting.")
        exit()

    print(f"\n📰 Fetching news for: {', '.join(selected)}\n")

    all_results = []
    summary_results = []
    os.makedirs("data", exist_ok=True)

    for ticker in selected:
        print(f"--- {ticker} ---")
        news_data = fetch_news(ticker, days=5, limit=10)
        print(f"Fetched {len(news_data)} news articles.")

        sentiment_results = analyze_sentiment(news_data)

        for r in sentiment_results:
            all_results.append({"ticker": ticker, **r})

        # --- Summary ---
        if sentiment_results:
            total = len(sentiment_results)
            counts = {"positive": 0, "neutral": 0, "negative": 0}
            for r in sentiment_results:
                counts[r["sentiment"]] += 1
            summary_results.append({
                "ticker": ticker,
                "total_articles": total,
                "positive_ratio": round(counts["positive"] / total, 3),
                "neutral_ratio": round(counts["neutral"] / total, 3),
                "negative_ratio": round(counts["negative"] / total, 3)
            })

    # --- Save to JSON ---
    with open("data/sentiment_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    with open("data/sentiment_summary.json", "w") as f:
        json.dump(summary_results, f, indent=2)

    print("\n✅ Sentiment analysis completed!")
    print("Results saved to:")
    print("  • data/sentiment_results.json")
    print("  • data/sentiment_summary.json")
