# Online Shopping Clickstream Dashboard (DSCI 551)

This project is for the DSCI 551 course project. It's a self-service customer insights dashboard built with **Streamlit**, **Python**, and **DuckDB** on top of the Kaggle "Clickstream Data for Online Shopping" dataset. The goal is to explore user behavior on an e-commerce site (for maternity clothing) and connect what the dashboard does to DuckDB's internals like columnar storage and vectorized execution.

## Tech stack

- Python 3.11+
- DuckDB (in-process analytical database)
- Streamlit (web UI framework)
- Pandas for data wrangling
- Plotly for interactive charts

## Dataset

We use the **Clickstream Data for Online Shopping** dataset from Kaggle.  
It contains 165,474 rows and 14 columns of click events (session IDs, timestamps, product/category info, price, country, etc.) collected over five months.

Dataset link:  
https://www.kaggle.com/datasets/tunguz/clickstream-data-for-online-shopping

## Project structure

```
.
├── app.py              # Streamlit app entrypoint (dashboard UI)
├── db.py               # DuckDB connection, ingestion, and query functions
├── requirements.txt    # Python dependencies
├── data/
│   ├── e-shop clothing 2008.csv   # Kaggle dataset (included in repo)
│   └── clickstream.duckdb         # Generated on first run -- do not commit
└── documentation/      # PDFs: project proposal and professor guidelines
```

## Dashboard pages

| Page | Business question answered |
|------|---------------------------|
| Traffic Overview | How popular has the site been overall by month? |
| Product Performance | Which products/categories get the most clicks? |
| Geographic Analysis | Which countries generate the most traffic? |
| Session Engagement | Does price tier affect how long users browse? |
| Category Depth | Which categories do users explore deepest? |
| DuckDB Internals | Run EXPLAIN / EXPLAIN ANALYZE on any SQL query |

## Credentials / API Keys

**No API keys or credentials are required to run this application.**

The dataset can be downloaded manually (no account required) from the Kaggle link in the Dataset section above.

The optional Kaggle CLI download method requires a Kaggle API token:
- Obtain it at: Kaggle → Account Settings → API → **Create New Token** (downloads `kaggle.json`)
- Place the file at `~/.kaggle/kaggle.json` (macOS/Linux) or `%USERPROFILE%\.kaggle\kaggle.json` (Windows)
- Set permissions: `chmod 600 ~/.kaggle/kaggle.json`
- **Do not commit this file to the repository** — it contains your personal API credentials

If you prefer not to use the CLI, skip the Kaggle token entirely and download the CSV manually (see Setup step 3).

## Setup

1. Clone the repo and create a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. The dataset is included in the repository (`data/e-shop clothing 2008.csv`) — no separate download needed.

   If the file is missing for any reason, download it manually:
   - From: https://www.kaggle.com/datasets/tunguz/clickstream-data-for-online-shopping
   - File must be named **`e-shop clothing 2008.csv`** and placed in the `data/` folder.
   - Or via the Kaggle CLI (requires API token — see Credentials section above):

     ```bash
     pip install kaggle
     kaggle datasets download tunguz/clickstream-data-for-online-shopping --unzip -p data/
     ```

4. Run the Streamlit app:

   ```bash
   streamlit run app.py
   ```

   The app opens at `http://localhost:8501`.  
   On first launch, DuckDB ingests the CSV into `data/clickstream.duckdb` automatically (takes a few seconds).  
   Subsequent launches reuse the `.duckdb` file directly -- no re-ingestion needed.

5. (Optional) Test the backend queries without the browser:

   ```bash
   python db.py
   ```

   This prints the output of all query functions to the terminal to verify data loaded correctly.

## Project goals (course)

Analyze DuckDB internals with a focus on:

- **Columnar storage** -- column pruning, segments/row groups, compressed representation.
- **Vectorized query execution** -- DataChunks, operator pipeline, cache-friendly batch processing.
- **CSV ingestion** -- `read_csv_auto` schema inference and how data is transformed into DuckDB's internal columnar format.

For each major dashboard operation the code documents: what the app does, what DuckDB does internally, and why that matters for performance.

