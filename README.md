# The National Mineral Intelligence Hub | Zimbabwe 2026
> **Sovereign Earth Observation, Mineral Cadastre, Remote Sensing & Digital Mining Platform**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI / Starlette](https://img.shields.io/badge/backend-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![Leaflet GIS](https://img.shields.io/badge/mapping-Leaflet%201.9-orange.svg)](https://leafletjs.com/)
[![Sentinel-2 MSI](https://img.shields.io/badge/satellite-Sentinel--2%20MSI-blue.svg)](https://sentinel.esa.int/)
[![Google Earth Engine](https://img.shields.io/badge/GEE-Ready-teal.svg)](https://earthengine.google.com/)

---

## 💎 Project Overview
**The National Mineral Intelligence Hub** is a national-scale geospatial intelligence and digital mining platform designed for Zimbabwe's mineral sovereignty. It bridges multi-spectral satellite remote sensing, sovereign cadastre compliance, small-scale/artisanal miner empowerment, and institutional capacity building.

---

## 🏛️ The 4 Core Platform Modules

### 1. Remote Sensing & Spectral Earth Observation
- **Sentinel-2 Multi-Spectral Indices:** 10m spatial resolution monitoring across the Great Dyke, Kadoma Gold Corridor, Bikita Pegmatite Belt, and Gwanda Greenstone Complex.
- **Mineral Alteration Band Math:**
  - Iron Oxide Gossans ($B4 / B2$)
  - Clay Minerals & Hydrothermal Alteration ($B11 / B12$)
  - Ferrous Iron Silicates ($B12 / B8$)
  - Gossan Weathering Cap ($SWIR / NIR$)
  - Environmental reNDVI Biomass & Flooded Pit (WRI) monitoring
- **Field Optical Camera & Mineral Specimen Analyzer:**
  - Device camera viewfinder with HUD reticle, laser scanline animation, and GPS telemetry.
  - Automated client-side spectral reflectance breakdown (RGB channel balance, Iron Oxide ratio, Hydrothermal Alteration index).
  - Machine classification for Zimbabwean lithologies (Gossanous Ironstone, Secondary Copper Malachite, Pegmatitic Spodumene, Ultramafic Serpentinite).
  - One-click **Plot on Map** to drop ground-truth field markers.
- **Google Earth Engine (GEE) Satellite Suite:**
  - Interactive multi-temporal Sentinel-2 compositor.
  - Custom GEE App connection via URL embedding.
  - Ready-to-run Google Earth Engine JavaScript/Python script library.

### 2. Career & Skills Hub
- **Akello & Higher Life Foundation Curriculum:** Industry-standard micro-credentials for small-scale miners, geology graduates, and GIS technicians.
- **Interactive Course Pathways:** Drone Photogrammetry, Safety & Environmental Compliance, Spectral Alteration Mapping, and EcoCash FinTech Permitting.
- **Verifiable Digital Badges:** Cryptographic credentials linked to applicant profile.

### 3. Mentorship & Talent Network
- **Verified Mining Executives & Metallurgical Mentors:** Direct 1-on-1 advisory booking with senior professionals.
- **Integrated Booking Engine:** Date/time scheduling, on-site inspection requests, and subsidized session tokens.
- **Graduate Talent Pipeline:** Connects NUST and University of Zimbabwe geology & mining graduates directly with licensed concessions.

### 4. EcoCash Digital Mining Wallet & QR Cadastre
- **Instant Transit Royalty Payments:** Direct EcoCash mobile money payment integration for mining royalties, cadastre renewals, and lab assay fees.
- **Cryptographic Ground QR Permits:** Generates verifiable, tamper-evident inspection passes for mining monitors, police checkpoints, and MMCZ compliance officers.
- **Gold Backing & Currency Stabilization:** Live price tracking for the Reserve Bank of Zimbabwe (RBZ) Zimbabwe Gold (ZiG) sovereign asset-backed currency and international metal spot prices (Gold, Platinum, Palladium, Copper, Lithium).

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10 or higher
- Modern Web Browser (Chrome, Edge, Firefox, Safari)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/MTN-spec/The-National-mineral-Intelligence-Hub.git
cd "The-National-mineral-Intelligence-Hub"

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Launching the System
```bash
python api.py
```
Open your browser to:
```
http://localhost:8000/
```

### 4. Default Demo Credentials
- **Authorized Email:** `mhandutakunda@gmail.com`
- **Security Password:** `Mimosa@2030`
- *(Or use any authorized mining registry credential)*

---

## 📁 Repository Directory Structure

```
├── api.py                                 # Main FastAPI backend server & endpoints
├── boundary_service.py                    # Zimbabwean provincial, district & ward GIS boundaries
├── market_service.py                      # Live commodities (Gold, PGE, Lithium, ZiG) pricing
├── mentorship_service.py                  # Mentorship booking engine & talent database
├── requirements.txt                       # Python dependencies
├── render.yaml / vercel.json              # Cloud deployment configurations
├── generate_whatsapp_qr.py                # Script to generate presentation WhatsApp QR assets
├── whatsapp_presentation_slide.png        # 1920x1080 Full HD presentation slide
├── whatsapp_qr_takunda_mhandu.png         # Standalone 300 DPI WhatsApp QR code
├── whatsapp_qr_code.svg                   # Vector SVG QR code
├── Team_and_Organization_Artwork_...pdf   # Official Organization & Artwork Showcase Specification
├── The_National_Mineral_Intelligence_...  # Technical Architecture Specification Document
└── src/
    └── dashboard/
        ├── index.html                     # Primary Hub single-page application
        ├── app.js                         # Core GIS, camera, spectral analysis & API logic
        ├── styles.css                     # Dark-mode EOSDA/Bloomberg glassmorphism design
        └── whatsapp_presentation.html     # Live presentation contact card page
```

---

## 🌐 External Dataset Integrations
The Hub is configured to integrate with local GIS and Earth Observation datasets:
- **Rivers & Hydrology:** `F:\Datasets\DATA_SETS\Rivers - Zimbabwe (my codes)` — Alluvial drainage networks for gold placer panning.
- **Soils & Lithology:** `F:\Datasets\DATA_SETS\World Soil Data` — HWSD FAO soil and serpentine ultramafic soil layers.

---

## 👤 Lead Innovator & Project Contact
- **Lead Architect:** Takunda Nigel Mhandu
- **Institution:** National University of Science & Technology (NUST) | Earth Observation & Mineral Intelligence
- **WhatsApp / Mobile:** `+263 779 770 395` ([Chat on WhatsApp](https://wa.me/263779770395))
- **Email:** `mhandutakunda@gmail.com`
- **Presentation QR Card:** [http://localhost:8000/whatsapp_presentation.html](http://localhost:8000/whatsapp_presentation.html)

---
*The National Mineral Intelligence Hub &copy; 2026. All rights reserved. Zimbabwe Mineral Sovereignty Initiative.*
