from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument

from microservices.common.config import MONGO_URI

client = AsyncIOMotorClient(MONGO_URI)

async def next_sequence(counters_collection, name: str) -> int:
    doc = await counters_collection.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return doc["seq"]