import uuid
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")
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