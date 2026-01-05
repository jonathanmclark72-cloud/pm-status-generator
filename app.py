import streamlit as st
import pandas as pd
from status_harness import normalize_dataframe, generate_report_llm, DEFAULT_COLUMN_MAPPING

st.set_page_config(page_title="PM Status Generator", layout="centered")
st.title("📊 PM Status Generator")

uploaded = st.file_uploader("Upload Excel or CSV", type=["xlsx", "csv"])

if uploaded:
    if uploaded.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded)
    else:
        df = pd.read_csv(uploaded)

    st.subheader("Preview")
    st.dataframe(df.head())

    audience = st.selectbox("Audience", ["INTERNAL", "LEADERSHIP", "CUSTOMER"])

    if st.button("Generate Status Report"):
        payload = normalize_dataframe(
            df=df,
            mapping=DEFAULT_COLUMN_MAPPING,
            file_name=uploaded.name,
            sheet_name="Uploaded"
        )

        report = generate_report_llm(payload, audience)

        st.subheader("Generated Report")
        st.text_area("Output", report, height=400)

        st.download_button(
            "Download report",
            report,
            file_name=f"status_{audience.lower()}.txt"
        )
