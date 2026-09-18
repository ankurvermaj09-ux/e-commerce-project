from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")

# ===================================
# OLD MONOLITH DATABASE
# ===================================

source_db = client["minie"]

# ===================================
# TARGET DATABASES
# (match your microservices DB names)
# ===================================

services = {
    "auth_db": {
        "collections": ["users"]
    },

    "product_db": {
        "collections": ["products"]
    },

    "order_db": {
        "collections": ["orders"]
    },

    "cart_db": {
        "collections": ["cart"]
    },

    "wishlist_db": {
        "collections": ["wishlist"]
    },

    "review_db": {
        "collections": ["reviews"]
    }
}

# ===================================
# MIGRATION
# ===================================

for db_name, config in services.items():

    target_db = client[db_name]

    print(f"\n==============================")
    print(f"Migrating -> {db_name}")
    print(f"==============================")

    for collection_name in config["collections"]:

        source_collection = source_db[collection_name]
        target_collection = target_db[collection_name]

        documents = list(source_collection.find())

        if not documents:
            print(f"[SKIPPED] '{collection_name}' is empty")
            continue

        # Avoid duplicate migration
        if target_collection.count_documents({}) > 0:
            print(f"[SKIPPED] '{collection_name}' already has data")
            continue

        target_collection.insert_many(documents)

        print(
            f"[DONE] {len(documents)} documents migrated "
            f"from '{collection_name}'"
        )

print("\nMigration completed successfully!")