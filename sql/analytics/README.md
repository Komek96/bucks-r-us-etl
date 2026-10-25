# Bucks-R-Us Retail Inventory Analytics

This directory contains PostgreSQL reports that answer
retail inventory and store management questions.

## Available Reports

| SQL File | Business Question |
|---|---|
| 001_low_stock_report.sql | Which active products have 10 or fewer units? |
| 002_store_inventory_summary.sql | How much inventory does each active store have? |
| 003_product_inventory_summary.sql | How much inventory does each active product have across stores? |
| 004_closed_store_inventory.sql | What inventory was last recorded at closed stores? |
| 005_closed_store_reconciliation.sql | Which closed stores need inventory reconciliation review? |

## Methodology

Inventory records are timestamped snapshots.

Reports select the most recent snapshot for each
store and SKU combination to avoid double-counting
historical inventory.

Operational reports include active stores and products.
Closed-store reports examine historical inventory
regardless of product status.

## Sample Findings

- Active store BRU-0001 tracks 5 products and 134 units.
- Crossword Puzzle has 8 units and is flagged as low stock.
- No tracked active products are out of stock.
- Closed store BRU-0002 last recorded 20 Paper Towels
  before its closure.

## Limitations

- Inventory snapshots are not necessarily real-time.
- Missing inventory records do not imply zero stock.
- The low-stock threshold of 10 units is illustrative.
- Historical inventory at closed stores does not prove
  that merchandise is still physically present.
- The sample dataset is fictional.

## Running a Report

From the repository root:

    docker compose exec -T postgres psql       -U bru_user       -d bucks_r_us       -v ON_ERROR_STOP=1       -f /dev/stdin       < sql/analytics/001_low_stock_report.sql

Replace the SQL filename to run another report.
