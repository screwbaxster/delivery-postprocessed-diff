import streamlit as st
import zipfile
import pandas as pd
import io
import csv
import requests
from bs4 import BeautifulSoup
import re

# =========================
# THEME / STYLING
# =========================
st.markdown(
    """
    <style>
    /* Global background */
    .stApp {
        background-color: #102E50;
        color: #F5C45E;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #F5C45E;
    }

    section[data-testid="stSidebar"] * {
        color: #102E50;
    }

    /* Card component */
    .porticus-card {
        background-color: #F5C45E;
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid #E78B48;
        box-shadow: 0 6px 14px rgba(0,0,0,0.25);
        margin-bottom: 1.75rem;
        color: #102E50;
    }

    /* Headings */
    h1, h2, h3 {
        color: #BE3D2A;
    }

    /* Buttons */
    .stButton > button {
        background-color: #E78B48;
        color: #102E50;
        border-radius: 6px;
        border: none;
        font-weight: 600;
    }

    .stButton > button:hover {
        background-color: #BE3D2A;
        color: #F5C45E;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def card(html: str):
    st.markdown(f'<div class="porticus-card">{html}</div>', unsafe_allow_html=True)

# =========================
# DOMAIN KEYWORDS
# =========================
DOMAIN_KEYWORDS = {
    "Education": ["school", "university", "college", "student", "education", "learning", "course"],
    "Finance": ["bank", "loan", "credit", "finance", "investment", "interest", "insurance"],
    "Medical": ["doctor", "hospital", "clinic", "medical", "health", "medicine", "patient"],
    "Retail": ["store", "shop", "retail", "sale", "customer", "product"],
    "Tax": ["tax", "vat", "irs", "income tax", "deduction"],
    "Travel": ["travel", "flight", "hotel", "booking", "tourism"],
    "Vehicle": ["car", "vehicle", "auto", "automobile", "truck", "engine"],
}

# =========================
# UTILITIES
# =========================
def normalize(filename: str) -> str:
    name = filename.lower().strip()
    if "." in name:
        name = name.rsplit(".", 1)[0]
    return name

def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def detect_sector(text: str) -> str:
    text = normalize_text(text)
    scores = {
        sector: sum(1 for kw in kws if kw in text)
        for sector, kws in DOMAIN_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Unclassified"

@st.cache_data(ttl=3600)
def fetch_page_text(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return normalize_text(soup.get_text(" "))
    except Exception:
        return ""

def read_excel_safe(uploaded_file):
    try:
        return pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Cannot read Excel file: {e}")
        st.stop()

# =========================
# SIDEBAR
# =========================
st.sidebar.title("Porticus")
tool = st.sidebar.radio(
    "Available tools",
    [
        "Home",
        "Comparatio (Folder Difference)",
        "Collectio (Excel File Lookup)",
        "Duplicatio (Common Files)",
        "Classificatio (URL Domain)"
    ]
)

# =========================
# HOME (REFACTORED)
# =========================
if tool == "Home":

    card("""
    <h2>Welcome to The Porticus</h2>
    <p>
    Porticus is a small collection of practical internal tools,
    designed to support users of the great Temple of Scripts.
    </p>
    """)

    card("""
    <h3>Available Tools</h3>
    <ul>
        <li><b>Comparatio</b> — Compare two folders and retrieve files missing from a delivery.</li>
        <li><b>Collectio</b> — Collect files from a folder based on an Excel list.</li>
        <li><b>Duplicatio</b> — Identify duplicate filenames across folders.</li>
        <li><b>Classificatio</b> — Classify URLs by sector using keywords and webpage content.</li>
    </ul>
    """)

    card("""
    <h3>Design Philosophy</h3>
    <p>
    What exists because it must, not because it is popular.
    </p>
    """)

# =========================
# (OTHER TOOLS UNCHANGED)
# =========================
# Comparatio, Collectio, Duplicatio, Classificatio
# remain exactly as you already implemented them
# and can be pasted below without modification.
# =========================

st.caption("Files are processed in-memory only. Porticus is an internal utility.")
