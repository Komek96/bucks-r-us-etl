
import sys
import hashlib
import logging
import pandas as pd
from database import get_connection
from extract_inventory import (
    validate_inventory,
    SHEET_URL,
    PRODUCTS_URL,
    STORES_URL
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

inventory = pd.read_csv(SHEET_URL)
inventory_csv = inventory.to_csv(index=False)
delivery_hash = hashlib.sha256(
    inventory_csv.encode("utf-8")
).hexdigest()
logger.info("Inventory delivery SHA-256: %s", delivery_hash)
with get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM delivery_history WHERE delivery_hash = %s",
            (delivery_hash,)
        )
        delivery_exists = cursor.fetchone()[0]
logger.info("Delivery found in PostgreSQL: %s", delivery_exists)
if delivery_exists == 1:
    logger.warning("DUPLICATE DELIVERY DETECTED")
    sys.exit(0)
else:
    logger.info("NEW DELIVERY DETECTED")
products = pd.read_csv(PRODUCTS_URL)
stores = pd.read_csv(STORES_URL)

logger.info("Downloaded %s inventory records.", len(inventory))
logger.info("Downloaded %s products.", len(products))
logger.info("Downloaded %s stores.", len(stores))

#Inventory Validation

valid_inventory, rejected_inventory = validate_inventory(
    inventory,
    products,
    stores
)

logger.info("Valid inventory records: %s", len(valid_inventory))
if len(rejected_inventory) > 0:
    logger.warning("Rejected inventory records: %s", len(rejected_inventory))
else:
    logger.info("Rejected inventory records: 0")

valid_inventory = valid_inventory.copy()

valid_inventory["inventory_timestamp"] = pd.to_datetime(
    valid_inventory["inventory_timestamp"]
)

logger.info("Validated inventory ready for PostgreSQL:")
logger.info("\n%s", valid_inventory.to_string(index=False))

inserted_count = 0
skipped_count = 0

with get_connection() as conn:
    with conn.cursor() as cursor:
        for _, item in valid_inventory.iterrows():
            cursor.execute(
                """
                INSERT INTO inventory (
                    store_id,
                    sku,
                    quantity_on_hand,
                    inventory_timestamp
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (store_id, sku, inventory_timestamp)
                DO NOTHING;
                """,
                (
                    item["store_id"],
                    item["sku"],
                    int(item["quantity_on_hand"]),
                    item["inventory_timestamp"].to_pydatetime()
                )
            )

            if cursor.rowcount == 1:
                inserted_count += 1
                logger.info("Inserted inventory: %s - %s", item["store_id"], item["sku"])
            else:
                skipped_count += 1
                logger.info("Skipped existing inventory: %s - %s", item["store_id"], item["sku"])

        cursor.execute(
            """
            INSERT INTO delivery_history (
                delivery_hash,
                records_inserted,
                records_skipped
            )
            VALUES (%s, %s, %s)
            ON CONFLICT (delivery_hash) DO NOTHING;
            """,
            (delivery_hash, inserted_count, skipped_count)
        )

logger.info("Total new inventory records inserted: %s", inserted_count)
logger.info("Total existing inventory records skipped: %s", skipped_count)
logger.info("Delivery fingerprint successfully registered in PostgreSQL.")
