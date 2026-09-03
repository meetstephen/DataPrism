# DataPrism

> Raw data. Traceable analysis. Defensible decisions.

DataPrism is a Streamlit analysis workbench for turning supported datasets and
documents into a reproducible analytical package. The primary workflow is:

1. ingest and validate a source;
2. inspect schema and data quality;
3. review and apply conservative cleaning actions;
4. calculate descriptive evidence and surface patterns;
5. export cleaned data, a readable report, and a machine-readable audit manifest.

The core calculations are deterministic and run locally in Python. Optional AI
features can explain results or support chat, but they are not the source of the
quality score, statistics, correlations, or cleaning audit.

## Start here

```bash
git clone https://github.com/meetstephen/DataPrism.git
cd DataPrism
python -m venv .venv

# Windows
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\streamlit run app.py

# macOS / Linux
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/streamlit run app.py
```

Open `http://localhost:8501`, then choose **Analysis Workbench**.

Python 3.11 or newer is recommended.

## File support

| Input | Behavior | Important limits |
|---|---|---|
| CSV, TSV | Encoding and delimiter detection, then tabular analysis | Files over 200 MB are rejected |
| Excel `.xlsx`, `.xls` | Every non-empty sheet is exposed separately | Legacy `.xls` uses `xlrd` |
| JSON, JSONL, NDJSON | Nested records are normalized; record collections become separate tables | Scalar-only JSON is not a dataset |
| Parquet | Loaded as a typed table | Requires `pyarrow` |
| PDF | Selectable text is extracted; detected tables become analyzable datasets | Scanned pages require OCR before upload; table extraction is best-effort |
| DOCX | Paragraph text and document tables are extracted | Legacy `.doc` is not supported |
| TXT, Markdown | Text analysis; delimiter detection also attempts to find a table | Unstructured prose is not forced into rows and columns |

“Any data” cannot honestly mean every proprietary, encrypted, scanned, or
corrupted format. DataPrism rejects unsupported input clearly instead of
silently inventing a parse.

## Analysis Workbench

The workbench in `pages/0_Guided_Analysis.py` is the canonical workflow.

### 1. Ingest

- validates extension, size, encoding, and structure;
- handles multi-table sources without discarding sheets or document tables;
- preserves source metadata and extraction warnings;
- separates document evidence from structured tables.

### 2. Profile

- row, column, cell, memory, missingness, and duplicate metrics;
- semantic type inference with a confidence value;
- per-column cardinality, completeness, descriptive statistics, and IQR flags;
- a deterministic quality score and explicit issue register.

The quality score is a triage indicator, not a certification. Its inputs are
shown so an analyst can challenge the result.

### 3. Clean

Low-risk normalization is recommended by default:

- stable SQL-friendly column names;
- consistent missing-value tokens;
- trimmed text values.

Potentially destructive operations such as removing duplicates or dropping
constant fields require explicit selection. The original table is retained,
the result can be restored, and every applied step records its before/after
shape, affected values, and timestamp.

Outliers are flagged, not automatically deleted. Missing values are not blindly
imputed. Both choices depend on domain meaning and should be made by an analyst.

### 4. Analyze

- numeric summaries including count, mean, median, spread, minimum, and maximum;
- strongest pairwise Pearson relationships with complete-row counts;
- categorical concentration summaries;
- IQR-based extreme-value evidence;
- interactive distributions and category charts;
- limitations attached to the findings.

Correlation results are explicitly described as non-causal. A dataset cannot,
by itself, prove that one variable caused another.

### 5. Report and export

Each run can export:

- a Markdown analysis report;
- the active cleaned table as UTF-8 CSV;
- a JSON manifest containing source metadata, profile, cleaning audit, findings,
  and limitations.

## Additional tools

The sidebar retains focused tools for advanced exploration:

- manual data cleaning and validation rules;
- advanced charts, group-by analysis, pivots, statistics, and forecasting;
- read-only SQL over in-memory tables;
- joins and concatenation;
- data dictionary and profiling;
- dashboard and HTML/PDF/DOCX report generation;
- optional Gemini insights and data/document chat;
- optional Supabase authentication and cloud workspace.

These pages share session datasets, but new ingestion should begin in the
Analysis Workbench so provenance and extraction warnings are retained.

## Optional configuration

Create `.streamlit/secrets.toml` only when the related integration is needed:

```toml
GEMINI_API_KEY = "your-key"

# Optional cloud workspace and authentication
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key"
ADMIN_EMAIL = "admin@example.com"
```

Never commit this file. The app operates in local/open mode without these
values. Supabase schema setup is documented in `SUPABASE_SETUP.md`.

## Architecture

```text
app.py                              home and session entry point
pages/0_Guided_Analysis.py          canonical A-to-Z workbench
utils/analysis_pipeline.py          pure ingestion, profiling, cleaning, analysis, reporting
utils/data_loader.py                session/sample helpers and legacy-page compatibility
utils/data_engine.py                manual interactive cleaning operations
utils/statistics.py                 focused statistical and ML utilities
utils/forecasting.py                Holt-Winters forecasting
utils/report_generator.py           formatted HTML/PDF/DOCX reporting
tests/test_analysis_pipeline.py     workbench contract tests
tests/test_data_loader.py           delimited-file regression tests
tests/test_chat_charts.py           safe chart-spec tests
```

`utils/analysis_pipeline.py` has no Streamlit dependency. This keeps the
analytical contract independently testable and prevents UI reruns from changing
calculation logic.

## Security and privacy

- Uploaded files are processed in the active app process and are not sent to an
  AI model by the deterministic workbench.
- Model-produced chart code is never executed; chat charts use an allow-listed
  JSON specification.
- The SQL page accepts read-only `SELECT` / `WITH` queries and blocks other
  statement classes.
- Calculated fields and regex operations remain constrained. Treat any public
  deployment as an internet-facing application and keep dependencies patched.
- Optional Supabase row-level security must be configured exactly as described
  before storing user data.

Do not upload data you are not authorized to process. Review sensitive columns
before sharing reports or using optional AI features.

## Verification

```bash
python -m pytest -q
python -m compileall -q app.py pages utils tests
```

The analysis-pipeline suite covers encoding and delimiter detection,
multi-sheet workbooks, nested JSON, semantic profiling, conservative cleaning,
audit records, evidence-backed findings, document extraction summaries, and
clear failures for empty or unsupported input.

No software can guarantee zero errors for arbitrary real-world data. The
engineering goal is instead to fail clearly, avoid silent data corruption,
preserve provenance, test supported behavior, and make analytical limitations
visible.

## Deployment

For Streamlit Community Cloud, connect this repository, set `app.py` as the
entry point, and add only the secrets needed by the enabled integrations. The
included `.streamlit/config.toml` sets the 200 MB upload limit.

Before production use, add organization-specific controls for retention,
encryption, access review, monitoring, backups, incident response, and data
residency. “Enterprise-grade” is an operational property, not a UI theme.

## License

This repository currently contains no license file. Add an explicit license
before distributing or accepting external contributions.
