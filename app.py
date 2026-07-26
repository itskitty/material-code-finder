import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz

# Page Setup
st.set_page_config(page_title="Material Code Finder", page_icon="🔍", layout="wide")
st.title("🔍 Material Code Finder")
st.write("Type any product description or specification to quickly find the Product Code.")

# 1. Replace with your actual Google Sheet ID
SHEET_ID = "YOUR_SHEET_ID_HERE"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# Cache data for 10 minutes for fast performance
@st.cache_data(ttl=600)
def load_data():
    return pd.read_csv(URL)

try:
    df = load_data()
    
    # Search Input Box
    query = st.text_input("Enter description / keywords:", placeholder="e.g. 200 lb gemtex hfc227")
    
    if query:
        po_names = df['ชื่อในPO'].astype(str).tolist()
        
        # Fuzzy match
        matches = process.extract(
            query, 
            po_names, 
            scorer=fuzz.token_set_ratio, 
            limit=10
        )
        
        results = []
        for text_match, score, original_index in matches:
            row = df.iloc[original_index]
            results.append({
                "Product Code": row["Product Code"],
                "PO Description": row["ชื่อในPO"],
                "Unit": row.get("Unit Name (PO)", "Ea"),
                "Match Score": f"{round(score, 1)}%"
            })
            
        # Display Results Table
        st.subheader("Search Results")
        st.dataframe(pd.DataFrame(results), use_container_width=True)

except Exception as e:
    st.error(f"Error loading Google Sheet. Please check your Sheet ID and sharing permissions. Details: {e}")
