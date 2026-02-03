import streamlit as st
import zipfile
import pandas as pd
import io
import csv
import re
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0

INSPIRING_QUOTES = [

    # Marcus Aurelius — The Stoic Mind
    "The happiness of your life depends upon the quality of your thoughts. — Marcus Aurelius",
    "Waste no more time arguing about what a good man should be. Be one. — Marcus Aurelius",
    "The best revenge is to be unlike him who performed the injury. — Marcus Aurelius",
    "Everything we hear is an opinion, not a fact. Everything we see is a perspective, not the truth. — Marcus Aurelius",
    "If it is not right, do not do it; if it is not true, do not say it. — Marcus Aurelius",
    "Very little is needed to make a happy life; it is all within yourself, in your way of thinking. — Marcus Aurelius",
    "The soul becomes dyed with the color of its thoughts. — Marcus Aurelius",
    "When you arise in the morning, think of what a precious privilege it is to be alive. — Marcus Aurelius",
    "Loss is nothing else but change, and change is Nature’s delight. — Marcus Aurelius",
    "Accept the things to which fate binds you, and love the people with whom fate brings you together. — Marcus Aurelius",
    "He who lives in harmony with himself lives in harmony with the universe. — Marcus Aurelius",
    "The impediment to action advances action. What stands in the way becomes the way. — Marcus Aurelius",
    "Our life is what our thoughts make it. — Marcus Aurelius",
    "It is not death that a man should fear, but he should fear never beginning to live. — Marcus Aurelius",
    "Because a thing seems difficult for you, do not think it impossible for anyone to accomplish. — Marcus Aurelius",
    "Receive without conceit, release without struggle. — Marcus Aurelius",
    "Nowhere can man find a quieter or more untroubled retreat than in his own soul. — Marcus Aurelius",
    "Think of yourself as dead. You have lived your life. Now, take what’s left and live it properly. — Marcus Aurelius",
    "Do every act of your life as though it were the very last act of your life. — Marcus Aurelius",
    "Time is a sort of river of passing events, and strong is its current. — Marcus Aurelius",
    "Limit yourself to the present. — Marcus Aurelius",

    # Seneca — Resilience
    "Luck is what happens when preparation meets opportunity. — Seneca",
    "We suffer more often in imagination than in reality. — Seneca",
    "Difficulties strengthen the mind, as labor does the body. — Seneca",
    "If a man knows not to which port he sails, no wind is favorable. — Seneca",
    "True happiness is to enjoy the present without anxious dependence upon the future. — Seneca",
    "Fire tests gold, adversity tests brave men. — Seneca",
    "While we are postponing, life speeds by. — Seneca",
    "Begin at once to live, and count each separate day as a separate life. — Seneca",
    "The greatest remedy for anger is delay. — Seneca",
    "Sometimes even to live is an act of courage. — Seneca",
    "Life is long if you know how to use it. — Seneca",

    # Cicero — Wisdom and Statecraft
    "A room without books is like a body without a soul. — Cicero",
    "While there’s life, there’s hope. — Cicero",
    "To be ignorant of what occurred before you were born is to remain always a child. — Cicero",
    "Gratitude is not only the greatest of virtues, but the parent of all others. — Cicero",
    "If you have a garden and a library, you have everything you need. — Cicero",
    "Great is the power of habit. — Cicero",
    "Brief is the life given us by nature, but the memory of a life well spent is eternal. — Cicero",
    "Silence is one of the great arts of conversation. — Cicero",
    "Friendship improves happiness and abates misery. — Cicero",

    # Poets & Playwrights
    "Fortune favors the bold. — Virgil",
    "Love conquers all; let us, too, yield to love. — Virgil",
    "Seize the day, trusting as little as possible in tomorrow. — Horace",
    "Dripping water hollows out stone, not through force but through persistence. — Ovid",
    "He who has begun has half done. Dare to be wise; begin! — Horace",
    "The burden which is well borne becomes light. — Ovid",

    # General Roman Wisdom
    "A healthy mind in a healthy body. — Juvenal",
    "Men willingly believe what they wish to be true. — Julius Caesar",
    "In wine, there is truth. — Pliny the Elder",
    "Great things are not done by impulse, but by a series of small things brought together.",
    "Everything changes, nothing perishes. — Ovid"
]
if "quotes_shuffled" not in st.session_state:
        random.shuffle (INSPIRING_QUOTES)
        st.session_state.quotes_shuffled = True
    
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
        "Classificatio (Multilingual URL Domain)",
        "Gratia (Inspire me)"
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

st.markdown(
    "Compares two folders and identifies files that exist in Folder B but not in Folder A. "
    "File extensions are ignored, and input files are never modified."
)
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
# Duplicatio
# =========================
if tool == "Gratia (Inspire me)":
    st.title("Gratia")

    st.write(
        "A small pause. Nothing to optimize. Nothing to fix."
    )

    if "gratia_index" not in st.session_state:
        st.session_state.gratia_index = 0

    if st.button("Tell me something to reflect on"):
        quote = INSPIRING_QUOTES[st.session_state.gratia_index]
        st.session_state.gratia_index = (
            st.session_state.gratia_index + 1
        ) % len(INSPIRING_QUOTES)
        st.success(quote)

# =========================
# Footer
# =========================
st.caption("Files are processed in-memory only. Porticus is an internal utility.")
