def normalize(filename: str) -> str:
    name = filename.lower().strip()
    if "." in name:
        name = name.rsplit(".", 1)[0]
    return name


st.sidebar.title("Porticus")
st.sidebar.markdown("Practical tools")

tool = st.sidebar.radio(
    "Available scripts",
    ["Delivery vs Postprocessed"]
)


st.markdown("## Welcome to the Porticus")
st.markdown(
    "This space hosts a small collection of practical tools, "
    "built to support everyday workflows and complement "
    "the greater Temple of Scripts."
)
st.markdown("---")


if tool == "Delivery vs Postprocessed":
    st.title("Delivery vs Postprocessed")
    st.write(
        "Upload files from a previous **Delivery** and from **Postprocessed**. "
        "The app will generate a ZIP with files that were not previously delivered "
        "(comparison ignores file extensions)."
    )


st.markdown("## Welcome to the Porticus")
st.markdown(
    "This space hosts a small collection of practical tools, "
    "built to support everyday workflows and complement "
    "the greater Temple of Scripts."
)

st.title("Delivery vs Postprocessed")
st.write(
    "Upload files from a previous **Delivery** and from **Postprocessed**. "
    "The app will generate a ZIP with files that were not previously delivered "
    "(comparison ignores file extensions)."
)

delivery_files = st.file_uploader(
    "Delivery files (already sent)",
    accept_multiple_files=True
)

postprocessed_files = st.file_uploader(
    "Postprocessed files (completed)",
    accept_multiple_files=True
)

if st.button("Compare"):

    if not delivery_files or not postprocessed_files:
        st.error("Please upload files in both sections.")
    else:
        delivery_names = {
            normalize(f.name) for f in delivery_files
        }

        new_files = [
            f for f in postprocessed_files
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
###
# Delivery vs Postprocessed – File Comparison Tool
#
# Compares Delivery and Postprocessed files by base filename
# (case-insensitive, extension ignored) and returns a ZIP
# containing only files not previously delivered.
###
