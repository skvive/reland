# Google Maps (RE:LAND `/map`)

## Env

| Variable | Scope |
|----------|--------|
| `GOOGLE_MAPS_BROWSER_KEY` | Vercel Production (browser-restricted key) |

Fallback: `GOOGLE_MAPS_API_KEY` (same value).

Exposed to the SPA via `GET /api/config` → `google_maps_browser_key`. When set, `/map` uses **Maps JavaScript API**; otherwise **Leaflet + OpenStreetMap**.

## Google Cloud (lexidkay@gmail.com)

1. Project with billing (e.g. `lexid-land`).
2. Enable **Maps JavaScript API**.
3. Credentials → **Create credentials** → **API key**.
4. Restrict key:
   - Application: HTTP referrers  
     `https://reland.lexid.site/*`  
     `https://*.vercel.app/*`  
     `http://localhost:*/*`
   - API: Maps JavaScript API only.

## Vercel

```powershell
cd E:\currsor_C\blog\reland-deploy
vercel env add GOOGLE_MAPS_BROWSER_KEY production
vercel --prod --yes
```

## Verify

- `https://reland.lexid.site/api/config` → non-empty `google_maps_browser_key`
- `/map` → label **Google Maps · 정확한 경계 아님 · 지역 기준점**

Disclaimer on map remains: points are administrative / CSV centroids, not legal boundaries.
