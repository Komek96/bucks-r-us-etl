# Bucks-R-Us ETL & Retail Analytics System

Bucks-R-Us is a fictional multi-location fixed-price discount retailer created as the basis for a data analytics and ETL portfolio project.

Bucks-R-Us implements an end-to-end retail inventory ETL workflow. It extracts product, store, and inventory data from Google Sheets, validates operational records, loads them into PostgreSQL, and generates SQL analytics for an interactive Streamlit dashboard. Sales-demand analysis remains planned.

## Business Problem

Bucks-R-Us operates multiple retail locations selling most merchandise at a standardized company-wide price. Each store generates sales and inventory data, while product and store information are maintained separately.

The business needs a reliable way to combine these sources so analysts can answer questions such as:

- Which products sell differently across store locations?
- Which products or categories are increasing or declining in demand?
- Where are inventory shortages occurring?
- Are stores receiving inventory appropriate for their local demand?
- Are incoming operational records complete and trustworthy?

The initial development work is focused on building the ingestion and data-quality foundation required before those analyses can be trusted.

## Current Data Sources

The project currently uses three operational datasets maintained as separate tabs in a shared Google Sheet. The Python extraction script retrieves each dataset independently using CSV export endpoints.

### Inventory

Inventory represents a snapshot of product quantities at a store at a specific point in time.

| Field | Description |
|---|---|
| `store_id` | Store associated with the inventory record |
| `sku` | Product identifier |
| `quantity_on_hand` | Quantity of the product currently in inventory |
| `inventory_timestamp` | Time the inventory snapshot was recorded |

Inventory snapshots are intended to be received weekly for each store.

### Product Catalog

The product catalog provides reference information used to validate inventory SKUs.

| Field | Description |
|---|---|
| `sku` | Stable product identifier |
| `product_name` | Human-readable product name |
| `category` | Product category |
| `status` | Current product status |

### Store Catalog

The store catalog provides reference information used to validate store identifiers and will support historical handling of closed locations.

| Field | Description |
|---|---|
| `store_id` | Unique store identifier such as `BRU-0001` |
| `address` | Street address |
| `city` | City |
| `state` | State |
| `zip_code` | Postal code |
| `status` | Current store status |
| `closed_at` | Date/time the store closed, if applicable |

## Planned Data Sources

The complete system is intended to include sales transaction data in addition to the inventory, product, and store datasets already being developed.

Sales data is planned around a receipt-based structure where a receipt identifies the transaction and individual receipt-item records identify the products and quantities sold.

## Data Quality and Validation

Incoming inventory data is validated before it can be treated as trusted data. Invalid records are separated from valid records rather than silently corrected.

The following validation rules are currently implemented:

| Validation | Behavior |
|---|---|
| Negative quantity | Reject as `NEGATIVE_QUANTITY` |
| Missing SKU | Reject as `MISSING_SKU` |
| Unknown SKU | Reject as `UNKNOWN_SKU` |
| Unknown store | Reject as `UNKNOWN_STORE` |
| Missing or malformed timestamp | Reject as `INVALID_TIMESTAMP` |
| Exact duplicate inventory record | Reject both copies as `DUPLICATE_INVENTORY_RECORD` |
| Conflicting inventory records | Reject both records as `CONFLICTING_INVENTORY_RECORD` |
| Inventory after store closure | Reject as `INVENTORY_AFTER_STORE_CLOSURE` |

### Duplicate vs. Conflicting Records

The pipeline distinguishes between two different data-quality problems.

An **exact duplicate** occurs when the store, SKU, quantity, and inventory timestamp are identical across multiple records.

A **conflicting record** occurs when multiple records describe the same store, SKU, and inventory timestamp but report different quantities.

For example:

| store_id | sku | quantity_on_hand | inventory_timestamp |
|---|---|---:|---|
| BRU-0001 | SKU-20481 | 12 | 2026-10-05 08:00:00 |
| BRU-0001 | SKU-20481 | 99 | 2026-10-05 08:00:00 |

Because the system cannot determine which quantity is authoritative, both records are rejected rather than arbitrarily selecting one.

### Validation Testing

Validation rules have been tested by deliberately introducing bad records into the source data and verifying the resulting pipeline behavior.

Tests performed so far include:

- Supplying a negative inventory quantity.
- Removing a SKU from an inventory record.
- Supplying a SKU absent from the product catalog.
- Supplying an unknown store identifier.
- Supplying malformed timestamp data.
- Supplying a missing timestamp.
- Creating two identical inventory records.
- Creating two inventory records for the same store, SKU, and timestamp with different quantities.
- Supplying inventory dated after a store's recorded closure time.
- Verifying that historical inventory dated before a store's closure remains valid.

After each test, the source data was restored and the pipeline was rerun against the clean dataset to verify that valid records passed validation.

## Design and Failure-Handling Decisions

The pipeline is being designed around the principle that questionable source data should not be silently modified to make it appear valid. When the system cannot confidently determine the correct value, the record should be rejected or quarantined for investigation.

### Inventory Snapshot Model

Inventory is modeled as a recurring snapshot rather than a continuously updated quantity.

Each snapshot identifies:

- The store.
- The product SKU.
- The quantity observed.
- The time the inventory was observed.

Inventory reports are expected weekly, currently modeled as Monday snapshots.

### Late Inventory Data

A valid inventory snapshot may arrive after its expected delivery time.

Late data should not automatically be rejected. The system should distinguish between:

- `inventory_timestamp` — when the inventory was actually observed.
- `received_timestamp` — when the pipeline received the data.

This allows historical inventory data to remain valid while still making delayed reporting visible.

### Missing Inventory Reports

If an expected Monday inventory report has not arrived by Tuesday morning, the system should mark the report as missing and eventually generate an operational alert.

The system should not fabricate inventory values to replace a missing report.

### Closed Stores

A store's current status alone is not sufficient to determine whether historical inventory is valid.

Inventory from a closed store can still be valid when its `inventory_timestamp` occurred before the store's `closed_at` timestamp.

This preserves legitimate historical records after a location closes.

### Corrections and Historical Snapshots

Once an inventory snapshot has been successfully accepted, the current design treats that snapshot as immutable.

A later replacement claiming to correct an already accepted snapshot will be rejected rather than silently modifying historical data. Future inventory changes are represented by subsequent snapshots.

This is a deliberate simplification for the initial system and may be revisited if correction/versioning requirements are introduced.

### Rejected Records

The planned system will preserve rejected records rather than deleting them.

Rejected data will eventually be stored with information such as:

- The original supplied record.
- The rejection reason.
- When the record was received.
- Whether the issue was later resolved.

This provides an audit trail and makes data-quality failures diagnosable rather than allowing bad records to disappear silently.

### Idempotency

The pipeline supports safe reruns. Inventory deliveries are identified by SHA-256 fingerprints and recorded in PostgreSQL. Previously processed deliveries are detected and skipped without duplicating inventory records.

Product and store catalogs use conditional PostgreSQL upserts. An end-to-end rerun verified that all four database tables retained their original contents.

## Current Project Status

Bucks-R-Us is a functioning retail inventory ETL and analytics
system suitable for presentation as a technical portfolio project.
Additional operational capabilities remain on the roadmap.

### Implemented Features

- Google Sheets extraction for products, stores, and inventory.
- Inventory data-quality validation and reference checks.
- PostgreSQL persistence with transactional loading.
- Product and store synchronization using conditional upserts.
- SHA-256 inventory delivery tracking and duplicate prevention.
- Historical inventory validation for closed stores.
- Four-stage automated ETL and reporting pipeline.
- Five SQL analytics reports exported to CSV.
- Interactive Streamlit dashboard with Plotly visualizations.
- Persistent subprocess output and failure logging.
- Automatic log rotation and owner-only log permissions.
- Automated pytest regression and database integration tests.
- 51 passing tests in the latest full regression run.

### Planned Enhancements

- Sales transaction and receipt-item ingestion.
- Sales-demand analytics across stores and product categories.
- Automated missing and late inventory delivery alerts.
- Persistent storage and resolution tracking of rejected records.
- Unattended scheduled pipeline execution.
- Fully documented clean-environment provisioning.

These planned features are not represented as implemented.

## Analytics Reports

The system generates five SQL-based inventory reports:

1. **Low Stock Report** — identifies low inventory levels.
2. **Store Inventory Summary** — summarizes stock by location.
3. **Product Inventory Summary** — aggregates stock by SKU.
4. **Closed Store Inventory** — examines historical records.
5. **Closed Store Reconciliation** — identifies recorded stock
   requiring operational review after store closure.

Reports are based on inventory snapshots, not sales transactions.

## Technology Stack

- **Python** — extraction, validation, loading, and automation.
- **pandas** — source data processing.
- **PostgreSQL** — relational data storage and delivery tracking.
- **psycopg** — Python/PostgreSQL integration.
- **SQL** — retail inventory analytics.
- **Docker Compose** — PostgreSQL service management.
- **Streamlit** — interactive analytics interface.
- **Plotly** — data visualization.
- **pytest** — unit, regression, and integration testing.
- **Google Sheets / CSV** — operational data sources.
- **Git / GitHub** — source and version control.
- **GitHub Codespaces** — development environment.

## System Architecture

~~~text
Google Sheets
     |
     v
Product and Store Synchronization
     |
     v
Inventory Extraction and Validation
     |
     v
PostgreSQL and Delivery Tracking
     |
     v
SQL Analytics Reports
     |
     v
Streamlit Dashboard
~~~

The automation runner stops on failed stages and preserves
diagnostic information in rotating operational logs.

## Running the Project

These instructions assume the PostgreSQL schema and database
credentials have already been configured.

### Install Dependencies

~~~bash
python3 -m pip install -r requirements.txt
~~~

### Start PostgreSQL

~~~bash
docker compose up -d postgres
~~~

### Configure Database Credentials

In the configured development environment:

~~~bash
export POSTGRES_PASSWORD="$(
    docker compose exec -T postgres printenv POSTGRES_PASSWORD
)"
~~~

Credentials should never be committed to Git.

### Preview Pipeline Execution

~~~bash
python3 automation/run_pipeline.py --dry-run
~~~

### Run the ETL Pipeline

~~~bash
python3 automation/run_pipeline.py
~~~

This synchronizes catalogs, processes inventory deliveries,
and regenerates the five analytics reports.

### Launch the Dashboard

~~~bash
streamlit run dashboard/app.py
~~~

### Run Automated Tests

~~~bash
python3 -m pytest tests/ -v
~~~

Database integration tests require the isolated test database.

## Operational Logging

The ETL runner records pipeline stage events, subprocess output,
and exception details in `logs/pipeline.log`.

Logs rotate automatically and are excluded from Git.

The log directory uses owner-only permissions (`700`), and
operational log files use owner-only read/write permissions (`600`).

## Development Scope

Bucks-R-Us is a fictional retail business developed as a
data engineering and analytics portfolio project.

Its implemented capabilities focus on inventory visibility,
data integrity, and store-level operational reporting.

Sales analytics, missing-delivery alerts, and unattended
scheduling remain planned enhancements.
