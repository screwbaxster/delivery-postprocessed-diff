import streamlit as st
import zipfile
import io


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
    ["Home", "Comparatio (Folder Difference)"]
)


# =========================
# Main content
# =========================
if tool == "Home":
    st.markdown("## Welcome to the Porticus")
    st.markdown(
        "Porticus is a small collection of practical internal tools, "
        "designed to support everyday workflows and complement "
        "the great Temple of Scripts."
    )

    st.markdown("---")

    st.markdown("### Available tools")
    st.markdown(
        "- **Comparatio (Folder Difference)** — Compare two folders and "
        "retrieve files present in one set but not the other."
    )

    st.caption(
        "Porticus focuses on pragmatic, lightweight utilities. "
        "Tools may later be promoted to the Temple of Scripts."
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
