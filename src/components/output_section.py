import pandas as pd
import streamlit as st
from src.core.extractor import nlp_available
from src.utils.constants import SEPARATORS, FORMAT_COLUMNS
from src.utils.exporters import to_csv_bytes

_NER_TYPES = {"Names", "Organizations", "All"}


def _filtered_sorted(items: list[str], label: str = "") -> list[str]:
    if st.session_state.get("gmail_only") and label in ("emails", "email"):
        items = [i for i in items if i.endswith("@gmail.com")]
    q = st.session_state.filter_query.strip().lower()
    if q:
        items = [i for i in items if q in i.lower()]
    if st.session_state.sort_alphabetically:
        items = sorted(items)
    return items


def _render_result_block(items: list[str], label: str) -> None:
    items = _filtered_sorted(items, label)
    separator = SEPARATORS[st.session_state.separator]

    count = len(items)
    noun = label.rstrip("s") + ("s" if count != 1 else "")

    st.markdown(
        f'<div class="counter-badge">✅ {count} {noun} found</div>',
        unsafe_allow_html=True,
    )

    if not items:
        st.markdown(
            '<div class="empty-state"><div class="icon">🔍</div>'
            "<p>No results — try adjusting your filter.</p></div>",
            unsafe_allow_html=True,
        )
        return

    st.code(separator.join(items), language=None)

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
            '<div class="empty-state"><div class="icon">🗺️</div>'
            "<p>No entities with contact info found in the same block.</p></div>",
            unsafe_allow_html=True,
        )
        return

    fmt = st.session_state.output_format
    all_cols = ["Name", "URLs", "Emails", "Phones"]
    show_cols = FORMAT_COLUMNS.get(fmt, all_cols)

    # Rebuild df with only the selected columns
    df_full = pd.DataFrame(rows, columns=["Name", "Emails", "Phones", "URLs"])

    # Apply gmail filter to Emails column
    if st.session_state.get("gmail_only") and "Emails" in show_cols:
        def _filter_gmails(cell: str) -> str:
            return ", ".join(e for e in cell.split(", ") if e.endswith("@gmail.com"))
        df_full["Emails"] = df_full["Emails"].apply(_filter_gmails)

    df = df_full[[c for c in show_cols if c in df_full.columns]]

    # Drop rows where all shown contact columns are empty
    contact_cols = [c for c in show_cols if c != "Name"]
    if contact_cols:
        df = df[df[contact_cols].apply(lambda r: r.str.strip().any(), axis=1)]

    if df.empty:
        st.info("No results match the current format / filter.")
        return

    st.markdown(
        f'<div class="counter-badge">🗺️ {len(df)} entit{"y" if len(df) == 1 else "ies"} — {fmt}</div>',
        unsafe_allow_html=True,
    )

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.download_button(
        "⬇️  Download CSV",
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
            '<div class="card"><div class="empty-state"><div class="icon">📋</div>'
            "<p>Paste your text above and click <strong>Extract</strong> to get started.</p>"
            "</div></div>",
            unsafe_allow_html=True,
        )
        return

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 📤 Results")
    _render_entity_map()
    st.markdown("</div>", unsafe_allow_html=True)
