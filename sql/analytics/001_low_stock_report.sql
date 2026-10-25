-- Bucks-R-Us: Low Stock Inventory Report
-- Business question:
-- Which active products have 10 or fewer units
-- at each active store, based on their latest inventory snapshot?

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
  AND li.quantity_on_hand <= 10
  AND LOWER(s.status) = 'active'
  AND LOWER(p.status) = 'active'
ORDER BY
    li.quantity_on_hand ASC,
    s.store_id,
    p.product_name;
