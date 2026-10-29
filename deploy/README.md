# RE:LAND production (Neon + Vercel)

- `DATABASE_URL`: Neon **pooled** connection string (`-pooler` host) for Vercel serverless.
- `RELAND_ADMIN_KEY`: long random secret for admin API (`X-Admin-Key`).
- `GOOGLE_CLIENT_ID`: optional Google Sign-In client ID for production OAuth.
- `RELAND_PUBLIC_URL`: `https://rerand.lexid.site`

Local SQLite: omit `DATABASE_URL` and use `RELAND_DB=./data/reland.sqlite`.
