import io
import re
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from rapidfuzz import fuzz, process

APP_TITLE = "Nauruan Health Vocabulary Lookup & Validation MVP"
DATA_PATH = "data/health_lookup_records.csv"

st.set_page_config(page_title="Nauruan Health Lookup", page_icon="🏥", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].fillna("")
    df["has_candidate"] = df["nauruan"].astype(str).str.strip().ne("")
    df["search_blob"] = (
        df["english"].astype(str) + " " +
        df["nauruan"].astype(str) + " " +
        df["category"].astype(str) + " " +
        df["plain_language_use"].astype(str)
    ).str.lower()
    return df

def norm(text):
    text = str(text or "").lower().strip()
    text = re.sub(r"[^a-z0-9\s'-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def search_records(df, query, direction="English → Nauruan", limit=10):
    q = norm(query)
    if not q:
        return pd.DataFrame()
    candidates = df[df["has_candidate"]].copy()
    if direction == "English → Nauruan":
        key_col = "english"
    elif direction == "Nauruan → English":
        key_col = "nauruan"
    else:
        key_col = "search_blob"
    # Score exact/contains/fuzzy matches.
    rows = []
    for _, row in candidates.iterrows():
        target = norm(row.get(key_col, ""))
        blob = row.get("search_blob", "")
        score = 0
        if target == q:
            score = 100
        elif q in target or q in blob:
            score = 92
        else:
            score = max(
                fuzz.WRatio(q, target),
                fuzz.partial_ratio(q, target),
                fuzz.token_set_ratio(q, blob),
            )
        if score >= 55:
            out = row.to_dict()
            out["match_score"] = int(score)
            rows.append(out)
    if not rows:
        return pd.DataFrame()
    results = pd.DataFrame(rows).sort_values(["match_score", "priority"], ascending=[False, True])
    return results.head(limit)

def init_state():
    if "review_log" not in st.session_state:
        st.session_state.review_log = []

init_state()
df = load_data()

st.title(APP_TITLE)
st.caption("Prototype for reviewer testing. It is a lookup and validation tool, not an official translation authority.")

with st.sidebar:
    st.header("Reviewer details")
    reviewer_name = st.text_input("Reviewer name", placeholder="Optional")
    reviewer_role = st.selectbox(
        "Reviewer role",
        ["Native speaker", "Clinical reviewer", "Language authority", "Project team", "Other"],
        index=0,
    )
    st.divider()
    st.write("Records loaded:", len(df))
    st.write("Candidate translations:", int(df["has_candidate"].sum()))
    st.write("Backlog/no candidate:", int((~df["has_candidate"]).sum()))

lookup_tab, review_tab, backlog_tab, export_tab, about_tab = st.tabs([
    "Lookup", "Validate", "Backlog", "Export feedback", "About"
])

with lookup_tab:
    st.subheader("Search the current health vocabulary")
    c1, c2, c3 = st.columns([3, 1.5, 1])
    with c1:
        query = st.text_input("Search English or Nauruan", placeholder="e.g. hospital, pain, fever, good morning")
    with c2:
        direction = st.selectbox("Direction", ["English → Nauruan", "Nauruan → English", "Broad search"])
    with c3:
        limit = st.number_input("Max results", min_value=1, max_value=50, value=10)

    if query:
        results = search_records(df, query, direction, int(limit))
        if results.empty:
            st.warning("No strong match found. Try a simpler word, variant spelling, or broad search.")
        else:
            for _, r in results.iterrows():
                with st.container(border=True):
                    left, right = st.columns([1, 1])
                    with left:
                        st.markdown(f"### {r.get('english', '')}")
                        st.write(r.get("plain_language_use", ""))
                        st.write(f"**Category:** {r.get('category', '')}")
                        st.write(f"**Priority:** {r.get('priority', '')}")
                    with right:
                        st.markdown(f"### {r.get('nauruan', '')}")
                        st.write(f"**Source:** {r.get('source_id', '')} — {r.get('source_title', '')}")
                        st.write(f"**Source page:** PDF p.{r.get('pdf_page', '')} / dictionary p.{r.get('dictionary_page', '')}")
                        st.write(f"**Match score:** {r.get('match_score', '')}")
                        st.write(f"**Status:** {r.get('status', '')}")
                    if str(r.get("clinical_safety_flag", "")).lower().startswith("safety"):
                        st.error("Safety-critical term: requires careful review before operational use.")

with review_tab:
    st.subheader("Validate candidate translations")
    st.info("This demo stores review decisions in browser session memory only. Use 'Export feedback' before closing or refreshing the page.")

    candidates = df[df["has_candidate"]].copy()
    f1, f2, f3 = st.columns(3)
    with f1:
        categories = ["All"] + sorted([x for x in candidates["category"].unique() if x])
        selected_category = st.selectbox("Category", categories)
    with f2:
        priorities = ["All"] + sorted([x for x in candidates["priority"].unique() if x])
        selected_priority = st.selectbox("Priority", priorities)
    with f3:
        safety_filter = st.selectbox("Safety flag", ["All", "Safety critical", "Routine"])

    filtered = candidates
    if selected_category != "All":
        filtered = filtered[filtered["category"] == selected_category]
    if selected_priority != "All":
        filtered = filtered[filtered["priority"] == selected_priority]
    if safety_filter != "All":
        filtered = filtered[filtered["clinical_safety_flag"] == safety_filter]

    filtered = filtered.sort_values(["clinical_safety_flag", "priority", "record_id"], ascending=[True, True, True])
    options = [f"{r.record_id} | {r.english} → {r.nauruan}" for r in filtered.itertuples()]
    if not options:
        st.warning("No records match the selected filters.")
    else:
        selected = st.selectbox("Select record", options)
        record_id = selected.split(" | ")[0]
        rec = filtered[filtered["record_id"] == record_id].iloc[0].to_dict()

        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### Source candidate")
                st.write(f"**English:** {rec.get('english', '')}")
                st.write(f"**Plain-language use:** {rec.get('plain_language_use', '')}")
                st.write(f"**Nauruan candidate:** {rec.get('nauruan', '')}")
                st.write(f"**Safety:** {rec.get('clinical_safety_flag', '')}")
                st.write(f"**Evidence note:** {rec.get('evidence_note', '')}")
            with c2:
                st.markdown("#### Source details")
                st.write(f"**Source:** {rec.get('source_id', '')} — {rec.get('source_title', '')}")
                st.write(f"**PDF page:** {rec.get('pdf_page', '')}")
                st.write(f"**Dictionary page:** {rec.get('dictionary_page', '')}")
                if rec.get("source_url", ""):
                    st.write(f"**Source URL:** {rec.get('source_url', '')}")

        st.markdown("#### Review decision")
        d1, d2 = st.columns([1, 2])
        with d1:
            decision = st.radio(
                "Decision",
                ["Accept", "Correct", "Reject", "Needs discussion"],
                horizontal=False,
            )
        with d2:
            corrected_nauruan = st.text_input("Corrected Nauruan", value=rec.get("nauruan", ""))
            corrected_english = st.text_input("Corrected English / meaning", value=rec.get("english", ""))
            notes = st.text_area("Reviewer notes", placeholder="Comment on spelling, naturalness, register, safety, or context.")

        if st.button("Save review decision", type="primary"):
            entry = {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "reviewer_name": reviewer_name,
                "reviewer_role": reviewer_role,
                "record_id": rec.get("record_id", ""),
                "record_type": rec.get("record_type", ""),
                "english_original": rec.get("english", ""),
                "nauruan_original": rec.get("nauruan", ""),
                "decision": decision,
                "corrected_english": corrected_english,
                "corrected_nauruan": corrected_nauruan,
                "reviewer_notes": notes,
                "source_id": rec.get("source_id", ""),
                "pdf_page": rec.get("pdf_page", ""),
                "dictionary_page": rec.get("dictionary_page", ""),
                "clinical_safety_flag": rec.get("clinical_safety_flag", ""),
            }
            st.session_state.review_log.append(entry)
            st.success(f"Saved review for {rec.get('record_id', '')}. Export feedback before closing the page.")

with backlog_tab:
    st.subheader("Terms and phrases without a Nauruan candidate")
    backlog = df[~df["has_candidate"]].copy()
    st.write(f"Backlog records: {len(backlog)}")
    if not backlog.empty:
        st.dataframe(
            backlog[["record_id", "record_type", "category", "priority", "english", "evidence_note", "notes"]],
            use_container_width=True,
            hide_index=True,
        )

with export_tab:
    st.subheader("Export reviewer feedback")
    log = pd.DataFrame(st.session_state.review_log)
    st.write(f"Saved review decisions in this browser session: {len(log)}")
    if not log.empty:
        st.dataframe(log, use_container_width=True, hide_index=True)
        csv_bytes = log.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download validation feedback CSV",
            data=csv_bytes,
            file_name=f"nauruan_validation_feedback_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )
    else:
        st.warning("No feedback saved yet.")

with about_tab:
    st.subheader("About this MVP")
    st.markdown(
        """
This is a prototype validation interface for a Nauruan health vocabulary project.

Current function:

- Search English → Nauruan and Nauruan → English candidate records.
- Review and validate candidate terms.
- Export reviewer feedback as CSV.

Important limitations:

- This is not an official translation tool.
- Review data is not permanently stored unless exported or connected to a backend.
- Safety-critical terms require native-speaker and clinical review before operational use.
- The underlying records are assumed validated only for prototype testing.

Recommended deployment for field testing:

1. Host the app using Streamlit Community Cloud or Hugging Face Spaces.
2. Share the URL with reviewers.
3. Ask each reviewer to export their feedback CSV at the end of the session.
4. Merge feedback into the master validation workbook.
"""
    )
