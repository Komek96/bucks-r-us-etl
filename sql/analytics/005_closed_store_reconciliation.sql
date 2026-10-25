-- Bucks-R-Us: Closed Store Inventory Reconciliation
-- Business question:
-- Which closed stores have positive quantities
-- in their latest recorded inventory snapshots?

WITH latest_inventory AS (
    SELECT
        i.store_id,
        i.sku,
        i.quantity_on_hand,
        i.inventory_timestamp,
        ROW_NUMBER() OVER (
            PARTITION BY i.store_id, i.sku
            ORDER BY i.inventory_timestamp DESC
        ) AS row_num
    FROM inventory AS i
)
SELECT
    s.store_id,
    s.city,
    s.state,
    s.closed_at,
    COUNT(*) AS products_needing_review,
    SUM(li.quantity_on_hand) AS last_recorded_units,
    MAX(li.inventory_timestamp) AS latest_inventory_snapshot
FROM latest_inventory AS li
JOIN stores AS s
    ON li.store_id = s.store_id
WHERE li.row_num = 1
  AND LOWER(s.status) = 'closed'
  AND li.quantity_on_hand > 0
GROUP BY
    s.store_id,
    s.city,
    s.state,
    s.closed_at
ORDER BY
    last_recorded_units DESC;
