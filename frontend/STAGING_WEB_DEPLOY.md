# STAGING WEB BUILD - DEPLOYMENT INSTRUCTIONS

## Build Output

**Location:** `/app/frontend/dist/`
**Size:** ~9.2 MB
**Environment:** staging
**API Target:** `https://api-staging.mirror.emergentagent.com`

---

## Verified Configuration

The build has these environment values baked in:
- `EXPO_PUBLIC_ENV=staging`
- `EXPO_PUBLIC_API_BASE_URL=https://api-staging.mirror.emergentagent.com`
- `EXPO_PUBLIC_BUILD_VERSION=staging-v1.0.0`
- `EXPO_PUBLIC_DEBUG_MIRROR=true`

---

## Deployment Options

### Option A: Static File Hosting (Vercel, Netlify, Cloudflare Pages)

1. **Zip the dist folder:**
   ```bash
   cd /app/frontend
   zip -r staging-web-build.zip dist/
   ```

2. **Upload to your hosting provider:**
   - Vercel: Drag & drop the `dist` folder
   - Netlify: Drag & drop or connect to repo
   - Cloudflare Pages: Upload via dashboard

3. **Configure routing:**
   - Set fallback to `index.html` for SPA routing
   - Vercel: Add `vercel.json` with rewrites
   - Netlify: Add `_redirects` file

### Option B: Manual Server (nginx/Apache)

1. **Copy dist to server:**
   ```bash
   scp -r /app/frontend/dist/* user@staging-server:/var/www/mirror-staging/
   ```

2. **nginx config:**
   ```nginx
   server {
       listen 80;
       server_name staging.mirror.emergentagent.com;
       root /var/www/mirror-staging;
       index index.html;

       location / {
           try_files $uri $uri.html $uri/ /index.html;
       }
   }
   ```

### Option C: Serve from Backend (Already Configured)

The backend already serves static files from `/app/frontend/dist/` when it exists.

1. **Copy dist to backend deployment:**
   ```bash
   cp -r /app/frontend/dist /app/backend/web_dist
   ```

2. Backend will auto-serve at the root URL.

---

## Post-Deployment Verification

1. **Open staging web URL**
2. **Login as test user**
3. **Tap username → Build Info**
4. **Verify:**
   - Frontend ENV = `staging`
   - API_BASE_URL = `https://api-staging.mirror.emergentagent.com`
   - Backend ENV = `staging`
   - DB Name = `mirror_staging`

---

## Files Included

```
dist/
├── index.html              # Main entry point
├── welcome.html            # Welcome screen
├── build-info.html         # Build info screen
├── journal.html            # Journal tab
├── lenses.html             # Lenses tab
├── life.html               # Life tab
├── (tabs)/                 # Tab routes
├── enneagram/              # Enneagram flows
├── lenses/                 # Individual lens views
├── _expo/static/js/web/    # JavaScript bundles
├── assets/                 # Images & fonts
├── manifest.webmanifest    # PWA manifest
├── favicon.ico             # Favicon
└── icon-*.png              # App icons
```
