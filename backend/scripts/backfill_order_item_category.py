import asyncio
import sys
from pathlib import Path
from pymongo import UpdateOne

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from microservices.common.database import client
from microservices.common.config import PRODUCT_DB_NAME, ORDER_DB_NAME

async def backfill_categories() -> None:
    product_db = client[PRODUCT_DB_NAME]
    order_db = client[ORDER_DB_NAME]

    products_coll = product_db["products"]
    orders_coll = order_db["orders"]

    print("Fetching product categories...")
    products = await products_coll.find({}, {"product_id": 1, "category": 1, "_id": 0}).to_list(length=None)
    category_map = {p["product_id"]: p.get("category", "Uncategorized") for p in products}

    print("Fetching orders with missing item categories...")
    orders = await orders_coll.find({"items.category": {"$exists": False}}).to_list(length=None)

    if not orders:
        print("✅ No orders need category backfilling.")
        return

    updates = []
    for order in orders:
        updated_items = []
        modified = False
        for item in order.get("items", []):
            item_copy = dict(item)
            if "category" not in item_copy or not item_copy["category"]:
                item_copy["category"] = category_map.get(item_copy.get("product_id"), "Uncategorized")
                modified = True
            updated_items.append(item_copy)

        if modified:
            updates.append(
                UpdateOne(
                    {"_id": order["_id"]},
                    {"$set": {"items": updated_items}}
                )
            )

    if updates:
        res = await orders_coll.bulk_write(updates)
        print(f"✅ Successfully backfilled item categories for {res.modified_count} orders.")
    else:
        print("✅ All order items already have categories.")

if __name__ == "__main__":
    asyncio.run(backfill_categories())
