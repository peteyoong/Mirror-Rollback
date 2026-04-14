import asyncio, sys, os
sys.path.insert(0, '/app/backend')
os.environ.setdefault('MONGO_URL', 'mongodb://localhost:27017')

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime, timezone

async def setup():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client['test_database']
    
    accounts = [
        {"name": "Isaac Yoong", "email": "isaac.yoong@test.com", "birth": datetime(2012,4,5), "time": "05:25"},
        {"name": "Thaddeus Yoong", "email": "thaddeus.yoong@test.com", "birth": datetime(2014,6,23), "time": "18:17"},
    ]
    
    created_ids = {}
    for acct in accounts:
        existing = await db.users.find_one({"email": acct["email"]})
        if existing:
            created_ids[acct["email"]] = str(existing["_id"])
            print(f"EXISTS: {acct['name']} ({acct['email']})")
        else:
            oid = ObjectId()
            await db.users.insert_one({
                "_id": oid, "name": acct["name"], "email": acct["email"],
                "birth_date": acct["birth"], "birth_time": acct["time"],
                "city": "Petaling Jaya", "country": "Malaysia",
                "birth_location": {"city": "Petaling Jaya", "country": "Malaysia", "latitude": 3.1073, "longitude": 101.6067},
                "timezone": "Asia/Kuala_Lumpur", "created_at": datetime.now(timezone.utc),
            })
            created_ids[acct["email"]] = str(oid)
            print(f"CREATED: {acct['name']} ({oid})")
    
    # Compute charts via API
    import httpx
    async with httpx.AsyncClient(timeout=30) as c:
        for acct in accounts:
            uid = created_ids[acct["email"]]
            chart = await db.charts.find_one({"user_id": uid})
            if chart and chart.get("human_design"):
                print(f"CHART OK: {acct['name']}")
            else:
                resp = await c.post("http://localhost:8001/api/charts/calculate", json={
                    "user_id": uid, "birth_date": str(acct["birth"])[:10], "birth_time": acct["time"],
                    "latitude": 3.1073, "longitude": 101.6067,
                    "city": "Petaling Jaya", "country": "Malaysia", "timezone": "Asia/Kuala_Lumpur"
                })
                print(f"CHART COMPUTED: {acct['name']} ({resp.status_code})")
    
    # Forum
    pete_id = "697f0c6abf35c0528ff06954"
    mel_id = "697ec826ad4b18f75bf42616"
    existing = await db.forums.find_one({"name": "Yoong family"})
    if not existing:
        forum_oid = ObjectId()
        fid = str(forum_oid)
        await db.forums.insert_one({
            "_id": forum_oid, "name": "Yoong family", "description": "Family forum",
            "created_by": pete_id, "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc), "member_count": 4,
            "is_private": True, "status": "active", "invite_token": "yoong-family",
        })
        for uid, name, role in [(pete_id,"Pete","admin"),(created_ids["thaddeus.yoong@test.com"],"Thaddeus","member"),(created_ids["isaac.yoong@test.com"],"Isaac","member"),(mel_id,"Melissa","member")]:
            await db.forum_members.insert_one({"forum_id": fid, "user_id": uid, "name": name, "status": "active", "role": role, "joined_at": datetime.now(timezone.utc)})
        print(f"FORUM CREATED: Yoong family")
    else:
        print(f"FORUM EXISTS: Yoong family")
    
    print("\nDONE")

asyncio.run(setup())
