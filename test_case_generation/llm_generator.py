import streamlit as st
import pandas as pd
from groq import Groq
import os 
# configure Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

st.title("Test Scenario Generator")
st.write("Upload your CSV and generate test scenarios")

#File upload
uploaded_file = st.file_uploader("Upload CSV")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Raw data: ")
    st.dataframe(df)

    #generate button
    if st.button("Generate test Scenarios"):
        # Get ALL data (clicks + changes)
            df_clean = df.copy()
            df_clean['Value'] = df_clean.apply(
                lambda row: 'Click' if row['Action'] == 'click' else row['Value'],
                axis=1
            )
            
            # Get column names and original values
            labels = df_clean['Label'].tolist()
            original_values = df_clean['Value'].tolist()
            
            # Create header row string
            header = "Description," + ",".join(labels)
            
            # Create perfect row string
            perfect_row = "Perfect template," + ",".join(str(v) for v in original_values)
            
            # Find which indices are "change" (input fields)
            change_info = []
            for i, row in df_clean.iterrows():
                if row['Action'] == 'change':
                    change_info.append(f"- Index {i}: {row['Label']} = {row['Value']}")
            # The prompt
            prompt = f"""
You are a QA test data generator. Generate a CSV file.

COLUMNS (17 total, in this exact order):
{header}

ORIGINAL VALUES FOR PERFECT ROW:
{perfect_row}

INPUT FIELDS (only these should be modified for edge cases):
{chr(10).join(change_info)}

All other columns are "Click" - NEVER change them.

RULES:
1. First row: Perfect template with all original values
2. Each subsequent row: Change ONLY ONE input field, keep everything else exactly the same
3. Columns with "Click" must ALWAYS stay as "Click"

EDGE CASES TO CREATE FOR EACH INPUT FIELD:
- empty (leave blank)
- @#$%^& (special characters)
- 12345 (numbers only)  
- AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA (too long)

EXAMPLE ROWS:
{header}
{perfect_row}
firstName - empty,Click,,Click,PRAK@GMAIL.COM,Click,M,Click,123-4567,Click,CHAN,Click,Click,Click,Click,Click,Click
email - invalid,Click,PRAKYATH,Click,notanemail,Click,M,Click,123-4567,Click,CHAN,Click,Click,Click,Click,Click,Click

Generate around 20 test scenario rows.

Return ONLY CSV. No explanation. No markdown. No extra text.
"""

            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": prompt}]
            )
            
            result_text = response.choices[0].message.content
            
            # Clean up - remove any markdown or extra text
            if "```" in result_text:
                result_text = result_text.split("```")[1]
                if result_text.startswith("csv"):
                    result_text = result_text[3:]
            result_text = result_text.strip()
            
            st.write("### Generated Test Scenarios:")
            st.code(result_text)
            
            # Download button
            st.download_button(
                label="Download CSV",
                data=result_text,
                file_name="test_scenarios.csv",
                mime="text/csv"
            )

