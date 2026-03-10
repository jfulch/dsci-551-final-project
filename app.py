"""
app.py — Streamlit dashboard for the Clickstream Customer Insights app.

Frontend responsibilities (Vivian Tran): charts, layout, styling.
Backend wired here via db.py (Jesse Fulcher).
"""

import streamlit as st
import plotly.express as px

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

    top_n_cat  = st.slider("Top N categories", 5, 20, 10)
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
    st.caption(
        "Which countries generate the most clicks? "
        "Only `country`, `session_id`, `price` columns are scanned."
    )

    top_n = st.slider("Top N countries", 5, 50, 20)
    df = load_countries(top_n)

    fig = px.bar(df, x="country", y="total_clicks",
                 color="unique_sessions", color_continuous_scale="Teal",
                 labels={"country": "Country", "total_clicks": "Total Clicks"})
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Avg Price Viewed by Country")
    fig2 = px.bar(df.sort_values("avg_price_viewed", ascending=False),
                  x="country", y="avg_price_viewed",
                  labels={"country": "Country", "avg_price_viewed": "Avg Price Viewed"})
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("Raw data"):
        st.dataframe(df)


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
