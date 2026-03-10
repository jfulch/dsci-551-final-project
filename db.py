"""
db.py — DuckDB backend for the Clickstream Dashboard.

Responsibilities (Jesse Fulcher):
  - Open / reuse the DuckDB connection (in-process, file-backed).
  - Ingest the Kaggle clickstream CSV and persist it as a columnar table.
  - Expose typed query functions that the Streamlit app calls directly.

Dataset columns (e-shop clothing 2008):
  year, month, day, order, country, session_id,
  page_1_main_category, page_2_clothing_model,
  colour, location, model_photography,
  price, price_2, page
"""

import os
import duckdb
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH   = os.path.join(_BASE_DIR, "data", "clickstream.duckdb")
CSV_PATH  = os.path.join(_BASE_DIR, "data", "e-shop clothing 2008.csv")

TABLE_NAME = "clickstream"

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Return a persistent DuckDB connection backed by a file on disk.

    DuckDB internal note:
      Opening a file-backed database causes DuckDB to read its catalog and
      WAL (write-ahead log) pages; subsequent queries benefit from columnar
      storage already written to disk rather than re-scanning CSV every time.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return duckdb.connect(DB_PATH)


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------

def ingest_csv(con: duckdb.DuckDBPyConnection, csv_path: str = CSV_PATH) -> None:
    """
    Load the clickstream CSV into DuckDB as a permanent columnar table.

    DuckDB internal note — read_csv_auto:
      DuckDB's read_csv_auto samples the first rows to infer column types
      automatically (schema inference).  After inference, data is transformed
      into DuckDB's internal columnar format: values for each column are stored
      together in compressed row-group segments on disk.  This one-time cost
      makes all subsequent analytical queries much faster because only the
      columns a query touches are read from disk (column pruning).
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"CSV not found at: {csv_path}\n"
            "Download from https://www.kaggle.com/datasets/tunguz/clickstream-data-for-online-shopping "
            "and place it in the data/ folder."
        )

    # Drop and recreate so re-running the app is idempotent
    con.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")

    con.execute(f"""
        CREATE TABLE {TABLE_NAME} AS
        SELECT
            year::INTEGER                       AS year,
            month::INTEGER                      AS month,
            day::INTEGER                        AS day,
            "order"::INTEGER                    AS click_order,
            country::VARCHAR                    AS country,
            "session ID"::VARCHAR               AS session_id,
            "page 1 (main category)"::VARCHAR   AS main_category,
            "page 2 (clothing model)"::VARCHAR  AS clothing_model,
            colour::VARCHAR                     AS colour,
            location::INTEGER                   AS location,
            "model photography"::INTEGER        AS model_photography,
            price::DOUBLE                       AS price,
            "price 2"::INTEGER                  AS price_above_avg,
            page::INTEGER                       AS page_depth
        FROM read_csv_auto('{csv_path}', header=true, sep=';')
    """)
    print(f"[db] Loaded {row_count(con):,} rows into '{TABLE_NAME}'.")


def ensure_table(con: duckdb.DuckDBPyConnection) -> None:
    """Load the CSV if the table doesn't exist yet."""
    tables = con.execute("SHOW TABLES").fetchdf()["name"].tolist()
    if TABLE_NAME not in tables:
        ingest_csv(con)


def row_count(con: duckdb.DuckDBPyConnection) -> int:
    return con.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()[0]


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def traffic_overview(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    Monthly traffic summary: total clicks, unique sessions, avg clicks/session.

    DuckDB internal note — vectorized aggregation:
      GROUP BY + COUNT aggregations run in DataChunk batches (~1,024 rows).
      The vectorized engine processes each chunk with tight CPU loops, keeping
      data in L1/L2 cache.  Only the month, session_id columns are read from
      the columnar store (column pruning).
    """
    return con.execute(f"""
        SELECT
            year,
            month,
            COUNT(*)                            AS total_clicks,
            COUNT(DISTINCT session_id)          AS unique_sessions,
            ROUND(COUNT(*) * 1.0 /
                  NULLIF(COUNT(DISTINCT session_id), 0), 2) AS avg_clicks_per_session
        FROM {TABLE_NAME}
        GROUP BY year, month
        ORDER BY year, month
    """).fetchdf()


def clicks_by_country(con: duckdb.DuckDBPyConnection, top_n: int = 20) -> pd.DataFrame:
    """
    Total and average clicks per country (top N by total clicks).

    DuckDB internal note:
      Columnar storage means only the `country` column segment is read for
      the GROUP BY scan; the price column segment is scanned separately for
      the AVG — no unnecessary columns are touched.
    """
    return con.execute(f"""
        SELECT
            country,
            COUNT(*)                            AS total_clicks,
            COUNT(DISTINCT session_id)          AS unique_sessions,
            ROUND(AVG(price), 2)                AS avg_price_viewed
        FROM {TABLE_NAME}
        GROUP BY country
        ORDER BY total_clicks DESC
        LIMIT {top_n}
    """).fetchdf()


def top_categories(con: duckdb.DuckDBPyConnection, top_n: int = 10) -> pd.DataFrame:
    """
    Most-viewed main product categories ranked by click count.

    DuckDB internal note:
      Only main_category and the implicit row-count are needed; DuckDB's
      column pruning skips every other column segment on disk entirely.
    """
    return con.execute(f"""
        SELECT
            main_category,
            COUNT(*)                            AS total_clicks,
            COUNT(DISTINCT session_id)          AS unique_sessions,
            ROUND(AVG(price), 2)                AS avg_price
        FROM {TABLE_NAME}
        GROUP BY main_category
        ORDER BY total_clicks DESC
        LIMIT {top_n}
    """).fetchdf()


def top_products(con: duckdb.DuckDBPyConnection, top_n: int = 15) -> pd.DataFrame:
    """
    Most-viewed clothing models with their average price.
    """
    return con.execute(f"""
        SELECT
            clothing_model,
            main_category,
            COUNT(*)                            AS total_clicks,
            COUNT(DISTINCT session_id)          AS unique_sessions,
            ROUND(AVG(price), 2)                AS avg_price
        FROM {TABLE_NAME}
        WHERE clothing_model IS NOT NULL
        GROUP BY clothing_model, main_category
        ORDER BY total_clicks DESC
        LIMIT {top_n}
    """).fetchdf()


def session_engagement(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    Engagement breakdown: avg clicks per session by main_category and
    whether the user saw above- or below-average prices.

    Answers business question #4: does seeing lower prices increase clicks?

    DuckDB internal note:
      Multi-column GROUP BY with a CASE expression — the vectorized engine
      evaluates the CASE in a single DataChunk pass without materialising
      intermediate rows, keeping memory pressure low.
    """
    return con.execute(f"""
        SELECT
            main_category,
            CASE price_above_avg
                WHEN 1 THEN 'Above average'
                WHEN 2 THEN 'Below average'
                ELSE 'Unknown'
            END                                 AS price_tier,
            COUNT(DISTINCT session_id)          AS sessions,
            COUNT(*)                            AS total_clicks,
            ROUND(COUNT(*) * 1.0 /
                  NULLIF(COUNT(DISTINCT session_id), 0), 2) AS avg_clicks_per_session
        FROM {TABLE_NAME}
        GROUP BY main_category, price_above_avg
        ORDER BY avg_clicks_per_session DESC
    """).fetchdf()


def category_depth(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    Which categories do users browse deepest (highest page_depth reached)?

    Answers business question #5.

    DuckDB internal note:
      MAX() over a column segment benefits from run-length encoding: if many
      rows share the same page_depth value, DuckDB can evaluate the aggregate
      over the compressed representation directly.
    """
    return con.execute(f"""
        SELECT
            main_category,
            ROUND(AVG(page_depth), 2)           AS avg_page_depth,
            MAX(page_depth)                     AS max_page_depth,
            COUNT(DISTINCT session_id)          AS sessions
        FROM {TABLE_NAME}
        GROUP BY main_category
        ORDER BY avg_page_depth DESC
    """).fetchdf()


def price_distribution(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    Price distribution by main_category and photo location on the page.

    Answers part of business question #4 (does photo location affect clicks?).
    """
    return con.execute(f"""
        SELECT
            main_category,
            location,
            COUNT(*)                            AS click_count,
            ROUND(MIN(price), 2)                AS min_price,
            ROUND(AVG(price), 2)                AS avg_price,
            ROUND(MAX(price), 2)                AS max_price
        FROM {TABLE_NAME}
        GROUP BY main_category, location
        ORDER BY main_category, location
    """).fetchdf()


# ---------------------------------------------------------------------------
# Internals inspection helpers (used in report / optional debug page)
# ---------------------------------------------------------------------------

def explain_query(con: duckdb.DuckDBPyConnection, sql: str) -> str:
    """Return DuckDB's EXPLAIN output for a SQL string."""
    rows = con.execute(f"EXPLAIN {sql}").fetchall()
    return "\n".join(r[1] for r in rows)


def explain_analyze_query(con: duckdb.DuckDBPyConnection, sql: str) -> str:
    """Return EXPLAIN ANALYZE output (runs the query)."""
    rows = con.execute(f"EXPLAIN ANALYZE {sql}").fetchall()
    return "\n".join(r[1] for r in rows)


# ---------------------------------------------------------------------------
# Dev / quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    con = get_connection()
    ensure_table(con)
    print("\n--- Traffic Overview ---")
    print(traffic_overview(con))
    print("\n--- Top Categories ---")
    print(top_categories(con))
    print("\n--- Clicks by Country ---")
    print(clicks_by_country(con))
    print("\n--- Session Engagement ---")
    print(session_engagement(con))
    print("\n--- Category Depth ---")
    print(category_depth(con))
    con.close()
