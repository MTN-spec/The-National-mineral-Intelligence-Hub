import yfinance as yf
import feedparser
import random
import pandas as pd
import datetime

class MarketIntelligenceService:
    def __init__(self):
        # Top minerals for Zimbabwe/Zvishavane
        self.commodities = {
            "Gold": {"ticker": "GC=F", "type": "real"},
            "Platinum": {"ticker": "PL=F", "type": "real"},
            "Palladium": {"ticker": "PA=F", "type": "real"},
            "Silver": {"ticker": "SI=F", "type": "real"},
            "Copper": {"ticker": "HG=F", "type": "real"},
            # Harder to get public live futures for these, so we simulate realistic local prices
            "Lithium (Spodumene)": {"ticker": "LITH", "type": "mock", "base": 1200}, 
            "Chrome": {"ticker": "CHRM", "type": "mock", "base": 280},
            "Diamond (Industrial)": {"ticker": "DIAM", "type": "mock", "base": 85},
            "Asbestos": {"ticker": "ASB", "type": "mock", "base": 1500}, 
            "Iron Ore": {"ticker": "IRON", "type": "mock", "base": 110}
        }
        
    def get_prices(self):
        """Fetches live prices where possible, mocks others."""
        data = []
        
        # 1. Fetch Real Data in Batch (Faster)
        real_tickers = [v['ticker'] for k, v in self.commodities.items() if v['type'] == 'real']
        try:
            # Fetch last 5 days to calculate trend
            yf_data = yf.download(real_tickers, period="5d", interval="1d", progress=False)
        except Exception:
            yf_data = None # Fallback if offline

        for name, info in self.commodities.items():
            price = 0.0
            change = 0.0
            trend = []
            
            if info['type'] == 'real' and yf_data is not None and not yf_data.empty:
                try:
                    # Extract latest Close
                    # yf structure can be multi-index: ('Close', 'GC=F')
                    ticker = info['ticker']
                    # Handle multi-level columns if multiple tickers
                    if isinstance(yf_data.columns, pd.MultiIndex):
                        hist = yf_data['Close'][ticker].dropna()
                    else:
                        hist = yf_data['Close'].dropna() # Single ticker case usually returns series
                    
                    if not hist.empty:
                        price = float(hist.iloc[-1])
                        prev = float(hist.iloc[-2]) if len(hist) > 1 else price
                        change = ((price - prev) / prev) * 100
                        trend = hist.values.tolist()
                except Exception as e:
                    # Fallback
                    price = 0.0
            
            # Mock Data Logic (or fallback for failed real)
            if price == 0.0: 
                base = info.get('base', 1000)
                volatility = random.uniform(-0.05, 0.05)
                price = base * (1 + volatility)
                change = volatility * 100
                # Generate fake trend
                trend = [base * (1 + random.uniform(-0.05, 0.05)) for _ in range(5)]
                trend[-1] = price
            
            data.append({
                "Mineral": name,
                "Price": price,
                "Change": change,
                "Trend": trend # List of last 5 prices for sparkline
            })
            
        return pd.DataFrame(data)

    def get_news(self):
        """Fetches mining news from RSS."""
        feeds = [
            "https://news.google.com/rss/search?q=Zimbabwe+Mining+Minerals&hl=en-US&gl=US&ceid=US:en",
            "https://www.mining.com/feed/"
        ]
        
        articles = []
        try:
            for url in feeds:
                f = feedparser.parse(url)
                for entry in f.entries[:3]: # Top 3 from each
                    # Clean Up Date
                    published = entry.get("published", datetime.datetime.now().strftime("%a, %d %b %Y"))
                    
                    articles.append({
                        "title": entry.title,
                        "link": entry.link,
                        "source": entry.get("source", {}).get("title", "Mining News"),
                        "date": published
                    })
        except Exception:
            # Fallback Mock News
            articles = [
                {"title": "Zvishavane Production Hits Record Highs", "link": "#", "source": "Local News", "date": "Just Now"},
                {"title": "Lithium Prices Stabilize as Demand Grows", "link": "#", "source": "Market Watch", "date": "1 hour ago"},
            ]
            
        random.shuffle(articles)
        return articles[:6]

if __name__ == "__main__":
    ms = MarketIntelligenceService()
    print("Fetching Prices...")
    print(ms.get_prices())
    print("\nFetching News...")
    print(ms.get_news())
