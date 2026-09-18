from motor.motor_asyncio import AsyncIOMotorClient

from microservices.common.config import MONGO_URI

client = AsyncIOMotorClient(MONGO_URI)

print("✅ Connected to MongoDB Atlas")