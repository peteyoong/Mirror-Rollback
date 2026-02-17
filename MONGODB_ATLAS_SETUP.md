# MongoDB Atlas Setup - Step-by-Step Checklist

## Prerequisites
- MongoDB Atlas account (https://cloud.mongodb.com)
- Access to create databases and users

---

## Step 1: Create or Select a Cluster

1. Log into MongoDB Atlas: https://cloud.mongodb.com
2. Go to **Database** in the left sidebar
3. Either:
   - **Use existing cluster** (if you have one)
   - **Create new cluster** → Click "Build a Database"
     - Choose: M0 Free Tier (for testing) or M10+ (for production staging)
     - Provider: AWS/GCP/Azure (your choice)
     - Region: Choose closest to your staging server
     - Cluster name: `mirror-staging` (recommended)

---

## Step 2: Create the Staging Database

The database `mirror_staging` will be auto-created when you first connect.
No manual creation needed - MongoDB creates it on first write.

---

## Step 3: Create Database User

1. Go to **Database Access** in the left sidebar
2. Click **+ ADD NEW DATABASE USER**
3. Fill in:

| Field | Value |
|-------|-------|
| Authentication Method | Password |
| Username | `mirror_staging_user` |
| Password | Click "Autogenerate Secure Password" → **COPY THIS** |
| Database User Privileges | **Select "Specific Privileges"** |

4. Under **Specific Privileges**, click **+ Add Specific Privilege**:

| Database | Collection | Privilege |
|----------|------------|-----------|
| `mirror_staging` | (leave empty for all) | `readWrite` |

5. Click **Add User**

**⚠️ SAVE THE PASSWORD** - You won't be able to see it again!

---

## Step 4: Configure Network Access

1. Go to **Network Access** in the left sidebar
2. Click **+ ADD IP ADDRESS**
3. Choose ONE of these options:

### Option A: Allow from Anywhere (for initial testing only)
| Field | Value |
|-------|-------|
| Access List Entry | `0.0.0.0/0` |
| Comment | `Temporary - lock down after testing` |

### Option B: Specific IP (recommended for production)
| Field | Value |
|-------|-------|
| Access List Entry | `YOUR_STAGING_SERVER_IP` |
| Comment | `Staging server` |

4. Click **Confirm**

**⚠️ IMPORTANT:** If using 0.0.0.0/0, remember to restrict this after confirming the connection works!

---

## Step 5: Get Connection String

1. Go to **Database** in the left sidebar
2. Click **Connect** on your cluster
3. Select **Drivers** (Connect your application)
4. Select:
   - Driver: **Python**
   - Version: **3.12 or later**
5. Copy the connection string

It will look like:
```
mongodb+srv://mirror_staging_user:<password>@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
```

6. **Modify the connection string:**
   - Replace `<password>` with the actual password from Step 3
   - Add `/mirror_staging` before the `?`

**Final format:**
```
mongodb+srv://mirror_staging_user:YOUR_ACTUAL_PASSWORD@cluster0.abc123.mongodb.net/mirror_staging?retryWrites=true&w=majority
```

---

## Step 6: Verify Your Connection String

Your final `MONGO_URL` should match this pattern:
```
mongodb+srv://mirror_staging_user:PASSWORD@CLUSTER_HOST/mirror_staging?retryWrites=true&w=majority
                ^^^^^^^^^^^^^^^^^^^        ^^^^^^^^^^^^  ^^^^^^^^^^^^^^
                username                   password      database name
```

**Checklist:**
- [ ] Username is `mirror_staging_user`
- [ ] Password is the one you copied (URL-encoded if it has special chars)
- [ ] Database name `/mirror_staging` is in the path (before `?`)
- [ ] `retryWrites=true&w=majority` query params are present

---

## Step 7: Test Connection (Optional)

You can test with Python locally:

```python
from pymongo import MongoClient

uri = "mongodb+srv://mirror_staging_user:PASSWORD@cluster.mongodb.net/mirror_staging?retryWrites=true&w=majority"
client = MongoClient(uri)

# Test connection
db = client.mirror_staging
print("Connected to:", db.name)
print("Collections:", db.list_collection_names())
```

---

## Summary of Values to Set

| Environment Variable | Value |
|---------------------|-------|
| `MONGO_URL` | `mongodb+srv://mirror_staging_user:PASSWORD@CLUSTER.mongodb.net/mirror_staging?retryWrites=true&w=majority` |
| `DB_NAME` | `mirror_staging` |
| `ENV` | `staging` |

---

## Security Checklist

After confirming everything works:

- [ ] Remove `0.0.0.0/0` from Network Access (if added for testing)
- [ ] Add only your staging server's IP to Network Access
- [ ] Verify the user has `readWrite` on `mirror_staging` only (not admin)
- [ ] Store the connection string as a secret (not in version control)

---

## Verification After Backend Deployment

```bash
curl -s https://api-staging.mirror.emergentagent.com/api/health | jq
```

**Expected output:**
```json
{
  "env": "staging",
  "status": "healthy",
  "db_name": "mirror_staging",
  "db_type": "atlas"
}
```

**If you see `db_type: "local"` or `db_name: "test_database"`** → Your env vars are not set correctly.
