import streamlit as st
import pandas as pd

st.title("Test Scenarios CSV Validator")
st.write("Upload a generated test scenarios CSV to validate")

uploaded_file = st.file_uploader("Upload CSV")

if uploaded_file:
    # Read raw text for validation
    content = uploaded_file.getvalue().decode('utf-8')
    csv_rows = content.strip().split('\n')
    
    st.write("### Raw Data:")
    st.code(content)
    
    if st.button("Validate CSV"):
        validation_errors = []
        validation_passed = []
        
        header_row = csv_rows[0].split(',')
        perfect_row = csv_rows[1].split(',') if len(csv_rows) > 1 else []
        
        # Check 1: Column count consistency
        all_same_length = True
        for i, row in enumerate(csv_rows):
            cols = row.split(',')
            if len(cols) != len(header_row):
                all_same_length = False
                validation_errors.append(f"Row {i+1}: Expected {len(header_row)} columns, got {len(cols)}")
        
        if all_same_length:
            validation_passed.append(f"Column count: All {len(csv_rows)} rows have {len(header_row)} columns")
        
        # Check 2: Click preservation
        click_indices = [i for i, val in enumerate(perfect_row) if val == 'Click']
        click_errors = 0
        
        for row_num, row in enumerate(csv_rows[2:], start=3):
            cols = row.split(',')
            for idx in click_indices:
                if idx < len(cols) and cols[idx] != 'Click':
                    click_errors += 1
                    validation_errors.append(f"Row {row_num}, Col {idx+1}: Expected 'Click', got '{cols[idx]}'")
        
        if click_errors == 0:
            validation_passed.append(f"Click preservation: All {len(click_indices)} click columns preserved")
        
        # Check 3: One change per row
        one_change_errors = 0
        for row_num, row in enumerate(csv_rows[2:], start=3):
            cols = row.split(',')
            changes = 0
            for i, (test_val, perfect_val) in enumerate(zip(cols[1:], perfect_row[1:])):
                if test_val != perfect_val:
                    changes += 1
            if changes != 1:
                one_change_errors += 1
                validation_errors.append(f"Row {row_num}: Expected 1 change, found {changes}")
        
        if one_change_errors == 0:
            validation_passed.append("One change per row: All test cases modify exactly 1 field")
        
        # Check 4: Edge cases present
        edge_case_types = ['empty', 'special', 'numeric', 'long']
        found_types = set()
        for row in csv_rows[2:]:
            desc = row.split(',')[0].lower()
            for edge_type in edge_case_types:
                if edge_type in desc:
                    found_types.add(edge_type)
        
        missing_types = set(edge_case_types) - found_types
        if not missing_types:
            validation_passed.append(f"Edge cases: All types present ({', '.join(edge_case_types)})")
        else:
            validation_errors.append(f"Missing edge case types: {', '.join(missing_types)}")
        
        # Check 5: Perfect row has no empty values (except Description)
        empty_in_perfect = []
        for i, val in enumerate(perfect_row[1:], start=1):
            if val.strip() == '':
                empty_in_perfect.append(header_row[i] if i < len(header_row) else f"Col {i}")
        
        if not empty_in_perfect:
            validation_passed.append("Perfect row: No unexpected empty values")
        else:
            validation_errors.append(f"Perfect row has empty values in: {', '.join(empty_in_perfect)}")
        
        # Display results
        st.write("---")
        st.write("### Validation Results:")
        
        for msg in validation_passed:
            st.success(f"✓ {msg}")
        
        if validation_errors:
            for msg in validation_errors:
                st.error(f"✗ {msg}")
        else:
            st.success("✓ All validations passed!")
        
        # Summary
        st.write("---")
        st.write("### Summary:")
        st.write(f"- Total rows: {len(csv_rows)}")
        st.write(f"- Total columns: {len(header_row)}")
        st.write(f"- Test cases: {len(csv_rows) - 2}")
        st.write(f"- Passed checks: {len(validation_passed)}")
        st.write(f"- Failed checks: {len(validation_errors)}")
