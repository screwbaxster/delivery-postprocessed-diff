import streamlit as st
import zipfile
import pandas as pd
import io
import csv
import requests
from bs4 import BeautifulSoup
import re

st.markdown(
    """
    <style>
    /* App background */
    .stApp {
        background-color: #D7F9F1;
        color: #40531B;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #A9CDC3;
    }

    /* Main content cards */
    div[data-testid="stVerticalBlock"] > div {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 10px;
        border: 1px solid #7AA095;
        box-shadow: 0 2px 8px rgba(64, 83, 27, 0.08);
        margin-bottom: 1.5rem;
    }

    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: #40531B;
    }

    /* Buttons */
    .stButton > button {
        background-color: #618B4A;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1rem;
    }

    .stButton > button:hover {
        background-color: #40531B;
        color: white;
    }

    /* File uploader */
    div[data-testid="stFileUploader"] {
        border: 1px dashed #7AA095;
        background-color: #F5FBF9;
        border-radius: 6px;
    }

    /* Success messages */
    div[data-testid="stAlert"][role="alert"] {
        background-color: #AFBC88;
        color: #40531B;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================
# Domain keyword mapping
# =========================
DOMAIN_KEYWORDS = {
    "Education": [
        "school", "university", "college", "student", "teacher",
        "course", "education", "training", "academy", "degree"
    ],
    "Finance": [
        "bank", "loan", "credit", "investment", "finance",
        "interest", "mortgage", "insurance", "account", "payment"
    ],
    "Medical": [
        "doctor", "hospital", "clinic", "medical", "medicine",
        "patient", "health", "pharmacy", "treatment"
    ],
    "Retail": [
        "store", "shop", "retail", "sale", "customer",
        "product", "purchase", "order"
    ],
    "Tax": [
        "tax", "taxes", "vat", "irs", "income tax",
        "deduction", "withholding", "fiscal", "return"
    ],
    "Travel": [
        "travel", "flight", "hotel", "booking",
        "reservation", "tourism", "trip", "vacation"
    ],
    "Vehicle": [
        "car", "vehicle", "auto", "automobile",
        "truck", "motorcycle", "engine", "vin"
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

@st.cache_data(ttl=3600)
def fetch_page_text(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=5)

        if r.status_code !=200:
            return ""

        soup = BeautifulSoup(r.text, "html.parser")

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        return normalize_text(
                    soup.get_text(separator=" ", strip=True)
        )

    except Exception:
        return ""

def detect_sector(text: str) -> str:
        text = normalize_text(text)

        scores = {
            sector: sum(1 for kw in keywords if kw in text)
            for sector, keywords in DOMAIN_KEYWORDS.items()
        }

        best_sector = max(scores, key=scores.get)

        if scores[best_sector] == 0:
            return "Unclassified"

        return best_sector
    
def detect_sector(text: str) -> str:
    text = text.lower()
    for sector, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return sector
    return "Unclassified"

def read_excel_safe(uploaded_file):
    try:
        return pd.read_excel(uploaded_file)
    except ImportError:
        st.error("Missing dependency: openpyxl. Please install it to read Excel files.")
        st.stop()
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        st.stop()

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
        "Porticus is a small collection of practical internal tools, "
        "designed to support users of the great Temple of Scripts."
    )
    st.markdown("---")
    st.markdown(
        "- **Comparatio** — Compare folders\n"
        "- **Collectio** — Collect files from Excel list\n"
        "- **Duplicatio** — Detect duplicate filenames\n"
        "- **Classificatio** — Classify URLs by sector"
    )

# =========================
# Comparatio
# =========================
if tool == "Comparatio (Folder Difference)":
    st.title("Comparatio (Folder Difference)")
    st.write("Files in Folder B not present in Folder A (ignores extensions).")

    folder_a_files = st.file_uploader("Folder A", accept_multiple_files=True)
    folder_b_files = st.file_uploader("Folder B", accept_multiple_files=True)

    if st.button("Compare"):
        if not folder_a_files or not folder_b_files:
            st.error("Please upload both folders.")
        else:
            names_a = {normalize(f.name) for f in folder_a_files}
            new_files = [f for f in folder_b_files if normalize(f.name) not in names_a]

            if not new_files:
                st.info("No new files found.")
            else:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for f in new_files:
                        zf.writestr(f.name, f.read())
                zip_buffer.seek(0)

                st.success(f"{len(new_files)} new file(s) found.")
                st.download_button(
                    "Download ZIP",
                    zip_buffer,
                    "new_files.zip",
                    "application/zip"
                )

# =========================
# Collectio
# =========================
if tool == "Collectio (Excel File Lookup)":
    st.title("Collectio (Excel File Lookup)")
    st.write("Collect files listed in Excel (Column A, no extension).")

    excel_file = st.file_uploader("Excel file", type=["xlsx", "xls"])
    search_files = st.file_uploader("Folder files", accept_multiple_files=True)

    if st.button("Find and collect files"):
        if not excel_file or not search_files:
            st.error("Upload both Excel and files.")
        else:
            df = read_excel_safe(excel_file)
            targets = df.iloc[:, 0].dropna().astype(str).str.lower().str.strip().tolist()

            index = {}
            for f in search_files:
                stem = normalize(f.name)
                index.setdefault(stem, []).append(f)

            found = []
            for t in targets:
                found.extend(index.get(t, []))

            if not found:
                st.info("No files found.")
            else:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for f in found:
                        zf.writestr(f.name, f.read())
                zip_buffer.seek(0)

                st.success(f"{len(found)} file(s) collected.")
                st.download_button(
                    "Download ZIP",
                    zip_buffer,
                    "collected_files.zip",
                    "application/zip"
                )

# =========================
# Duplicatio
# =========================
if tool == "Duplicatio (Common Files)":
    st.title("Duplicatio (Common Files)")
    st.write("Find filenames present in both folders.")

    folder_a_files = st.file_uploader("Folder A", accept_multiple_files=True)
    folder_b_files = st.file_uploader("Folder B", accept_multiple_files=True)

    if st.button("Find duplicates"):
        if not folder_a_files or not folder_b_files:
            st.error("Upload both folders.")
        else:
            names_a = {f.name for f in folder_a_files}
            names_b = {f.name for f in folder_b_files}
            duplicates = sorted(names_a & names_b)

            if not duplicates:
                st.info("No duplicates found.")
            else:
                csv_buffer = io.StringIO()
                writer = csv.writer(csv_buffer)
                writer.writerow(["filename"])
                for d in duplicates:
                    writer.writerow([d])

                st.success(f"{len(duplicates)} duplicate(s) found.")
                st.download_button(
                    "Download CSV",
                    csv_buffer.getvalue(),
                    "duplicate_filenames.csv",
                    "text/csv"
                )

# =========================
# Classificatio
# =========================
if tool == "Classificatio (URL Domain)":
    st.title("Classificatio (URL Domain)")
    st.write(
        "Uses Column A (keywords) and Column C (context) "
        "to assign a sector to the URL in Column D."
    )

    uploaded_file = st.file_uploader("Excel file", type=["xlsx", "xls"])

    if uploaded_file:
        df = read_excel_safe(uploaded_file)

        if df.shape[1] < 4:
            st.error("Excel must have at least columns A, C, and D.")
        else:
            col_a = df.columns[0]
            col_c = df.columns[2]
            col_d = df.columns[3]

            sectors = []

            with st.spinner("Fetching webpages and classifying URLs..."):
                for _, row in df.iterrows():
                    local_text = (
                        str(row[col_a]) + " " + str(row[col_c])
                    )

                    url_text = fetch_page_text(str(row[col_d]))

                    combined_text = local_text + " " + url_text

                    sectors.append(detect_sector(combined_text))

            df["Sector"] = sectors

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
st.caption(
    "Disclaimer: Files are processed in-memory only. "
    "No data is stored, saved, or kept on this page. "
    "Porticus is an internal utility."
)
