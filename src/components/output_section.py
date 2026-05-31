import pandas as pd
import streamlit as st
from src.core.extractor import nlp_available
from src.core.formatter import format_items
from src.utils.constants import SEPARATORS
from src.utils.exporters import to_csv_bytes

_NER_TYPES = {"Names", "Organizations", "All"}


def _filtered_sorted(items: list[str]) -> list[str]:
    q = st.session_state.filter_query.strip().lower()
    if q:
        items = [i for i in items if q in i.lower()]
    if st.session_state.sort_alphabetically:
        items = sorted(items)
    return items


def _render_result_block(items: list[str], label: str) -> None:
    items = _filtered_sorted(items)
    separator = SEPARATORS[st.session_state.separator]
    fmt = st.session_state.output_format

    count = len(items)
    noun = label.rstrip("s") + ("s" if count != 1 else "")

    st.markdown(
        f'<div class="counter-badge">✅ {count} {noun} found</div>',
        unsafe_allow_html=True,
    )

    if not items:
        st.markdown(
            '<div class="empty-state">'
            '<div class="icon">🔍</div>'
            "<p>No results — try adjusting your filter.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    formatted = format_items(items, fmt, separator, label.rstrip("s"))
    st.code(formatted, language=None)

    st.download_button(
        "⬇️  Download CSV",
        data=to_csv_bytes(items, label.rstrip("s")),
        file_name=f"extracted_{label}.csv",
        mime="text/csv",
        use_container_width=True,
        key=f"dl_{label}",
    )


def _render_entity_map() -> None:
    if not nlp_available():
        st.warning(
            "spaCy model not found. Run: `python -m spacy download en_core_web_sm`",
            icon="⚠️",
        )
        return

    rows: list[dict] = st.session_state.entity_map

    if not rows:
        st.markdown(
            '<div class="empty-state">'
            '<div class="icon">🗺️</div>'
            "<p>No entities with contact info found in the same sentence.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    df = pd.DataFrame(rows, columns=["Name", "Emails", "Phones", "URLs"])

    st.markdown(
        f'<div class="counter-badge">🗺️ {len(df)} entit{"y" if len(df) == 1 else "ies"} mapped</div>',
        unsafe_allow_html=True,
    )

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.download_button(
        "⬇️  Download Map CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="entity_map.csv",
        mime="text/csv",
        use_container_width=True,
        key="dl_map",
    )


def _nlp_warning() -> None:
    st.warning(
        "spaCy model not found. Run: `python -m spacy download en_core_web_sm`",
        icon="⚠️",
    )


def render_output_section() -> None:
    if not st.session_state.has_extracted:
        st.markdown(
            '<div class="card">'
            '<div class="empty-state">'
            '<div class="icon">📋</div>'
            "<p>Paste your text above and click <strong>Extract</strong> to get started.</p>"
            "</div></div>",
            unsafe_allow_html=True,
        )
        return

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 📤 Results")

    etype = st.session_state.extraction_type

    if etype in _NER_TYPES and not nlp_available():
        _nlp_warning()

    if etype == "All":
        tab_e, tab_u, tab_p, tab_n, tab_o, tab_m = st.tabs(
            ["📧 Emails", "🔗 URLs", "📞 Phones", "👤 Names", "🏢 Organizations", "🗺️ Map"]
        )
        with tab_e:
            _render_result_block(st.session_state.emails, "emails")
        with tab_u:
            _render_result_block(st.session_state.urls, "urls")
        with tab_p:
            _render_result_block(st.session_state.phones, "phones")
        with tab_n:
            _render_result_block(st.session_state.names, "names")
        with tab_o:
            _render_result_block(st.session_state.orgs, "organizations")
        with tab_m:
            _render_entity_map()
    elif etype == "Emails":
        _render_result_block(st.session_state.emails, "emails")
    elif etype == "URLs":
        _render_result_block(st.session_state.urls, "urls")
    elif etype == "Phone Numbers":
        _render_result_block(st.session_state.phones, "phones")
    elif etype == "Names":
        _render_result_block(st.session_state.names, "names")
    elif etype == "Organizations":
        _render_result_block(st.session_state.orgs, "organizations")

    # Entity map expander for non-All modes
    if etype != "All":
        with st.expander("🗺️ Entity Map — name · email · phone · URL", expanded=False):
            _render_entity_map()

    st.markdown("</div>", unsafe_allow_html=True)
