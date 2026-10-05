import asyncio
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from microservices.common.database import client
from microservices.common.config import PRODUCT_DB_NAME, AUTH_DB_NAME

async def seed_counters() -> None:
    product_db = client[PRODUCT_DB_NAME]
    auth_db = client[AUTH_DB_NAME]

    products_coll = product_db["products"]
    product_counters = product_db["counters"]

    users_coll = auth_db["users"]
    user_counters = auth_db["counters"]

    # 1. Product counter
    max_product_doc = await products_coll.find_one(sort=[("product_id", -1)])
    max_product_id = max_product_doc["product_id"] if max_product_doc and "product_id" in max_product_doc else 0

    existing_p_counter = await product_counters.find_one({"_id": "product_id"})
    if not existing_p_counter:
        await product_counters.update_one(
            {"_id": "product_id"},
            {"$set": {"seq": max_product_id}},
            upsert=True
        )
        print(f"✅ Product counter initialized to seq = {max_product_id}")
    else:
        print(f"ℹ️ Product counter already exists (seq = {existing_p_counter.get('seq')})")

    # 2. User counter
    max_user_doc = await users_coll.find_one(sort=[("user_id", -1)])
    max_user_id = max_user_doc["user_id"] if max_user_doc and "user_id" in max_user_doc else 0

    existing_u_counter = await user_counters.find_one({"_id": "user_id"})
    if not existing_u_counter:
        await user_counters.update_one(
            {"_id": "user_id"},
            {"$set": {"seq": max_user_id}},
            upsert=True
        )
        print(f"✅ User counter initialized to seq = {max_user_id}")
    else:
        print(f"ℹ️ User counter already exists (seq = {existing_u_counter.get('seq')})")

if __name__ == "__main__":
    asyncio.run(seed_counters())
