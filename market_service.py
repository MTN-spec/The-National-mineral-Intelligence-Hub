import random
import pandas as pd
import datetime

# PURE MOCK SERVICE - NO EXTERNAL DEPENDENCIES TO GUARANTEE STABILITY
class MarketIntelligenceService:
    def __init__(self):
        # Top 10 Minerals in Zvishavane/Zimbabwe
        self.commodities = {
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
        
    def get_prices(self):
        """Generates realistic simulated market data."""
        data = []
        for name, info in self.commodities.items():
            base = info['base']
            volatility = info['volatility']
            
            # Simulate random daily fluctuation
            change_pct = random.uniform(-volatility, volatility)
            current_price = base * (1 + change_pct)
            
            # Simulate a 5-day trend
            trend = []
            price = current_price
            for _ in range(5):
                price = price * (1 + random.uniform(-volatility, volatility))
                trend.append(price)
            # Reverse so the last one is 'current' roughly
            trend = trend[::-1] 
            current_price = trend[-1]
            prev_price = trend[-2]
            change = ((current_price - prev_price) / prev_price) * 100
            
            data.append({
                "Mineral": name,
                "Price": current_price,
                "Change": change,
                "Trend": trend
            })
            
        return pd.DataFrame(data)

    def get_news(self):
        """Fetches REAL LIVE news using standard libraries (Crash-Proof)."""
        import urllib.request
        import xml.etree.ElementTree as ET
        
        url = "https://news.google.com/rss/search?q=Zimbabwe+Mining+Minerals&hl=en-US&gl=US&ceid=US:en"
        articles = []
        
        try:
            # 5-second timeout to prevent hanging
            with urllib.request.urlopen(url, timeout=5) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                
                # Iterate over channel items
                count = 0
                for item in root.findall('./channel/item'):
                    if count >= 6: break
                    
                    title = item.find('title').text
                    link = item.find('link').text
                    pubDate = item.find('pubDate').text
                    source = item.find('source').text if item.find('source') is not None else "Google News"
                    
                    # Simple date cleanup
                    # pubDate is usually "Tue, 17 Dec 2025 10:00:00 GMT"
                    try:
                        dt = pubDate[:16] # "Tue, 17 Dec 2025"
                    except:
                        dt = "Recenly"

                    articles.append({
                        "title": title,
                        "link": link,
                        "source": source,
                        "date": dt
                    })
                    count += 1
                    
        except Exception as e:
            print(f"News Fetch Error: {e}")
            # Fallback if internet is down
            return [
                {"title": "Check Internet Connection for Live News", "link": "#", "source": "System", "date": "Now"},
                {"title": "Zvishavane Production stable (Offline Mode)", "link": "#", "source": "Local Archive", "date": "Today"},
            ]
            
        return articles
