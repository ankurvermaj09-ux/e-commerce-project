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
from microservices.common.config import AUTH_DB_NAME, REVIEW_DB_NAME

async def backfill_review_usernames() -> None:
    auth_db = client[AUTH_DB_NAME]
    review_db = client[REVIEW_DB_NAME]

    users_coll = auth_db["users"]
    reviews_coll = review_db["reviews"]

    print("Fetching users for username mapping...")
    users = await users_coll.find({}, {"user_id": 1, "email": 1, "profile": 1, "name": 1, "_id": 0}).to_list(length=None)

    username_map = {}
    for u in users:
        uid = u.get("user_id")
        profile = u.get("profile")
        if isinstance(profile, dict) and profile.get("full_name"):
            name = profile["full_name"]
        elif u.get("name"):
            name = u["name"]
        elif u.get("email"):
            name = u["email"].split("@")[0]
        else:
            name = f"User {uid}"
        username_map[uid] = name

    print("Fetching reviews with missing usernames...")
    reviews = await reviews_coll.find({"username": {"$exists": False}}).to_list(length=None)

    if not reviews:
        print("✅ No reviews need username backfilling.")
        return

    updates = []
    for r in reviews:
        uid = r.get("user_id")
        uname = username_map.get(uid, f"User {uid}")
        updates.append(
            UpdateOne(
                {"_id": r["_id"]},
                {"$set": {"username": uname}}
            )
        )

    if updates:
        res = await reviews_coll.bulk_write(updates)
        print(f"✅ Successfully backfilled usernames for {res.modified_count} reviews.")
    else:
        print("✅ All reviews already have usernames.")

if __name__ == "__main__":
    asyncio.run(backfill_review_usernames())
