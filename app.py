import streamlit as st
import os
import google.generativeai as genai
from notion_client import Client
from datetime import datetime, timedelta
from PIL import Image
from io import BytesIO

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="TPP Studio Command", page_icon="🚀", layout="wide")

# --- 2. AUTHENTICATION (THE GATEKEEPER) ---
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password
        else:
            st.session_state["password_correct"] = False

    # Return True if the pass was verified earlier in the session
    if "password_correct" in st.session_state:
        if st.session_state["password_correct"]:
            return True

    # Show input for password
    st.title("🔒 TPP Studio Login")
    st.text_input(
        "Enter Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

# STOP HERE IF PASSWORD IS WRONG
if not check_password():
    st.stop()  # The app stops here. Nothing below runs.


# Custom CSS
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
        background-color: #FFFFFF; 
        color: #1F2A3C; 
        border-radius: 12px; 
        border: 1px solid #E0E0E0; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
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
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Status Badges */
    .status-ready { color: #2E7D32; font-weight: bold; }
    .status-scheduled { color: #F57F17; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

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

# --- 2. SIDEBAR (UPDATED) ---
with st.sidebar:
    st.header("🧬 Brand DNA")
    if os.path.exists("Taylored Pet Portraits-logo.gif"):
        st.image("Taylored Pet Portraits-logo.gif")

    # 1. VISUAL DNA (Existing)
    with st.expander("🎨 Visual Palette", expanded=False):
        c_bg1 = st.color_picker("Cool Blue", "#E4F3FF")
        c_acc1 = st.color_picker("Sky Blue", "#7DC6FF")
        c_text = st.color_picker("Navy Text", "#1F2A3C")

    # 2. VERBAL DNA (New!)
    with st.expander("🗣️ Brand Voice (Editable)", expanded=True):
        brand_mission = st.text_area(
            "Mission / Key Msg:", 
            value="We turn your pet photos into modern pop-art masterpieces. 5% of all profits are donated to local animal shelters."
        )
        founder_name = st.text_input("Founder Sign-off:", value="Taylor")
        
    st.divider()
    
    # 3. SETTINGS
    st.header("📢 Settings")
    output_format = st.radio("Format:", ["Square (1:1)", "Story (9:16)", "Landscape (16:9)"])
    caption_vibe = st.select_slider("Vibe:", ["Heartfelt ❤️", "Witty 🤪", "Luxury ✨", "Urgent 🚨"])

# --- 3. SMART SCHEDULER LOGIC ---

def get_next_optimal_slot(offset_days=0):
    """
    Finds the next high-engagement slot after the LAST scheduled post.
    """
    if not NOTION_KEY: return datetime.now()
    
    # 1. Find last scheduled date in Notion
    try:
        resp = notion.databases.query(
            **{"database_id": DATABASE_ID, 
               "sorts": [{"property": "Date", "direction": "descending"}],
               "page_size": 1}
        )
        if resp['results']:
            last_date_str = resp['results'][0]['properties']['Date']['date']['start']
            last_date = datetime.fromisoformat(last_date_str[:19]) # Strip timezone for simplicity
        else:
            last_date = datetime.now()
    except:
        last_date = datetime.now()
    
    # 2. Start calculation from Last Date + 1 Day (plus offset for batching)
    target_date = last_date + timedelta(days=1 + offset_days)
    weekday = target_date.weekday() # 0=Mon, 6=Sun
    
    # 3. Apply Heuristic Logic (Engagement Windows)
    if weekday <= 2: # Mon-Wed: Evening Commute
        optimal_hour = 18 # 6 PM
    elif weekday <= 4: # Thu-Fri: Lunch Break
        optimal_hour = 12 # 12 PM
    else: # Sat-Sun: Morning
        optimal_hour = 9 # 9 AM
        
    final_slot = target_date.replace(hour=optimal_hour, minute=0, second=0, microsecond=0)
    return final_slot

def save_to_vault(title, caption, status="Draft", schedule_date=None):
    if not schedule_date: schedule_date = datetime.now()
    
    try:
        notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties={
                "Name": {"title": [{"text": {"content": title}}]},
                "Caption": {"rich_text": [{"text": {"content": caption}}]},
                "Status": {"select": {"name": status}},
                "Date": {"date": {"start": schedule_date.isoformat()}}
            }
        )
        return True
    except: return False

# --- 4. ENGINE (GEMINI 3) ---

def generate_asset_pair(topic, raw_image, index):
    image_model = genai.GenerativeModel('gemini-3-pro-image-preview')
    
    layout = "Center subject."
    if "Story" in output_format: layout = "Generate TALL (9:16). Negative space at top."
    
    image_prompt = f"""
    Create high-fidelity social image for: '{topic}'.
    Palette: {c_bg1}, {c_acc1}, {c_text}.
    Format: {layout}
    Style: Pop-Art, Premium.
    """
    
    # TEXT LOGIC (Now reads the Sidebar!)
    text_model = genai.GenerativeModel('gemini-3-pro')
    
    text_prompt = f"""
    Write a social media caption for '{topic}' (Variation {index+1}).
    
    BRAND CONTEXT:
    - Mission: "{brand_mission}"
    - Founder: {founder_name}
    
    TONE: {caption_vibe}
    - If Heartfelt: Focus on the bond and the mission.
    - If Witty: Use puns relative to the pet breed.
    - If Luxury: Focus on 'Museum Quality' and 'Decor'.
    
    INSTRUCTIONS:
    - End with a sign-off from {founder_name} if appropriate.
    - Include 30 niche hashtags.
    """
    
    try:
        if raw_image:
            img = Image.open(raw_image)
            img_res = image_model.generate_content([image_prompt, img])
        else:
            img_res = image_model.generate_content(image_prompt)
            
        # Robust extract
        final_image = None
        part = img_res.parts[0]
        if hasattr(part, 'inline_data') and part.inline_data.data:
             final_image = Image.open(BytesIO(part.inline_data.data))
        elif hasattr(part, 'image'):
             final_image = part.image
        else:
             final_image = None

        txt_res = text_model.generate_content(text_prompt)
        return final_image, txt_res.text
    except Exception as e:
        return None, str(e)

# --- 5. MAIN UI ---
st.markdown("<h1 style='text-align: center;'>TPP Studio Command 🚀</h1>", unsafe_allow_html=True)

tab_create, tab_mockup, tab_queue = st.tabs(["✨ Content Factory", "🖼️ Mockup Studio", "🗓️ Smart Queue"])

# TAB 1: FACTORY
with tab_create:
    topic = st.text_input("Topic/Idea", placeholder="e.g. 'Barney Reveal'")
    files = st.file_uploader("Upload (Single or Batch)", accept_multiple_files=True)
    
    # Session State to hold results
    if 'generated_assets' not in st.session_state:
        st.session_state.generated_assets = []

    if st.button("Generate Assets"):
        st.session_state.generated_assets = [] # Clear previous
        if files and GEMINI_KEY:
            cols = st.columns(2)
            progress = st.progress(0)
            
            for i, f in enumerate(files):
                img, txt = generate_asset_pair(topic, f, i)
                if img:
                    st.session_state.generated_assets.append({"title": f"{topic} {i+1}", "caption": txt, "image": img})
                    with cols[i%2]:
                        st.image(img)
                        st.caption(txt[:100]+"...")
                progress.progress((i+1)/len(files))
    
    # Display Results from State
    if st.session_state.generated_assets:
        st.divider()
        st.write("### Actions")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔥 Post Now (Mark Ready)", type="primary"):
                for r in st.session_state.generated_assets:
                    save_to_vault(r['title'], r['caption'], "Ready", datetime.now())
                st.success("Sent to 'Ready' list!")
        with col_b:
            if st.button("⏳ Add to Smart Queue"):
                for i, r in enumerate(st.session_state.generated_assets):
                    # Stagger by 2 days each
                    slot = get_next_optimal_slot(offset_days=i*2)
                    save_to_vault(r['title'], r['caption'], "Scheduled", slot)
                st.balloons()
                st.success("Added to Smart Queue!")

# TAB 2: MOCKUP (Simplified for Demo)
with tab_mockup:
    st.info("Upload finished art to see it on a Canvas/Mug.")
    mock_file = st.file_uploader("Finished Art", type=['png','jpg'])
    mock_type = st.selectbox("Mockup Type", ["Living Room Canvas", "Coffee Mug", "Phone Case"])
    
    if st.button("Generate Mockup") and mock_file:
        # (Reuse generate logic with specific Mockup prompt)
        st.warning("Mockup Engine running... (Simulated)")
        st.image(mock_file, caption=f"Mockup: {mock_type}")

# TAB 3: QUEUE
with tab_queue:
    st.header("🗓️ Upcoming Schedule")
    if st.button("Refresh Queue"):
        if NOTION_KEY:
            try:
                resp = notion.databases.query(
                    **{"database_id": DATABASE_ID, 
                       "filter": {"property": "Status", "select": {"equals": "Scheduled"}},
                       "sorts": [{"property": "Date", "direction": "ascending"}]}
                )
                for page in resp['results']:
                    try: 
                        t = page['properties']['Name']['title'][0]['plain_text']
                        d = page['properties']['Date']['date']['start']
                        st.info(f"📅 {d[:16].replace('T', ' @ ')} — {t}")
                    except: pass
            except Exception as e:
                st.error(f"Error fetching queue: {e}")
