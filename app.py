import streamlit as st
import os
import google.generativeai as genai
from notion_client import Client
from datetime import datetime
from PIL import Image
from io import BytesIO

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="TPP Studio", page_icon="🍌", layout="wide")

# Secrets
try:
    NOTION_KEY = st.secrets["NOTION_KEY"]
    DATABASE_ID = st.secrets["DATABASE_ID"]
    GEMINI_KEY = st.secrets["GEMINI_KEY"]
except:
    NOTION_KEY = ""
    DATABASE_ID = ""
    GEMINI_KEY = ""

if GEMINI_KEY: genai.configure(api_key=GEMINI_KEY)
if NOTION_KEY: notion = Client(auth=NOTION_KEY)

# --- 2. CUSTOM CSS (Pomelli Hybrid) ---
st.markdown("""
    <style>
    /* Main Background & Text */
    .stApp { background-color: #FFFFFF; color: #1F2A3C; }
    
    /* Headers */
    h1, h2, h3 { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; letter-spacing: -0.5px; color: #1F2A3C; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #F7F9FC; border-right: 1px solid #E6E8EB; }
    
    /* Input Styling */
    .stTextInput>div>div>input { 
        background-color: #FAFAFA; 
        color: #1F2A3C; 
        border-radius: 12px; 
        border: 1px solid #E0E0E0; 
        padding: 10px 15px;
    }
    
    /* File Uploader */
    [data-testid="stFileUploader"] {
        background-color: #FAFAFA;
        border: 1px dashed #E0E0E0;
        border-radius: 12px;
        padding: 20px;
    }
    
    /* Primary Button */
    .stButton>button { 
        background-color: #1F2A3C; 
        color: white; 
        border-radius: 20px; 
        font-weight: 600; 
        border: none;
        width: 100%;
        padding: 8px 20px;
    }
    .stButton>button:hover { 
        background-color: #FF9AC4; 
        color: white; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Card Styling */
    div[data-testid="stVerticalBlock"] > div[style*="background-color"] {
        border: 1px solid #E0E0E0;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR: BRAND DNA ---
with st.sidebar:
    st.header("🧬 Brand DNA")
    if os.path.exists("Taylored Pet Portraits-logo.gif"):
        st.image("Taylored Pet Portraits-logo.gif")
    
    st.write("### 🎨 Active Palette")
    c_bg1 = st.color_picker("Cool Blue", "#E4F3FF")
    c_bg2 = st.color_picker("Soft Lilac", "#E0D6FF")
    c_acc1 = st.color_picker("Sky Blue", "#7DC6FF")
    c_acc2 = st.color_picker("Bubblegum Pink", "#FF9AC4")
    c_text = st.color_picker("Navy Text", "#1F2A3C")
    
    st.divider()
    if NOTION_KEY: 
        st.success("● Vault Connected")
    else: 
        st.warning("○ Vault Disconnected")

# --- 4. GEMINI 3 ENGINE ---

def generate_campaign_assets(topic, raw_image=None):
    """
    STRICTLY GEMINI 3 PRO.
    Visuals: gemini-3-pro-image-preview
    Copy: gemini-3-pro
    """
    # 1. VISUAL ENGINE
    img_model = genai.GenerativeModel('gemini-3-pro-image-preview')
    
    design_prompt = f"""
    Create a high-fidelity marketing image for the campaign: '{topic}'.
    
    DESIGN SYSTEM:
    - Primary Colors: {c_bg1}, {c_bg2}
    - Accent Colors: {c_acc1}, {c_acc2}
    - Key Text Color: {c_text}
    
    COMPOSITION:
    - Professional Studio Lighting.
    - If a pet photo is provided, style it as a Premium Art Portrait.
    - If no photo, create a conceptual illustration.
    - Overlay the campaign title '{topic}' using a clean, modern font.
    """
    
    # 2. COPY ENGINE
    txt_model = genai.GenerativeModel('gemini-3-pro')
    
    copy_prompt = f"""
    Write a high-converting Instagram caption for the campaign '{topic}'.
    
    TONE:
    - Empathetic but excited.
    - Use 1-2 emojis.
    - Include a Call to Action (CTA).
    - Add 3 relevant hashtags.
    """
    
    try:
        # Generate Image
        if raw_image:
            img_input = Image.open(raw_image)
            response_img = img_model.generate_content([design_prompt, img_input])
        else:
            response_img = img_model.generate_content(design_prompt)
            
        # Robust Image Extraction
        final_image = None
        part = response_img.parts[0]
        if hasattr(part, 'inline_data') and part.inline_data.data:
             final_image = Image.open(BytesIO(part.inline_data.data))
        elif hasattr(part, 'image'):
             final_image = part.image
        else:
             final_image = "Error: No image found in response."

        # Generate Text
        response_txt = txt_model.generate_content(copy_prompt)
        final_text = response_txt.text
        
        return final_image, final_text

    except Exception as e:
        return f"Gen Error: {e}", f"Gen Error: {e}"

def save_to_notion(title, caption):
    try:
        notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties={
                "Name": {"title": [{"text": {"content": title}}]},
                "Caption": {"rich_text": [{"text": {"content": caption}}]},
                "Status": {"select": {"name": "Draft"}},
                "Date": {"date": {"start": datetime.now().isoformat()}}
            }
        )
        return True
    except Exception as e:
        return str(e)

# --- 5. UI LAYOUT ---

st.markdown("<h1 style='text-align: center; margin-bottom: 2rem;'>What are we creating today?</h1>", unsafe_allow_html=True)

# INPUT DECK (CENTERED)
with st.container():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Row 1: Idea
        campaign_topic = st.text_input("Campaign Idea", placeholder="e.g. Valentine's Day Portrait Sale")
        
        # Row 2: Photo
        uploaded_file = st.file_uploader("Drop Pet Photo Reference 📸", type=['jpg', 'png', 'jpeg'])
        
        # Row 3: Action
        generate_btn = st.button("✨ Generate Campaign Assets")

# OUTPUT SECTION
if generate_btn and campaign_topic:
    st.divider()
    st.write(f"### 🍌 Developing: {campaign_topic}")
    
    if not GEMINI_KEY:
        st.error("Please add GEMINI_KEY to secrets.toml")
    else:
        with st.spinner("Gemini 3 is designing & writing..."):
            visual, copy = generate_campaign_assets(campaign_topic, uploaded_file)
            
            out_col1, out_col2 = st.columns(2)
            
            # Col 1: Visual
            with out_col1:
                st.caption("Visual (Nano Banana Pro)")
                if isinstance(visual, str):
                    st.error(visual)
                else:
                    st.image(visual, use_container_width=True)
            
            # Col 2: Copy
            with out_col2:
                st.caption("Copy (Gemini 3 Pro)")
                st.text_area("Caption", value=copy, height=400)
                
                if st.button("💾 Save to Vault"):
                    if NOTION_KEY:
                        res = save_to_notion(campaign_topic, copy)
                        if res is True:
                            st.success("Saved to Notion!")
                        else:
                            st.error(f"Notion Error: {res}")
                    else:
                        st.warning("Please connect Notion to save drafts.")

# DASHBOARD: RECENT CAMPAIGNS
st.divider()
st.subheader("Recent Campaigns")

if NOTION_KEY and DATABASE_ID:
    try:
        response = notion.databases.query(
            **{"database_id": DATABASE_ID, "page_size": 3, 
               "filter": {"property": "Status", "select": {"equals": "Draft"}}}
        )
        
        results = response.get("results", [])
        if results:
            d_cols = st.columns(3)
            for i, page in enumerate(results):
                # Safe Property Extraction
                props = page['properties']
                try: title = props['Name']['title'][0]['plain_text']
                except: title = "Untitled"
                try: caption = props['Caption']['rich_text'][0]['plain_text'][:100] + "..."
                except: caption = "No caption..."
                
                with d_cols[i]:
                    with st.container():
                        st.markdown(f"**{title}**")
                        st.caption(caption)
                        st.markdown("`Status: Draft`")
        else:
            st.info("No recent drafts found.")
            
    except Exception as e:
        st.error(f"Could not load dashboard: {e}")
else:
    st.info("Connect Notion to see recent campaigns.")
