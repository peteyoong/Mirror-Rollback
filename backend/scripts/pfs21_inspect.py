"""PFS-2.1 read-only inspection of preview topology data."""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    pete_id = "697f0c6abf35c0528ff06954"
    mel_id = "697ec826ad4b18f75bf42616"

    print("=== Pete forum_members ===")
    async for m in db.forum_members.find({"user_id": pete_id}):
        m.pop("_id", None)
        print(m)
    print()
    print("=== Mel forum_members ===")
    async for m in db.forum_members.find({"user_id": mel_id}):
        m.pop("_id", None)
        print(m)
    print()
    print("=== saved_people (Pete) ===")
    async for s in db.saved_people.find({"user_id": pete_id}).limit(20):
        s.pop("_id", None)
        print({k: v for k, v in s.items()
               if k in ("name", "relationship", "user_id",
                        "target_user_id", "role")})
    print()
    print("=== Users (Pete + Mel) ===")
    for uid in (pete_id, mel_id):
        u = await db.users.find_one({"_id": ObjectId(uid)})
        if u:
            print({"_id": str(u["_id"]), "name": u.get("name"),
                   "email": u.get("email")})
    print()
    print("=== forum_relationship_edges (full dump) ===")
    async for e in db.forum_relationship_edges.find():
        e.pop("_id", None)
        print(e)
    print()
    print("=== Forums table (all) ===")
    async for f in db.forums.find():
        print({"_id": str(f.get("_id")), "id": f.get("id"),
               "name": f.get("name")})


asyncio.run(main())
