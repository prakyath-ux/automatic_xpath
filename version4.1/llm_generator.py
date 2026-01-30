import streamlit as st
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
import os 

load_dotenv()
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
            
            
            # Count columns dynamically
            column_count = len(labels) + 1  # +1 for Description column

            # Build list of input fields (change actions only)
            input_fields = []
            for i, row in df_clean.iterrows():
                if row['Action'] == 'change':
                    input_fields.append(row['Label'])

            # The prompt (FULLY DYNAMIC - no hardcoded values)
            prompt = f"""You are a QA test data generator. Generate edge case test scenarios as CSV.

INPUT DATA:
- Total columns: {column_count}
- Header: {header}
- Perfect row: {perfect_row}

INPUT FIELDS THAT CAN BE MODIFIED (these have user-typed values):
{', '.join(input_fields)}

CLICK FIELDS (these are button/dropdown clicks - NEVER modify these):
All columns with value "Click" must ALWAYS remain exactly "Click"

TRANSFORMATION RULES:
1. Row 1: Header row exactly as provided above
2. Row 2: "Perfect template" row with all original values exactly as provided
3. Rows 3+: Edge case rows - each row tests ONE input field

FOR EACH INPUT FIELD, CREATE THESE EDGE CASES:
- [fieldName] - empty (leave the field blank, empty string)
- [fieldName] - special (use: @#$%^&)
- [fieldName] - numeric (use: 12345)
- [fieldName] - long (use: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA)

CRITICAL RULES:
- Every row must have EXACTLY {column_count} columns
- "Click" values are NEVER changed - copy them exactly
- Only modify ONE input field per row
- Keep all other values identical to the perfect row
- Description format: "[fieldName] - [edgeCase]"

OUTPUT FORMAT:
- Return ONLY valid CSV
- No markdown, no code blocks, no explanation
- First row is header, second row is perfect template, then edge cases
"""

            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": prompt}]
            )
            
            result_text = response.choices[0].message.content
            
                        # ========== POST-PROCESSING VALIDATION ==========
            # Clean up markdown if present
            if "```" in result_text:
                result_text = result_text.split("```")[1] # Get content between ```
                if result_text.startswith("csv"):
                    result_text = result_text[3:]   # Remove "csv" language tag
            result_text = result_text.strip()       # Remove whitespace
            
            # Validate and fix column counts
            lines = result_text.split('\n')
            header_cols = len(lines[0].split(',')) # counter header columns
            
            validated_lines = [lines[0]]  # Keep header as-is
            for line in lines[1:]:
                if not line.strip():  # Skip empty lines
                    continue
                cols = line.split(',')
                if len(cols) < header_cols:
                    # Add missing Clicks at the end
                    cols.extend(['Click'] * (header_cols - len(cols)))
                elif len(cols) > header_cols:
                    # Trim extra columns from the end
                    cols = cols[:header_cols]
                validated_lines.append(','.join(cols))
            
            result_text = '\n'.join(validated_lines)

            
            st.write("### Generated Test Scenarios:")
            st.code(result_text)
            
            # Download button
            st.download_button(
                label="Download CSV",
                data=result_text,
                file_name="test_scenarios.csv",
                mime="text/csv"
            )

