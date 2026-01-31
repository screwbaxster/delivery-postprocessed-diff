import streamlit as st
import zipfile
import pandas as pd
import io
import csv
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0

# =========================
# Language → Family mapping
# =========================
LANGUAGE_TO_FAMILY = {
    # Germanic
    "en": "germanic", "de": "germanic", "nl": "germanic",
    "sv": "germanic", "da": "germanic", "no": "germanic", "is": "germanic",
    # Romance
    "es": "romance", "fr": "romance", "it": "romance",
    "pt": "romance", "ro": "romance",
    # Slavic
    "ru": "slavic", "pl": "slavic", "cs": "slavic", "sk": "slavic",
    "uk": "slavic", "bg": "slavic", "sr": "slavic", "hr": "slavic",
    # Baltic
    "lt": "baltic", "lv": "baltic",
    # Celtic
    "ga": "celtic", "gd": "celtic", "cy": "celtic", "br": "celtic",
    # Uralic
    "fi": "uralic", "et": "uralic", "hu": "uralic",
}

# =========================
# Keyword sets by family
# =========================
KEYWORDS_BY_FAMILY = {
    "germanic": {
        "Education": ["school", "university", "student", "education", "course"],
        "Finance": ["bank", "loan", "payment", "insurance", "account"],
        "Medical": ["health", "doctor", "hospital", "patient"],
        "Retail": ["store", "shop", "order", "purchase"],
        "Tax": ["tax", "vat", "income", "fiscal"],
        "Travel": ["travel", "flight", "hotel", "booking"],
        "Vehicle": ["vehicle", "car", "registration", "license"],
    },
    "romance": {
        "Education": ["escuela", "université", "università", "educación", "étudiant"],
        "Finance": ["banco", "banque", "pagamento", "assurance"],
        "Medical": ["salud", "médecin", "ospedale"],
        "Retail": ["tienda", "magasin", "ordine"],
        "Tax": ["impuesto", "taxe", "imposta", "iva"],
        "Travel": ["viaje", "vol", "hotel", "réservation"],
        "Vehicle": ["vehículo", "voiture", "auto"],
    },
    "slavic": {
        "Education": ["школа", "университет", "учеба"],
        "Finance": ["банк", "кредит", "платеж"],
        "Medical": ["здоровье", "врач", "больница"],
        "Retail": ["магазин", "покупка"],
        "Tax": ["налог", "фискальный"],
        "Travel": ["путешествие", "отель"],
        "Vehicle": ["автомобиль", "регистрация"],
    },
    "baltic": {
        "Education": ["mokykla", "haridus"],
        "Finance": ["bankas", "konto"],
        "Medical": ["sveikata", "gydytojas"],
        "Retail": ["parduotuvė"],
        "Tax": ["mokestis"],
        "Travel": ["kelionė"],
        "Vehicle": ["automobilis"],
    },
    "celtic": {
        "Education": ["scoil", "oideachas"],
        "Finance": ["banc", "íocaíocht"],
        "Medical": ["sláinte", "dochtúir"],
        "Retail": ["siopa"],
        "Tax": ["cáin"],
        "Travel": ["taisteal"],
        "Vehicle": ["feithicil"],
    },
    "uralic": {
        "Education": ["koulu", "haridus", "iskola"],
        "Finance": ["pankki", "pank", "bank"],
        "Medical": ["terveys", "tervis", "egészség"],
        "Retail": ["kauppa", "pood", "bolt"],
        "Tax": ["vero", "maks", "adó"],
        "Travel": ["matka", "reis", "utazás"],
        "Vehicle": ["ajoneuvo", "sõiduk", "jármű"],
    },
}

# =========================
# Utility functions
# =========================
def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-zA-ZÀ-ž0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text)

def normalize_filename(filename: str) -> str:
    name = filename.lower().strip()
    if "." in name:
        name = name.rsplit(".", 1)[0]
    return name

def detect_document_language(df, columns):
    sample = " ".join(df[columns].astype(str).head(20).values.flatten())
    return detect(sample)

def detect_sector(text: str, keywords: dict) -> str:
    text = normalize(text)
    scores = {s: sum(1 for kw in kws if kw in text) for s, kws in keywords.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Unclassified"

@st.cache_data(ttl=3600)
def fetch_domain_text(url: str) -> str:
    try:
        domain = urlparse(url).netloc
        if not domain:
            return ""
        r = requests.get(f"https://{domain}", timeout=2)
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return normalize(soup.get_text())
    except Exception:
        return ""

# =========================
# Sidebar
# =========================
st.sidebar.title("Porticus")
tool = st.sidebar.radio(
    "Available tools",
    [
        "Home",
        "Comparatio (Folder Difference)",
        "Collectio (Excel File Lookup)",
        "Duplicatio (Common Files)",
        "Classificatio (Multilingual URL Domain)"
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
        "- **Classificatio** — Multilingual URL classification"
    )

# =========================
# Comparatio
# =========================
if tool == "Comparatio (Folder Difference)":
    st.title("Comparatio")
    a = st.file_uploader("Folder A", accept_multiple_files=True)
    b = st.file_uploader("Folder B", accept_multiple_files=True)

    if st.button("Compare"):
        if not a or not b:
            st.error("Upload both folders.")
        else:
            names_a = {normalize_filename(f.name) for f in a}
            diff = [f for f in b if normalize_filename(f.name) not in names_a]

            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
                for f in diff:
                    z.writestr(f.name, f.read())
            buf.seek(0)

            st.download_button("Download ZIP", buf, "new_files.zip")

# =========================
# Collectio
# =========================
if tool == "Collectio (Excel File Lookup)":
    st.title("Collectio")
    excel = st.file_uploader("Excel file", type=["xlsx"])
    files = st.file_uploader("Files", accept_multiple_files=True)

    if st.button("Collect"):
        df = pd.read_excel(excel)
        targets = df.iloc[:, 0].astype(str).str.lower().tolist()

        index = {}
        for f in files:
            index.setdefault(normalize_filename(f.name), []).append(f)

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for t in targets:
                for f in index.get(t, []):
                    z.writestr(f.name, f.read())
        buf.seek(0)

        st.download_button("Download ZIP", buf, "collected_files.zip")

# =========================
# Duplicatio
# =========================
if tool == "Duplicatio (Common Files)":
    st.title("Duplicatio")
    a = st.file_uploader("Folder A", accept_multiple_files=True)
    b = st.file_uploader("Folder B", accept_multiple_files=True)

    if st.button("Find duplicates"):
        dupes = sorted({f.name for f in a} & {f.name for f in b})
        csv_buf = io.StringIO()
        writer = csv.writer(csv_buf)
        writer.writerow(["filename"])
        for d in dupes:
            writer.writerow([d])
        st.download_button("Download CSV", csv_buf.getvalue(), "duplicates.csv")

# =========================
# Classificatio
# =========================
if tool == "Classificatio (Multilingual URL Domain)":
    st.title("Classificatio")

    use_web = st.checkbox("Use webpage content (slow)", value=False)
    uploaded = st.file_uploader("Upload Excel file", type=["xlsx"])

    if uploaded:
        df = pd.read_excel(uploaded)

        col_a = df.columns[0]
        col_c = df.columns[2]
        col_d = df.columns[3]

        lang = detect_document_language(df, [col_a, col_c])
        family = LANGUAGE_TO_FAMILY.get(lang)

        if not family:
            st.error(f"Unsupported language detected: {lang}")
            st.stop()

        st.info(f"Detected language: {lang.upper()} | Family: {family.capitalize()}")

        keywords = KEYWORDS_BY_FAMILY[family]

        sectors = []
        for _, row in df.iterrows():
            text = f"{row[col_a]} {row[col_c]}"
            if use_web:
                text += " " + fetch_domain_text(str(row[col_d]))
            sectors.append(detect_sector(text, keywords))

        df["Sector"] = sectors
        st.dataframe(df[[col_a, col_c, col_d, "Sector"]])

# =========================
# Footer
# =========================
st.caption("Files are processed in-memory only. Porticus is an internal utility.")
