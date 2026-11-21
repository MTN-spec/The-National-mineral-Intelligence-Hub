import os
import json
import html
import hmac
import hashlib
import secrets
import random
import time
import datetime
import sqlite3
from collections import defaultdict
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

# Import existing domain services
from auth_service import AuthService
from market_service import MarketIntelligenceService
from boundary_service import boundary_service
from mentorship_service import mentorship_service
from api_gateway import EcoCashGateway, SmsService, EmailService, APILogger
from mock_services import AkelloService, EcoCashService, GigEngine
import db as pg_db

# Initialize FastAPI App
app = FastAPI(
    title="The National Mineral Intelligence Hub API",
    description="Banking-Grade Sovereign Backend for Zimbabwe Mineral Intelligence, Sentinel-2 Remote Sensing, Market Pricing, and MTNSPEC Change It / EcoCash Settlement Rails.",
    version="2.1.0"
)

# ==========================================
# BANKING-GRADE CORS & SECURITY HEADERS
# ==========================================
ALLOWED_ORIGINS = [
    "https://mtnspec.co.zw",
    "https://www.mtnspec.co.zw",
    "https://mining.mtnspec.co.zw",
    "https://mineralhub.mtnspec.co.zw",
    "https://nationalmineralintelligencehub.co.zw",
    "https://www.nationalmineralintelligencehub.co.zw",
    "http://localhost:8000",
    "http://localhost:8080",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
)


@app.middleware("http")
async def banking_security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(self), camera=(self), microphone=()"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    return response


# Cryptographic HMAC key for signing ore transit permits (rotatable via NMIH_HMAC_SECRET env var)
PERMIT_HMAC_KEY = os.environ.get("NMIH_HMAC_SECRET", secrets.token_hex(32)).encode("utf-8")

# Sliding-window brute-force rate limiter for /api/auth/login
_FAILED_LOGINS: Dict[str, List[float]] = defaultdict(list)
MAX_LOGIN_ATTEMPTS = 8
LOGIN_WINDOW_SECONDS = 300


def _sanitize_text(val: Optional[str], max_len: int = 140) -> str:
    cleaned = (val or "").strip()[:max_len]
    return html.escape(cleaned, quote=True)


def _sign_permit_payload(payload: Dict[str, Any]) -> str:
    canonical = json.dumps(
        {k: v for k, v in sorted(payload.items()) if k != "hmac_signature"},
        separators=(",", ":"),
        sort_keys=True
    ).encode("utf-8")
    return hmac.new(PERMIT_HMAC_KEY, canonical, hashlib.sha256).hexdigest()


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
        return round(self.balance, 2)

    def process_transfer(self, recipient_phone: str, amount: float, note: str):
        if amount <= 0:
            return False, "Amount must be strictly positive."
        if self.balance < amount:
            return False, "Insufficient Change It balance."
        self.balance = round(self.balance - amount, 2)
        tx_id = f"CHG-{secrets.randbelow(900000) + 100000}"
        self.transactions.insert(0, {
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "desc": f"Change It P2P to {_sanitize_text(recipient_phone, 32)}: {_sanitize_text(note, 80)}",
            "amount": -round(amount, 2),
            "type": "debit",
            "gateway": "Change It (MTNSPEC)",
            "tx_id": tx_id
        })
        return True, tx_id

    def credit_account(self, amount: float, description: str):
        if amount <= 0:
            return False, "Amount must be strictly positive."
        self.balance = round(self.balance + amount, 2)
        tx_id = f"CHG-{secrets.randbelow(900000) + 100000}"
        self.transactions.insert(0, {
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "desc": _sanitize_text(description, 100),
            "amount": round(amount, 2),
            "type": "credit",
            "gateway": "Change It (MTNSPEC)",
            "tx_id": tx_id
        })
        return True, tx_id


change_it_service = ChangeItService()

# Seed Admin User ONLY if NMIH_ADMIN_PASSWORD is supplied securely in environment variables
auth_service.seed_admin(
    os.environ.get("NMIH_ADMIN_EMAIL", "mhandutakunda@gmail.com"),
    os.environ.get("NMIH_ADMIN_PASSWORD", ""),
    "Takunda Nigel Mhandu",
    "+263779770395"
)


# ==========================================
# PYDANTIC SCHEMAS (STRICT BOUNDS)
# ==========================================
class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=120)
    password: str = Field(..., min_length=1, max_length=128)


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=2, max_length=120)
    phone: str = Field(..., min_length=6, max_length=32)


class PaymentRequest(BaseModel):
    phone: str = Field(..., min_length=6, max_length=32)
    amount: float = Field(..., gt=0.0, le=100000.0)
    reference: str = Field(..., min_length=2, max_length=120)
    gateway: Optional[str] = "ecocash"


class TransferRequest(BaseModel):
    recipient_phone: str = Field(..., min_length=6, max_length=32)
    amount: float = Field(..., gt=0.0, le=100000.0)
    note: Optional[str] = "P2P Mineral Hub Transfer"
    gateway: Optional[str] = "change_it"


class PermitRequest(BaseModel):
    concession_id: str = Field(..., min_length=3, max_length=40)
    miner_name: str = Field(..., min_length=2, max_length=120)
    mineral_type: str = Field(..., min_length=2, max_length=80)
    tonnage: float = Field(..., gt=0.0, le=50000.0)
    destination: str = Field(..., min_length=2, max_length=120)
    vehicle_reg: str = Field(..., min_length=2, max_length=40)


class MentorBookingRequest(BaseModel):
    mentor_id: str = Field(..., min_length=3, max_length=32)
    applicant_name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., min_length=4, max_length=120)
    topic: str = Field(..., min_length=3, max_length=500)
    date: str = Field(..., min_length=6, max_length=32)
    time: str = Field(..., min_length=3, max_length=32)
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
    db_status = pg_db.check_db_health()
    return {
        "status": "healthy",
        "system": "The National Mineral Intelligence Hub",
        "security_standard": "MTN-SPEC Banking-Grade (PBKDF2-SHA256 + HMAC-SHA256)",
        "database": db_status,
        "year": 2026,
        "timestamp": datetime.datetime.now().isoformat()
    }


# --- AUTHENTICATION ---
@app.post("/api/auth/login")
def login(req: LoginRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    _FAILED_LOGINS[client_ip] = [t for t in _FAILED_LOGINS[client_ip] if now - t < LOGIN_WINDOW_SECONDS]
    if len(_FAILED_LOGINS[client_ip]) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail="Too many failed sign-in attempts. Please wait 5 minutes before retrying."
        )

    user, _ = auth_service.login_user(req.email, req.password)
    if not user:
        _FAILED_LOGINS[client_ip].append(now)
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    _FAILED_LOGINS.pop(client_ip, None)
    admin_email = os.environ.get("NMIH_ADMIN_EMAIL", "mhandutakunda@gmail.com").strip().lower()
    return {
        "success": True,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "phone": user["phone"],
            "is_subscribed": bool(user["is_subscribed"]),
            "role": "Chief Mineral Intelligence Officer" if user["email"].lower() == admin_email else "Registered Miner"
        }
    }


@app.post("/api/auth/register")
def register(req: RegisterRequest):
    success, msg = auth_service.register_user(req.email, req.password, req.name, req.phone)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}


# --- MINING CONCESSIONS & CLAIMS ---
@app.get("/api/concessions")
def get_concessions(filter_status: Optional[str] = Query(None)):
    """Return all monitored mining concessions and claims across Zimbabwe from PostgreSQL/PostGIS."""
    if pg_db.is_db_configured():
        data = pg_db.query_concessions_from_db(filter_status)
        all_data = pg_db.query_concessions_from_db(None) if filter_status and filter_status != "all" else data
        source = "PostgreSQL/PostGIS"
    else:
        all_data = MINING_CONCESSIONS
        data = MINING_CONCESSIONS
        if filter_status and filter_status != "all":
            data = [c for c in data if c["status"].lower() == filter_status.lower() or c["yield_rating"].lower().replace(" ", "") == filter_status.lower()]
        source = "in-memory (DATABASE_URL unset)"
    return {
        "source": source,
        "total": len(data),
        "concessions": data,
        "summary": {
            "total_monitored": len(all_data),
            "high_yield_count": sum(1 for c in all_data if c.get("yield_rating") == "High Yield"),
            "active_count": sum(1 for c in all_data if "active" in str(c.get("status", "")).lower()),
            "alerts_count": sum(1 for c in all_data if c.get("status") == "Warning" or c.get("risk_level") == "Severe")
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
    return boundary_service.get_provinces()


@app.get("/api/boundaries/districts")
def get_boundary_districts():
    return boundary_service.get_districts()


@app.get("/api/boundaries/wards")
def get_boundary_wards():
    return boundary_service.get_wards()


@app.get("/api/boundaries/protected-areas")
def get_boundary_protected_areas():
    return boundary_service.get_protected_areas()


@app.get("/api/boundaries/rivers")
def get_boundary_rivers():
    return boundary_service.get_rivers()


@app.get("/api/boundaries/soil")
def get_boundary_soil():
    return boundary_service.get_soil()


@app.get("/api/boundaries/geology")
def get_boundary_geology():
    return boundary_service.get_geology()


@app.get("/api/boundaries/summary")
def get_boundaries_summary(refresh: bool = False):
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
    prices = market_service.get_prices_list()
    if pg_db.is_db_configured():
        try:
            pg_db.record_market_snapshot(prices)
        except Exception as e:
            print(f"[Market Snapshot DB Warn]: {e}")
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
    return market_service.get_news()


# --- UNIFIED FINTECH GATEWAY: MTNSPEC CHANGE IT™ + ECOCASH ---
@app.get("/api/fintech/wallet")
def get_unified_wallet():
    ecocash_bal = ecocash_service.get_balance()
    change_it_bal = change_it_service.get_balance()
    total_usd = round(ecocash_bal + change_it_bal, 2)
    total_zig = round(total_usd * 26.85, 2)

    eco_txs = [{**tx, "gateway": "EcoCash USSD", "tx_id": tx.get("tx_id", f"ECO-{secrets.randbelow(90000)+10000}")} for tx in ecocash_service.transactions]
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
    gw = (req.gateway or "change_it").lower()
    clean_phone = _sanitize_text(req.phone, 32)
    clean_ref = _sanitize_text(req.reference, 100)
    if gw == "change_it":
        if change_it_service.get_balance() < req.amount:
            raise HTTPException(status_code=400, detail="Insufficient Change It wallet balance.")
        success, tx_id = change_it_service.process_transfer(clean_phone, req.amount, clean_ref)
        return {
            "success": success,
            "gateway": "Change It (MTNSPEC)",
            "transaction_id": tx_id,
            "message": f"Payment of ${req.amount:.2f} processed via MTNSPEC Change It",
            "new_balance": change_it_service.get_balance()
        }
    else:
        success, res = EcoCashGateway.initiate_payment(req.amount, clean_phone, clean_ref)
        if success:
            ecocash_service.pay_user(-req.amount, f"EcoCash Merchant: {clean_ref}")
        return {
            "success": success,
            "gateway": "EcoCash USSD",
            "response": res,
            "new_balance": ecocash_service.get_balance()
        }


@app.post("/api/fintech/transfer")
def unified_transfer(req: TransferRequest):
    gw = (req.gateway or "change_it").lower()
    clean_phone = _sanitize_text(req.recipient_phone, 32)
    clean_note = _sanitize_text(req.note or "Mineral Hub P2P", 100)
    if gw == "change_it":
        if req.amount > change_it_service.get_balance():
            raise HTTPException(status_code=400, detail="Insufficient Change It balance.")
        success, tx_id = change_it_service.process_transfer(clean_phone, req.amount, clean_note)
        return {
            "success": success,
            "gateway": "MTNSPEC Change It",
            "transaction_id": tx_id,
            "message": f"Successfully transferred ${req.amount:.2f} to {clean_phone} via MTNSPEC Change It",
            "new_balance": change_it_service.get_balance(),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        if req.amount > ecocash_service.get_balance():
            raise HTTPException(status_code=400, detail="Insufficient EcoCash balance.")
        tx_id = f"ECO-{secrets.randbelow(900000) + 100000}"
        ecocash_service.pay_user(-req.amount, f"P2P Transfer to {clean_phone}: {clean_note}")
        return {
            "success": True,
            "gateway": "EcoCash",
            "transaction_id": tx_id,
            "message": f"Successfully transferred ${req.amount:.2f} to {clean_phone} via EcoCash",
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


# --- DIGITAL TRANSIT & COMPLIANCE PERMITS (HMAC-SHA256 SIGNED QR CODE) ---
@app.post("/api/permits/generate")
def generate_permit(req: PermitRequest):
    """Generate authenticated mining ore transit permit payload with HMAC-SHA256 signature & QR code."""
    import base64
    import qrcode
    from io import BytesIO

    permit_id = f"ZIM-MIN-PRM-{secrets.randbelow(900000) + 100000}"
    issue_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    expiry_date = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")

    permit_payload = {
        "permit_id": permit_id,
        "authority": "Ministry of Mines & Mining Development Zimbabwe",
        "cadastre_system": "The National Mineral Intelligence Hub",
        "technology_partner": "MTN-SPEC (https://mtnspec.co.zw)",
        "settlement_engine": "MTNSPEC Change It™ / EcoCash Unified Rails",
        "concession_id": _sanitize_text(req.concession_id, 40),
        "miner": _sanitize_text(req.miner_name, 100),
        "mineral": _sanitize_text(req.mineral_type, 80),
        "tonnage": round(req.tonnage, 2),
        "destination": _sanitize_text(req.destination, 100),
        "vehicle": _sanitize_text(req.vehicle_reg, 40),
        "issued_at": issue_date,
        "expires_at": expiry_date,
        "verification_url": f"https://mtnspec.co.zw/mineral-hub/?verify={permit_id}"
    }
    permit_payload["hmac_signature"] = _sign_permit_payload(permit_payload)

    if pg_db.is_db_configured():
        try:
            pg_db.record_permit_to_db({
                "permit_id": permit_id,
                "claim_id": permit_payload["concession_id"],
                "mineral_type": permit_payload["mineral"],
                "tonnage_mt": permit_payload["tonnage"],
                "origin_district": "Zimbabwe",
                "destination_plant": permit_payload["destination"],
                "transporter_reg": permit_payload["vehicle"],
                "hmac_signature": permit_payload["hmac_signature"],
            })
        except Exception as e:
            print(f"[Permit DB Warn]: {e}")

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


@app.post("/api/permits/verify")
def verify_permit(payload: Dict[str, Any]):
    """Cryptographically verify an HMAC-SHA256 signed ore transit permit."""
    provided_sig = str(payload.get("hmac_signature", ""))
    if not provided_sig:
        return {"valid": False, "reason": "Missing HMAC signature"}
    expected_sig = _sign_permit_payload(payload)
    is_valid = hmac.compare_digest(provided_sig, expected_sig)
    return {
        "valid": is_valid,
        "permit_id": payload.get("permit_id"),
        "verified_at": datetime.datetime.now().isoformat()
    }


# --- SKILLS & GIG ENGINE ---
@app.get("/api/skills/courses")
def get_courses():
    return akello_service.get_courses()


@app.get("/api/skills/gigs")
def get_gigs():
    if hasattr(gig_engine, "get_open_gigs"):
        return gig_engine.get_open_gigs()
    return gig_engine.get_gigs()


@app.post("/api/skills/gigs/{gig_id}/claim")
def claim_gig(gig_id: int):
    if hasattr(gig_engine, "claim_gig"):
        success, msg = gig_engine.claim_gig(gig_id)
        return {"success": success, "message": msg}
    return {"success": True, "message": f"Field gig #{gig_id} assigned to your verified miner profile."}


# --- MODULE 3: MENTORSHIP & TALENT ECOSYSTEM ---
@app.get("/api/mentorship/mentors")
def get_mentors():
    return {"mentors": mentorship_service.get_mentors()}


@app.get("/api/mentorship/talent")
def get_talent():
    return {"talent": mentorship_service.get_talent()}


@app.get("/api/mentorship/bookings")
def get_mentor_bookings():
    return {"bookings": mentorship_service.get_bookings()}


@app.post("/api/mentorship/book")
def book_mentor(req: MentorBookingRequest):
    try:
        booking = mentorship_service.book_session(
            mentor_id=_sanitize_text(req.mentor_id, 32),
            applicant_name=_sanitize_text(req.applicant_name, 120),
            email=_sanitize_text(req.email, 120),
            topic=_sanitize_text(req.topic, 400),
            date=_sanitize_text(req.date, 32),
            time=_sanitize_text(req.time, 32),
            session_type=_sanitize_text(req.session_type or "Virtual 1-on-1", 80)
        )
        return {"success": True, "message": "Advisory session booked successfully", "booking": booking}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- LIVE POSTGIS BOREHOLES, SPATIAL ANALYTICS, AI TELEMETRY & LLM ADVISOR ---
class SpatialAdvisorRequest(BaseModel):
    target_name: str = "Selected Exploration Target"
    lat: float
    lng: float
    radius_m: int = 2500
    question: str = "Generate an executive JORC/SAMREC technical prospect appraisal for this location."


@app.get("/api/boreholes")
def get_boreholes(domain: Optional[str] = Query(None), limit: int = Query(1000, ge=1, le=5000)):
    if not pg_db.is_db_configured():
        raise HTTPException(status_code=503, detail="DATABASE_URL not configured. PostGIS required.")
    return pg_db.query_boreholes_geojson(domain=domain, limit=limit)


@app.get("/api/spatial/analyze")
def spatial_analyze(lat: float = Query(...), lng: float = Query(...), radius_m: int = Query(2500, ge=100, le=50000)):
    if not pg_db.is_db_configured():
        raise HTTPException(status_code=503, detail="DATABASE_URL not configured. PostGIS required.")
    return pg_db.analyze_spatial_target(lat=lat, lng=lng, radius_m=radius_m)


@app.get("/api/ai/telemetry")
def get_ai_telemetry():
    if not pg_db.is_db_configured():
        raise HTTPException(status_code=503, detail="DATABASE_URL not configured. PostGIS required.")
    data = pg_db.get_latest_ai_telemetry()
    if not data:
        raise HTTPException(status_code=404, detail="No AI training runs recorded in database.")
    return data


@app.post("/api/ai/advisor")
def ai_geological_advisor(req: SpatialAdvisorRequest):
    if not pg_db.is_db_configured():
        raise HTTPException(status_code=503, detail="DATABASE_URL not configured. PostGIS required.")

    spatial_ctx = pg_db.analyze_spatial_target(lat=req.lat, lng=req.lng, radius_m=req.radius_m)
    bh = spatial_ctx.get("borehole_analytics", {})
    fault = spatial_ctx.get("nearest_fault", {})
    block = spatial_ctx.get("enclosing_resource_block") or {}
    crs_arc = spatial_ctx.get("coordinates", {}).get("arc1950_utm36s", {})

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    model_used = "postgis-spatial-rag"
    answer_text = ""

    if gemini_key:
        try:
            import requests as http_requests
            system_prompt = (
                "You are the Chief Exploration Geologist & Mining Investment Advisor for MTN-SPEC (Zimbabwe). "
                "Provide concise, authoritative, JORC/SAMREC-aligned technical prospect appraisals using ONLY "
                "the verified PostGIS spatial telemetry provided. Never invent unverified drill grades."
            )
            user_prompt = (
                f"Target: {req.target_name}\n"
                f"Client Question: {req.question}\n"
                f"Verified PostGIS Spatial Context:\n{json.dumps(spatial_ctx, indent=2)}"
            )
            resp = http_requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}",
                json={
                    "contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}],
                    "generationConfig": {"temperature": 0.25, "maxOutputTokens": 650},
                },
                timeout=15,
            )
            if resp.ok:
                candidates = resp.json().get("candidates", [])
                if candidates:
                    answer_text = candidates[0]["content"]["parts"][0]["text"]
                    model_used = "gemini-2.0-flash+postgis-rag"
        except Exception as e:
            print(f"[Gemini Advisor Warn]: {e}")

    if not answer_text:
        bh_cnt = bh.get("borehole_count") or 0
        avg_rl = bh.get("avg_msz_rl_m")
        avg_depth = bh.get("avg_msz_depth_m")
        oxide_cnt = bh.get("oxide_count") or 0
        struc_cnt = bh.get("structural_fault_flags") or 0
        fault_dist = fault.get("distance_m")
        fault_name = fault.get("name") or "Mapped Structural Lineament"
        block_name = block.get("block_name") or "Outside Great Dyke Resource Block"

        answer_text = (
            f"### MTN-SPEC Technical Appraisal: {req.target_name}\n"
            f"- **Legal Projection (Arc 1950 UTM 36S):** E {crs_arc.get('easting')} m, N {crs_arc.get('northing')} m\n"
            f"- **Resource Domain:** {block_name}\n"
            f"- **Subsurface Control ({req.radius_m}m PostGIS Radius):** {bh_cnt} desurveyed drillholes intercepted"
            + (f" (Mean MSZ RL: {avg_rl} m, Mean Depth: {avg_depth} m, Oxide Holes: {oxide_cnt}, Structural Flags: {struc_cnt}).\n" if bh_cnt > 0 else ".\n")
            + f"- **Structural Risk:** Nearest fault ({fault_name}) is {fault_dist} m away.\n"
            + "- **Recommendation:** "
            + ("High subsurface confidence; prioritize fresh sulphide MSZ core logging and geotechnical bolting near structural zones." if bh_cnt > 0 else "Greenfield target outside dense Mimosa drill grid; commission Sentinel-2 B4/B2 gossan verification and preliminary trenching.")
        )

    inquiry_id = pg_db.record_advisor_inquiry(
        target_name=_sanitize_text(req.target_name, 200),
        lat=req.lat,
        lng=req.lng,
        question=_sanitize_text(req.question, 1000),
        spatial_context=spatial_ctx,
        response_text=answer_text,
        model_used=model_used,
    )

    return {
        "inquiry_id": inquiry_id,
        "model_used": model_used,
        "spatial_context": spatial_ctx,
        "appraisal": answer_text,
    }


# --- STATIC FILES FOR DASHBOARD & ASSETS ---
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.join(ROOT_DIR, "src", "dashboard")
DASHBOARD_ASSETS_DIR = os.path.join(DASHBOARD_DIR, "assets")

if os.path.exists(DASHBOARD_ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=DASHBOARD_ASSETS_DIR), name="assets")

if os.path.exists(DASHBOARD_DIR):
    app.mount("/", StaticFiles(directory=DASHBOARD_DIR, html=True), name="dashboard")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("THE NATIONAL MINERAL INTELLIGENCE HUB (BANKING-GRADE)")
    print("   Zimbabwe 2026 - MTN-SPEC Earth Observation & Mining Engine")
    print("   Serving on: http://localhost:8000")
    print("   API Docs:   http://localhost:8000/docs")
    print("=" * 60 + "\n")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
