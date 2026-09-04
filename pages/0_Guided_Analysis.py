"""DataPrism Analysis Workbench: one auditable workflow from source to report."""
from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.analysis_pipeline import (
    DataLoadError,
    LoadResult,
    analyze_dataframe,
    analyze_document_text,
    apply_cleaning_plan,
    export_csv_safe,
    load_source,
    profile_dataframe,
    recommend_cleaning,
    render_markdown_report,
)
from utils.data_loader import SAMPLE_DATASETS, init_all_session_state, load_sample_dataset


init_all_session_state()

DEFAULTS = {
    "dp_source": None,
    "dp_source_id": None,
    "dp_dataset_name": None,
    "dp_original": None,
    "dp_cleaned": None,
    "dp_pipeline_profile": None,
    "dp_pipeline_analysis": None,
    "dp_pipeline_audit": [],
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def reset_outputs() -> None:
    st.session_state.dp_cleaned = None
    st.session_state.dp_pipeline_profile = None
    st.session_state.dp_pipeline_analysis = None
    st.session_state.dp_pipeline_audit = []


def activate_dataset(name: str) -> None:
    result = st.session_state.dp_source
    frame = result.datasets[name].copy()
    st.session_state.dp_dataset_name = name
    st.session_state.dp_original = frame
    st.session_state.uploaded_df = frame
    st.session_state.raw_df = frame.copy()
    st.session_state.working_df = frame.copy()
    reset_outputs()


st.title("💠 Analysis Workbench")
st.markdown(
    "A professional, evidence-first workflow: **ingest → profile → clean → analyze → report**. "
    "Core calculations run locally and deterministically; AI is optional, not a substitute for evidence."
)

with st.expander("What this workbench supports", expanded=False):
    st.markdown(
        "**Structured:** CSV, TSV, Excel (all sheets), JSON/JSONL, Parquet.  "
        "**Documents:** PDF and DOCX text plus detected tables; TXT/Markdown.\n\n"
        "Scanned PDFs need OCR before reliable analysis. Password-protected files and proprietary "
        "formats are rejected with a clear error instead of being guessed."
    )

upload_tab, sample_tab = st.tabs(["Upload data", "Use a verified sample"])

with upload_tab:
    uploaded = st.file_uploader(
        "Choose a file",
        type=["csv", "tsv", "txt", "xlsx", "xls", "json", "jsonl", "ndjson", "parquet", "pdf", "docx", "md"],
        help="Maximum 200 MB. Files are processed in memory for this session.",
    )
    if uploaded is not None:
        signature = hashlib.sha256(uploaded.getvalue()).hexdigest()
        if signature != st.session_state.dp_source_id:
            with st.spinner("Validating and extracting the source…"):
                try:
                    result = load_source(uploaded.getvalue(), uploaded.name)
                    st.session_state.dp_source = result
                    st.session_state.dp_source_id = signature
                    if result.datasets:
                        activate_dataset(next(iter(result.datasets)))
                    else:
                        st.session_state.dp_dataset_name = None
                        st.session_state.dp_original = None
                        reset_outputs()
                    st.success(f"Loaded {uploaded.name}")
                except DataLoadError as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("The file could not be processed safely. Verify that it is valid and try again.")

with sample_tab:
    sample_name = st.selectbox(
        "Sample dataset", list(SAMPLE_DATASETS),
        format_func=lambda name: f"{name} — {SAMPLE_DATASETS[name]['description']}",
    )
    if st.button("Load sample", use_container_width=True):
        frame = load_sample_dataset(sample_name)
        st.session_state.dp_source = LoadResult(
            source_name=f"sample:{sample_name}", source_format="generated", datasets={"data": frame},
            metadata={"dataset_count": 1, "provenance": "DataPrism deterministic sample generator"},
        )
        st.session_state.dp_source_id = f"sample::{sample_name}"
        activate_dataset("data")
        st.rerun()

source = st.session_state.dp_source
if source is None:
    st.info("Upload a file or load a sample to begin.")
    st.stop()

for warning in source.warnings:
    st.warning(warning)

meta1, meta2, meta3, meta4 = st.columns(4)
meta1.metric("Source", source.source_name)
meta2.metric("Format", source.source_format.upper())
meta3.metric("Tables", len(source.datasets))
meta4.metric("Extracted text", f"{len(source.document_text):,} chars")

if len(source.datasets) > 1:
    options = list(source.datasets)
    current = st.session_state.dp_dataset_name if st.session_state.dp_dataset_name in options else options[0]
    selected = st.selectbox("Table or sheet to analyze", options, index=options.index(current))
    if selected != st.session_state.dp_dataset_name:
        activate_dataset(selected)
        st.rerun()

if source.document_text:
    with st.expander("Document evidence", expanded=not source.datasets):
        doc_result = analyze_document_text(source.document_text)
        d1, d2, d3 = st.columns(3)
        d1.metric("Words", f"{doc_result['words']:,}")
        d2.metric("Numbers found", f"{doc_result.get('number_count', 0):,}")
        d3.metric("Characters", f"{doc_result['characters']:,}")
        if doc_result["top_terms"]:
            st.markdown("**Frequent substantive terms**")
            st.dataframe(pd.DataFrame(doc_result["top_terms"].items(), columns=["Term", "Count"]), hide_index=True, use_container_width=True)
        if doc_result["key_sentences"]:
            st.markdown("**Extractive key passages**")
            for sentence in doc_result["key_sentences"]:
                st.markdown(f"- {sentence}")
        with st.expander("Extracted text preview"):
            st.text(source.document_text[:30_000])

original = st.session_state.dp_original
if original is None:
    st.info("This source has no reliably detected table. The extractive document analysis above is available; use an OCR-enabled source for scanned pages.")
    st.stop()

active = st.session_state.dp_cleaned if st.session_state.dp_cleaned is not None else original
st.caption(f"Active table: **{st.session_state.dp_dataset_name}** · {len(active):,} rows × {len(active.columns):,} columns")

profile_tab, clean_tab, analyze_tab, report_tab = st.tabs(
    ["1 · Profile", "2 · Clean", "3 · Analyze", "4 · Report & export"]
)

with profile_tab:
    profile = profile_dataframe(active)
    st.session_state.dp_pipeline_profile = profile
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Quality score", f"{profile['quality_score']}/100")
    q2.metric("Missing cells", f"{profile['missing_pct']:.2f}%")
    q3.metric("Exact duplicates", f"{profile['duplicate_rows']:,}")
    q4.metric("Memory", f"{profile['memory_bytes'] / 1024 / 1024:.2f} MB")
    st.markdown("#### Schema and field diagnostics")
    fields = pd.DataFrame(profile["column_profiles"])
    visible = [c for c in ["column", "dtype", "semantic_type", "type_confidence", "missing_pct", "unique", "unique_pct", "outliers_iqr"] if c in fields.columns]
    st.dataframe(fields[visible], hide_index=True, use_container_width=True)
    st.markdown("#### Quality issue register")
    if profile["issues"]:
        st.dataframe(pd.DataFrame(profile["issues"]), hide_index=True, use_container_width=True)
    else:
        st.success("No rule-based quality issues were detected.")
    with st.expander("Raw data preview"):
        st.dataframe(active.head(100), use_container_width=True)

with clean_tab:
    base_profile = profile_dataframe(original)
    actions = recommend_cleaning(original, base_profile)
    st.markdown(
        "Cleaning is conservative by design. Low-risk normalization is preselected; row deletion and "
        "schema changes require your explicit approval. Every applied step is recorded."
    )
    chosen = []
    for action in actions:
        checked = st.checkbox(
            action["label"], value=bool(action["recommended"]),
            key=f"clean::{st.session_state.dp_source_id}::{action['id']}",
            help=f"Reason: {action['reason']} · Risk: {action['risk']}",
        )
        if checked:
            chosen.append(action)
    left, right = st.columns(2)
    with left:
        if st.button("Apply selected plan", type="primary", use_container_width=True, disabled=not chosen):
            try:
                cleaned, audit = apply_cleaning_plan(original, chosen)
                st.session_state.dp_cleaned = cleaned
                st.session_state.working_df = cleaned.copy()
                st.session_state.dp_pipeline_audit = audit
                st.session_state.dp_pipeline_analysis = None
                st.success(f"Applied {len(audit)} steps. Active data: {len(cleaned):,} × {len(cleaned.columns):,}.")
                st.rerun()
            except Exception as exc:
                st.error(f"No changes were saved because the cleaning plan failed: {exc}")
    with right:
        if st.button("Restore original", use_container_width=True, disabled=st.session_state.dp_cleaned is None):
            st.session_state.dp_cleaned = None
            st.session_state.working_df = original.copy()
            st.session_state.dp_pipeline_audit = []
            st.session_state.dp_pipeline_analysis = None
            st.rerun()
    if st.session_state.dp_pipeline_audit:
        st.markdown("#### Cleaning audit trail")
        st.dataframe(pd.DataFrame(st.session_state.dp_pipeline_audit), hide_index=True, use_container_width=True)
        st.markdown("#### Before / after")
        before, after = st.columns(2)
        before.dataframe(original.head(25), use_container_width=True)
        after.dataframe(st.session_state.dp_cleaned.head(25), use_container_width=True)

with analyze_tab:
    goal = st.text_area(
        "Analysis goal or decision",
        placeholder="Example: Which customer segments and factors are associated with higher revenue?",
        help="The goal is recorded in the report. Automatic calculations remain evidence-driven.",
    )
    if st.button("Run professional analysis", type="primary", use_container_width=True):
        with st.spinner("Computing descriptive statistics and relationships…"):
            st.session_state.dp_pipeline_analysis = analyze_dataframe(active, goal)
    analysis = st.session_state.dp_pipeline_analysis
    if analysis:
        st.markdown("#### Evidence-backed findings")
        if analysis["findings"]:
            for finding in analysis["findings"]:
                with st.container(border=True):
                    st.markdown(f"**{finding['title']}**")
                    st.write(finding["evidence"])
                    st.caption(f"Caveat: {finding['caveat']}")
        else:
            st.info("No automatic finding met the reporting threshold. This is a valid result, not an error.")
        numeric_cols = active.select_dtypes(include=np.number).columns.tolist()
        categorical_cols = [c for c in active.columns if active[c].dtype == "object" and active[c].nunique(dropna=True) <= 50]
        st.markdown("#### Visual exploration")
        if numeric_cols:
            chart_col = st.selectbox("Numeric field", numeric_cols, key="workbench_numeric")
            st.plotly_chart(px.histogram(active, x=chart_col, marginal="box", title=f"Distribution of {chart_col}"), use_container_width=True)
        if categorical_cols:
            category_col = st.selectbox("Category field", categorical_cols, key="workbench_category")
            counts = active[category_col].fillna("(missing)").astype(str).value_counts().head(20).rename_axis(category_col).reset_index(name="count")
            st.plotly_chart(px.bar(counts, x=category_col, y="count", title=f"Top values in {category_col}"), use_container_width=True)
        if analysis["correlations"]:
            st.markdown("#### Numeric relationships")
            st.dataframe(pd.DataFrame(analysis["correlations"]), hide_index=True, use_container_width=True)
        st.markdown("#### Interpretation limits")
        for limitation in analysis["limitations"]:
            st.markdown(f"- {limitation}")

with report_tab:
    analysis = st.session_state.dp_pipeline_analysis
    if not analysis:
        st.info("Run the analysis in step 3 to create a report.")
    else:
        report = render_markdown_report(
            source.source_name, st.session_state.dp_dataset_name, analysis, st.session_state.dp_pipeline_audit,
        )
        st.markdown(report)
        manifest = {
            "source": source.source_name,
            "dataset": st.session_state.dp_dataset_name,
            "source_metadata": source.metadata,
            "profile": analysis["profile"],
            "cleaning_audit": st.session_state.dp_pipeline_audit,
            "analysis": {key: value for key, value in analysis.items() if key != "profile"},
        }
        c1, c2, c3 = st.columns(3)
        c1.download_button("Download report", report, f"dataprism_{st.session_state.dp_dataset_name}_report.md", "text/markdown", use_container_width=True)
        c2.download_button("Download cleaned data", export_csv_safe(active), f"dataprism_{st.session_state.dp_dataset_name}_cleaned.csv", "text/csv", use_container_width=True)
        c3.download_button("Download audit manifest", json.dumps(manifest, indent=2, default=str), "dataprism_manifest.json", "application/json", use_container_width=True)
