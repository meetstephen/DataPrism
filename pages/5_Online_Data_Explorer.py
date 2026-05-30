import streamlit as st

st.set_page_config(page_title="Online Data Explorer", page_icon="\U0001F310", layout="wide")

import pandas as pd
from utils.online_data import (
    fetch_data_from_url,
    scrape_tables_from_url,
    get_dataset_catalog,
    validate_dataframe,
    detect_file_type,
)

st.title("\U0001F310 Online Data Explorer")
st.markdown("Fetch and analyze datasets from the internet. Load CSV, JSON, or Excel files from any URL, browse curated public datasets, or scrape tables from web pages.")

# Sidebar - data source info
with st.sidebar:
    st.markdown("### Online Data")
    if "online_df" in st.session_state and st.session_state.online_df is not None:
        st.success(f"Data loaded: {len(st.session_state.online_df)} rows, {len(st.session_state.online_df.columns)} cols")
        if "online_data_source" in st.session_state:
            st.caption(f"Source: {st.session_state.online_data_source}")
    else:
        st.info("No online data loaded yet.")

# Main tabs
tab1, tab2, tab3 = st.tabs(["Fetch from URL", "Public Dataset Catalog", "Scrape Web Tables"])

# --- Tab 1: Fetch from URL ---
with tab1:
    st.markdown("### Fetch Data from URL")
    st.markdown("Enter a direct link to a CSV, JSON, or Excel file.")

    url_input = st.text_input(
        "Data URL",
        placeholder="https://example.com/data.csv",
        key="fetch_url_input",
    )

    col_type, col_fetch = st.columns([1, 1])
    with col_type:
        file_type_option = st.selectbox(
            "File type",
            options=["auto", "csv", "json", "excel"],
            index=0,
            help="Auto-detect will infer the type from the URL extension.",
        )
    with col_fetch:
        st.markdown("")
        st.markdown("")
        fetch_button = st.button("\U0001F4E5 Fetch Data", type="primary", key="fetch_url_btn")

    if fetch_button and url_input:
        with st.spinner("Fetching data..."):
            df, error = fetch_data_from_url(url_input, file_type=file_type_option)

        if error:
            st.error(f"Failed to fetch data: {error}")
        else:
            validation = validate_dataframe(df)
            if not validation["is_valid"]:
                for issue in validation["issues"]:
                    st.warning(issue)
            else:
                if validation["issues"]:
                    for issue in validation["issues"]:
                        st.info(issue)

                st.session_state.online_df = df
                st.session_state.online_data_source = url_input
                st.success("Data loaded successfully!")

    elif fetch_button and not url_input:
        st.warning("Please enter a URL.")

# --- Tab 2: Public Dataset Catalog ---
with tab2:
    st.markdown("### Public Dataset Catalog")
    st.markdown("Browse and load curated public datasets from various categories.")

    catalog = get_dataset_catalog()

    for category, datasets in catalog.items():
        with st.expander(f"\U0001F4C2 {category} ({len(datasets)} datasets)", expanded=False):
            for i, dataset in enumerate(datasets):
                col_info, col_action = st.columns([3, 1])
                with col_info:
                    st.markdown(f"**{dataset['name']}**")
                    st.caption(f"{dataset['description']} | Format: {dataset['format'].upper()}")
                with col_action:
                    if st.button(
                        "Load",
                        key=f"catalog_{category}_{i}",
                        type="secondary",
                    ):
                        with st.spinner(f"Loading {dataset['name']}..."):
                            df, error = fetch_data_from_url(
                                dataset["url"], file_type=dataset["format"]
                            )
                        if error:
                            st.error(f"Failed to load: {error}")
                        else:
                            validation = validate_dataframe(df)
                            if not validation["is_valid"]:
                                for issue in validation["issues"]:
                                    st.warning(issue)
                            else:
                                st.session_state.online_df = df
                                st.session_state.online_data_source = dataset["name"]
                                st.success(f"Loaded {dataset['name']}!")
                st.markdown("---")

# --- Tab 3: Scrape Web Tables ---
with tab3:
    st.markdown("### Scrape Tables from Web Page")
    st.markdown("Extract HTML tables from any web page.")

    scrape_url = st.text_input(
        "Web Page URL",
        placeholder="https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)",
        key="scrape_url_input",
    )

    scrape_button = st.button("\U0001F50D Scrape Tables", type="primary", key="scrape_btn")

    if scrape_button and scrape_url:
        with st.spinner("Scraping tables from page..."):
            tables, error = scrape_tables_from_url(scrape_url)

        if error:
            st.error(f"Failed to scrape tables: {error}")
        else:
            st.success(f"Found {len(tables)} table(s) on this page.")
            st.session_state.scraped_tables = tables

    elif scrape_button and not scrape_url:
        st.warning("Please enter a URL.")

    if "scraped_tables" in st.session_state and st.session_state.scraped_tables:
        tables = st.session_state.scraped_tables
        table_index = st.selectbox(
            "Select a table",
            options=range(len(tables)),
            format_func=lambda x: f"Table {x + 1} ({len(tables[x])} rows, {len(tables[x].columns)} columns)",
            key="table_selector",
        )

        selected_table = tables[table_index]
        st.dataframe(selected_table, use_container_width=True)

        if st.button("Use this table", key="use_scraped_table"):
            st.session_state.online_df = selected_table
            st.session_state.online_data_source = f"Scraped table from {st.session_state.get('scrape_url_input', 'web page')}"
            st.success("Table loaded as active dataset!")

# --- Display loaded data ---
st.markdown("---")
st.markdown("### Loaded Data Preview")

if "online_df" in st.session_state and st.session_state.online_df is not None:
    df = st.session_state.online_df

    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rows", f"{len(df):,}")
    with col2:
        st.metric("Columns", len(df.columns))
    with col3:
        memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        st.metric("Memory", f"{memory_mb:.2f} MB")

    # Preview
    st.dataframe(df.head(100), use_container_width=True)

    # Column info
    with st.expander("Column Information"):
        col_info = pd.DataFrame({
            "Type": df.dtypes.astype(str),
            "Non-Null Count": df.count(),
            "Null Count": df.isna().sum(),
            "Unique Values": df.nunique(),
        })
        st.dataframe(col_info, use_container_width=True)

    # Download button
    csv_data = df.to_csv(index=False)
    st.download_button(
        label="\U0001F4BE Download as CSV",
        data=csv_data,
        file_name="online_data_export.csv",
        mime="text/csv",
    )
else:
    st.info("No data loaded yet. Use one of the tabs above to fetch data from the web.")
