# Bucks-R-Us ETL & Retail Analytics System

Bucks-R-Us is a fictional multi-location fixed-price discount retailer created as the basis for a data analytics and ETL portfolio project.

The goal of the project is to build a reproducible data pipeline that extracts operational retail data from multiple sources, validates and transforms that data, loads trustworthy records into an analytical database, and ultimately supports analysis of product demand and inventory needs across store locations.

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

The pipeline is intended to be safe to rerun.

Repeated processing of the same successfully processed delivery should not duplicate or corrupt analytical data. Duplicate file/delivery detection will be added as the ingestion layer develops.

## Current Project Status

The project is currently in active development. The initial inventory extraction and validation layer is operational.

### Completed

- Created the Bucks-R-Us fictional retail business and defined the initial analytics problem.
- Defined identifiers and schemas for stores, products, inventory, and planned sales data.
- Created separate inventory, product, and store source datasets.
- Connected Python directly to the current Google Sheets data sources.
- Implemented inventory extraction using Python and pandas.
- Implemented reference validation against the product and store catalogs.
- Implemented detection and rejection of:
  - Negative quantities.
  - Missing SKUs.
  - Unknown SKUs.
  - Unknown stores.
  - Missing or malformed timestamps.
  - Exact duplicate inventory records.
  - Conflicting inventory records.
- Manually tested each implemented validation rule using deliberately malformed source data.
- Verified that the pipeline returns to a clean state after test data is corrected.
- Established Git/GitHub version control for the project.

### In Progress / Planned

The next stages of development include:

1. Expand validation and transformation logic, including historical store-status handling.
2. Track source deliveries and processing runs to support idempotency and safe reruns.
3. Detect late and missing inventory reports.
4. Persist rejected records and their rejection reasons.
5. Add sales transaction ingestion.
6. Introduce PostgreSQL as the analytical data store.
7. Design the analytical schema for sales, products, stores, dates, and inventory snapshots.
8. Load validated data into the analytical database.
9. Build SQL analyses around store-level product demand and inventory behavior.
10. Add pipeline logging, run statistics, failure reporting, and data-freshness monitoring.
11. Test operational failures such as unavailable sources, schema changes, interrupted processing, and database outages.
12. Make the complete project reproducible from a clean environment.

## Technology Used So Far

- **Python** — pipeline and validation logic.
- **pandas** — data extraction, transformation, and validation.
- **Google Sheets / CSV exports** — current development data sources.
- **Git** — source control.
- **GitHub** — remote repository and project history.
- **GitHub Codespaces** — cloud-based development environment.

Additional technologies such as PostgreSQL will be introduced when the pipeline reaches the appropriate stage rather than being added solely for the sake of increasing the technology stack.

## Project Goal

The finished project should demonstrate an end-to-end path from imperfect operational data to trustworthy analytical information:

**Source Data → Extraction → Validation & Transformation → PostgreSQL → SQL Analytics**

The final system should be reproducible, safe to rerun, capable of identifying bad data, and able to explain what happened when processing fails.

Most importantly, the resulting data should support useful analysis of how product demand and inventory needs differ across Bucks-R-Us locations.

## Running the Current Project

### Requirements

- Python 3
- Git
- Internet access to retrieve the current Google Sheets source data

Install the Python dependencies with:

```bash
pip install -r requirements.txt
```

### Run the Inventory Pipeline

From the project root directory:

```bash
python extract_inventory.py
```

The script currently:

1. Extracts inventory data from the inventory source.
2. Extracts the product catalog.
3. Extracts the store catalog.
4. Validates incoming inventory records.
5. Separates valid records from rejected records.
6. Assigns rejection reasons to invalid records.
7. Displays diagnostic information for the current pipeline run.

Example rejection reasons include:

```text
NEGATIVE_QUANTITY
MISSING_SKU
UNKNOWN_SKU
UNKNOWN_STORE
INVALID_TIMESTAMP
DUPLICATE_INVENTORY_RECORD
CONFLICTING_INVENTORY_RECORD
```

> **Note:** The project is under active development. The current script demonstrates the extraction and validation portion of the pipeline. Database persistence, automated ingestion tracking, sales ingestion, and analytical reporting have not yet been implemented.
