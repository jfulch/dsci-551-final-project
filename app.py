import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

import db

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Clickstream Customer Insights",
    page_icon="🛍️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# DuckDB connection (cached so it's reused across Streamlit reruns)
# ---------------------------------------------------------------------------
@st.cache_resource
def get_con():
    con = db.get_connection()
    db.ensure_table(con)
    return con


con = get_con()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("🛍️ Clickstream Dashboard")
st.sidebar.caption("Online Clothing Store — 2008 Clickstream Data")

page = st.sidebar.radio(
    "Navigation",
    [
        "📈 Traffic Overview",
        "🏷️ Product Performance",
        "🌍 Geographic Analysis",
        "🔁 Session Engagement",
        "📄 Category Depth",
        "🔬 DuckDB Internals",
    ],
)

# ---------------------------------------------------------------------------
# Helper: cached query calls
# ---------------------------------------------------------------------------
@st.cache_data
def load_traffic():
    return db.traffic_overview(con)

@st.cache_data
def load_countries(top_n=20):
    return db.clicks_by_country(con, top_n=top_n)

@st.cache_data
def load_categories(top_n=10):
    return db.top_categories(con, top_n=top_n)

@st.cache_data
def load_products(top_n=15):
    return db.top_products(con, top_n=top_n)

@st.cache_data
def load_engagement():
    return db.session_engagement(con)

@st.cache_data
def load_depth():
    return db.category_depth(con)

@st.cache_data
def load_price_dist():
    return db.price_distribution(con)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

# ── 1. Traffic Overview ────────────────────────────────────────────────────
if page == "📈 Traffic Overview":
    st.title("📈 Traffic Overview")
    st.caption(
        "How popular has the website been overall? "
        "DuckDB reads only the `month`, `session_id` columns from disk (column pruning)."
    )

    df = load_traffic()
    df["period"] = df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Clicks",    f"{df['total_clicks'].sum():,}")
    col2.metric("Unique Sessions", f"{df['unique_sessions'].sum():,}")
    col3.metric("Avg Clicks / Session",
                f"{(df['total_clicks'].sum() / df['unique_sessions'].sum()):.2f}")

    st.subheader("Monthly Clicks")
    fig = px.bar(df, x="period", y="total_clicks",
                 labels={"period": "Month", "total_clicks": "Total Clicks"},
                 color_discrete_sequence=["#636EFA"])
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Unique Sessions per Month")
    fig2 = px.line(df, x="period", y="unique_sessions", markers=True,
                   labels={"period": "Month", "unique_sessions": "Unique Sessions"})
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("Raw data"):
        st.dataframe(df)


# ── 2. Product Performance ─────────────────────────────────────────────────
elif page == "🏷️ Product Performance":
    st.title("🏷️ Product Performance")
    st.caption(
        "Which products and categories get the most clicks? "
        "DuckDB scans only `main_category`, `clothing_model`, `price` column segments."
    )

    top_n_cat  = st.slider("Top N categories", 1, 10, 4)
    top_n_prod = st.slider("Top N products",   5, 30, 15)

    df_cat  = load_categories(top_n_cat)
    df_prod = load_products(top_n_prod)

    st.subheader("Top Categories by Clicks")
    fig = px.bar(df_cat, x="total_clicks", y="main_category", orientation="h",
                 color="avg_price", color_continuous_scale="Blues",
                 labels={"main_category": "Category", "total_clicks": "Clicks"})
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top Products by Clicks")
    fig2 = px.bar(df_prod, x="total_clicks", y="clothing_model", orientation="h",
                  color="main_category",
                  labels={"clothing_model": "Product", "total_clicks": "Clicks"})
    fig2.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("Raw data — categories"):
        st.dataframe(df_cat)
    with st.expander("Raw data — products"):
        st.dataframe(df_prod)





# ── 3. Geographic Analysis ─────────────────────────────────────────────────
elif page == "🌍 Geographic Analysis":
    st.title("🌍 Geographic Analysis")
    st.caption("Which countries have shown the most website activity?")

    # load data 
    df = load_countries(100) 

    import pandas as pd
    import numpy as np
    import plotly.express as px

    # --- If df uses numeric country codes, map them (fallback mapping) ---
    num_to_name = {
        1: "Australia", 2: "Austria", 3: "Belgium", 4: "British Virgin Islands",
        5: "Cayman Islands", 6: "Christmas Island", 7: "Croatia", 8: "Cyprus",
        9: "Czech Republic", 10: "Denmark", 11: "Estonia", 12: None,
        13: "Faroe Islands", 14: "Finland", 15: "France", 16: "Germany",
        17: "Greece", 18: "Hungary", 19: "Iceland", 20: "India", 21: "Ireland",
        22: "Italy", 23: "Latvia", 24: "Lithuania", 25: "Luxembourg", 26: "Mexico",
        27: "Netherlands", 28: "Norway", 29: "Poland", 30: "Portugal", 31: "Romania",
        32: "Russia", 33: "San Marino", 34: "Slovakia", 35: "Slovenia", 36: "Spain",
        37: "Sweden", 38: "Switzerland", 39: "Ukraine", 40: "United Arab Emirates",
        41: "United Kingdom", 42: "United States"
    }

    # ensure country_name exists
    if "country_name" not in df.columns:
        def to_int_safe(v):
            try:
                return int(v)
            except Exception:
                return None
        df = df.copy()
        df["country_code_num"] = df["country"].apply(to_int_safe)
        df["country_name"] = df["country_code_num"].map(num_to_name)

    # Ensure numeric metrics exist
    for c in ["total_clicks", "unique_sessions", "avg_price_viewed"]:
        if c not in df.columns:
            df[c] = 0
    df["total_clicks"] = pd.to_numeric(df["total_clicks"], errors="coerce").fillna(0)
    df["unique_sessions"] = pd.to_numeric(df["unique_sessions"], errors="coerce").fillna(0)
    df["avg_price_viewed"] = pd.to_numeric(df["avg_price_viewed"], errors="coerce")

    # ------------------- layout: controls (LEFT), chart (RIGHT) -------------------
    col_controls, col_chart = st.columns([1, 4])

    # ─── Controls column (LEFT) ─────────────────────
    with col_controls:
        st.subheader("Controls")
        top_n = st.slider("Number of countries", 5, 50, 10)  # default to 10
        show_europe_only = st.checkbox("Show only Europe", value=False)
        metric = st.selectbox(
            "Metric",
            ("total_clicks", "unique_sessions", "avg_price_viewed"),
            format_func=lambda x: {
                "total_clicks": "Total Clicks",
                "unique_sessions": "Unique Sessions",
                "avg_price_viewed": "Avg Price Viewed"
            }[x]
        )

        st.divider()
        st.subheader("Activity Summary")
        # placeholders
        total_clicks_placeholder = st.empty()
        unique_sessions_placeholder = st.empty()
        avg_price_placeholder = st.empty()

        st.divider()
        st.caption("Download")
        # (download buttons will be added after table is built)

    # Filter dataset based on Europe selection
    europe_countries = {
        "Austria","Belgium","Croatia","Cyprus","Czech Republic","Denmark","Estonia",
        "Faroe Islands","Finland","France","Germany","Greece","Hungary","Iceland",
        "Ireland","Italy","Latvia","Lithuania","Luxembourg","Netherlands","Norway",
        "Poland","Portugal","Romania","San Marino","Slovakia","Slovenia","Spain",
        "Sweden","Switzerland","United Kingdom","Russia","Ukraine"
    }

    if show_europe_only:
        df_plot = df[df["country_name"].isin(europe_countries)].copy()
    else:
        df_plot = df.copy()

    if df_plot.empty:
        with col_chart:
            st.warning("No country rows available for the selected filter. Try disabling 'Show only Europe' or increase Number of countries.")
    else:
        # aggregate / group in case of duplicates
        agg = (
            df_plot.groupby("country_name", dropna=True)
            .agg(
                total_clicks=pd.NamedAgg(column="total_clicks", aggfunc="sum"),
                unique_sessions=pd.NamedAgg(column="unique_sessions", aggfunc="sum"),
                avg_price_viewed=pd.NamedAgg(column="avg_price_viewed", aggfunc="mean")
            )
            .reset_index()
        )

        # select and sort top_n by chosen metric
        agg["sort_val"] = agg[metric]
        agg = agg.sort_values("sort_val", ascending=False).head(top_n).reset_index(drop=True)

        # Prepare display values (formatted) for labels
        agg["display_val"] = agg[metric].map(lambda v: "{:,}".format(int(v)) if pd.notna(v) else "—")
        # color and style
        single_color = "#2be6cf"

        # Build horizontal bar chart — set height to fill control column visually
        chart_height = 560
        fig = px.bar(
            agg,
            x=metric,
            y="country_name",
            orientation="h",
            labels={"country_name": "Country",
                    metric: {"total_clicks": "Total Clicks", "unique_sessions": "Unique Sessions", "avg_price_viewed": "Avg Price Viewed"}[metric]},
            height=chart_height,
        )

        fig.update_traces(
            marker_color=single_color,
            marker_line_color="white",
            marker_line_width=0.5,
            width=0.65,                 
            text=agg["display_val"],
            textposition="outside",
        )

        # Make width depend on number of countries so wide labels can scroll horizontally if necessary
        base_width = 780
        per_row = 18
        chart_width = base_width + len(agg) * per_row

        # Tighten margins and ensure the layout height matches chart_height
        fig.update_layout(
            margin=dict(l=140, r=80, t=8, b=24),
            yaxis=dict(autorange="reversed"),
            width=chart_width,
            height=chart_height,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        # chart (inside scrollable container to allow horizontal scrolling) -- this isn't working right now
        with col_chart:
            st.subheader("Country ranking")
            st.markdown(
                f'<div style="overflow-x:auto; -webkit-overflow-scrolling: touch; padding-bottom:6px;"><div style="min-width:{chart_width}px">',
                unsafe_allow_html=True,
            )
            st.plotly_chart(fig, use_container_width=False, config={"displayModeBar": False})
            st.markdown('</div></div>', unsafe_allow_html=True)

        # Update KPIs in the left column placeholders using the actual displayed set
        total_clicks_displayed = int(agg["total_clicks"].sum())
        unique_sessions_displayed = int(agg["unique_sessions"].sum())
        avg_price_displayed = agg["avg_price_viewed"].dropna().mean() if not agg["avg_price_viewed"].dropna().empty else 0.0

        with col_controls:
            total_clicks_placeholder.metric("Total Clicks", f"{total_clicks_displayed:,}")
            unique_sessions_placeholder.metric("Unique Sessions", f"{unique_sessions_displayed:,}")
            avg_price_placeholder.metric("Avg Price Viewed", f"${avg_price_displayed:,.2f}")

        # ------------------ bottom: full-metrics table for displayed countries ------------------
        displayed_countries = agg["country_name"].tolist()
        metrics_df = (
            df_plot
            .groupby("country_name", dropna=True)
            .agg(
                total_clicks=pd.NamedAgg(column="total_clicks", aggfunc="sum"),
                unique_sessions=pd.NamedAgg(column="unique_sessions", aggfunc="sum"),
                avg_price_viewed=pd.NamedAgg(column="avg_price_viewed", aggfunc="mean"),
            )
            .reset_index()
        )
        metrics_df = metrics_df[metrics_df["country_name"].isin(displayed_countries)].copy()
        # reorder to match chart order
        metrics_df["__order"] = metrics_df["country_name"].apply(lambda x: displayed_countries.index(x) if x in displayed_countries else 999)
        metrics_df = metrics_df.sort_values("__order").drop(columns="__order").reset_index(drop=True)

        # change display
        display_table = metrics_df.copy()
        display_table["Total Clicks"] = display_table["total_clicks"].map("{:,}".format)
        display_table["Unique Sessions"] = display_table["unique_sessions"].map("{:,}".format)
        display_table["Avg Price Viewed"] = display_table["avg_price_viewed"].map(lambda v: f"${v:,.2f}" if pd.notna(v) else "—")
        display_table = display_table[["country_name", "Total Clicks", "Unique Sessions", "Avg Price Viewed"]]
        display_table = display_table.rename(columns={"country_name": "Country"})

        st.divider()
        st.subheader("Data — displayed countries (all metrics)")
        st.dataframe(display_table, use_container_width=True)

        # Downloads both the displayed table and raw numeric CSV
        csv_pretty = display_table.to_csv(index=False).encode("utf-8")
        st.download_button("Download displayed table (pretty CSV)", csv_pretty, file_name="countries_displayed_pretty.csv", mime="text/csv")

        csv_raw = metrics_df.rename(columns={
            "country_name": "Country",
            "total_clicks": "Total Clicks",
            "unique_sessions": "Unique Sessions",
            "avg_price_viewed": "Avg Price Viewed"
        }).to_csv(index=False).encode("utf-8")
        st.download_button("Download displayed table (raw CSV)", csv_raw, file_name="countries_displayed_raw.csv", mime="text/csv")

# ── 4. Session Engagement ──────────────────────────────────────────────────
elif page == "🔁 Session Engagement":
    st.title("🔁 Session Engagement")
    st.caption(
        "Does seeing above- or below-average prices affect how long users browse? "
        "DuckDB evaluates the CASE expression in a single vectorized DataChunk pass."
    )

    df = load_engagement()

    fig = px.bar(df, x="main_category", y="avg_clicks_per_session",
                 color="price_tier", barmode="group",
                 labels={
                     "main_category": "Category",
                     "avg_clicks_per_session": "Avg Clicks / Session",
                     "price_tier": "Price Tier",
                 })
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Price Distribution by Category")
    df_price = load_price_dist()
    fig2 = px.box(
        con.execute(
            "SELECT main_category, price FROM clickstream WHERE price IS NOT NULL"
        ).fetchdf(),
        x="main_category", y="price",
        labels={"main_category": "Category", "price": "Price"},
        color="main_category",
    )
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("Raw engagement data"):
        st.dataframe(df)


# ── 5. Category Depth ──────────────────────────────────────────────────────
elif page == "📄 Category Depth":
    st.title("📄 Category Depth")
    st.caption(
        "Which categories do users explore deepest (highest page number reached)? "
        "DuckDB's MAX() can leverage run-length encoding in compressed column segments."
    )

    df = load_depth()

    fig = px.bar(df, x="avg_page_depth", y="main_category", orientation="h",
                 color="max_page_depth", color_continuous_scale="Oranges",
                 labels={
                     "main_category": "Category",
                     "avg_page_depth": "Avg Page Depth",
                     "max_page_depth": "Max Page Depth",
                 })
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Raw data"):
        st.dataframe(df)


# ── 6. DuckDB Internals ────────────────────────────────────────────────────
elif page == "🔬 DuckDB Internals":
    st.title("🔬 DuckDB Internals Explorer")
    st.caption(
        "Run EXPLAIN or EXPLAIN ANALYZE on any query to see DuckDB's physical plan "
        "and operator pipeline — useful for the final report."
    )

    default_sql = (
        "SELECT main_category, COUNT(*) AS clicks, AVG(price) AS avg_price\n"
        "FROM clickstream\n"
        "GROUP BY main_category\n"
        "ORDER BY clicks DESC"
    )

    sql = st.text_area("SQL query", value=default_sql, height=120)

    col1, col2 = st.columns(2)
    if col1.button("EXPLAIN (logical plan)"):
        try:
            plan = db.explain_query(con, sql)
            st.code(plan, language="text")
        except Exception as e:
            st.error(str(e))

    if col2.button("EXPLAIN ANALYZE (with runtime stats)"):
        try:
            plan = db.explain_analyze_query(con, sql)
            st.code(plan, language="text")
        except Exception as e:
            st.error(str(e))

    st.divider()
    st.subheader("Run a raw query")
    if st.button("Run query"):
        try:
            df = con.execute(sql).fetchdf()
            st.dataframe(df)
        except Exception as e:
            st.error(str(e))
