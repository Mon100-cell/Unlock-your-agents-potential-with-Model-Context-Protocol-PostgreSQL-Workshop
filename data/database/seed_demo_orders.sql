DO $$
DECLARE
    demo_order_count integer;
BEGIN
    SELECT COUNT(*)
    INTO demo_order_count
    FROM retail.orders
    WHERE order_date BETWEEN DATE '2099-01-15' AND DATE '2099-01-17';

    IF demo_order_count = 0 THEN
        INSERT INTO retail.orders (customer_id, store_id, order_date)
        SELECT customer_id,
               (SELECT store_id FROM retail.stores ORDER BY store_id LIMIT 1),
               DATE '2099-01-15' + row_number() OVER (ORDER BY customer_id)::integer - 1
        FROM (
            SELECT customer_id
            FROM retail.customers
            ORDER BY customer_id
            LIMIT 3
        ) AS selected_customers;

        INSERT INTO retail.order_items (
            order_id,
            store_id,
            product_id,
            quantity,
            unit_price,
            discount_percent,
            discount_amount,
            total_amount
        )
        SELECT o.order_id,
               o.store_id,
               p.product_id,
               CASE WHEN p.product_id = first_product.product_id THEN 2 ELSE 1 END,
               p.base_price,
               CASE WHEN p.product_id = first_product.product_id THEN 10 ELSE 0 END,
               CASE WHEN p.product_id = first_product.product_id THEN p.base_price * 0.20 ELSE 0 END,
               CASE WHEN p.product_id = first_product.product_id THEN p.base_price * 1.80 ELSE p.base_price END
        FROM retail.orders AS o
        CROSS JOIN LATERAL (
            SELECT product_id, base_price
            FROM retail.products
            ORDER BY product_id
            LIMIT 2
        ) AS p
        CROSS JOIN LATERAL (
            SELECT MIN(product_id) AS product_id
            FROM retail.products
        ) AS first_product
        WHERE o.order_date BETWEEN DATE '2099-01-15' AND DATE '2099-01-17';
    END IF;
END
$$;
