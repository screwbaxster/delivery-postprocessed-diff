import streamlit as st
import zipfile
import pandas as pd
import io
import csv
import requests
import re
import tempfile
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# =========================
# Domain keyword mapping
# =========================
DOMAIN_KEYWORDS = {
    "Education": [
        "school", "schools", "university", "universities", "college", "campus",
        "faculty", "student", "students", "teacher", "teachers", "professor",
        "lecturer", "instructor", "education", "educational", "learning",
        "online learning", "e learning", "distance learning",
        "course", "courses", "curriculum", "syllabus",
        "degree", "degrees", "bachelor", "master", "phd",
        "certificate", "certification", "diploma",
        "tuition", "fees", "enrollment", "admissions",
        "classroom", "credits", "exam", "assessment",
        "training", "academy", "seminar", "workshop",
        "learning platform", "lms", "student portal"
    ],
    "Finance": [
        "bank", "banks", "banking", "financial", "finance",
        "loan", "loans", "lending", "credit", "debit", "mortgage",
        "interest", "interest rate", "apr",
        "investment", "investing", "portfolio", "assets",
        "capital", "fund", "funding",
        "insurance", "policy", "premium", "claim",
        "account", "accounts", "checking", "savings",
        "payment", "payments", "billing", "invoice",
        "transaction", "transfer", "wire",
        "swift", "iban",
        "wallet", "digital wallet", "fintech",
        "checkout", "subscription", "pricing",
        "payroll", "salary"
    ],
    "Medical": [
        "doctor", "physician", "hospital", "clinic",
        "medical", "medicine", "health", "healthcare",
        "patient", "patients", "patient care",
        "appointment", "schedule",
        "diagnosis", "diagnostic", "treatment", "therapy",
        "prescription", "pharmacy", "medication",
        "nurse", "nursing",
        "laboratory", "lab results", "imaging", "radiology",
        "surgery", "procedure",
        "telemedicine", "virtual visit",
        "ehr", "emr", "patient portal",
        "coverage", "wellness", "mental health"
    ],
    "Retail": [
        "store", "shop", "shopping", "retail",
        "product", "products", "catalog", "inventory",
        "purchase", "buy", "order",
        "checkout", "cart", "basket",
        "customer", "pricing", "price",
        "discount", "promotion",
        "sale", "offers", "deals",
        "shipping", "delivery", "returns",
        "refund", "exchange",
        "online store", "ecommerce",
        "wishlist", "tracking",
        "brand", "subscription", "membership"
    ],
    "Tax": [
        "tax", "taxes", "taxation",
        "income tax", "corporate tax", "sales tax",
        "vat", "value added tax",
        "irs", "tax authority",
        "tax return", "filing",
        "deduction", "exemption", "credit",
        "withholding", "payroll tax",
        "fiscal", "audit", "compliance",
        "liability", "refund",
        "tax forms", "tax advisor",
        "self assessment", "tax payment"
    ],
    "Travel": [
        "travel", "trip", "tourism",
        "flight", "airline",
        "hotel", "accommodation",
        "booking", "reservation",
        "destination", "itinerary",
        "vacation", "holiday",
        "tour", "excursion",
        "boarding pass", "check in",
        "car rental", "cruise",
        "airport", "transport",
        "fare", "ticket",
        "travel insurance", "travel agency"
    ],
    "Vehicle": [
        "vehicle", "car", "auto", "automobile",
        "truck", "van", "suv",
        "motorcycle", "motorbike",
        "engine", "transmission", "fuel",
        "electric vehicle", "ev",
        "vin", "registration",
        "license plate", "inspection",
        "insurance", "auto insurance",
        "maintenance", "service",
        "repair", "parts",
        "dealer", "dealership",
        "leasing", "warranty"
    ],
}

# =========================
# Utility functions
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
        sector: sum(1 for kw in keywords if kw in text)
        for sector, keywords in DOMAIN_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Unclassified"

def read_excel_safe(uploaded_file):
    try:
        return pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        st.stop()

@st.cache_data(ttl=3600)
def fetch_domain_text(url: str) -> str:
    try:
        domain = urlparse(url).netloc
        if not domain:
            return ""

        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(
            f"https://{domain}",
            headers=headers,
            timeout=2
        )

        if r.status_code != 200:
            return ""

        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        return normalize_text(
            soup.get_text(separator=" ", strip=True)
        )
    except Exception:
        return ""

# =========================
# Sidebar
# =========================
st.sidebar.title("Porticus")
st.sidebar.markdown("Practical tools")

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
# Home
# =========================
if tool == "Home":
    st.markdown("## Welcome to The Porticus")
    st.markdown(
        "- **Comparatio** — Compare folders\n"
        "- **Collectio** — Collect files from Excel list\n"
        "- **Duplicatio** — Detect duplicate filenames\n"
        "- **Classificatio** — Classify URLs by sector"
    )

# =========================
# Classificatio
# =========================
if tool == "Classificatio (URL Domain)":
    st.title("Classificatio (URL Domain)")
    st.write(
        "Default behaviour uses only Excel content. "
        "Optional webpage scanning increases accuracy but is slower."
    )

    use_web = st.checkbox("Use webpage content (slow)", value=False)
    BATCH_SIZE = 25

    uploaded_file = st.file_uploader("Excel file", type=["xlsx", "xls"])

    if uploaded_file:
        df = read_excel_safe(uploaded_file)

        if df.shape[1] < 4:
            st.error("Excel must contain at least columns A, C, and D.")
            st.stop()

        col_a = df.columns[0]
        col_c = df.columns[2]
        col_d = df.columns[3]

        if "sector_results" not in st.session_state:
            st.session_state.sector_results = {}

        total_rows = len(df)
        progress = st.progress(0.0)
        status = st.empty()

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            temp_path = tmp.name

        for start in range(0, total_rows, BATCH_SIZE):
            end = min(start + BATCH_SIZE, total_rows)
            status.write(f"Processing rows {start + 1}–{end} of {total_rows}")

            batch = df.iloc[start:end]

            for idx, row in batch.iterrows():
                if idx in st.session_state.sector_results:
                    continue

                local_text = str(row[col_a]) + " " + str(row[col_c])
                url_text = fetch_domain_text(str(row[col_d])) if use_web else ""
                combined = local_text + " " + url_text

                st.session_state.sector_results[idx] = detect_sector(combined)

            df["Sector"] = df.index.map(
                lambda i: st.session_state.sector_results.get(i, "")
            )
            df.to_excel(temp_path, index=False)

            progress.progress(end / total_rows)

        df["Sector"] = df.index.map(
            lambda i: st.session_state.sector_results.get(i, "Unclassified")
        )

        st.success("Sector classification complete.")
        st.dataframe(df[[col_a, col_c, col_d, "Sector"]])

        output = "urls_classified_by_sector.xlsx"
        df.to_excel(output, index=False)

        with open(output, "rb") as f:
            st.download_button(
                "Download Excel",
                f,
                output,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# =========================
# Footer
# =========================
st.caption("Files are processed in-memory only. Porticus is an internal utility.")
