# Automatic XPath - Project Summary

## Project Goal
Build an automated QA testing tool that:
1. Captures XPaths and user input values from web forms via browser recording
2. Generates test case data (edge cases, permutations) for QA automation testing
3. Outputs in company format for integration with existing QA workflows

---

## Version 4: XPath Recorder (COMPLETE)

### Location: `/version4_QA/`

### Files:
- `recorder.py` - Subprocess that launches Chromium, captures XPaths + values via JavaScript injection
- `app_v4.py` - Streamlit UI with URL input, format selection (JSON/CSV/Python), Start/Stop buttons

### How it works:
1. User enters URL in Streamlit UI
2. Clicks "Start Recording" → Streamlit runs `recorder.py` as subprocess
3. Chromium browser opens, user interacts with form (clicks, types values)
4. JavaScript captures: Label, XPath, Strategy, Matches, Action (click/change), Value
5. User clicks "Stop Recording" → Streamlit sends SIGTERM → `recorder.py` saves files and exits
6. Output files saved to `version4_QA/xpath_data_retrieved/`

### Key Technical Concepts:
- `subprocess.Popen()` - Run recorder.py as background process
- `signal.signal(SIGTERM, cleanup)` - Handle stop signal from Streamlit
- `page.wait_for_timeout(500)` - Keep Playwright event loop running (not time.sleep!)
- `page.expose_function("reportXPath", handle_xpath)` - Bridge between JS and Python

### Output CSV Format:
Label,XPath,Strategy,Matches,Action,Value
firstName,//[@id="firstName"],id,1,click,NaN
firstName,//[@id="firstName"],id,1,change,PRAKYATH
email,//*[@id="email"],id,1,change,PRAK@GMAIL.COM
...



---

## Test Case Generation (IN PROGRESS)

### Location: `/test_case_generation/`

### Files:
- `test.ipynb` - Faker-based generator (creates 100 random test data rows)
- `test2.ipynb` - Manual scenario generator with descriptions (non-LLM approach)
- `llm_generator.py` - Streamlit UI + Groq LLM for generating edge case test scenarios
- `xpaths_*.csv` - Sample input data from V4 recorder

### Approach 1: Faker Library (test.ipynb) - COMPLETE
Generates 100 rows of random test data using Python Faker library.

Key functions:
- `detect_field_type(label)` - Detects if field is name/email/phone/text based on label
- `generate_values(field_type, original_value, count)` - Creates fake values for each type
- `generate_test_cases(df, num_rows)` - Main function that produces output DataFrame
Limitation: Values/Columns have to be hardcoded, needs to be dynamic for different use-cases

### Approach 2: LLM Generator (llm_generator.py) - IN PROGRESS

Uses Groq API (free tier) with gpt-oss model to generate edge case test scenarios.

**Current Status:** Working but has issues with:
1. Missing columns (middleName click column gets dropped)
2. Inconsistent CSV output (sometimes wrong field count per row)
3. Hardcoded values in prompt that break with different input CSVs

**Environment Variable Required:**
```bash
export GROQ_API_KEY="your-key-here"
Or use .env file with python-dotenv

Prompt Issues to Fix (in llm_generator.py):

Line 51: Hardcoded column names pose a problem for tool being dynamic, different csv will cause an error in required output
Lines 76-77: Hardcoded example rows with specific column names - should be removed or made dynamic
LLM sometimes confuses column structure when there are duplicate column names (click/input pairs)
Company QA Format
The company expects test data in this format:

Row 1: Element names (horizontal)
Row 2: Actions (click/change)
Row 3+: Test cases (TC_001, TC_002, etc.)

Description        | firstName | firstName | email | email          | ...
Action             | click     | change    | click | change         | ...
Perfect template   | Click     | PRAKYATH  | Click | PRAK@GMAIL.COM | ...
firstName - empty  | Click     |           | Click | PRAK@GMAIL.COM | ...
email - invalid    | Click     | PRAKYATH  | Click | notanemail     | ...

Next Steps
Fix LLM prompt in llm_generator.py:

Make prompt fully dynamic for any CSV input
Test with different forms:

Test Scenarios: Edge cases with descriptions (current focus)
Test Cases: Column order permutations (what if user fills form in different order?)
Dependencies

playwright>=1.48.0
streamlit>=1.32.0
pandas
numpy
matplotlib
google-generativeai
faker
groq
python-dotenv
Running the Apps

# V4 Recorder
cd version4_QA
streamlit run app_v4.py

# LLM Test Generator
cd test_case_generation
export GROQ_API_KEY="your-key"
streamlit run llm_generator.py


---
