# pages/1_Live_View.py - Live XPath Capture Viewer
import streamlit as st
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import time

st.set_page_config(page_title="Live View", page_icon="👁️", layout="wide")

# Paths
BASE_DIR = Path(__file__).parent.parent
STATE_FILE = BASE_DIR / ".recording_state.json"
LIVE_CAPTURE_FILE = BASE_DIR / ".live_capture.jsonl"

# CSS Styling (matching app_v4.py)
st.markdown("""
<style>
    [data-testid="metric-container"] {
        background-color: #262730;
        border-radius: 10px;
        padding: 15px;
    }
    .stDataFrame { border-radius: 10px; }
    .stApp { background-color: #0e1117; }
    .stMarkdown, h1, h2, h3, p { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("# Live XPath Capture")
st.markdown("*Real-time view of captured elements*")
st.divider()

# Check recording state
if not STATE_FILE.exists():
    st.warning("No active recording session.")
    st.info("Go to the **app_v4** page in the sidebar to start a new recording.")
    st.stop()

# Load state
with open(STATE_FILE) as f:
    state = json.load(f)

# Display recording info
st.success(f"Recording Active since {state['started_at'][:19]}")
st.info(f"URL: {state['url']}")

st.divider()

# ============ GROUP ASSIGNMENT SECTION ============
st.subheader("Assign Group")
col1, col2 = st.columns([3, 1])
with col1:
    group_name = st.text_input("Group name:", placeholder="e.g., Personal Info, Contact Details")
with col2:
    st.write("")  # Spacer
    if st.button("Assign Group", type="primary", use_container_width=True):
        if group_name.strip():
            # Check if last line is a group marker (allow rename)
            should_replace = False
            if LIVE_CAPTURE_FILE.exists():
                with open(LIVE_CAPTURE_FILE, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        try:
                            last_entry = json.loads(lines[-1].strip())
                            if last_entry.get("type") == "group":
                                should_replace = True
                        except:
                            pass
            
            if should_replace:
                # Remove last line and rewrite
                with open(LIVE_CAPTURE_FILE, 'w') as f:
                    f.writelines(lines[:-1])
            
            # Write new group marker
            group_entry = {
                "type": "group",
                "name": group_name.strip(),
                "timestamp": datetime.now().isoformat()
            }
            with open(LIVE_CAPTURE_FILE, 'a') as f:
                f.write(json.dumps(group_entry) + '\n')
            st.success(f"Group '{group_name}' assigned!")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("Please enter a group name")


st.divider()

# Auto-refresh settings
col1, col2 = st.columns([1, 3])
with col1:
    auto_refresh = st.checkbox("Auto-refresh", value=True)
with col2:
    refresh_interval = st.slider("Interval (seconds)", 1, 10, 2, disabled=not auto_refresh)

# Display settings
max_entries = st.slider("Show last N entries", 10, 200, 50)

st.divider()

# Load and display live data
if not LIVE_CAPTURE_FILE.exists():
    st.info("Waiting for first interaction...")
else:
    # Read JSONL file and process groups
    entries = []
    group_markers = []  # List of (index, group_name)
    
    with open(LIVE_CAPTURE_FILE) as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get("type") == "group":
                    # Record where this group marker appears
                    group_markers.append((len(entries), entry["name"]))
                elif entry.get("type") == "xpath":
                    entries.append(entry)
            except json.JSONDecodeError:
                continue
    
    if not entries:
        st.info("Waiting for interactions...")
    else:
                # Assign groups to entries (retroactive assignment)
        # Group marker at position N means: all entries BEFORE it (0 to N-1) get that group
        for i, entry in enumerate(entries):
            entry["group"] = ""  # Default: no group
        
        # Process group markers in order
        prev_idx = 0
        for marker_idx, group_name in group_markers:
            # Assign group name to entries from prev_idx to marker_idx-1
            for i in range(prev_idx, marker_idx):
                entries[i]["group"] = group_name
            prev_idx = marker_idx
        # Entries after last marker remain ungrouped (empty)

        
        # Summary metrics
        st.subheader(f"Captured: {len(entries)} elements")
        
        col1, col2, col3, col4 = st.columns(4)
        clicks = sum(1 for e in entries if e["action"] == "click")
        inputs = sum(1 for e in entries if e["action"] != "click")
        ungrouped = sum(1 for e in entries if e["group"] == "")
        col1.metric("Total", len(entries))
        col2.metric("Clicks", clicks)
        col3.metric("Inputs", inputs)
        col4.metric("Ungrouped", ungrouped)
        
        # Show last N entries
        recent_entries = entries[-max_entries:]
        df = pd.DataFrame(recent_entries)
        
        # Reorder columns - Group first for visibility
        display_cols = ["group", "label", "action", "values", "strategy", "xpath"]
        df = df[[c for c in display_cols if c in df.columns]]
        df.columns = ["Group", "Element", "Action", "Value", "Strategy", "XPath"]
        
        st.dataframe(df, use_container_width=True, height=400)
        
        # Show latest entry highlighted
        st.subheader("Latest Capture")
        latest = entries[-1]
        st.code(f"""Group:    {latest.get('group', '')}
Element:  {latest['label']}
Action:   {latest['action']}
Value:    {latest.get('values', '')}
XPath:    {latest['xpath']}
Strategy: {latest['strategy']}""")

# Auto-refresh logic
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()

# Footer
st.divider()
st.markdown("*Switch to app_v4 in the sidebar to stop recording*")
