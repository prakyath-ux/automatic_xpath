# app_v4.py - Streamlit Dashboard with Recording Control
import streamlit as st
import subprocess
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import time
import os

st.set_page_config(page_title="XPath Analytics Recorder", page_icon="🎯", layout="wide")

# CSS Styling
st.markdown("""
<style>
    [data-testid="metric-container"] {
        background-color: #262730;
        border-radius: 10px;
        padding: 15px;
    }
    .stDataFrame {
        border-radius: 10px;
    }
    .stApp {
        background-color: #0e1117;
    }
    .stMarkdown, h1, h2, h3, p {
        color: #ffffff !important;
    }
    .stSubheader, [data-testid="stSubheader"] {
        color: #ffffff !important;
        font-weight: 600;
    }
    .stRadio label, .stSelectbox label {
        color: #ffffff !important;
    }
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
        color: #ffffff !important;
    }
    .stDownloadButton button {
        background-color: #262730 !important;
        color: #ffffff !important;
        border: 1px solid #4a4a5a !important;
    }
    .stDownloadButton button:hover {
        background-color: #3a3a4a !important;
        border-color: #6a6a7a !important;
    }
</style>    
""", unsafe_allow_html=True)

STATE_FILE = Path(__file__).parent / ".recording_state.json"
LIVE_CAPTURE_FILE = Path(__file__).parent / ".live_capture.jsonl"

# Initialize session state
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'process' not in st.session_state:
    st.session_state.process = None
if 'last_json' not in st.session_state:
    st.session_state.last_json = None

st.markdown("# 🎯 XPath Analytics Recorder")
st.markdown("*Automated element capture for QA testing*")

st.divider()

# ============ RECORDING SECTION ============
st.subheader("🎬 Record New Session")

col1, col2 = st.columns([3, 1])

with col1:
    url_input = st.text_input("Enter URL:", placeholder="https://example.com/app")

with col2:
    st.write("")  # Spacer
    st.write("")  # Spacer

# Format selection with checkboxes
st.write("**Output Formats:**")
format_col1, format_col2, format_col3 = st.columns(3)
with format_col1:
    format_json = st.checkbox("JSON", value=True)
with format_col2:
    format_csv = st.checkbox("CSV", value=True)
with format_col3:
    format_py = st.checkbox("Python", value=False)

# Build format string
formats = []
if format_json:
    formats.append('json')
if format_csv:
    formats.append('csv')
if format_py:
    formats.append('py')

# Start/Stop buttons
if not st.session_state.recording:
    if st.button("🚀 Start Recording", type="primary", use_container_width=True):
        if not url_input:
            st.error("❌ Please enter a URL")
        elif not url_input.startswith(('http://', 'https://')):
            st.error("❌ Invalid URL. Must start with http:// or https://")
        elif not formats:
            st.error("❌ Please select at least one output format")
        else:
            # Start the recorder subprocess
            format_str = ','.join(formats)
            output_dir = str(Path(__file__).parent)
            
            # Write state file for Live View page
            state = {
                "is_recording": True,
                "url": url_input,
                "started_at": datetime.now().isoformat(),
                "formats": formats
            }
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f)
            
            # Clear previous live capture file
            if LIVE_CAPTURE_FILE.exists():
                LIVE_CAPTURE_FILE.unlink()
            
            st.session_state.process = subprocess.Popen(
                ['python', 'recorder.py', url_input, format_str, output_dir, str(LIVE_CAPTURE_FILE)],
                cwd=output_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            st.session_state.recording = True
            st.rerun()

else:
    # Show recording status
    st.warning("🔴 **Recording in progress...** Click elements in the browser window.")
    st.info(f"📍 URL: {url_input}")
    
    if st.button("Stop Recording", type="secondary", use_container_width=True):
        if st.session_state.process:
            st.session_state.process.terminate()
            time.sleep(1)  # Wait for files to be saved
            st.session_state.process = None
        st.session_state.recording = False
        
        # Clean up state file
        if STATE_FILE.exists():
            STATE_FILE.unlink()
        
        st.success("Recording stopped. Processing data...")
        time.sleep(1)
        st.rerun()


st.divider()

# ============ RESULTS SECTION ============
st.subheader("📊 View Results")

# Find all JSON files
json_files = sorted(Path(__file__).parent.glob("xpaths_*.json"), reverse=True)

if not json_files:
    st.info("No captured sessions yet. Start a recording above!")
    st.stop()

# File selector
selected_file = st.selectbox(
    "Select captured session:",
    json_files,
    format_func=lambda x: x.name
)

# Load data
with open(selected_file) as f:
    data = json.load(f)

st.success(f"✅ Loaded {data['total_elements']} elements from session")

# Summary stats
st.subheader("📊 Summary")
col1, col2, col3, col4 = st.columns(4)

clicks = sum(1 for x in data["xpaths"] if x["action"] == "click")
changes = sum(1 for x in data["xpaths"] if x["action"] == "change")

col1.metric("Total Elements", data["total_elements"])
col2.metric("Clicks", clicks)
col3.metric("Input (Changes)", changes)
col4.metric("URL", data["url"][:30] + "...")

# View options
st.subheader("📋 Captured Data")

view_option = st.radio(
    "Select view:",
    [
        "Full Data (with XPath)",
        "Simple View (no XPath)",
        "Developer View (XPath Only)",
        "QA View (Label + Action + Value)"
    ],
    horizontal=True
)

# Create dataframe
df = pd.DataFrame(data["xpaths"])
df["action"] = df["action"].replace("change", "Input")

# Display based on selection
if view_option == "Full Data (with XPath)":
    st.dataframe(df, use_container_width=True)

elif view_option == "Simple View (no XPath)":
    simple_df = df[["label", "action", "strategy", "values"]].copy()
    simple_df.columns = ["Element Name", "Action", "Strategy Used", "Value Entered"]
    st.dataframe(simple_df, use_container_width=True)

elif view_option == "Developer View (XPath Only)":
    dev_df = df[["label", "xpath", "action"]].copy()
    dev_df.columns = ["Element", "XPath", "Action"]
    st.dataframe(dev_df, use_container_width=True)

elif view_option == "QA View (Label + Action + Value)":
    qa_df = df[["label", "action", "values"]].copy()
    qa_df.columns = ["Element", "Action", "Value"]
    st.dataframe(qa_df, use_container_width=True)

st.divider()

# Download Section
st.subheader("📥 Download")

col1, col2 = st.columns(2)

with col1:
    csv_data = df.to_csv(index=False)
    st.download_button("Download CSV", csv_data, file_name="xpaths_export.csv", mime="text/csv")

with col2:
    st.download_button("Download JSON", json.dumps(data, indent=2), file_name="xpaths_export.json", mime="application/json")

st.divider()
st.markdown("*Built by QA Automation Team • Impacto Digital*")
