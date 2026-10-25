-- Bucks-R-Us: Store Inventory Summary
-- Business question:
-- How much inventory does each active store have
-- based on its latest recorded product snapshots?

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
    s.store_id,
    s.city,
    s.state,
    COUNT(*) AS products_tracked,
    SUM(li.quantity_on_hand) AS total_units_on_hand,
    COUNT(*) FILTER (
        WHERE li.quantity_on_hand <= 10
    ) AS low_stock_products,
    COUNT(*) FILTER (
        WHERE li.quantity_on_hand = 0
    ) AS out_of_stock_products
FROM latest_inventory AS li
JOIN stores AS s
    ON li.store_id = s.store_id
JOIN products AS p
    ON li.sku = p.sku
WHERE li.row_num = 1
  AND LOWER(s.status) = 'active'
  AND LOWER(p.status) = 'active'
GROUP BY
    s.store_id,
    s.city,
    s.state
ORDER BY
    s.store_id;
