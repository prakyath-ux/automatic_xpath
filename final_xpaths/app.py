import streamlit as st
import json
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="XPath Analytics Recorder Dashboard", page_icon="🎯", layout="wide")

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


st.markdown("# 🎯 XPath Analytics Recorder")
st.markdown("*Automated element capture for QA testing*")

st.divider()

#Find all JSON files
json_files = list(Path(".").glob("xpaths_*.json"))

if not json_files:
    st.warning("No captured data found. Run version3.py first to capture Xpaths.")
    st.stop()

# File selector
selected_file = st.selectbox("Select captured session:", json_files, format_func= lambda x: x.name)

#Load data
with open(selected_file) as f:
    data = json.load(f)
st.success(f" Loaded {data['total_elements']} elements from session")
#summary stats
st.subheader("📊 Summary")
col1, col2, col3, col4 = st.columns(4)

clicks = sum(1 for x in data["xpaths"] if x["action"] == "click")
changes = sum(1 for x in data["xpaths"] if x["action"] == "change")

col1.metric("Total Elements", data["total_elements"])
col2.metric("Clicks", clicks)
col3.metric("Input (Changes)", changes)
col4.metric("URL", data["url"][:30] + "...")

#view options
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

#create data frame
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

#Download Section
st.subheader("📥 Download") 

col1, col2 = st.columns(2)

with col1:
    csv_data = df.to_csv(index=False)
    st.download_button("Download CSV", csv_data, file_name="xpaths_export.csv", mime="text/csv")

with col2:
    st.download_button("Download JSON", json.dumps(data, indent=2), file_name="xpaths_export.json", mime="application/json")


