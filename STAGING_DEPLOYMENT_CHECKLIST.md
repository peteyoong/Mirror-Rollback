# STAGING DEPLOYMENT CHECKLIST
## Project Mirror - Environment Setup Guide

---

## 1. BACKEND ENVIRONMENT VARIABLES

### Required Variables (app will crash without these):

| Variable | Example Value | Description |
|----------|---------------|-------------|
| `MONGO_URL` | `mongodb+srv://mirror-staging:SecurePass@cluster.mongodb.net/?retryWrites=true&w=majority` | MongoDB Atlas connection string |
| `DB_NAME` | `mirror_staging` | Database name (must be unique per environment) |
| `EMERGENT_LLM_KEY` | `sk-emergent-c740b6fF4020b7a102` | Emergent LLM API key |
| `ENV` | `staging` | Environment identifier |

### Optional Variables (have defaults):

| Variable | Default | Description |
|----------|---------|-------------|
| `BUILD_LABEL` | `dev-local` | Build label for provenance |
| `GIT_SHA` | Auto-detected | Git commit SHA |
| `DEBUG_MIRROR` | `false` | Enable verbose logging |
| `ENNEAGRAM_PDF_PATH` | `/app/backend/data/JOH_Book_1.pdf` | Path to Enneagram KB PDF |

---

## 2. MONGODB ATLAS SETUP

### Recommended Cluster/Database Naming:

| Environment | Cluster Name | Database Name |
|-------------|--------------|---------------|
| Development | `mirror-dev` | `test_database` |
| **Staging** | `mirror-staging` | `mirror_staging` |
| Production | `mirror-prod` | `mirror_prod` |

### Steps to Create Staging Database:

1. **Log into MongoDB Atlas**: https://cloud.mongodb.com

2. **Create/Select Cluster**: 
   - Recommended: Create dedicated staging cluster `mirror-staging`
   - Or use existing cluster with separate database

3. **Create Database User**:
   - Username: `mirror-staging` (or your preference)
   - Password: Generate secure password
   - Role: `readWrite` on `mirror_staging` database

4. **Get Connection String**:
   - Click "Connect" → "Connect your application"
   - Select: Driver = Python, Version = 3.12+
   - Copy the connection string
   - Replace `<password>` with actual password
   - Replace `<dbname>` with `mirror_staging` (or remove - it's set via `DB_NAME`)

5. **Whitelist IPs**:
   - Add staging server IP to Network Access
   - Or use `0.0.0.0/0` for testing (not recommended for production)

---

## 3. WHERE TO PUT CREDENTIALS

### Option A: Direct `.env` file (for manual deployment)

On your staging server, create `/app/backend/.env`:

```bash
# Copy from .env.staging template and fill in real values
MONGO_URL="mongodb+srv://mirror-staging:YOUR_PASSWORD@mirror-staging.abc123.mongodb.net/?retryWrites=true&w=majority"
DB_NAME="mirror_staging"
EMERGENT_LLM_KEY="sk-emergent-c740b6fF4020b7a102"
ENV="staging"
BUILD_LABEL="staging-v1.0.0"
DEBUG_MIRROR="true"
```

### Option B: Environment Variables (for containerized deployment)

Set these in your deployment platform (Railway, Render, Fly.io, etc.):

```
MONGO_URL=mongodb+srv://mirror-staging:YOUR_PASSWORD@mirror-staging.abc123.mongodb.net/?retryWrites=true&w=majority
DB_NAME=mirror_staging
EMERGENT_LLM_KEY=sk-emergent-c740b6fF4020b7a102
ENV=staging
BUILD_LABEL=staging-v1.0.0
DEBUG_MIRROR=true
```

---

## 4. VERIFICATION STEPS

### Step 1: Test MongoDB Connection

After setting up credentials, verify the backend can connect:

```bash
# Start the backend
cd /app/backend
python -c "from motor.motor_asyncio import AsyncIOMotorClient; import os; from dotenv import load_dotenv; load_dotenv(); c = AsyncIOMotorClient(os.environ['MONGO_URL']); print('Connected to:', c.server_info())"
```

### Step 2: Check /api/health Endpoint

```bash
curl -s https://api-staging.mirror.emergentagent.com/api/health | python3 -m json.tool
```

**Expected output for STAGING:**
```json
{
    "env": "staging",
    "status": "healthy",
    "build_version": "v30-environment-separation",
    "build_label": "staging-v1.0.0",
    "git_sha": "abc1234",
    "db_name": "mirror_staging",
    "db_type": "atlas",
    "timestamp_utc": "2026-02-17T14:30:00.000000+00:00",
    "expected_frontend_env": "staging"
}
```

### Step 3: Verify Key Fields

| Field | Expected Value | What It Means |
|-------|----------------|---------------|
| `env` | `staging` | Backend knows it's staging |
| `db_name` | `mirror_staging` | Using staging database |
| `db_type` | `atlas` | Connected to MongoDB Atlas (not local) |
| `status` | `healthy` | All systems operational |

---

## 5. FRONTEND STAGING CONFIG

Frontend `.env.staging` is already configured:

```
EXPO_PUBLIC_ENV=staging
EXPO_PUBLIC_API_BASE_URL=https://api-staging.mirror.emergentagent.com
EXPO_PUBLIC_BUILD_VERSION=staging-v1.0.0
EXPO_PUBLIC_DEBUG_MIRROR=true
```

### For EAS Build (TestFlight):

```bash
cd /app/frontend
eas build --profile staging --platform ios
```

### For Web Export:

```bash
cd /app/frontend
cp .env.staging .env
npx expo export --platform web
# Deploy dist/ folder to staging web host
```

---

## 6. DEPLOYMENT SEQUENCE

### Backend First:
1. ✅ Create MongoDB Atlas staging database
2. ✅ Create database user with `readWrite` permissions
3. ✅ Get connection string
4. ✅ Set environment variables on staging server
5. ✅ Deploy backend code
6. ✅ Verify `/api/health` returns `env: "staging"` and `db_name: "mirror_staging"`

### Frontend Second:
1. ✅ Verify `.env.staging` points to `https://api-staging.mirror.emergentagent.com`
2. ✅ Build with staging profile: `eas build --profile staging`
3. ✅ Deploy web build to staging URL
4. ✅ Open staging web and check Build Info screen shows `staging • v30-...`

---

## 7. QUICK COPY-PASTE TEMPLATE

### Backend .env for Staging:

```env
MONGO_URL="PASTE_YOUR_MONGODB_ATLAS_CONNECTION_STRING_HERE"
DB_NAME="mirror_staging"
EMERGENT_LLM_KEY="sk-emergent-c740b6fF4020b7a102"
ENV="staging"
BUILD_LABEL="staging-v1.0.0"
GIT_SHA="manual-deploy"
DEBUG_MIRROR="true"
```

Replace:
- `PASTE_YOUR_MONGODB_ATLAS_CONNECTION_STRING_HERE` with your actual MongoDB Atlas staging connection string

---

## 8. TROUBLESHOOTING

### "db_type": "local" in /api/health
- **Problem**: Still using local MongoDB
- **Fix**: Check `MONGO_URL` starts with `mongodb+srv://`

### "db_name": "test_database" in /api/health
- **Problem**: Using dev database
- **Fix**: Set `DB_NAME="mirror_staging"` in env

### "env": "dev" in /api/health
- **Problem**: ENV variable not set
- **Fix**: Set `ENV="staging"` in env

### Connection refused to MongoDB
- **Problem**: Network access not configured
- **Fix**: Whitelist server IP in MongoDB Atlas Network Access
