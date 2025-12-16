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
        """Returns simulated news headlines."""
        # Static list of realistic headlines
        headlines = [
            {"title": "Zvishavane Production hits record high for Q4", "source": "Mining Weekly"},
            {"title": "Lithium demand surges as EV market expands", "source": "Market Watch"},
            {"title": "New environmental regulations for Chrome mining", "source": "EMA Update"},
            {"title": "Global Gold prices stabilize amid inflation concerns", "source": "Bloomberg"},
            {"title": "Mimosa Mine announces community development fund", "source": "Local News"},
            {"title": "Small-scale miners to receive government grants", "source": "Govt Gazette"}
        ]
        
        articles = []
        random.shuffle(headlines)
        for h in headlines[:4]:
            articles.append({
                "title": h['title'],
                "link": "#",
                "source": h['source'],
                "date": datetime.datetime.now().strftime("%d %b %Y")
            })
        return articles
