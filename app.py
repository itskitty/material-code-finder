import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
import pdfplumber

# Page Setup
st.set_page_config(page_title="Material Code Finder", page_icon="🔍", layout="wide")
st.title("🔍 Material Code Finder")
st.write("Find product codes individually, paste batch material lists, or process PDF BOQ files.")

# 1. Google Sheet Setup
SHEET_ID = "1fChLWdhv385Zt0dyVVVixz7esTrMxQYePc3ugvsIPgg"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=600)
def load_data():
    return pd.read_csv(URL)

try:
    df = load_data()
    po_names = df['ชื่อในPO'].astype(str).tolist()

    # Create 3 Navigation Tabs
    tab1, tab2, tab3 = st.tabs(["1️⃣ Single Item Search", "2️⃣ Paste List of Materials", "3️⃣ Upload PDF BOQ"])

    # -------------------------------------------------------------
    # TAB 1: Single Item Search
    # -------------------------------------------------------------
    with tab1:
        query = st.text_input("Enter description / keywords:", placeholder="e.g. 200 lb gemtex hfc227")
        if query:
            matches = process.extract(query, po_names, scorer=fuzz.token_set_ratio, limit=10)
            results = []
            for text_match, score, original_index in matches:
                row = df.iloc[original_index]
                results.append({
                    "Product Code": row["Product Code"],
                    "PO Description": row["ชื่อในPO"],
                    "Unit": row.get("Unit Name (PO)", "Ea"),
                    "Match Score": f"{round(score, 1)}%"
                })
            st.dataframe(pd.DataFrame(results), use_container_width=True)

    # -------------------------------------------------------------
    # TAB 2: Batch List Search (Multiple lines pasted)
    # -------------------------------------------------------------
    with tab2:
        st.subheader("Batch Material Matcher")
        st.write("Paste multiple lines of material descriptions below:")
        batch_input = st.text_area("Material List (one item per line):", height=200, 
                                   placeholder="Cabinet WxHxD 400x1100x300\nGemtex HFC-227ea 106-liter\nSelector valve 2 inch")
        
        if st.button("Process Batch List"):
            lines = [l.strip() for l in batch_input.split("\n") if l.strip()]
            if lines:
                batch_results = []
                for line in lines:
                    match = process.extractOne(line, po_names, scorer=fuzz.token_set_ratio)
                    if match:
                        best_match, score, idx = match
                        row = df.iloc[idx]
                        batch_results.append({
                            "Pasted Material Item": line,
                            "Matched Product Code": row["Product Code"],
                            "Matched PO Description": row["ชื่อในPO"],
                            "Unit": row.get("Unit Name (PO)", "Ea"),
                            "Match Score": f"{round(score, 1)}%"
                        })
                res_df = pd.DataFrame(batch_results)
                st.dataframe(res_df, use_container_width=True)
                
                # Download Button
                csv_data = res_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Results (CSV)", csv_data, "matched_materials.csv", "text/csv")

    # -------------------------------------------------------------
    # TAB 3: PDF File Upload (Powered by pdfplumber)
    # -------------------------------------------------------------
    with tab3:
        st.subheader("PDF BOQ Processing")
        uploaded_pdf = st.file_uploader("Upload a PDF file (BOQ, Purchase Order, or Spec Sheet):", type=["pdf"])
        
        if uploaded_pdf is not None:
            pdf_lines = []
            
            # Extract text using pdfplumber
            with pdfplumber.open(uploaded_pdf) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        for line in text.split("\n"):
                            clean_line = line.strip()
                            # Filter out very short noise lines
                            if len(clean_line) > 3:
                                pdf_lines.append(clean_line)
            
            st.info(f"Successfully extracted {len(pdf_lines)} text lines from PDF.")
            
            if pdf_lines and st.button("Match PDF Lines to Material Codes"):
                pdf_results = []
                for line in pdf_lines:
                    match = process.extractOne(line, po_names, scorer=fuzz.token_set_ratio)
                    if match:
                        best_match, score, idx = match
                        # Filter to relevant matches (score > 40%)
                        if score > 40:
                            row = df.iloc[idx]
                            pdf_results.append({
                                "PDF Line Item": line,
                                "Matched Product Code": row["Product Code"],
                                "Matched PO Description": row["ชื่อในPO"],
                                "Unit": row.get("Unit Name (PO)", "Ea"),
                                "Match Score": f"{round(score, 1)}%"
                            })
                
                res_pdf_df = pd.DataFrame(pdf_results)
                st.dataframe(res_pdf_df, use_container_width=True)
                
                # Download Button
                csv_pdf = res_pdf_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download PDF Matches (CSV)", csv_pdf, "pdf_matched_materials.csv", "text/csv")

except Exception as e:
    st.error(f"Error loading app data. Details: {e}")
