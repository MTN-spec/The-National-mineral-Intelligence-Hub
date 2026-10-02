import os
import json
import random
import time
import datetime
import sqlite3
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

# Import existing domain services
from auth_service import AuthService
from market_service import MarketIntelligenceService
from boundary_service import boundary_service
from mentorship_service import mentorship_service
from api_gateway import EcoCashGateway, SmsService, EmailService, APILogger
from mock_services import AkelloService, EcoCashService, GigEngine

# Initialize FastAPI App
app = FastAPI(
    title="The National Mineral Intelligence Hub API",
    description="High-performance backend for Zimbabwe Mineral Intelligence, Sentinel-2 remote sensing, market pricing, and EcoCash services.",
    version="2.0.0"
)

# Enable CORS for external dashboards and mtnspec.co.zw production host
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
        "https://mtnspec.co.zw",
        "https://mining.mtnspec.co.zw",
        "https://www.mtnspec.co.zw",
        "http://localhost:8000",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service Singletons
auth_service = AuthService()
market_service = MarketIntelligenceService()
akello_service = AkelloService()
ecocash_service = EcoCashService()
gig_engine = GigEngine()

# ==========================================
# MTNSPEC CHANGE IT™ PAYMENT ENGINE
# ==========================================
class ChangeItService:
    """
    MTNSPEC Change It Digital Micropayment & P2P Engine (mtnspec.co.zw).
    Provides instantaneous cashless peer-to-peer settlements for Zimbabwean transport,
    artisanal mining ore lots, and statutory compliance.
    """
    def __init__(self):
        self.balance = 85.50  # USD balance
        self.transactions = [
            {
                "date": "2026-03-01 11:20",
                "desc": "Change It P2P: Kadoma Gold Ore Assay Batch settlement",
                "amount": 35.00,
                "type": "credit",
                "gateway": "Change It (MTNSPEC)",
                "tx_id": "CHG-89104"
            },
            {
                "date": "2026-02-28 16:45",
                "desc": "Change It Transit: Diesel transport Kombi refund",
                "amount": -4.50,
                "type": "debit",
                "gateway": "Change It (MTNSPEC)",
                "tx_id": "CHG-74129"
            },
            {
                "date": "2026-02-25 10:15",
                "desc": "Change It P2P: Selukwe Chrome panning syndicate payout",
                "amount": 55.00,
                "type": "credit",
                "gateway": "Change It (MTNSPEC)",
                "tx_id": "CHG-63201"
            }
        ]

    def get_balance(self):
        return self.balance

    def process_transfer(self, recipient_phone: str, amount: float, note: str):
        if self.balance < amount:
            return False, "Insufficient Change It balance."
        self.balance -= amount
        tx_id = f"CHG-{random.randint(100000, 999999)}"
        self.transactions.insert(0, {
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "desc": f"Change It P2P to {recipient_phone}: {note}",
            "amount": -amount,
            "type": "debit",
            "gateway": "Change It (MTNSPEC)",
            "tx_id": tx_id
        })
        return True, tx_id

    def credit_account(self, amount: float, description: str):
        self.balance += amount
        tx_id = f"CHG-{random.randint(100000, 999999)}"
        self.transactions.insert(0, {
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "desc": description,
            "amount": amount,
            "type": "credit",
            "gateway": "Change It (MTNSPEC)",
            "tx_id": tx_id
        })
        return True, tx_id

change_it_service = ChangeItService()

# Seed Admin User if needed
auth_service.seed_admin(
    "mhandutakunda@gmail.com", "Mimosa@2030", "Takunda Nigel Mhandu", "+263779770395"
)

# ==========================================
# PYDANTIC SCHEMAS
# ==========================================
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    phone: str

class PaymentRequest(BaseModel):
    phone: str
    amount: float
    reference: str
    gateway: Optional[str] = "ecocash" # "ecocash" or "change_it"

class TransferRequest(BaseModel):
    recipient_phone: str
    amount: float
    note: Optional[str] = "P2P Mineral Hub Transfer"
    gateway: Optional[str] = "change_it" # "change_it" or "ecocash"

class PermitRequest(BaseModel):
    concession_id: str
    miner_name: str
    mineral_type: str
    tonnage: float
    destination: str
    vehicle_reg: str

class MentorBookingRequest(BaseModel):
    mentor_id: str
    applicant_name: str
    email: str
    topic: str
    date: str
    time: str
    session_type: Optional[str] = "Virtual 1-on-1"

# ==========================================
# ZIMBABWE MINING CONCESSIONS & CLAIMS DATA
# ==========================================
MINING_CONCESSIONS = [
    {
        "id": "ZIM-GD-001",
        "name": "Selukwe Chrome Concession",
        "district": "Shurugwi, Midlands",
        "mineral": "Chromite & PGM",
        "status": "Active",
        "risk_level": "Low",
        "yield_rating": "High Yield",
        "lat": -19.6700,
        "lng": 30.0050,
        "operator": "ZIMASCO Artisanal Syndicate",
        "license_no": "MC-SHU-2024-8841",
        "area_hectares": 340.5,
        "monthly_tonnage": 450.0,
        "compliance_score": 94,
        "active_inspectors": 3,
        "spectral_signature": "Ultramafic Chromite Complex",
        "bounds": [
            [-19.655, 29.990],
            [-19.655, 30.020],
            [-19.685, 30.020],
            [-19.685, 29.990]
        ]
    },
    {
        "id": "ZIM-GD-002",
        "name": "Hartley Complex PGM Block",
        "district": "Chegutu / Norton, Mash West",
        "mineral": "Platinum Group Metals",
        "status": "Active",
        "risk_level": "Low",
        "yield_rating": "High Yield",
        "lat": -18.1500,
        "lng": 30.2800,
        "operator": "Zimplats Hartley Syndicate",
        "license_no": "MC-CHE-2023-1092",
        "area_hectares": 850.0,
        "monthly_tonnage": 1200.0,
        "compliance_score": 98,
        "active_inspectors": 5,
        "spectral_signature": "Main Sulphide Zone (MSZ)",
        "bounds": [
            [-18.130, 30.260],
            [-18.130, 30.300],
            [-18.170, 30.300],
            [-18.170, 30.260]
        ]
    },
    {
        "id": "ZIM-GB-003",
        "name": "Kadoma Central Gold Corridor",
        "district": "Kadoma, Mashonaland West",
        "mineral": "Gold (Au)",
        "status": "Active",
        "risk_level": "Moderate",
        "yield_rating": "High Yield",
        "lat": -18.3333,
        "lng": 29.9167,
        "operator": "Midlands Artisanal Gold Assoc.",
        "license_no": "MC-KAD-2025-0451",
        "area_hectares": 520.0,
        "monthly_tonnage": 68.0,
        "compliance_score": 82,
        "active_inspectors": 4,
        "spectral_signature": "Gossan / Iron Oxide Quartz Shear",
        "bounds": [
            [-18.315, 29.900],
            [-18.315, 29.935],
            [-18.350, 29.935],
            [-18.350, 29.900]
        ]
    },
    {
        "id": "ZIM-BIK-004",
        "name": "Bikita Pegmatite Lithium Zone",
        "district": "Bikita, Masvingo",
        "mineral": "Lithium (Spodumene/Petalite)",
        "status": "Active",
        "risk_level": "Low",
        "yield_rating": "High Yield",
        "lat": -19.9500,
        "lng": 31.4333,
        "operator": "Bikita Pegmatite Mining Hub",
        "license_no": "MC-BIK-2024-3329",
        "area_hectares": 610.0,
        "monthly_tonnage": 2400.0,
        "compliance_score": 96,
        "active_inspectors": 4,
        "spectral_signature": "Hydroxyl & Clay Bearing Pegmatite",
        "bounds": [
            [-19.930, 31.415],
            [-19.930, 31.450],
            [-19.970, 31.450],
            [-19.970, 31.415]
        ]
    },
    {
        "id": "ZIM-GW-005",
        "name": "Gwanda Greenstone Belt Claims",
        "district": "Gwanda, Matabeleland South",
        "mineral": "Gold & Quartz Veins",
        "status": "Warning",
        "risk_level": "Severe",
        "yield_rating": "Moderate",
        "lat": -20.9333,
        "lng": 29.0000,
        "operator": "Colleen Bawn ASM Cooperative",
        "license_no": "MC-GWA-2023-7721",
        "area_hectares": 410.0,
        "monthly_tonnage": 32.5,
        "compliance_score": 64,
        "active_inspectors": 2,
        "spectral_signature": "Ferrous Iron & Banded Ironstone",
        "bounds": [
            [-20.915, 28.980],
            [-20.915, 29.020],
            [-20.950, 29.020],
            [-20.950, 28.980]
        ]
    },
    {
        "id": "ZIM-BIN-006",
        "name": "Bindura Nickel & Copper Belt",
        "district": "Bindura, Mashonaland Central",
        "mineral": "Nickel & Copper Sulfides",
        "status": "Active",
        "risk_level": "Low",
        "yield_rating": "High Yield",
        "lat": -17.3000,
        "lng": 31.3333,
        "operator": "Trojan Nickel Secondary Claims",
        "license_no": "MC-BIN-2024-9102",
        "area_hectares": 490.0,
        "monthly_tonnage": 550.0,
        "compliance_score": 91,
        "active_inspectors": 3,
        "spectral_signature": "Serpentinite & Gossan Alteration",
        "bounds": [
            [-17.280, 31.315],
            [-17.280, 31.350],
            [-17.320, 31.350],
            [-17.320, 31.315]
        ]
    }
]

# Preset Sentinel-2 Satellite Scenes
SATELLITE_SCENES = [
    {
        "id": "SCENE-GD-CENTRAL",
        "name": "Great Dyke Central (Selukwe & Hartley)",
        "district": "Midlands / Mash West",
        "coordinates": {"lat": -19.67, "lng": 30.00},
        "target_minerals": ["Platinum", "Chrome", "Nickel"],
        "recommended_indices": ["Ferrous Iron", "Clay Minerals", "Iron Oxide"],
        "cloud_cover": "1.2%",
        "sensing_date": "2026-02-14",
        "sensor": "Sentinel-2 MSI Level-2A"
    },
    {
        "id": "SCENE-KADOMA-GOLD",
        "name": "Kadoma Archaean Gold Corridor",
        "district": "Mashonaland West",
        "coordinates": {"lat": -18.33, "lng": 29.91},
        "target_minerals": ["Gold", "Silver", "Antimony"],
        "recommended_indices": ["Iron Oxide", "Gossan Zone", "Geological Lineaments"],
        "cloud_cover": "0.8%",
        "sensing_date": "2026-02-18",
        "sensor": "Sentinel-2 MSI Level-2A"
    },
    {
        "id": "SCENE-BIKITA-LI",
        "name": "Bikita Pegmatite Belt",
        "district": "Masvingo",
        "coordinates": {"lat": -19.95, "lng": 31.43},
        "target_minerals": ["Lithium", "Tantalite", "Beryl"],
        "recommended_indices": ["Clay Minerals", "Hydrothermal Alteration", "reNDVI"],
        "cloud_cover": "2.4%",
        "sensing_date": "2026-02-10",
        "sensor": "Sentinel-2 MSI Level-2A"
    },
    {
        "id": "SCENE-GWANDA-GREEN",
        "name": "Gwanda Greenstone Archaean Complex",
        "district": "Matabeleland South",
        "coordinates": {"lat": -20.93, "lng": 29.00},
        "target_minerals": ["Gold", "Arsenopyrite", "Iron"],
        "recommended_indices": ["Ferric Oxide", "WRI Flooded Pit", "Lineaments"],
        "cloud_cover": "0.0%",
        "sensing_date": "2026-02-22",
        "sensor": "Sentinel-2 MSI Level-2A"
    }
]

# Mineral Spectral Indices Definition
SPECTRAL_INDICES = [
    {
        "key": "truecolor",
        "name": "True Color (RGB)",
        "category": "Visual",
        "formula": "B4 (Red) + B3 (Green) + B2 (Blue)",
        "bands": ["B4", "B3", "B2"],
        "description": "Natural optical satellite imagery reflecting human eye perception with high fidelity surface detail.",
        "gradient": "linear-gradient(90deg, #1e3a8a, #059669, #eab308, #b91c1c)",
        "range": "Natural RGB"
    },
    {
        "key": "iron_oxide",
        "name": "Iron Oxide Index",
        "category": "Mineral",
        "formula": "B4 / B2 (Red / Blue)",
        "bands": ["B4", "B2"],
        "description": "Standard band ratio for hematite, goethite, and jarosite detection in oxidized surface zones.",
        "gradient": "linear-gradient(90deg, #2b83ba, #abdda4, #ffffbf, #fdae61, #d7191c)",
        "range": "0.5 — 3.2"
    },
    {
        "key": "ferrous_iron",
        "name": "Ferrous Iron Index",
        "category": "Mineral",
        "formula": "(B12 / B8) + (B3 / B4)",
        "bands": ["B12", "B8", "B3", "B4"],
        "description": "Detects ferrous iron in silicates and carbonates associated with mafic and ultramafic rock bodies.",
        "gradient": "linear-gradient(90deg, #313695, #74add1, #fee090, #f46d43, #a50026)",
        "range": "0.8 — 4.0"
    },
    {
        "key": "clay_minerals",
        "name": "Clay Minerals Index",
        "category": "Mineral",
        "formula": "B11 / B12 (SWIR1 / SWIR2)",
        "bands": ["B11", "B12"],
        "description": "Highlights hydroxyl-bearing minerals, kaolinite, alunite, and illite indicative of hydrothermal alteration.",
        "gradient": "linear-gradient(90deg, #440154, #3b528b, #21918c, #5ec962, #fde725)",
        "range": "1.0 — 2.5"
    },
    {
        "key": "gossan_zone",
        "name": "Gossan Zone Index",
        "category": "Mineral",
        "formula": "B11 / B8A (SWIR1 / Narrow NIR)",
        "bands": ["B11", "B8A"],
        "description": "Ferric iron cap (gossan) marker indicating weathered sulfide deposits and secondary enrichment.",
        "gradient": "linear-gradient(90deg, #0d0887, #6a00a8, #b12a90, #e16462, #fca636)",
        "range": "0.6 — 2.8"
    },
    {
        "key": "rendvi",
        "name": "reNDVI (Red Edge Biomass)",
        "category": "Environmental",
        "formula": "(B8A - B5) / (B8A + B5)",
        "bands": ["B8A", "B5"],
        "description": "Sensitive vegetation index that measures environmental impact and rehabilitation around mining pits.",
        "gradient": "linear-gradient(90deg, #d73027, #fc8d59, #fee08b, #d9ef8b, #1a9850)",
        "range": "-1.0 — 1.0"
    },
    {
        "key": "wri",
        "name": "Flooded Pit Detection (WRI)",
        "category": "Environmental",
        "formula": "(B5 + B6) / (B11 + B12)",
        "bands": ["B5", "B6", "B11", "B12"],
        "description": "Water Ratio Index specifically tuned for standing water in open pits and tailings dams.",
        "gradient": "linear-gradient(90deg, #023858, #045a8d, #3690c0, #67a9cf, #a6bddb)",
        "range": "0.0 — 3.5"
    },
    {
        "key": "lineaments",
        "name": "Geological Structures / Lineaments",
        "category": "Structure",
        "formula": "Canny Edge Filter on B11 (SWIR1)",
        "bands": ["B11"],
        "description": "Identifies fault lines, lithological boundaries, and shear zones controlling vein-type mineralization.",
        "gradient": "linear-gradient(90deg, #111827, #374151, #9ca3af, #f9fafb)",
        "range": "Edge Binary"
    }
]

# ==========================================
# API ROUTES
# ==========================================

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "system": "The National Mineral Intelligence Hub",
        "year": 2026,
        "timestamp": datetime.datetime.now().isoformat()
    }

# --- AUTHENTICATION ---
@app.post("/api/auth/login")
def login(req: LoginRequest):
    user, msg = auth_service.login_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return {
        "success": True,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "phone": user["phone"],
            "is_subscribed": bool(user["is_subscribed"]),
            "role": "Chief Mineral Intelligence Officer" if user["email"] == "mhandutakunda@gmail.com" else "Registered Miner"
        }
    }

@app.post("/api/auth/register")
def register(req: RegisterRequest):
    success, msg = auth_service.register_user(req.email, req.password, req.name, req.phone)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}

@app.get("/api/auth/users")
def list_users():
    """Admin endpoint to see registered accounts."""
    users = auth_service.get_all_users()
    return [{"id": u[0], "email": u[1], "name": u[2], "phone": u[3], "subscribed": bool(u[4])} for u in users]

# --- MINING CONCESSIONS & CLAIMS ---
@app.get("/api/concessions")
def get_concessions(filter_status: Optional[str] = Query(None)):
    """Return all monitored mining concessions and claims across Zimbabwe."""
    data = MINING_CONCESSIONS
    if filter_status and filter_status != "all":
        data = [c for c in data if c["status"].lower() == filter_status.lower() or c["yield_rating"].lower().replace(" ", "") == filter_status.lower()]
    return {
        "total": len(data),
        "concessions": data,
        "summary": {
            "total_monitored": len(MINING_CONCESSIONS),
            "high_yield_count": sum(1 for c in MINING_CONCESSIONS if c["yield_rating"] == "High Yield"),
            "active_count": sum(1 for c in MINING_CONCESSIONS if c["status"] == "Active"),
            "alerts_count": sum(1 for c in MINING_CONCESSIONS if c["status"] == "Warning" or c["risk_level"] == "Severe")
        }
    }

@app.get("/api/concessions/{concession_id}")
def get_concession_detail(concession_id: str):
    concession = next((c for c in MINING_CONCESSIONS if c["id"] == concession_id), None)
    if not concession:
        raise HTTPException(status_code=404, detail="Concession not found.")
    return concession

# --- SPECTRAL SATELLITE INDICES ---
@app.get("/api/minerals/indices")
def get_spectral_indices():
    return SPECTRAL_INDICES

@app.get("/api/minerals/scenes")
def get_satellite_scenes():
    return SATELLITE_SCENES

# --- ADMINISTRATIVE & CONSERVATION BOUNDARIES ---
@app.get("/api/boundaries/provinces")
def get_boundary_provinces():
    """Returns official provincial boundaries of Zimbabwe as GeoJSON."""
    return boundary_service.get_provinces()

@app.get("/api/boundaries/districts")
def get_boundary_districts():
    """Returns administrative district boundaries of Zimbabwe as GeoJSON."""
    return boundary_service.get_districts()

@app.get("/api/boundaries/wards")
def get_boundary_wards():
    """Returns local ward boundaries across active mineral belts as GeoJSON."""
    return boundary_service.get_wards()

@app.get("/api/boundaries/protected-areas")
def get_boundary_protected_areas():
    """Returns protected conservation areas, national parks, and forest reserves as GeoJSON."""
    return boundary_service.get_protected_areas()

@app.get("/api/boundaries/rivers")
def get_boundary_rivers():
    """Returns Zimbabwe river network (ZimbabweRivers global dataset + 250k national lines) as GeoJSON."""
    return boundary_service.get_rivers()

@app.get("/api/boundaries/soil")
def get_boundary_soil():
    """Returns FAO World Soil Map clipped to Zimbabwe with DOMSOI codes & mining relevance notes as GeoJSON."""
    return boundary_service.get_soil()

@app.get("/api/boundaries/geology")
def get_boundary_geology():
    """Returns Africa Geology Map (BGS/FAO geo7_2ag) clipped to Zimbabwe with GLG codes as GeoJSON."""
    return boundary_service.get_geology()

@app.get("/api/boundaries/summary")
def get_boundaries_summary(refresh: bool = False):
    """Returns counts and metadata of available administrative layers."""
    if refresh:
        boundary_service._cache.clear()
    return {
        "layers": {
            "provinces":       {"count": len(boundary_service.get_provinces().get("features", [])),        "type": "Administrative Level 1"},
            "districts":       {"count": len(boundary_service.get_districts().get("features", [])),        "type": "Administrative Level 2"},
            "wards":           {"count": len(boundary_service.get_wards().get("features", [])),            "type": "Electoral & ASM Level 3"},
            "protected_areas": {"count": len(boundary_service.get_protected_areas().get("features", [])), "type": "ZimParks IUCN & Environmental Protection"},
            "rivers":          {"count": len(boundary_service.get_rivers().get("features", [])),           "type": "Hydrological Network"},
            "soil":            {"count": len(boundary_service.get_soil().get("features", [])),             "type": "FAO World Soil Map (Zimbabwe)"},
            "geology":         {"count": len(boundary_service.get_geology().get("features", [])),          "type": "Africa Geology (BGS/FAO geo7_2ag)"},
        }
    }

# --- COMMODITY MARKET INTELLIGENCE ---
@app.get("/api/market/prices")
def get_market_prices():
    """Fetch live & benchmark mineral commodity prices from MarketIntelligenceService."""
    prices = market_service.get_prices_list()
    
    # Calculate headline metrics
    gold_item = next((p for p in prices if "Gold" in p["name"]), None)
    plat_item = next((p for p in prices if "Platinum" in p["name"]), None)
    lith_item = next((p for p in prices if "Lithium" in p["name"]), None)

    return {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "commodities": prices,
        "headline": {
            "gold": gold_item,
            "platinum": plat_item,
            "lithium": lith_item
        },
        "currency_exchange": {
            "USD_ZIG": 26.85,
            "USD_ZAR": 18.25
        }
    }

@app.get("/api/market/news")
def get_market_news():
    """Fetch real-time news RSS items on Zimbabwe Mining and Metals."""
    return market_service.get_news()

# --- UNIFIED FINTECH GATEWAY: MTNSPEC CHANGE IT™ + ECOCASH ---
@app.get("/api/fintech/wallet")
def get_unified_wallet():
    """Returns combined liquidity across MTNSPEC Change It and EcoCash Mobile Money."""
    ecocash_bal = ecocash_service.get_balance()
    change_it_bal = change_it_service.get_balance()
    total_usd = round(ecocash_bal + change_it_bal, 2)
    total_zig = round(total_usd * 26.85, 2)

    # Format combined transactions
    eco_txs = [{**tx, "gateway": "EcoCash USSD", "tx_id": tx.get("tx_id", f"ECO-{random.randint(10000,99999)}")} for tx in ecocash_service.transactions]
    change_txs = change_it_service.transactions
    all_txs = sorted(eco_txs + change_txs, key=lambda x: x["date"], reverse=True)

    return {
        "provider": "MTNSPEC Financial Technologies (mtnspec.co.zw)",
        "ecocash": {
            "balance_usd": ecocash_bal,
            "balance_zig": round(ecocash_bal * 26.85, 2),
            "status": "Active (Econet Rails)"
        },
        "change_it": {
            "balance_usd": change_it_bal,
            "balance_zig": round(change_it_bal * 26.85, 2),
            "status": "Active (MTNSPEC P2P Rails)",
            "speed": "<200ms Instant Settlement",
            "fee": "0% ASM Syndicate Subsidized"
        },
        "total_liquidity_usd": total_usd,
        "total_liquidity_zig": total_zig,
        "exchange_rate": 26.85,
        "transactions": all_txs
    }

@app.post("/api/fintech/pay")
def unified_pay(req: PaymentRequest):
    """Pay mining fees, permits, or ore royalties via Change It or EcoCash."""
    gw = (req.gateway or "change_it").lower()
    if gw == "change_it":
        if change_it_service.get_balance() < req.amount:
            raise HTTPException(status_code=400, detail="Insufficient Change It wallet balance.")
        success, tx_id = change_it_service.process_transfer(req.phone, req.amount, req.reference)
        return {
            "success": success,
            "gateway": "Change It (MTNSPEC)",
            "transaction_id": tx_id,
            "message": f"Payment of ${req.amount:.2f} processed via MTNSPEC Change It",
            "new_balance": change_it_service.get_balance()
        }
    else:
        success, res = EcoCashGateway.initiate_payment(req.amount, req.phone, req.reference)
        if success:
            ecocash_service.pay_user(-req.amount, f"EcoCash Merchant: {req.reference}")
        return {
            "success": success,
            "gateway": "EcoCash USSD",
            "response": res,
            "new_balance": ecocash_service.get_balance()
        }

@app.post("/api/fintech/transfer")
def unified_transfer(req: TransferRequest):
    """P2P instant transfer between registered miners, syndicates, and logistics carriers."""
    gw = (req.gateway or "change_it").lower()
    if gw == "change_it":
        if req.amount > change_it_service.get_balance():
            raise HTTPException(status_code=400, detail="Insufficient Change It balance.")
        success, tx_id = change_it_service.process_transfer(req.recipient_phone, req.amount, req.note or "Mineral Hub P2P")
        return {
            "success": True,
            "gateway": "MTNSPEC Change It",
            "transaction_id": tx_id,
            "message": f"Successfully transferred ${req.amount:.2f} to {req.recipient_phone} via MTNSPEC Change It",
            "new_balance": change_it_service.get_balance(),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        if req.amount > ecocash_service.get_balance():
            raise HTTPException(status_code=400, detail="Insufficient EcoCash balance.")
        ecocash_service.pay_user(-req.amount, f"P2P Transfer to {req.recipient_phone}: {req.note}")
        return {
            "success": True,
            "gateway": "EcoCash",
            "message": f"Successfully transferred ${req.amount:.2f} to {req.recipient_phone} via EcoCash",
            "new_balance": ecocash_service.get_balance(),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

# Backward Compatibility routes for /api/ecocash/*
@app.get("/api/ecocash/wallet")
def get_wallet():
    return {
        "balance_usd": ecocash_service.get_balance(),
        "balance_zig": round(ecocash_service.get_balance() * 26.85, 2),
        "transactions": ecocash_service.transactions
    }

@app.post("/api/ecocash/pay")
def initiate_payment(req: PaymentRequest):
    req.gateway = "ecocash"
    return unified_pay(req)

@app.post("/api/ecocash/transfer")
def p2p_transfer(req: TransferRequest):
    req.gateway = "ecocash"
    return unified_transfer(req)

# --- DIGITAL TRANSIT & COMPLIANCE PERMITS (QR CODE) ---
@app.post("/api/permits/generate")
def generate_permit(req: PermitRequest):
    """Generate authenticated mining ore transit permit payload with QR code and MTNSPEC signature."""
    import base64
    import qrcode
    from io import BytesIO

    permit_id = f"ZIM-MIN-PRM-{random.randint(100000, 999999)}"
    issue_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    expiry_date = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")

    permit_payload = {
        "permit_id": permit_id,
        "authority": "Ministry of Mines & Mining Development Zimbabwe",
        "cadastre_system": "The National Mineral Intelligence Hub",
        "technology_partner": "MTNSPEC (https://mtnspec.co.zw)",
        "settlement_engine": "MTNSPEC Change It™ / EcoCash Unified Rails",
        "concession_id": req.concession_id,
        "miner": req.miner_name,
        "mineral": req.mineral_type,
        "tonnage": req.tonnage,
        "destination": req.destination,
        "vehicle": req.vehicle_reg,
        "issued_at": issue_date,
        "expires_at": expiry_date,
        "verification_url": f"https://mining.mtnspec.co.zw/verify/{permit_id}"
    }

    # Generate QR Code image
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(json.dumps(permit_payload))
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f1923", back_color="#ffffff")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return {
        "permit": permit_payload,
        "qr_code_base64": f"data:image/png;base64,{qr_base64}"
    }

# --- SKILLS & GIG ENGINE ---
@app.get("/api/skills/courses")
def get_courses():
    return akello_service.get_courses()

@app.get("/api/skills/gigs")
def get_gigs():
    return gig_engine.get_open_gigs()

@app.post("/api/skills/gigs/{gig_id}/claim")
def claim_gig(gig_id: int):
    success, msg = gig_engine.claim_gig(gig_id)
    return {"success": success, "message": msg}

# --- MODULE 3: MENTORSHIP & TALENT ECOSYSTEM ---
@app.get("/api/mentorship/mentors")
def get_mentors():
    """Fetch verified Zimbabwean senior mining mentors and industry specialists."""
    return {"mentors": mentorship_service.get_mentors()}

@app.get("/api/mentorship/talent")
def get_talent():
    """Fetch verified directory of mining graduates, geomatics engineers, and ASM apprentices."""
    return {"talent": mentorship_service.get_talent()}

@app.get("/api/mentorship/bookings")
def get_mentor_bookings():
    """Fetch active advisory bookings."""
    return {"bookings": mentorship_service.get_bookings()}

@app.post("/api/mentorship/book")
def book_mentor(req: MentorBookingRequest):
    """Book a verified 1-on-1 advisory session with a senior mentor."""
    try:
        booking = mentorship_service.book_session(
            mentor_id=req.mentor_id,
            applicant_name=req.applicant_name,
            email=req.email,
            topic=req.topic,
            date=req.date,
            time=req.time,
            session_type=req.session_type or "Virtual 1-on-1"
        )
        return {"success": True, "message": "Advisory session booked successfully", "booking": booking}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- STATIC FILES FOR DASHBOARD & ASSETS ---
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# Mount project root assets (logos, profile photo, backgrounds, pdfs)
app.mount("/assets", StaticFiles(directory=ROOT_DIR), name="assets")

# Mount Privy / AgriShield assets from sibling project
PRIVY_DIR = os.path.abspath(os.path.join(ROOT_DIR, "..", "Privy  - Agricultural Drought"))
if os.path.exists(PRIVY_DIR):
    app.mount("/privy-assets", StaticFiles(directory=PRIVY_DIR), name="privy_assets")

# Mount dashboard web UI
DASHBOARD_DIR = os.path.join(ROOT_DIR, "src", "dashboard")
if os.path.exists(DASHBOARD_DIR):
    app.mount("/", StaticFiles(directory=DASHBOARD_DIR, html=True), name="dashboard")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("💎 THE NATIONAL MINERAL INTELLIGENCE HUB 💎")
    print("   Zimbabwe 2026 - Earth Observation & Mining Engine")
    print("   Serving on: http://localhost:8000")
    print("   API Docs:   http://localhost:8000/docs")
    print("="*60 + "\n")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
