import streamlit as st
import json
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="XPath Analytics Recorder Dashboard")

st.title("XPath Analytics Recorder Dashboard")

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

#summary stats
st.subheader("Summary")
col1, col2, col3, col4 = st.columns(4)

clicks = sum(1 for x in data["xpaths"] if x["action"] == "click")
changes = sum(1 for x in data["xpaths"] if x["action"] == "change")

col1.metric("Total Elements", data["total_elements"])
col2.metric("Clicks", clicks)
col3.metric("Changes", changes)
col4.metric("URL", data["url"][:30] + "...")

st.divider()

#view options
st.subheader("Captured Data")

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

# Display based on selection
if view_option == "Full Data (with XPath)":
    st.dataframe(df, use_container_width=True)

elif view_option == "Simple View (no XPath)":
    simple_df = df[["label", "action", "strategy", "values"]].copy()
    simple_df.columns = ["element Name", "Action", "Stratergy Used", "Value Entered"]
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
st.subheader("Download")

col1, col2 = st.columns(2)

with col1:
    csv_data = df.to_csv(index=False)
    st.download_button("Download CSV", csv_data, file_name="xpaths_export.csv", mime="text/csv")

with col2:
    st.download_button("Download JSON", json.dumps(data, indent=2), file_name="xpaths_export.json", mime="application/json")


