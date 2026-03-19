import random
import pandas as pd
import datetime

# Try to import yfinance for live data
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

class MarketIntelligenceService:
    """
    Market Intelligence Service for mineral and commodity prices.
    Uses yfinance for live data with mock fallback.
    """
    
    # Mapping of commodity names to Yahoo Finance tickers
    COMMODITY_TICKERS = {
        "Gold": "GC=F",
        "Platinum": "PL=F",
        "Palladium": "PA=F",
        "Silver": "SI=F",
        "Copper": "HG=F",
        "Iron Ore": "TIOE.JK",       # Iron ore proxy
    }
    
    # Commodities without reliable free tickers — use mock data
    MOCK_ONLY = {
        "Lithium (Spodumene)": {"base": 1300, "volatility": 0.08},
        "Chrome": {"base": 280, "volatility": 0.03},
        "Diamond (Industrial)": {"base": 90, "volatility": 0.01},
        "Asbestos": {"base": 1500, "volatility": 0.00},
    }
    
    def __init__(self):
        self._cache = None
        self._cache_time = None
        self._cache_duration = datetime.timedelta(minutes=15)  # Cache for 15 min
    
    def _get_live_prices(self):
        """Fetch real prices from Yahoo Finance."""
        data = []
        
        for name, ticker in self.COMMODITY_TICKERS.items():
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="5d")
                
                if hist.empty or len(hist) < 2:
                    # Fallback to mock if no data
                    data.append(self._mock_commodity(name, 0, 0))
                    continue
                
                prices = hist['Close'].tolist()
                current = prices[-1]
                prev = prices[-2] if len(prices) >= 2 else current
                change = ((current - prev) / prev) * 100 if prev != 0 else 0
                
                # Pad trend to 5 entries if needed
                while len(prices) < 5:
                    prices.insert(0, prices[0])
                trend = prices[-5:]
                
                data.append({
                    "Mineral": name,
                    "Price": current,
                    "Change": change,
                    "Trend": trend,
                    "Source": "Live"
                })
            except Exception:
                # Fallback for individual ticker failures
                data.append(self._mock_commodity(name, 0, 0))
        
        # Add mock-only commodities
        for name, info in self.MOCK_ONLY.items():
            data.append(self._mock_commodity(name, info['base'], info['volatility']))
        
        return data
    
    def _mock_commodity(self, name, base=0, volatility=0.03):
        """Generate mock data for a single commodity."""
        # Lookup base if not provided
        bases = {
            "Gold": 2000, "Platinum": 950, "Palladium": 1200,
            "Silver": 24, "Copper": 3.8, "Iron Ore": 115,
            "Lithium (Spodumene)": 1300, "Chrome": 280,
            "Diamond (Industrial)": 90, "Asbestos": 1500,
        }
        if base == 0:
            base = bases.get(name, 100)
        
        change_pct = random.uniform(-volatility, volatility)
        current_price = base * (1 + change_pct)
        
        trend = []
        price = current_price
        for _ in range(5):
            price = price * (1 + random.uniform(-volatility, volatility))
            trend.append(price)
        trend = trend[::-1]
        current_price = trend[-1]
        prev_price = trend[-2]
        change = ((current_price - prev_price) / prev_price) * 100
        
        return {
            "Mineral": name,
            "Price": current_price,
            "Change": change,
            "Trend": trend,
            "Source": "Simulated"
        }
    
    def _get_mock_prices(self):
        """Full mock data fallback."""
        commodities = {
            "Gold": {"base": 2000, "volatility": 0.02},
            "Platinum": {"base": 950, "volatility": 0.03},
            "Palladium": {"base": 1200, "volatility": 0.04},
            "Silver": {"base": 24, "volatility": 0.05},
            "Copper": {"base": 3.8, "volatility": 0.02},
            "Lithium (Spodumene)": {"base": 1300, "volatility": 0.08},
            "Chrome": {"base": 280, "volatility": 0.03},
            "Diamond (Industrial)": {"base": 90, "volatility": 0.01},
            "Asbestos": {"base": 1500, "volatility": 0.00},
            "Iron Ore": {"base": 115, "volatility": 0.02}
        }
        return [self._mock_commodity(name, info['base'], info['volatility']) for name, info in commodities.items()]
    
    def get_prices(self):
        """Get commodity prices — live if available, mock otherwise."""
        # Check cache
        if self._cache is not None and self._cache_time is not None:
            if datetime.datetime.now() - self._cache_time < self._cache_duration:
                return self._cache
        
        if HAS_YFINANCE:
            try:
                data = self._get_live_prices()
            except Exception:
                data = self._get_mock_prices()
        else:
            data = self._get_mock_prices()
        
        df = pd.DataFrame(data)
        self._cache = df
        self._cache_time = datetime.datetime.now()
        return df

    def get_news(self):
        """Fetches REAL LIVE news using standard libraries (Crash-Proof)."""
        import urllib.request
        import xml.etree.ElementTree as ET
        
        url = "https://news.google.com/rss/search?q=Zimbabwe+Mining+Minerals&hl=en-US&gl=US&ceid=US:en"
        articles = []
        
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                
                count = 0
                for item in root.findall('./channel/item'):
                    if count >= 6: break
                    
                    title = item.find('title').text
                    link = item.find('link').text
                    pubDate = item.find('pubDate').text
                    source = item.find('source').text if item.find('source') is not None else "Google News"
                    
                    try:
                        dt = pubDate[:16]
                    except:
                        dt = "Recently"

                    articles.append({
                        "title": title,
                        "link": link,
                        "source": source,
                        "date": dt
                    })
                    count += 1
                    
        except Exception as e:
            print(f"News Fetch Error: {e}")
            return [
                {"title": "Check Internet Connection for Live News", "link": "#", "source": "System", "date": "Now"},
                {"title": "Zvishavane Production stable (Offline Mode)", "link": "#", "source": "Local Archive", "date": "Today"},
            ]
            
        return articles
