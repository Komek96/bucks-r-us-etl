-- Bucks-R-Us: Closed Store Inventory Report
-- Business question:
-- What inventory was last recorded at closed stores?

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
    p.sku,
    p.product_name,
    p.category,
    li.quantity_on_hand,
    li.inventory_timestamp
FROM latest_inventory AS li
JOIN stores AS s
    ON li.store_id = s.store_id
JOIN products AS p
    ON li.sku = p.sku
WHERE li.row_num = 1
  AND LOWER(s.status) = 'closed'
ORDER BY
    s.store_id,
    p.product_name;
