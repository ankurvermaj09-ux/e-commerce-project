from typing import Dict, List, Any
from motor.motor_asyncio import AsyncIOMotorClient
from microservices.common.config import (
    AUTH_DB_NAME,
    PRODUCT_DB_NAME,
    CART_DB_NAME,
    ORDER_DB_NAME,
    REVIEW_DB_NAME,
    WISHLIST_DB_NAME,
    TICKET_DB_NAME,
)

async def check_duplicate_keys(client: AsyncIOMotorClient) -> List[Dict[str, Any]]:
    duplicates = []

    unique_specs = [
        (AUTH_DB_NAME, "users", "email", {"email": "$email"}),
        (AUTH_DB_NAME, "users", "user_id", {"user_id": "$user_id"}),
        (PRODUCT_DB_NAME, "products", "product_id", {"product_id": "$product_id"}),
        (ORDER_DB_NAME, "orders", "order_id", {"order_id": "$order_id"}),
        (CART_DB_NAME, "carts", "user_id", {"user_id": "$user_id"}),
        (WISHLIST_DB_NAME, "wishlist", "user_id", {"user_id": "$user_id"}),
        (
            REVIEW_DB_NAME,
            "reviews",
            "product_id, user_id",
            {"product_id": "$product_id", "user_id": "$user_id"},
        ),
    ]

    for db_name, collection_name, key_name, group_id in unique_specs:
        collection = client[db_name][collection_name]
        pipeline = [
            {"$group": {"_id": group_id, "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
        ]
        dups = await collection.aggregate(pipeline).to_list(length=None)
        if dups:
            duplicates.append(
                {
                    "database": db_name,
                    "collection": collection_name,
                    "key": key_name,
                    "duplicates": dups,
                }
            )

    return duplicates

async def ensure_indexes(client: AsyncIOMotorClient) -> bool:
    duplicates = await check_duplicate_keys(client)
    if duplicates:
        print("❌ Duplicate keys found for unique constraints:")
        for dup in duplicates:
            print(f"   DB: {dup['database']}, Collection: {dup['collection']}, Key: {dup['key']}")
            for item in dup["duplicates"]:
                print(f"      Value: {item['_id']} (Count: {item['count']})")
        print("Aborting unique index creation due to existing duplicate records.")
        return False

    auth_db = client[AUTH_DB_NAME]
    await auth_db["users"].create_index("email", unique=True)
    await auth_db["users"].create_index("user_id", unique=True)

    product_db = client[PRODUCT_DB_NAME]
    await product_db["products"].create_index("product_id", unique=True)
    await product_db["products"].create_index("category")
    await product_db["products"].create_index([("name", "text")])

    order_db = client[ORDER_DB_NAME]
    await order_db["orders"].create_index("order_id", unique=True)
    await order_db["orders"].create_index("user_id")
    await order_db["orders"].create_index([("status", 1), ("created_at", -1)])
    await order_db["orders"].create_index("items.product_id")

    cart_db = client[CART_DB_NAME]
    await cart_db["carts"].create_index("user_id", unique=True)

    wishlist_db = client[WISHLIST_DB_NAME]
    await wishlist_db["wishlist"].create_index("user_id", unique=True)

    review_db = client[REVIEW_DB_NAME]
    await review_db["reviews"].create_index(
        [("product_id", 1), ("user_id", 1)], unique=True
    )
    await review_db["reviews"].create_index("product_id")

    ticket_db = client[TICKET_DB_NAME]
    await ticket_db["tickets"].create_index("status")
    await ticket_db["tickets"].create_index("user_id")

    print("✅ All database indexes created successfully.")
    return True
