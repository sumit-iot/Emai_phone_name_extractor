import streamlit as st
from src.utils.constants import SEPARATORS, OUTPUT_FORMATS, EXTRACTION_TYPES


def render_controls() -> None:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### ⚙️ Options")

    col1, col2 = st.columns(2)

    with col1:
        st.selectbox("Extraction Type", EXTRACTION_TYPES, key="extraction_type")
        st.selectbox("Separator", list(SEPARATORS.keys()), key="separator")

    with col2:
        st.selectbox(
            "Output Format",
            OUTPUT_FORMATS,
            key="output_format",
            index=0,
        )
        st.text_input(
            "Filter (contains)",
            key="filter_query",
            placeholder="e.g. gmail.com",
        )

    col_sort, col_gmail = st.columns(2)
    with col_sort:
        st.checkbox("Sort alphabetically", key="sort_alphabetically")
    with col_gmail:
        st.checkbox("Gmail only", key="gmail_only")
    st.markdown("</div>", unsafe_allow_html=True)
