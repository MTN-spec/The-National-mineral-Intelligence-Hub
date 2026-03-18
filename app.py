import streamlit as st
import random
import numpy as np
import matplotlib.pyplot as plt
from mineral_indices import Sentinel2Indices
from mock_services import AkelloService, EcoCashService, GigEngine
from api_gateway import EcoCashGateway, SmsService, EmailService, APILogger
from auth_service import AuthService
import pandas as pd
from streamlit_js_eval import get_geolocation
import folium
from streamlit_folium import st_folium
import matplotlib.cm as cm
import matplotlib.colors as colors
import datetime
import os

# Page Config
st.set_page_config(
    page_title="The National Mineral Intelligence Hub", 
    page_icon="⛏️", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Auth Service
import auth_service
import importlib
# Force reload to get new methods (fix for AttributeError)
importlib.reload(auth_service)
from auth_service import AuthService

if 'auth_service' not in st.session_state or 'p2p_fixed' not in st.session_state:
    st.session_state.auth_service = AuthService()
    st.session_state.p2p_fixed = True
    # Seed Admin User again just in case
    st.session_state.auth_service.seed_admin(
        "mhandutakunda@gmail.com", "Mimosa@2030", "Takunda Nigel Mhandu", "+263779770395"
    )

# Initialize Session State for Auth
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None

# ==========================================
# AUTHENTICATION FLOW
# ==========================================
if not st.session_state.authenticated:
    st.title("The National Mineral Intelligence Hub")
    st.subheader("Login to access the platform")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            user, msg = st.session_state.auth_service.login_user(email, password)
            if user:
                st.session_state.authenticated = True
                st.session_state.user = user
                st.success(f"Welcome back, {user['name']}!")
                st.rerun()
            else:
                st.error(msg)
                
    with tab2:
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_pass")
        new_name = st.text_input("Full Name", key="signup_name")
        new_phone = st.text_input("Phone Number", key="signup_phone")
        
        if st.button("Sign Up"):
            if new_email and new_password and new_name:
                success, msg = st.session_state.auth_service.register_user(new_email, new_password, new_name, new_phone)
                if success:
                    st.success("Account created! Please login.")
                else:
                    st.error(msg)
            else:
                st.warning("Please fill in all fields.")
    
    st.stop() # Stop execution if not logged in

# ==========================================
# MAIN APPLICATION (PROTECTED)
# ==========================================

# Initialize Services (using Session State to persist data)
# Initialize Services (using Session State to persist data)
# (Initialization moved to consolidated block below)

# FORCE RELOAD for Gig Engine to ensure fresh data
import importlib
import mock_services
importlib.reload(mock_services)
from mock_services import AkelloService, EcoCashService, GigEngine, MentorService, FieldDataService

try:
    from market_service import MarketIntelligenceService
except ImportError:
    # If even the file import fails, defining a dummy class locally
    class MarketIntelligenceService:
        def get_prices(self):
            import pandas as pd
            return pd.DataFrame([{"Mineral": "Service Unavailable", "Price": 0, "Change": 0, "Trend": []}])
        def get_news(self):
             return [{"title": "Service Unavailable", "link": "#", "source": "System", "date": "Now"}]

# Session State Initialization
# Check Subscription Status (placeholder function import)
# (imports are below)

# Session State Initialization (Must be before Auth Flow)
if 'init' not in st.session_state:
    st.session_state.init = True
    st.session_state.akello = AkelloService()
    st.session_state.ecocash = EcoCashService()
    st.session_state.gig_engine_board_v3 = GigEngine()
    st.session_state.mentor_service_v2 = MentorService()
    st.session_state.field_service = FieldDataService()
    st.session_state.market_service = MarketIntelligenceService()
    # Do NOT reset user/auth here if they might already exist, though 'init' check prevents double run.
    # But just in case, we initialize them only if missing.
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

# Sidebar
st.sidebar.title("Mineral Intelligence Hub")
st.sidebar.info("Connecting Youth Skills to Mining Opportunities")
st.sidebar.markdown("---")

# Use Authenticated User Details
# Use Authenticated User Details
current_user = st.session_state.user
if not current_user:
    st.info("Please log in to continue.")
    st.stop()

user_name = f"{current_user['name']} (Student Miner)"
user_phone = current_user['phone']
user_email = current_user['email']

# Custom User Image
# Custom User Image Logic
if user_email == "mhandutakunda@gmail.com":
    user_image_path = "user_profile.jpg"
else:
    # Generate unique avatar based on name for other users
    import urllib.parse
    safe_name = urllib.parse.quote(current_user['name'])
    user_image_path = f"https://ui-avatars.com/api/?name={safe_name}&background=random&size=200"

# Calculate Reputation Score based on Wallet Balance (Proxy Metric)
# In real app, we'd query a 'completed_gigs' table
reputation_points = int(st.session_state.ecocash.get_balance() * 2.5) 
star_rating = "⭐⭐⭐⭐⭐" if reputation_points > 500 else "⭐⭐⭐⭐" if reputation_points > 200 else "⭐⭐⭐"

# Check Subscription Status
if not st.session_state.user.get('is_subscribed', False):
    st.markdown("<h1 style='text-align: center; color: #00FF7F;'>🔓 Unlock Full Access</h1>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background-color: #1E1E1E; padding: 20px; border-radius: 10px; border: 1px solid #333; text-align: center;'>
        <h2>Membership Required</h2>
        <p>To access the National Mineral Intelligence Hub & Academy, a subscription is required.</p>
        <h1 style='color: white;'>$300.00 <span style='font-size: 0.5em; color: #888;'>/ month</span></h1>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💳 Pay with EcoCash")
        current_bal = st.session_state.ecocash.get_balance()
        st.metric("Your Wallet Balance", f"${current_bal:.2f}")
        
        if current_bal < 300:
            st.error("Insufficient Funds.")
            # Helper to add funds for demo
            if st.button("➕ Admin Override: Grant $300"):
                st.session_state.ecocash.pay_user(300.00, "Admin Adjustment: Subscription Credit")
                st.rerun()
        else:
            if st.button("✅ Confirm Payment ($300)", type="primary"):
                # Process Payment
                st.session_state.ecocash.charge_user(300.00, "Subscription: Monthly Access Fee")
                # Update DB
                st.session_state.auth_service.set_subscription_status(st.session_state.user['email'], True)
                # Update Session
                st.session_state.user['is_subscribed'] = True
                
                st.balloons()
                st.success("Welcome Aboard! Accessing Dashboard...")
                import time
                time.sleep(2)
                st.rerun()
                
    with col2:
        st.info("Scan to Pay (Alternative)")
        # Show a static QR for simulation
        st.image("ecocash_logo.png", width=150, caption="Merchant Code: 112233")
        
    st.stop() # Stop execution here until subscribed

# Sidebar Profile
st.sidebar.image(user_image_path, width=120)
st.sidebar.markdown(f"<h2 style='text-align: center; color: #00FF7F;'>👤 {user_name}</h2>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h3 style='text-align: center; color: #00FF7F;'>🏆 {reputation_points} XP</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h2 style='text-align: center;'>{star_rating}</h2>", unsafe_allow_html=True)
st.sidebar.markdown(f"<p style='text-align: center;'>📱 {user_phone}</p>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h3 style='text-align: center; color: #00FF7F;'>💰 ${st.session_state.ecocash.get_balance():.2f}</h3>", unsafe_allow_html=True)

if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()

st.sidebar.markdown("---")

# Navigation
page = st.sidebar.radio(
    "Navigate", 
    ["🏠 Home", "🛰️ Remote Sensing Satellite Imagery Data", "💼 Career & Skills Hub", "🎓 Mentorship & Talent", "💳 EcoCash Wallet"]
)
# ==========================================
# HOME PAGE
# ==========================================
if page == "🏠 Home":
    st.markdown("<h1 style='text-align: center; color: #00FF7F; text-shadow: 2px 2px 4px #000000;'>The National Mineral Intelligence Hub 🇿🇼</h1>", unsafe_allow_html=True)
    
    # Function to set background
    import base64
    def set_bg_hack(main_bg):
        # ... (keep existing background logic) ...
        main_bg_ext = "jpg"
        st.markdown(
            f"""
            <style>
            .stApp {{
                background: url(data:image/{main_bg_ext};base64,{base64.b64encode(open(main_bg, "rb").read()).decode()});
                background-size: cover;
                background-attachment: fixed;
            }}
             /* Global Text Color Fix for Dark Overlay */
            .main .block-container {{
                background-color: rgba(10, 10, 20, 0.85); 
                border-radius: 15px;
                padding: 30px;
                margin-top: 20px;
            }}
            h1, h2, h3, h4 {{ color: #00FF7F !important; text-shadow: 1px 1px 2px black; }}
            p, label, .stMarkdown {{ color: #E0FFFF !important; }}
            .metric-card {{
                background-color: #222;
                border: 1px solid #444;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                margin-bottom: 10px;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

    try:
        if os.path.exists('mining_background_final.jpg'):
            set_bg_hack('mining_background_final.jpg')
        else:
             st.info("Background image not found, skipping.")
    except Exception:
        pass

    # --- LIVE DASHBOARD CONTENT ---
    
    st.markdown("### 📊 Live Mineral Markets (Zimbabwe & Global)")
    
    # 1. MARKET DATA
    if 'market_service' not in st.session_state:
        st.session_state.market_service = MarketIntelligenceService()
        
    with st.spinner("Fetching Live Market Data..."):
        df_prices = st.session_state.market_service.get_prices()
    
    # Display Ticker Tape (Top 5 visible, others in expander or scroll)
    # create 5 columns
    cols = st.columns(5)
    for index, row in df_prices.head(5).iterrows():
        with cols[index]:
            delta_color = "normal" if row['Change'] > 0 else "inverse"
            st.metric(label=row['Mineral'], value=f"${row['Price']:,.2f}", delta=f"{row['Change']:.2f}%")
            
    with st.expander("View All Mineral Prices"):
         st.dataframe(df_prices.style.format({"Price": "${:,.2f}", "Change": "{:.2f}%"}))

    st.divider()

    # 2. SPLIT VIEW: CHARTS & NEWS
    c_chart, c_news = st.columns([2, 1])
    
    with c_chart:
        st.subheader("📈 Price Trends")
        selected_mineral = st.selectbox("Select Mineral to Analyze", df_prices['Mineral'].unique())
        
        # Get trend data for selected
        mineral_data = df_prices[df_prices['Mineral'] == selected_mineral].iloc[0]
        trend_prices = mineral_data['Trend']
        
        # Simple Line Chart
        chart_data = pd.DataFrame({
            "Day": ["T-4", "T-3", "T-2", "T-1", "Now"],
            "Price": trend_prices
        })
        st.line_chart(chart_data.set_index("Day"))
        st.caption(f"5-Day Trend for {selected_mineral}")

    with c_news:
        st.subheader("📰 Live Mining News")
        news_items = st.session_state.market_service.get_news()
        
        for item in news_items:
            with st.container(border=True):
                st.markdown(f"**[{item['title']}]({item['link']})**")
                st.caption(f"{item['source']} • {item['date']}")

# (Section Moved to Job Board)

# ==========================================
# MINERAL PROSPECTOR TAB (Redesigned GIS Layout)
# ==========================================
# ==========================================
# MINERAL PROSPECTOR TAB (Fixed GIS Layout)
# ==========================================
elif page == "🛰️ Remote Sensing Satellite Imagery Data":
    
    # --- GEE IMPORT & INITIALIZATION ---
    import ee
    import json
    from google.oauth2 import service_account
    
    def initialize_gee():
        """Initializes Earth Engine safely with robust credential handling."""
        # 1. Try standard initialization (Local Auth)
        try:
            ee.Initialize()
            return True
        except Exception:
            pass # Fall through to Secrets Auth

        # 2. Try Secrets Auth
        if "gcp_service_account" in st.secrets:
            try:
                # Convert Secrets object to standard dict
                service_account_info = dict(st.secrets["gcp_service_account"])
                
                # Fix Private Key formatting (common streamlit secrets issue)
                if "\\n" in service_account_info["private_key"]:
                    service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")
                
                # Create Credentials using google-auth (Modern Way)
                creds = service_account.Credentials.from_service_account_info(service_account_info)
                ee.Initialize(credentials=creds)
                return True
            except Exception as e:
                st.error(f"GEE Auth Failed with Secrets: {e}")
                st.write(f"Key ID present: {service_account_info.get('private_key_id', 'N/A')}")
                return False
        else:
            st.warning("GEE Not Authenticated. Access restricted.")
            st.info(f"Detected Secret Sections: {list(st.secrets.keys())}")
            st.markdown("Please ensure `[gcp_service_account]` exists in `.streamlit/secrets.toml`.")
            return False

    gee_ready = initialize_gee()
    
    def add_ee_layer_to_folium(folium_map, ee_image, vis_params, name):
        """Add a Google Earth Engine image layer to a folium map using getMapId."""
        try:
            map_id_dict = ee.Image(ee_image).getMapId(vis_params)
            folium.TileLayer(
                tiles=map_id_dict['tile_fetcher'].url_format,
                attr='Google Earth Engine',
                name=name,
                overlay=True,
                control=True,
                opacity=0.9
            ).add_to(folium_map)
        except Exception as e:
            st.warning(f"Could not add GEE layer '{name}': {e}")
    
    # Custom CSS for Fixed 100vh Layout
    st.markdown("""
    <style>
    /* 1. Force Full Screen & Remove Scroll */
    .appview-container .main .block-container {
        padding: 0rem !important;
        margin: 0rem !important;
        max-width: 100%;
        overflow: hidden; /* Prevent body scroll */
    }
    footer {display: none !important;}
    
    /* 2. Map Container Adjustment */
    iframe {
        height: 100vh !important; /* Force map to take full viewport height */
    }
    
    /* 3. Compact Right Panel Styling */
    .scene-card {
        border: 1px solid #444; border-radius: 4px; padding: 8px; margin-bottom: 5px; background: #222;
        cursor: pointer; transition: 0.2s; font-size: 0.9em;
    }
    .scene-card:hover { border-color: #00FF7F; background: #333; }
    
    /* 4. Floating Action Button for Field Data */
    .fab-container {
        position: fixed; bottom: 30px; left: 30px; z-index: 9999;
    }
    </style>
    """, unsafe_allow_html=True)

    # Defaults
    default_center = [-20.32, 30.06]

    # MAIN LAYOUT: Map (Left 5) | Data Panel (Right 1.5)
    col_map, col_right = st.columns([5, 1.5], gap="small")
    
    # --- RIGHT PANEL (COMPACT TABS) ---
    with col_right:
        # Base Map Selector (Above tabs for better accessibility)
        st.caption("🗺️ Base Map")
        base_map_choice = st.selectbox(
            "Choose Layer",
            ["🛰️ Satellite (Esri)", "🗺️ OpenStreetMap", "🌍 CartoDB Positron", "🌑 CartoDB Dark"],
            index=0,
            help="Select base map - changes apply immediately",
            key="base_map_selector"
        )
        st.divider()
        
        # Use Tabs to save vertical space
        tab_layers, tab_tools, tab_info = st.tabs(["Layers", "Tools", "Info"])
        
        with tab_layers:
            st.caption("Active Imagery")
            # Search
            with st.expander("📍 Search", expanded=False):
                 st.text_input("Place", placeholder="Search...")
            
            with st.expander("📍 Search Location"):
                 loc_search = st.text_input("Place Name")
            
            if not gee_ready:
                st.error("⚠️ Earth Engine not connected. Real data unavailable.")
                scenes = []
            else:
                # REAL GEE DATA QUERY
                roi = ee.Geometry.Point([default_center[1], default_center[0]])
                
                # Filter Sentinel-2
                collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                              .filterBounds(roi)
                              .filterDate(datetime.datetime.now() - datetime.timedelta(days=30), datetime.datetime.now())
                              .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                              .sort('system:time_start', False)
                              .limit(5))
                
                # Fetch metadata client-side
                try:
                    features = collection.getInfo()['features']
                    scenes = []
                    for f in features:
                        props = f['properties']
                        date = datetime.datetime.fromtimestamp(props['system:time_start']/1000).strftime('%d %b %Y')
                        cid = f['id']
                        scenes.append({
                            "date": date,
                            "cloud": f"{props['CLOUDY_PIXEL_PERCENTAGE']:.1f}%",
                            "sensor": "Sentinel-2 L2A",
                            "id": cid,
                            "ee_obj": f
                        })
                except Exception as e:
                    st.warning(f"Could not fetch GEE scenes: {e}")
                    scenes = [] # Fail gracefully if query fails
            
            if not scenes and gee_ready:
                st.info("No recent cloud-free images found.")
            
            # Scene Selector
            sel_id = None
            if scenes:
                sel_id = st.radio("Select Scene", [s["id"] for s in scenes], label_visibility="collapsed", format_func=lambda x: "")
            else:
                st.radio("Select Scene", [], label_visibility="collapsed")
            
            selected_scene_meta = next((s for s in scenes if s['id'] == sel_id), None)

            # Render Cards
            for s in scenes:
                color = "#00FF7F" if sel_id == s['id'] else "#555"
                st.markdown(f"""
                <div class='scene-card' style='border-left: 3px solid {color};'>
                    <b>{s['date']}</b> <span style='float:right; color:#888'>{s['sensor']}</span><br>
                    <span style='font-size:0.8em; color:#aaa'>☁️ {s['cloud']}</span>
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()
            st.caption("Overlay Layers")
            show_gt = st.checkbox("Ground Truth Points", value=True)

        with tab_tools:
            st.caption("Advanced Processing")
            
            # 1. Select Data Type
            sensor_type = st.selectbox("Sensor Class", 
                ["🌈 Multispectral (Optical)", "📡 Radar (SAR)", "🧠 AI Models"],
                help="Select the type of remote sensing data to analyze.")
            
            vis_params = {}
            ee_layer = None
            layer_name = "Selection"

            # 2. Dynamic Analysis Options
            if "Multispectral" in sensor_type:
                ms_category = st.radio("Target", ["Visual (RGB)", "Mineral Alteration", "Vegetation & Health"], horizontal=True, label_visibility="collapsed")
                
                if ms_category == "Visual (RGB)":
                     index_choice = "True Color"
                elif ms_category == "Mineral Alteration":
                    index_choice = st.selectbox("Index", ["Iron Oxide", "Ferrous Iron", "Clay Minerals", "Gossan Zone"])
                else:
                    index_choice = st.selectbox("Index", ["NDVI", "SAVI", "Moisture Index"])
            
            elif "Radar" in sensor_type:
                sar_mode = st.selectbox("Mode", ["Roughness (VV/VH)", "Structure/Lineaments"])
                index_choice = f"SAR: {sar_mode}"
                
            elif "AI Models" in sensor_type:
                ai_model = st.selectbox("Model", ["Land Cover Classification (ESA WorldCover)", "Mineral Potential Heatmap"])
                index_choice = f"AI: {ai_model}"

            st.divider()
             
            if st.button("⚡ Run Processing", type="primary", use_container_width=True):
                 if not gee_ready:
                     st.error("Cannot run processing: Earth Engine not connected.")
                 elif not selected_scene_meta:
                     st.warning("Please select an image scene first.")
                 else:
                     st.session_state.trigger_analysis = True
                     st.session_state.current_analysis = {
                         "sensor": sensor_type,
                         "method": index_choice,
                         "scene_id": sel_id
                     }
                     st.rerun()

        with tab_info:
            if gee_ready:
                st.success("✅ GEE Connected")
            else:
                st.error("❌ GEE Disconnected")
            
            if 'current_analysis' in st.session_state and st.session_state.current_analysis:
                st.subheader("Last Analysis:")
                st.json(st.session_state.current_analysis)
            else:
                st.info("No analysis run yet.")


    # --- LEFT PANEL (FOLIUM MAP with GEE Tile Layers) ---
    with col_map:
        # Determine which base layer to use
        if "Satellite" in base_map_choice:
            m = folium.Map(
                location=default_center, 
                zoom_start=12,
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attr='Esri World Imagery'
            )
        elif "OpenStreetMap" in base_map_choice:
            m = folium.Map(location=default_center, zoom_start=12, tiles='OpenStreetMap')
        elif "Positron" in base_map_choice:
            m = folium.Map(location=default_center, zoom_start=12, tiles='CartoDB positron')
        else:  # Dark
            m = folium.Map(location=default_center, zoom_start=12, tiles='CartoDB dark_matter')
        
        # Add alternative base layers for easy switching
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri World Imagery',
            name='🛰️ Satellite',
            overlay=False,
            control=True
        ).add_to(m)
        
        folium.TileLayer(
            tiles='OpenStreetMap',
            name='🗺️ OpenStreetMap',
            overlay=False,
            control=True
        ).add_to(m)
        
        folium.TileLayer(
            tiles='CartoDB positron',
            name='🌍 Positron (Light)',
            overlay=False,
            control=True
        ).add_to(m)
        
        folium.TileLayer(
            tiles='CartoDB dark_matter',
            name='🌑 Dark Matter',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Add Roads/Labels overlay for satellite view
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}',
            attr='Esri Transportation',
            name='🛣️ Roads & Labels',
            overlay=True,
            control=True,
            opacity=0.8
        ).add_to(m)
        
        # Add GEE Earth Engine layer if scene is selected
        if gee_ready and selected_scene_meta:
            img = ee.Image(selected_scene_meta['id'])
            
            # PROCESSING LOGIC
            active_analysis = st.session_state.get("current_analysis", {})
            method = active_analysis.get("method", "True Color")
            
            final_layer = img  # Default
            v_params = {"bands": ['B4', 'B3', 'B2'], "min": 0, "max": 3000}  # Default RGB
            
            if method == "True Color":
                final_layer = img
                v_params = {"bands": ['B4', 'B3', 'B2'], "min": 0, "max": 3000}
                
            elif method == "NDVI":
                final_layer = img.normalizedDifference(['B8', 'B4']).rename('NDVI')
                v_params = {"min": -0.2, "max": 0.8, "palette": ['red', 'yellow', 'green']}
                
            elif method == "Iron Oxide":
                final_layer = img.expression("b('B4') / b('B2')").rename('Iron_Oxide')
                v_params = {"min": 1, "max": 3, "palette": ['blue', 'yellow', 'red']}
                
            elif method == "Ferrous Iron":
                final_layer = img.expression("b('B11') / b('B8')").rename('Ferrous_Iron')
                v_params = {"min": 0.5, "max": 2, "palette": ['blue', 'cyan', 'yellow', 'red']}

            elif method == "Clay Minerals":
                final_layer = img.expression("b('B11') / b('B12')").rename('Clay_Minerals')
                v_params = {"min": 1, "max": 3, "palette": ['gray', 'yellow', 'orange']}
                
            elif method == "Gossan Zone":
                iron_oxide = img.expression("b('B4') / b('B2')")
                clay_minerals = img.expression("b('B11') / b('B12')")
                final_layer = iron_oxide.add(clay_minerals).rename('Gossan_Index')
                v_params = {"min": 2, "max": 6, "palette": ['blue', 'green', 'yellow', 'red']}

            elif method == "SAVI":
                L = ee.Number(0.5)
                final_layer = img.expression(
                    '((NIR - RED) / (NIR + RED + L)) * (1 + L)', {
                        'NIR': img.select('B8'),
                        'RED': img.select('B4'),
                        'L': L
                    }).rename('SAVI')
                v_params = {"min": -0.2, "max": 0.8, "palette": ['brown', 'yellow', 'green']}

            elif method == "Moisture Index":
                final_layer = img.normalizedDifference(['B8', 'B11']).rename('NDMI')
                v_params = {"min": -1, "max": 1, "palette": ['brown', 'white', 'blue']}
                
            elif "AI" in method:
                try:
                    roi = ee.Geometry.Point([default_center[1], default_center[0]])
                    final_layer = ee.ImageCollection("ESA/WorldCover/v100").filterBounds(roi).first()
                    v_params = {"bands": ["Map"]}
                    method = "ESA WorldCover"
                except Exception as e:
                    st.warning(f"Could not load AI model data: {e}")
                    final_layer = img
                    v_params = {"bands": ['B4', 'B3', 'B2'], "min": 0, "max": 3000}
                    method = "True Color (Fallback)"
            
            # Add the GEE layer to folium map using getMapId
            add_ee_layer_to_folium(m, final_layer, v_params, method)
        
        # Add field markers if available
        if 'field_service' in st.session_state and show_gt:
            for sub in st.session_state.field_service.submissions:
                folium.Marker(
                    [sub['lat'], sub['lon']], 
                    popup=sub['desc'], 
                    icon=folium.Icon(color="green", icon="info-sign")
                ).add_to(m)
        
        # Add Layer Control to the map
        folium.LayerControl(position='topright', collapsed=False).add_to(m)
        
        # Render folium map
        st_folium(m, height=850, width=None)


        # --- FLOATING ACTION BUTTON ---
        with st.expander("📝 Log Field Observation", expanded=False):
             with st.form("fab_log"):
                 c1, c2 = st.columns(2)
                 lat = c1.number_input("Lat", value=-20.30)
                 lon = c2.number_input("Lon", value=30.00)
                 desc = st.text_input("Observation")
                 
                 # Camera Input (Restored)
                 img_buffer = st.camera_input("Take a Photo")
                 
                 if st.form_submit_button("Submit Point"):
                     st.session_state.field_service.add_submission(lat, lon, desc, img_buffer, user_name)
                     st.rerun()

# ==========================================
# JOB BOARD TAB
# ==========================================
elif page == "💼 Career & Skills Hub":
    st.title("💼 Career & Skills Hub") 
    
    # Create Tabs for Jobs and Learning
    tab_jobs, tab_learn = st.tabs(["💼 Gig Opportunities", "📚 Akello Mining Academy"])

    with tab_jobs:
        st.markdown("Earn income by completing **Ground Truthing** or **Online Freelance** tasks.")
        
        # Session state to track active gig
        if 'active_gig' not in st.session_state:
            st.session_state.active_gig = None
            
        gigs = st.session_state.gig_engine_board_v3.get_gigs()
        
        if st.session_state.active_gig is None:
            # LIST VIEW
            for gig in gigs:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.subheader(gig['title'])
                        st.info(f"📍 {gig.get('location', 'N/A')} | 💰 Reward: **${gig['reward']}** | 🏷️ Type: {gig.get('type', 'Standard')}")
                    with c2:
                        if st.button(f"View Briefing", key=f"btn_{gig['id']}"):
                            st.session_state.active_gig = gig
                            st.rerun()
        else:
            # DETAILED VIEW & WORKFLOW
            gig = st.session_state.active_gig
            st.button("← Back to Jobs", on_click=lambda: st.session_state.update(active_gig=None))
            
            st.divider()
            st.header(f"🚀 {gig['title']}")
            st.markdown(f"**Reward:** ${gig['reward']} | **Location:** {gig['location']}")
            
            with st.container(border=True):
                st.subheader("📋 Mission Briefing")
                st.write(gig['briefing'])
                
            st.subheader("✍️ Submit Work & Proof")
            st.markdown("To complete this gig, you must answer the validation question correctly. Our **AI Agent** will grade your response immediately.")
            
            user_answer = st.text_area("Your Response / Findings:", placeholder="Type your answer here based on the briefing...")
            
            if st.button("Submit Work for AI Grading"):
                if not user_answer:
                    st.warning("Please provide an answer first.")
                else:
                    with st.spinner("🤖 AI Agent is analyzing your submission..."):
                        import time
                        time.sleep(2) # Simulate AI thinking
                        
                        # AUTOMATED GRADING SYSTEM
                        keywords = gig['expected_answer'].lower().split()
                        user_text = user_answer.lower()
                        
                        passed = False
                        if "csv" in keywords and "csv" in user_text: passed = True
                        elif "red" in keywords and ("red" in user_text or "rust" in user_text): passed = True
                        elif "swir" in keywords and "swir" in user_text: passed = True
                        elif "shapefile" in keywords and ("shapefile" in user_text or "shp" in user_text): passed = True
                        elif "toxic" in keywords and ("toxic" in user_text or "health" in user_text or "poison" in user_text): passed = True
                        
                        score = 0
                        if passed:
                            score = random.randint(85, 100)
                        else:
                            score = random.randint(20, 50)
                            
                        if score >= 80:
                            st.balloons()
                            st.success(f"✅ **PASSED!** AI Grade: {score}/100")
                            st.markdown(f"> **AI Feedback:** Excellent work! Your response matched the verification criteria.")
                            
                            # Process Payment
                            st.session_state.ecocash.pay_user(gig['reward'], f"Gig Payment: {gig['title']}")
                            SmsService.send_sms(user_phone, f"You earned ${gig['reward']}! New Balance: ${st.session_state.ecocash.get_balance():.2f}")
                            
                            st.success("💰 Payment Disbursed to EcoCash Wallet.")
                            
                            # Reset
                            if st.button("Complete & Find More Work"):
                                st.session_state.active_gig = None
                                st.rerun()
                        else:
                            st.error(f"❌ **FAILED.** AI Grade: {score}/100")
                            st.markdown(f"> **AI Feedback:** Your response did not meet the criteria. Hint: {gig['ai_grading_prompt']}")
                            st.warning("Please review the briefing and try again.")

    with tab_learn:
        st.header("📚 Mining Academy")
        st.markdown("Upskill yourself to unlock high-paying gigs. **New: Downloadable Guides**")

        if 'active_module' not in st.session_state:
            st.session_state.active_module = None

        if st.session_state.active_module is None:
            # === LIST VIEW ===
            # === Existing Akello Courses ===
            courses = st.session_state.akello.get_courses()
            
            col1, col2 = st.columns(2)
            for idx, course in enumerate(courses):
                with (col1 if idx % 2 == 0 else col2):
                    with st.container(border=True):
                        # Icon based on type
                        icon = "📄" if course['title'].endswith(('.pdf', '.docx')) else "🎓"
                        st.subheader(f"{icon} {course['title']}")
                        st.write(f"**XP:** {course['xp']} | **Type:** {course['duration']}")
                        status = course['status']
                        
                        if status == "In Progress":
                            if st.button(f"Continue Learning #{course['id']}"):
                                st.success("Module Loaded... (Simulation)")
                                done, xp = st.session_state.akello.complete_course(course['id'])
                                if done:
                                    EmailService.send_email(user_email, "Course Completed!", f"Well done Tino! You earned {xp} XP.")
                                    st.rerun()
                        elif status == "Locked":
                            st.button(f"Unlock (Requires Prerequisites)", disabled=True, key=f"lock_{course['id']}")
                        elif status == "Available":
                            # Logic for Interactive Learning
                            if st.button(f"🎓 Start Module", key=f"start_{course['id']}"):
                                st.session_state.active_module = course
                                st.rerun()
                        else:
                            st.success("Completed ✅")

        # === Active Module View ===
        if 'active_module' in st.session_state and st.session_state.active_module:
            module = st.session_state.active_module
            st.divider()
            
            # Header
            c1, c2 = st.columns([4, 1])
            with c1:
                st.header(f"📖 {module['title']}")
                st.caption("AI-Powered Learning Mode")
            with c2:
                if st.button("❌ Close", type="secondary"):
                    st.session_state.active_module = None
                    st.rerun()

            # Mock Document Viewer
            with st.container(border=True):
                st.markdown(f"### 📄 Document Content: {module['title']}")
                st.info("Displaying document content... (Simulated viewer for .docx/.pdf)")
                # In a real version, we'd use pdfjs or mammoth to render the doc here
                st.markdown("""
                *Sustainable Mining Practices - Chapter 1*
                
                Mining is a critical industry for economic development, but it must be balanced with environmental stewardship. 
                Before breaking ground, one must understand the geological implications and legal requirements defined by the EMA...
                
                [... Content continues ...]
                """)
            
            # AI Tutor Section
            st.markdown("---")
            st.subheader("🤖 AI Tutor: Knowledge Check")
            st.markdown("I have analyzed this document. Creating a validation question for you...")
            
            # Generate Question based on keywords in title
            question = "What is the primary focus of this module?"
            if "Safety" in module['title'] or "SHEQ" in module['title']:
                question = "List three critical PPE items required for underground safety mentioned in this text."
                hint = "Think about head, respiratory, and foot protection."
            elif "Legal" in module['title'] or "Law" in module['title']:
                question = "Which government body is responsible for environmental compliance certificates?"
                hint = "It's a three-letter acronym starting with E."
            elif "GPS" in module['title']:
                question = "Explain the difference between a Waypoint and a Track in GPS usage."
                hint = "One is a point, the other is a path."
            else:
                question = "Summarize the key takeaway of this module in one sentence."
                hint = "Focus on the main topic title."
                
            st.write(f"**Q: {question}**")
            
            answer = st.text_area("Your Answer:", key=f"ans_{module['id']}")
            
            if st.button("Submit Answer", key=f"sub_{module['id']}"):
                with st.spinner("AI is grading your understanding..."):
                    import time
                    time.sleep(1.5)
                    
                    # Mock Grading
                    if len(answer) > 10:
                        st.balloons()
                        st.success(f"✅ Correct! You demonstrated good understanding.")
                        st.markdown(f"> **AI Comment:** Good job! You captured the essence of *{module['title']}*.")
                        
                        # Award XP
                        st.session_state.akello.complete_course(module['id'])
                        SmsService.send_sms(user_phone, f"Akello: Module '{module['title'][:20]}...' Completed! +{module['xp']} XP")
                        
                        if st.button("Finish & Return"):
                            st.session_state.active_module = None
                            st.rerun()
                    else:
                        st.error("❌ Too short. Please provide a more detailed answer.")
                        st.info(f"Hint: {hint}")

# ==========================================
# MENTORSHIP TAB
# ==========================================
elif page == "🎓 Mentorship & Talent":
    st.title("🎓 Mentorship & Talent Hub")
    st.markdown("Connect with industry experts, find mentors, and grow your career in mining.")
    
    mentors = st.session_state.mentor_service_v2.get_mentors()
    
    # Filter
    expertise_filter = st.selectbox("Filter by Expertise", ["All", "Exploration Geology", "Mining Engineering", "EIA & Sustainability", "Remote Sensing & Mapping"])
    
    filtered_mentors = mentors
    if expertise_filter != "All":
        filtered_mentors = [m for m in mentors if m['expertise'] == expertise_filter]
    
    for mentor in filtered_mentors:
        with st.container(border=True):
            cols = st.columns([1, 4])
            with cols[0]:
                st.image(mentor['image'], width=100)
            with cols[1]:
                st.subheader(f"{mentor['name']}")
                st.caption(f"**{mentor.get('organization', 'Independent')}** | {mentor['role']}")
                st.write(f"**Expertise:** {mentor['expertise']}")
                st.write(f"📝 {mentor['bio']}")
                
                c_a, c_b = st.columns([1, 3])
                with c_a:
                    st.success(f"**{mentor['rate']}**")
                
                with c_b:
                    if st.button(f"Request Session", key=f"mentor_{mentor['id']}"):
                        # Contact Form Modal (expander for simplicity)
                        with st.expander("✉️ Send Connection Request", expanded=True):
                            msg_text = st.text_area("Message", f"Hello {mentor['name'].split(' ')[-1]}, I am interested in mentorship regarding...")
                            if st.button("Send Request", key=f"snd_{mentor['id']}"):
                                with st.spinner("Dispatching request..."):
                                    EmailService.send_email(user_email, "Mentorship Request Sent", f"Request sent to {mentor['name']}. Message: {msg_text}")
                                    st.success("Request Sent! The mentor will contact you shortly.")

# ==========================================
# WALLET TAB
# ==========================================
elif page == "💳 EcoCash Wallet":
    # st.title("💳 EcoCash Wallet")
    st.image("ecocash_logo.png", width=300)
    
    balance = st.session_state.ecocash.get_balance()
    st.metric("Current Balance", f"${balance:.2f}", "+20.00 today")
    
    st.subheader("Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # QR PAY LOGIC
        with st.popover("Scan QR (Pay)", use_container_width=True):
            st.markdown("### 📷 Scan Merchant Code")
            
            # Helper: Show QR Code
            with st.expander("Show Test Merchant QR"):
                st.image("supermarket_qr.png", caption="Scan this code (TM Pick n Pay - $20)")
            
            # Camera Input
            qr_image = st.camera_input("Point camera at QR Code")
            
            if qr_image is not None:
                # In a real app, we would decode the QR here using cv2 or pyzbar
                # Assuming camera detected validating QR code
                
                with st.spinner("Decoding..."):
                    import time
                    time.sleep(1.5) # Processing Transaction
                    
                st.success("✅ **TM Pick n Pay** Detected")
                st.metric("Amount to Pay", "$20.00")
                
                if st.button("Confirm Payment ($20.00)"):
                    current_balance = st.session_state.ecocash.get_balance()
                    if current_balance >= 20.00:
                        st.session_state.ecocash.charge_user(20.00, "QR Payment: TM Pick n Pay")
                        st.balloons()
                        st.success("Payment Successful! Receipt ID: INV-882193-X")
                        SmsService.send_sms(user_phone, "EcoCash: Paid $20.00 to TM Pick n Pay. Txn: INV-882193-X")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("Insufficient Funds!")
                
    with col2:
        # P2P Transfer Logic
        with st.popover("Send Money (P2P)", use_container_width=True):
            st.markdown("### 💸 Send to Peer")
            
            # Fetch Peers
            all_users = st.session_state.auth_service.get_all_users()
            # Filter out current user
            peers = [u for u in all_users if u['id'] != st.session_state.user['id']]
            
            if not peers:
                st.warning("No other users found.")
            else:
                peer_map = {f"{p['name']} ({p['phone']})": p for p in peers}
                selected_peer_name = st.selectbox("Select Recipient", list(peer_map.keys()))
                selected_peer = peer_map[selected_peer_name]
                
                amount = st.number_input("Amount ($)", min_value=1.0, max_value=1000.0, step=1.0)
                
                if st.button("Confirm Send"):
                    current_balance = st.session_state.ecocash.get_balance()
                    if current_balance >= amount:
                        # Deduct from Sender
                        st.session_state.ecocash.charge_user(amount, f"P2P Sent to {selected_peer['name']}")
                        # In a real app, we would add to recipient's wallet here. 
                        # For simulation, we assume success.
                        st.success(f"Sent ${amount} to {selected_peer['name']}!")
                        st.rerun()
                    else:
                        st.error("Insufficient Funds")
    with col3:
        st.button("Cash Out", use_container_width=True)
        
    st.subheader("Transaction History")
    for txn in st.session_state.ecocash.transactions:
        color = "green" if txn['type'] == "credit" else "red"
        st.markdown(f"**{txn['date']}** - {txn['desc']} : <span style='color:{color}'>${abs(txn['amount']):.2f}</span>", unsafe_allow_html=True)

# ==========================================
# DEVELOPER CONSOLE (API DEBUGGER) - HIDDEN
# ==========================================
# st.markdown("---")
# with st.expander("👨‍💻 Developer Console (API Gateway Logs)"):
#     st.caption("Live monitoring of API calls to EcoCash, SMS Gateway, and SMTP Server.")
#     if st.button("Clear Logs"):
#         APILogger.logs = []
#         
#     for log in APILogger.logs:
#         st.markdown(f"**[{log['timestamp']}] {log['service']} - {log['method']} {log['url']}**")
#         c1, c2 = st.columns(2)
#         with c1:
#             st.json(log['payload'], expanded=False)
#         with c2:
#             st.json(log['status'], expanded=False)
#             st.json(log['response'], expanded=False)
#         st.divider()
