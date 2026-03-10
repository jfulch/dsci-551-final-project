# Online Shopping Clickstream Dashboard (DSCI 551)

This project is for the DSCI 551 course project. It’s a self‑service customer insights dashboard built with **Streamlit**, **Python**, and **DuckDB** on top of the Kaggle “Clickstream Data for Online Shopping” dataset.[file:65][web:44] The goal is to explore user behavior on an e‑commerce site (for maternity clothing) and connect what the dashboard does to DuckDB’s internals like columnar storage and vectorized execution.[file:65][web:13][web:18]

## Tech stack

- Python 3.10+
- DuckDB (in‑process analytical database)
- Streamlit (web UI framework)
- Pandas for basic data handling

## Dataset

We use the **Clickstream Data for Online Shopping** dataset from Kaggle.[file:65][web:44]  
It contains 165,474 rows and 14 columns of click events (session IDs, timestamps, product/category info, price, country, etc.) collected over five months.[file:65][web:44]

Dataset link:  
https://www.kaggle.com/datasets/tunguz/clickstream-data-for-online-shopping

## Project structure

- `app.py` – Streamlit app entrypoint (dashboard UI).
- `db.py` – DuckDB connection + helper functions and SQL queries.
- `data/` – Clickstream CSV and any other input data.
- `notebooks/` (optional) – Exploration, `EXPLAIN` plans, and notes on DuckDB internals.

## Features (planned / current)

- Traffic overview: total/average clicks and unique sessions by month and country.[file:65]
- Product performance: most viewed product categories and products.[file:65]
- Engagement: how long users stay on the site (clicks per session), and which categories they explore the most.[file:65]
- Early experiments comparing:
  - Querying the raw CSV via `read_csv_auto`.
  - Querying data stored in a DuckDB table (to highlight columnar storage and vectorized execution).[file:65][web:22][web:13]

## Setup

1. Clone the repo and create a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

2. Install dependencies:

   ```bash
    pip install -r requirements.txt
   ```

3. Download the Kaggle clickstream CSV into the data/ folder (or update db.py to point to the correct path).

4. Run the Streamlit app:

   ```bash
   streamlit run app.py
   ```

## Project goals (course)
Analyze DuckDB internals with a focus on:
- Columnar storage (column pruning, segments/row groups).
- Vectorized query execution (DataChunks, operator pipeline).
- CSV ingestion (read_csv_auto) and how data is loaded into DuckDB’s internal format.[file:65][web:13][web:18][web:22]

Build a small but functional dashboard and explain, for each key feature, what the app does, what DuckDB does internally, and why that matters for performance and behavior.[file:66]
