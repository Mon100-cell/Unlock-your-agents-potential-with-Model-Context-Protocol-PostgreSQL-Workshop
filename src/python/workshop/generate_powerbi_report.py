"""Generate a Power BI-ready sales report package from the workshop database."""

import argparse
import asyncio
import csv
import json
import os
from pathlib import Path
from typing import Any

import asyncpg
from dotenv import load_dotenv

load_dotenv(override=False)

DEFAULT_POSTGRES_URL = "postgresql://store_manager:StoreManager123!@db:5432/zava"

REPORT_QUERY = """
SELECT
    o.order_id,
    o.order_date::date AS order_date,
    o.customer_id,
    o.store_id,
    oi.product_id,
    oi.quantity,
    oi.unit_price,
    oi.quantity * oi.unit_price AS sales_amount,
    p.product_name,
    p.product_type_id,
    p.category_id,
    s.store_name,
    s.city AS store_city,
    s.is_online,
    c.category_name
FROM retail.orders AS o
JOIN retail.order_items AS oi ON oi.order_id = o.order_id
JOIN retail.products AS p ON p.product_id = oi.product_id
JOIN retail.stores AS s ON s.store_id = o.store_id
JOIN retail.categories AS c ON c.category_id = p.category_id
ORDER BY o.order_date, o.order_id, oi.product_id
"""


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)


async def generate(postgres_url: str, output_dir: Path) -> int:
    connection = await asyncpg.connect(postgres_url)
    try:
        records = await connection.fetch(REPORT_QUERY)
    finally:
        await connection.close()

    rows = [
        {
            key: value.isoformat() if hasattr(value, "isoformat") else value
            for key, value in record.items()
        }
        for record in records
    ]
    write_csv(output_dir / "fact_sales.csv", rows)

    metadata = {
        "name": "Zava Retail Sales Report",
        "source": "PostgreSQL retail schema",
        "tables": [{"name": "fact_sales", "file": "fact_sales.csv", "row_count": len(rows)}],
        "measures": {
            "Total Sales": "SUM(fact_sales[sales_amount])",
            "Order Count": "DISTINCTCOUNT(fact_sales[order_id])",
            "Units Sold": "SUM(fact_sales[quantity])",
            "Average Order Value": "DIVIDE([Total Sales], [Order Count])",
        },
        "suggested_visuals": [
            {"type": "card", "title": "Total Sales", "measure": "[Total Sales]"},
            {"type": "card", "title": "Orders", "measure": "[Order Count]"},
            {"type": "line", "title": "Sales Trend", "axis": "order_date", "value": "[Total Sales]"},
            {"type": "bar", "title": "Sales by Category", "axis": "category_name", "value": "[Total Sales]"},
            {"type": "bar", "title": "Sales by Store", "axis": "store_name", "value": "[Total Sales]"},
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "powerbi_report.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("powerbi_report"))
    parser.add_argument("--postgres-url", default=os.getenv("POSTGRES_URL", DEFAULT_POSTGRES_URL))
    args = parser.parse_args()
    row_count = asyncio.run(generate(args.postgres_url, args.output))
    print(f"Generated {row_count} sales rows in {args.output}")


if __name__ == "__main__":
    main()