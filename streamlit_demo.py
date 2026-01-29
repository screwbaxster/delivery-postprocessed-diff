import streamlit as st
import zipfile
import pandas as pd
from pathlib import Path
import io
import csv


def normalize(filename: str) -> str:
    """
    Normalize filename for comparison:
    - lowercase
    - strip extension
    """
    name = filename.lower().strip()
    if "." in name:
        name = name.rsplit(".", 1)[0]
    return name


# =========================
# Sidebar (navigation)
# =========================
st.sidebar.title("Porticus")
st.sidebar.markdown("Practical tools")

tool = st.sidebar.radio(
    "Available tools",
    ["Home", 
     "Comparatio (Folder Difference)",
     "Collectio (Excel File Lookup)",
     "Duplicatio (Common Files)"
    ]
)


# =========================
# Main content
# =========================
if tool == "Home":
    st.markdown("## Welcome to the Porticus")

    st.markdown(
    "Porticus is a small collection of practical internal tools, "
    "designed to support users of "
    "the great Temple of Scripts."
)
    
    st.markdown("---")

    st.markdown("### Available tools")
    st.markdown(
        "- **Comparatio (Folder Difference)** — Compare two folders and "
        "retrieve files present in one set but not the other."
        "- **Collectio (Excel File Lookup)** - Copy files from a folder "
        "on a list of names provided in an Excel file."
        "- **Duplication (Common Files)** - Identify filenames that "
        "appear in both Folder A and Folder B and exports a CSV report."
    )


if tool == "Comparatio (Folder Difference)":

    st.markdown("## Welcome to the Porticus")
    st.markdown(
        "This space hosts a small collection of practical tools, "
        "built to support everyday workflows and complement "
        "the greater Temple of Scripts."
    )
    st.markdown("---")

    st.title("Comparatio (Folder Difference)")
    st.write(
        "Upload files from **Folder A** and **Folder B**. "
        "The app will generate a ZIP containing files present in Folder B "
        "but not in Folder A (comparison ignores file extensions)."
    )

    folder_a_files = st.file_uploader(
        "Folder A",
        accept_multiple_files=True
    )

    folder_b_files = st.file_uploader(
        "Folder B",
        accept_multiple_files=True
    )

    if st.button("Compare"):

        if not folder_a_files or not folder_b_files:
            st.error("Please upload files in both sections.")
        else:
            delivery_names = {
                normalize(f.name) for f in folder_a_files
            }

            new_files = [
                f for f in folder_b_files
                if normalize(f.name) not in delivery_names
            ]

            if not new_files:
                st.info("No new files found.")
            else:
                st.success(f"{len(new_files)} new file(s) found.")

                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for f in new_files:
                        zf.writestr(f.name, f.read())

                zip_buffer.seek(0)

                st.download_button(
                    label="Download ZIP with new files",
                    data=zip_buffer,
                    file_name="new_files.zip",
                    mime="application/zip"
                )
if tool == "Collectio (Excel File Lookup)":

    st.title("Collectio (Excel File Lookup)")
    st.write(
        "Upload an Excel file containing filenames (no extensions) and a folder of files. "
        "The app will find matching files and return them as a ZIP."
    )

    excel_file = st.file_uploader(
        "Excel file with filenames (first column, no extension)",
        type=["xlsx", "xls"]
    )

    search_files = st.file_uploader(
        "Folder files to search",
        accept_multiple_files=True
    )

    if st.button("Find and collect files"):

        if not excel_file or not search_files:
            st.error("Please upload both the Excel file and the folder files.")
        else:
            df = pd.read_excel(excel_file, header=None)
            base_names = (
                df[0]
                .dropna()
                .astype(str)
                .str.strip()
                .str.lower()
                .tolist()
            )

            if not base_names:
                st.error("No filenames found in the Excel file.")
            else:
                # Index uploaded files by stem
                file_index = {}
                for f in search_files:
                    stem = f.name.rsplit(".", 1)[0].lower()
                    file_index.setdefault(stem, []).append(f)

                found_files = []
                missing = []

                for base in base_names:
                    if base in file_index:
                        found_files.extend(file_index[base])
                    else:
                        missing.append(base)

                if not found_files:
                    st.info("No matching files found.")
                else:
                    st.success(f"Files found: {len(found_files)}")
                    st.write(f"Names not found: {len(missing)}")

                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                        for f in found_files:
                            zf.writestr(f.name, f.read())

                    zip_buffer.seek(0)

                    st.download_button(
                        label="Download ZIP with found files",
                        data=zip_buffer,
                        file_name="collected_files.zip",
                        mime="application/zip"
                    )

if tool == "Duplicatio (Common Files)":

    st.title("Duplicatio (Common Files)")
    st.write(
        "Upload files from **Folder A** and **Folder B**. "
        "The app will identify filenames that exist in both folders "
        "and generate a CSV report."
    )

    folder_a_files = st.file_uploader(
        "Folder A",
        accept_multiple_files=True
    )

    folder_b_files = st.file_uploader(
        "Folder B",
        accept_multiple_files=True
    )

    if st.button("Find duplicate filenames"):

        if not folder_a_files or not folder_b_files:
            st.error("Please upload files for both Folder A and Folder B.")
        else:
            names_a = {f.name for f in folder_a_files}
            names_b = {f.name for f in folder_b_files}

            duplicates = sorted(names_a & names_b)

            if not duplicates:
                st.info("No duplicate filenames found.")
            else:
                st.success(f"{len(duplicates)} duplicate filename(s) found.")

                csv_buffer = io.StringIO()
                writer = csv.writer(csv_buffer)
                writer.writerow(["filename", "found_in"])

                for name in duplicates:
                    writer.writerow([name, "both_folders"])

                st.download_button(
                    label="Download CSV report",
                    data=csv_buffer.getvalue(),
                    file_name="duplicate_filenames.csv",
                    mime="text/csv"
                )
