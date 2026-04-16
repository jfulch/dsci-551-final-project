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
│   ├── e-shop clothing 2008.csv   # Kaggle dataset (downloaded separately)
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

3. Download the Kaggle clickstream CSV and place it in `data/`:

   - File must be named **`e-shop clothing 2008.csv`** (the default Kaggle filename).
   - Download from: https://www.kaggle.com/datasets/tunguz/clickstream-data-for-online-shopping
   - Or via the Kaggle CLI (recommended):

     ```bash
     # Install the Kaggle CLI
     pip install kaggle

     # Place your API token at ~/.kaggle/kaggle.json
     # (Kaggle account -> Settings -> API -> Create New Token)

     # Download and unzip directly into data/
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

---

## Implementation status

### Done

- DuckDB connection, CSV ingestion via `read_csv_auto`, persistent `.duckdb` file
- All 5 business questions answered as interactive Streamlit pages
- `EXPLAIN` / `EXPLAIN ANALYZE` explorer on the DuckDB Internals page
- Internals mapping comments in every query function in `db.py`
- Dataset, source code, and run instructions ready for TA/instructor review

### Still needed (before demo -- 4/20)

1. **Runtime CSV upload** -- The proposal stated users can load new CSV data at runtime to demonstrate `read_csv_auto`. Need a file-upload widget on the Internals page that ingests an uploaded CSV into a temporary DuckDB table.

2. **CSV-direct vs. DuckDB-table benchmark** -- Need a section that runs the same query against (a) the raw CSV via `read_csv_auto` and (b) the persisted columnar table, side-by-side with timing, to visibly demonstrate the columnar storage speedup.

3. **Standalone setup script** -- The professor's rubric requires a separate "database schema / setup scripts" artifact. An `init_db.py` that a TA can run independently to ingest the CSV without launching the full Streamlit app.

### Final report -- due 5/8 (10-12 pages for a group of 3)

Required sections:
- Introduction & Motivation
- DuckDB System Overview
- Internal Architecture (columnar storage, vectorized execution, CSV ingestion)
- Application Design
- Mapping Internals to Application Behavior (most heavily weighted)
- Comparison with MySQL and MongoDB
- Limitations & Lessons Learned
- Link to Google Drive with all code and documentation
