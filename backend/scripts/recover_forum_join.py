#!/usr/bin/env python3
"""
Recover Forum Join — Step 6 of the P0 debugging plan.

Usage (from /app/backend, with backend/.env loaded):

    python scripts/recover_forum_join.py --invite-token <token> \
        --emails jay@pulsifi.me Jaanhao@pulsifi.me

What it does:
  1. Locates the forum by invite_token (or forum_id).
  2. For each email, looks up the user (case-insensitive).
  3. Adds a forum_members doc (role=member, status=active) if missing.
  4. Reactivates any soft-removed membership.
  5. Prints a clear report of what changed, so we can verify the fix.

Safe to re-run: operations are idempotent.
"""
from __future__ import annotations
import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Load backend/.env relative to this script
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(ROOT, ".env"))


async def recover(invite_token: str | None, forum_id: str | None, emails: list[str]) -> int:
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "test_database")
    if not mongo_url:
        print("ERROR: MONGO_URL is not set", file=sys.stderr)
        return 2

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    print(f"[recover] DB={db_name}")

    forum = None
    if invite_token:
        forum = await db.forums.find_one({"invite_token": invite_token})
    if not forum and forum_id and ObjectId.is_valid(forum_id):
        forum = await db.forums.find_one({"_id": ObjectId(forum_id)})
    if not forum:
        print("ERROR: No forum found for the provided identifier.")
        return 3

    fid = str(forum["_id"])
    print(f"[recover] Forum: '{forum.get('name')}' (_id={fid}) invite_token={forum.get('invite_token')}")

    now = datetime.now(timezone.utc)
    added = reactivated = already = missing_user = 0

    for email in emails:
        user = await db.users.find_one({"email": {"$regex": f"^{email}$", "$options": "i"}})
        if not user:
            print(f"  - {email}: USER NOT FOUND — skipping")
            missing_user += 1
            continue
        uid = str(user["_id"])
        existing = await db.forum_members.find_one({"forum_id": fid, "user_id": uid})
        if existing and existing.get("status") == "active":
            print(f"  - {email} ({uid}): already active member — no-op")
            already += 1
            continue
        if existing:
            await db.forum_members.update_one(
                {"_id": existing["_id"]},
                {"$set": {"status": "active", "joined_at": now}},
            )
            print(f"  - {email} ({uid}): reactivated membership")
            reactivated += 1
        else:
            await db.forum_members.insert_one(
                {
                    "forum_id": fid,
                    "user_id": uid,
                    "role": "member",
                    "status": "active",
                    "invited_at": now,
                    "joined_at": now,
                }
            )
            print(f"  - {email} ({uid}): added as member")
            added += 1

    print(
        f"[recover] DONE — added={added} reactivated={reactivated} "
        f"already_member={already} user_not_found={missing_user}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Recover missing forum memberships.")
    parser.add_argument("--invite-token", help="Forum invite token (e.g. cb8cd54847e5)")
    parser.add_argument("--forum-id", help="Forum _id (alternative to --invite-token)")
    parser.add_argument("--emails", nargs="+", required=True, help="One or more user emails to add")
    args = parser.parse_args()
    if not args.invite_token and not args.forum_id:
        parser.error("Provide --invite-token or --forum-id")
    return asyncio.run(recover(args.invite_token, args.forum_id, args.emails))


if __name__ == "__main__":
    sys.exit(main())
