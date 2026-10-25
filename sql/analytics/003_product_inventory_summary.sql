-- Bucks-R-Us: Product Inventory Summary
-- Business question:
-- How much inventory does each active product have
-- across active stores with recorded inventory?

WITH latest_inventory AS (
    SELECT
        i.store_id,
        i.sku,
        i.quantity_on_hand,
        ROW_NUMBER() OVER (
            PARTITION BY i.store_id, i.sku
            ORDER BY i.inventory_timestamp DESC
        ) AS row_num
    FROM inventory AS i
)
SELECT
    p.sku,
    p.product_name,
    p.category,
    COUNT(DISTINCT li.store_id) AS stores_tracked,
    SUM(li.quantity_on_hand) AS total_units_on_hand,
    MIN(li.quantity_on_hand) AS lowest_store_quantity,
    MAX(li.quantity_on_hand) AS highest_store_quantity
FROM latest_inventory AS li
JOIN products AS p
    ON li.sku = p.sku
JOIN stores AS s
    ON li.store_id = s.store_id
WHERE li.row_num = 1
  AND LOWER(p.status) = 'active'
  AND LOWER(s.status) = 'active'
GROUP BY
    p.sku,
    p.product_name,
    p.category
ORDER BY
    total_units_on_hand ASC,
    p.product_name;
