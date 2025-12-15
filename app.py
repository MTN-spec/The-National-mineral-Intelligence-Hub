import streamlit as st
import random
import numpy as np
import matplotlib.pyplot as plt
from mineral_indices import Sentinel2Indices
from mock_services import AkelloService, EcoCashService, GigEngine
from api_gateway import EcoCashGateway, SmsService, EmailService, APILogger
from auth_service import AuthService
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from streamlit_js_eval import get_geolocation
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
import matplotlib.cm as cm
import matplotlib.colors as colors

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
    st.markdown("""
    <h3 style='text-align: center; color: #00FF7F;'>Empowering the Next Generation of Digital Miners.</h3>
    <p style='text-align: center; font-size: 1.1em;'>This platform integrates specific indices for mineral detection with a skills-to-earning framework.</p>
    """, unsafe_allow_html=True)
    
    # Content Image (Centered & Sizable)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.image("content_image.png", use_container_width=True)
        # Vivid Green for the caption
        st.markdown("<h3 style='text-align: center; color: #00FF7F; text-shadow: 2px 2px 4px #000000;'>Leadership in Mineral Development</h3>", unsafe_allow_html=True)

    # Function to set background
    import base64
    def set_bg_hack(main_bg):
        '''
        A function to unpack an image from root folder and set as bg.
        The bg will be static and cover the full screen.
        '''
        # set bg name
        main_bg_ext = "jpg"
            
        st.markdown(
            f"""
            <style>
            .stApp {{
                background: url(data:image/{main_bg_ext};base64,{base64.b64encode(open(main_bg, "rb").read()).decode()});
                background-size: cover;
                background-attachment: fixed;
            }}
            /* Center all text on the main page */
            .main .block-container {{
                text-align: center;
                background-color: rgba(0, 0, 0, 0.6); /* Semi-transparent dark overlay for readability */
                border-radius: 15px;
                padding: 20px;
                margin-top: 50px;
            }}
            
            /* GLOBAL TEXT COLORING - VIVID GREEN THEME */
            h1, h2, h3, h4, h5, h6 {{
                color: #00FF7F !important; /* SpringGreen */
                text-shadow: 1px 1px 2px black;
            }}
            
            p, li, label, .stMarkdown, .stText {{
                color: #E0FFFF !important; /* LightCyan for readability */
                font-weight: 500;
            }}
            
            /* Sidebar Text */
            [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {{
                color: #00FF7F !important;
            }}
            
            /* Specific fix for lists to look decent centered */
            ul {{
                display: inline-block;
                text-align: left;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

    try:
        set_bg_hack('mining_background_final.jpg')
    except Exception as e:
        st.warning(f"Could not load background image: {e}")
        st.image("mining_background.jpg")

# (Section Moved to Job Board)

# ==========================================
# MINERAL PROSPECTOR TAB (Redesigned GIS Layout)
# ==========================================
elif page == "🛰️ Remote Sensing Satellite Imagery Data":
    
    # Custom CSS for the GIS Look & Full Screen
    st.markdown("""
    <style>
    /* Maximize Screen Real Estate */
    .appview-container .main .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .scene-card {
        border: 1px solid #444;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
        background-color: #222;
        cursor: pointer;
    }
    .scene-card:hover {
        border-color: #00FF7F;
        background-color: #2b2b2b;
    }
    .scene-meta {
        font-size: 0.8em;
        color: #aaa;
    }
    .stButton button {
        width: 100%;
    }
    /* Hide the full-screen button on images inside cards */
    button[title="View fullscreen"] {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header Overlay (could be improved, but sticking to standard structure for now)
    # st.title("🛰️ Remote Sensing Studio") # Optional: remove title to save space? Keeping it for nav clarity.

    # MAIN LAYOUT: Map (Left 3) | Data Panel (Right 1)
    col_map, col_right = st.columns([3, 1])
    
    # --- RIGHT PANEL (DATA & SETTINGS) ---
    with col_right:
        st.subheader("Imagery & Layers")
        
        # 1. Search / Location
        with st.expander("📍 Location Search", expanded=True):
             st.text_input("Go to location", placeholder="Search places...")
             if st.button("Use GPS Location"):
                st.info("Locating user...")
        
        # 2. Imagery Selector (Visual Cards)
        st.markdown("##### Available Scenes")
        
        # Mock Data for Scenes targeting the selected area
        scenes = [
            {"date": "13 Dec 2025", "cloud": "0.1%", "sensor": "Sentinel-2 L2A", "id": "S2A_20251213"},
            {"date": "08 Dec 2025", "cloud": "12.4%", "sensor": "Sentinel-2 L2A", "id": "S2B_20251208"},
            {"date": "28 Nov 2025", "cloud": "2.1%", "sensor": "Landsat 9", "id": "L9_20251128"},
        ]
        
        # Scene Selector Logic
        selected_scene_id = st.radio("Select Scene", [s["id"] for s in scenes], label_visibility="collapsed", format_func=lambda x: "")
        
        # Render Custom Cards
        for s in scenes:
            is_selected = (selected_scene_id == s['id'])
            border_color = "#00FF7F" if is_selected else "#444"
            st.markdown(f"""
            <div style='border: 1px solid {border_color}; border-radius: 5px; padding: 10px; margin-bottom: 8px; background-color: #222;'>
                <div style='font-weight: bold; color: {border_color};'>{s['date']}</div>
                <div style='font-size: 0.8em; color: #ddd;'>{s['sensor']}</div>
                <div style='font-size: 0.8em; color: #aaa;'>Cloud Cover: {s['cloud']}</div>
            </div>
            """, unsafe_allow_html=True)
            if is_selected:
                st.caption(f"✅ Active: {s['sensor']} ({s['date']})")

        st.divider()
        
        # 3. Analysis Tools (Moved from Left)
        st.markdown("##### 🛠️ Processing")
        
        calc_mode = st.radio("Mode", ["Standard Indices", "Custom Script"], horizontal=True)
        
        if calc_mode == "Standard Indices":
            index_choice = st.selectbox("Spectral Index", 
                [
                    "Iron Oxide (Red/Blue)", 
                    "Ferric Oxide (SWIR1/NIR)", 
                    "Ferrous Iron", 
                    "Clay Minerals",
                    "reNDVI (Vegetation Health)",
                    "MSI (Moisture Stress)",
                    "WRI (Flooded Pits)",
                    "Geological Structures"
                ])
        else:
             custom_formula = st.text_input("Band Math", "(B8 - B4) / (B8 + B4)")
             index_choice = "Custom Formula"

        # The Analyze Button
        analyze_btn = st.button("⚡ Run Analysis", type="primary")

        # GIS Report Button (Conditional)
        if 'analysis_result' in st.session_state and st.session_state.analysis_result:
             st.divider()
             st.success("Analysis Ready")
             if st.button("📧 Email Report"):
                 # Trigger quick email
                 with st.spinner("Sending..."):
                     try:
                        EmailService.send_email(user_email, f"Quick GIS Report", "Analysis completed.")
                        st.balloons()
                     except Exception as e:
                        st.error(str(e))


    # --- LEFT PANEL (MAP INTERFACE) ---
    with col_map:
        # Map Tools Bar (Horizontal)
        c_tools1, c_tools2, c_tools3 = st.columns([1, 1, 1])
        with c_tools1:
             data_source = st.checkbox("Use Local Data", value=False)
        with c_tools2:
             st.caption("Draw box to analyze")
        
        # MAP LOGIC
        # Default Map Center (Zvishavane)
        default_center = [-20.32, 30.06]
        
        m = folium.Map(location=default_center, zoom_start=12, tiles=None) # Start with no default tiles to adding our own
        
        # Mapbox (Dark/Satellite)
        MAPBOX_TOKEN = "sk.eyJ1IjoibWhhbmR1dGFrdW5kYW5pZ2VsIiwiYSI6ImNtNnpoaDd5dTA0bHAybHNrd2pqYXR3ZmEifQ.u1NRx5Q4yTwBktfuzpXiCQ"
        folium.TileLayer(
            tiles=f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{{z}}/{{x}}/{{y}}?access_token={MAPBOX_TOKEN}",
            attr='Mapbox',
            name='Satellite',
            overlay=False,
            control=True
        ).add_to(m)

        # Draw Control
        draw = Draw(
            export=False,
            position='topleft',
            draw_options={'polyline': False, 'polygon': False, 'circle': False, 'marker': True, 'circlemarker': False, 'rectangle': True},
            edit_options={'edit': True}
        )
        draw.add_to(m)

        # Field Data Markers
        if 'field_service' in st.session_state:
            for sub in st.session_state.field_service.submissions:
                color = "green" if sub.get('user') == user_name else "blue"
                popup_html = f"<b>{sub['desc']}</b><br>User: {sub.get('user')}"
                folium.Marker(
                    [sub['lat'], sub['lon']],
                    popup=folium.Popup(popup_html, max_width=200),
                    icon=folium.Icon(color=color, icon="info-sign")
                ).add_to(m)

        # Analysis Overlay
        if 'analysis_result' in st.session_state and st.session_state.analysis_result:
            res = st.session_state.analysis_result
            folium.raster_layers.ImageOverlay(
                image=res['image'],
                bounds=res['bounds'],
                opacity=0.7,
                name="Analysis Layer"
            ).add_to(m)

        folium.LayerControl().add_to(m)
        
        # RENDER MAP
        # Make it tall - Height 850px to match a "Studio" feel
        output = st_folium(m, width=None, height=850, use_container_width=True)

        # --- FIELD DATA FORM (BELOW MAP) ---
        with st.expander("📝 Field Observation Log", expanded=False):
             with st.form("quick_log"):
                 f_c1, f_c2, f_c3 = st.columns(3)
                 lat = f_c1.number_input("Lat", value=-20.30)
                 lon = f_c2.number_input("Lon", value=30.00)
                 desc = f_c3.text_input("Observation")
                 if st.form_submit_button("Log Point"):
                     st.session_state.field_service.add_submission(lat, lon, desc, None, user_name)
                     st.success("Logged")
                     st.rerun()

        # --- ANALYSIS LOGIC (Triggered by button in Right Panel) ---
        if analyze_btn:
            # Check for Drawing
            roi_bounds = None
            if output and 'all_drawings' in output and output['all_drawings']:
                last_draw = output['all_drawings'][-1]
                if last_draw['geometry']['type'] == 'Polygon':
                    coords = last_draw['geometry']['coordinates'][0]
                    lons = [c[0] for c in coords]
                    lats = [c[1] for c in coords]
                    roi_bounds = [[min(lats), min(lons)], [max(lats), max(lons)]]
            
            if not roi_bounds:
                 # Default Test Box
                 roi_bounds = [[-20.35, 30.00], [-20.28, 30.12]]
                 st.toast("Using default test area (No drawing found)")

            with st.spinner("Processing Spectral Data..."):
                 # Mock Processing Logic (Preserved from original)
                 # Generate Mock Bands
                 height, width = 500, 500
                 bands = {}
                 for b in ['B2', 'B3', 'B4', 'B5', 'B8', 'B11', 'B12']:
                     bands[b] = np.random.uniform(0.1, 0.4, (height, width))
                 
                 # Add Fake Feature
                 y, x = np.ogrid[-250:250, -250:250]
                 mask = x*x + y*y <= 80**2
                 if "Iron" in index_choice:
                    bands['B4'][mask] = 0.6
                 
                 # Calculate
                 if calc_mode == "Standard Indices":
                        calculator = Sentinel2Indices(bands)
                        res_map = calculator.calculate_all().get(index_choice, bands['B4'])
                 else:
                        # Simple eval fallback
                        res_map = bands['B8'] 
                 
                 # Colorize
                 clean = np.nan_to_num(res_map, nan=0.0)
                 norm = colors.Normalize(vmin=np.percentile(clean, 2), vmax=np.percentile(clean, 98))
                 cmap = cm.get_cmap('RdYlBu_r')
                 colored_img = cmap(norm(clean))
                 
                 st.session_state.analysis_result = {
                    'image': colored_img,
                    'bounds': roi_bounds
                 }
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
