import os
import uuid
from pymongo import MongoClient

mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(mongo_uri)
db = client["minie"]
order_collection = db["orders"]

for order in order_collection.find({"order_id":{"$exists":False}}):
    new_order_id = str(uuid.uuid4())
    order_collection.update_one(
        {"_id": order["_id"]},
        {
            "$set": {
                "order_id": new_order_id
            }
        }
    )