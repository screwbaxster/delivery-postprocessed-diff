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

    # =========================
    # GERMANIC
    # =========================
    "germanic": {
        "Education": [
            "school", "schools", "education", "educational", "student", "students",
            "teacher", "teachers", "university", "college", "campus", "degree",
            "course", "courses", "curriculum", "enrollment", "admissions",
            "training", "academy", "learning", "learning platform", "lms"
        ],
        "Finance": [
            "bank", "banking", "financial", "finance", "loan", "credit", "debit",
            "account", "accounts", "payment", "payments", "billing", "invoice",
            "transaction", "transfer", "interest", "mortgage", "insurance",
            "policy", "premium", "portfolio", "investment", "fund", "capital"
        ],
        "Medical": [
            "health", "healthcare", "medical", "medicine", "doctor", "physician",
            "hospital", "clinic", "patient", "patients", "appointment",
            "treatment", "therapy", "prescription", "pharmacy", "diagnosis",
            "care", "wellness", "mental health"
        ],
        "Retail": [
            "store", "shop", "retail", "product", "products", "catalog",
            "order", "orders", "purchase", "checkout", "cart", "customer",
            "pricing", "price", "sale", "discount", "promotion", "shipping",
            "delivery", "returns", "refund"
        ],
        "Tax": [
            "tax", "taxes", "taxation", "income tax", "sales tax", "vat",
            "fiscal", "tax return", "filing", "deduction", "withholding",
            "tax authority", "revenue service", "audit", "compliance"
        ],
        "Travel": [
            "travel", "trip", "tourism", "flight", "airline", "airport",
            "hotel", "accommodation", "booking", "reservation", "destination",
            "itinerary", "vacation", "holiday", "ticket", "boarding pass"
        ],
        "Vehicle": [
            "vehicle", "vehicles", "car", "auto", "automobile", "truck",
            "motorcycle", "engine", "registration", "license", "inspection",
            "insurance", "maintenance", "service", "repair", "dealer"
        ],
    },

    # =========================
    # ROMANCE
    # =========================
    "romance": {
        "Education": [
            "escuela", "école", "scuola", "educación", "éducation", "istruzione",
            "estudiante", "étudiant", "studente", "universidad", "université",
            "università", "curso", "cours", "corso", "formación", "formation",
            "apprentissage", "enseñanza", "insegnamento"
        ],
        "Finance": [
            "banco", "banque", "banca", "finanzas", "finance", "credito", "crédit",
            "cuenta", "compte", "conto", "pago", "paiement", "pagamento",
            "factura", "facturation", "assurance", "seguro", "investissement",
            "investimento", "fonds", "capital"
        ],
        "Medical": [
            "salud", "santé", "salute", "medicina", "médical", "médico",
            "doctor", "médecin", "ospedale", "hospital", "clínica", "clinique",
            "paciente", "patient", "traitement", "traitement", "prescripción",
            "farmacia"
        ],
        "Retail": [
            "tienda", "magasin", "negozio", "venta", "vente", "vendita",
            "producto", "produit", "prodotto", "pedido", "commande", "ordine",
            "cliente", "client", "prezzo", "prix", "promoción", "réduction"
        ],
        "Tax": [
            "impuesto", "impuestos", "taxe", "impôt", "imposta",
            "fiscal", "fiscale", "iva", "tva", "déclaration",
            "retenue", "retención", "autorité fiscale"
        ],
        "Travel": [
            "viaje", "voyage", "viaggio", "vuelo", "vol", "volo",
            "hotel", "hébergement", "prenotazione", "réservation",
            "destino", "destination", "vacances", "vacaciones"
        ],
        "Vehicle": [
            "vehículo", "véhicule", "veicolo", "auto", "voiture",
            "immatriculation", "registrazione", "assicurazione",
            "réparation", "entretien", "concessionnaire"
        ],
    },

    # =========================
    # SLAVIC
    # =========================
    "slavic": {
        "Education": [
            "школа", "университет", "образование", "учеба", "студент",
            "student", "kurs", "edukacja", "nauka", "uczelnia"
        ],
        "Finance": [
            "банк", "kredyt", "кредит", "płatność", "платеж",
            "konto", "счет", "ubezpieczenie", "страхование"
        ],
        "Medical": [
            "здоровье", "zdrowie", "zdraví", "врач", "lekarz",
            "больница", "szpital", "лечение", "terapia"
        ],
        "Retail": [
            "магазин", "sklep", "zakup", "покупка", "заказ",
            "zamówienie", "klient", "cena"
        ],
        "Tax": [
            "налог", "podatek", "daň", "фискальный",
            "rozliczenie", "deklaracja"
        ],
        "Travel": [
            "путешествие", "podróż", "cestování", "hotel",
            "lot", "рейс"
        ],
        "Vehicle": [
            "автомобиль", "samochód", "vozidlo", "rejestracja",
            "страховка", "ubezpieczenie"
        ],
    },

    # =========================
    # BALTIC
    # =========================
    "baltic": {
        "Education": [
            "mokykla", "haridus", "õpe", "õpilane", "studentas",
            "universitetas", "ülikool"
        ],
        "Finance": [
            "bankas", "pank", "konto", "makse", "laen",
            "kindlustus", "toetus"
        ],
        "Medical": [
            "sveikata", "tervis", "gydytojas", "arst",
            "haigla", "ligoninė"
        ],
        "Retail": [
            "parduotuvė", "pood", "klientas", "klient",
            "kaina", "hind"
        ],
        "Tax": [
            "mokestis", "mokesčiai", "maks", "maksustamine"
        ],
        "Travel": [
            "kelionė", "reis", "viešbutis", "majutus"
        ],
        "Vehicle": [
            "automobilis", "auto", "registreerimine", "registracija"
        ],
    },

    # =========================
    # CELTIC
    # =========================
    "celtic": {
        "Education": [
            "scoil", "oideachas", "foghlaim", "mac léinn"
        ],
        "Finance": [
            "banc", "íocaíocht", "airgead", "iasacht"
        ],
        "Medical": [
            "sláinte", "dochtúir", "othar"
        ],
        "Retail": [
            "siopa", "custaiméir", "praghas"
        ],
        "Tax": [
            "cáin", "ioncam"
        ],
        "Travel": [
            "taisteal", "óstán"
        ],
        "Vehicle": [
            "feithicil", "carr"
        ],
    },

    # =========================
    # URALIC
    # =========================
    "uralic": {
        "Education": [
            "koulu", "koulutus", "oppilaitos", "opiskelija",
            "yliopisto", "ammattikorkeakoulu", "opinto",
            "haridus", "õpilane", "ülikool",
            "iskola", "oktatás", "tanuló", "egyetem"
        ],
        "Finance": [
            "pankki", "pank", "bank", "tili", "konto", "számla",
            "laina", "laen", "hitel", "maksu", "makse", "fizetés",
            "rahoitus", "kindlustus", "biztosítás",
            "etuus", "toetus", "támogatás", "kela"
        ],
        "Medical": [
            "terveys", "tervis", "egészség",
            "lääkäri", "arst", "orvos",
            "sairaala", "haigla", "kórház",
            "potilas", "patsient", "beteg"
        ],
        "Retail": [
            "kauppa", "pood", "bolt",
            "ostos", "ost", "vásárlás",
            "asiakas", "klient", "ügyfél"
        ],
        "Tax": [
            "vero", "verotus", "verohallinto",
            "maks", "maksustamine",
            "adó", "adózás", "adóhatóság"
        ],
        "Travel": [
            "matka", "reis", "utazás",
            "lento", "lend", "repülés",
            "oleskelulupa", "viisumi", "vízum"
        ],
        "Vehicle": [
            "ajoneuvo", "sõiduk", "jármű",
            "auto", "autó",
            "rekisteröinti", "registreerimine",
            "vakuutus", "biztosítás"
        ],
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
    return best if scores[best] > 0 else "Out of domain scope"

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

        total_rows = len(df)
        progress_bar = st.progress(0.0)
        status_text = st.empty()

        sectors = []

        for i, (_, row) in enumerate(df.iterrows(), start=1):
            text = f"{row[col_a]} {row[col_c]}"
            if use_web:
                text += " " + fetch_domain_text(str(row[col_d]))
            sectors.append(detect_sector(text, keywords))
            
            progress_bar.progress(i / total_rows)
            status_text.write(f"Processing {i} of {total_rows}")

        df["Sector"] = sectors
        st.dataframe(df[[col_a, col_c, col_d, "Sector"]])

# =========================
# Footer
# =========================
st.caption("Files are processed in-memory only. Porticus is an internal utility.")
