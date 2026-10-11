# Deploy Career Compass AI on Vercel

The repository is configured for one Vercel project containing the React/Vite
frontend and FastAPI backend. It uses [Vercel Services](https://vercel.com/kb/guide/vercel-services),
currently in Beta. Both applications share one domain; API requests use `/api`.

## Keep the existing database

The current PostgreSQL database runs on this computer. Vercel needs a hosted
PostgreSQL database reachable over TLS. Copy the current database to that host
to preserve users, profiles, careers, recommendations, saved careers and chat
history. Keep the same Firebase project so existing Firebase user IDs continue
to match the database records.

A private custom-format backup was created at
`database/backups/career-compass-20261011-113657.dump` on 11 October 2026.
It contains schema and data for all nine tables. Backups are excluded from Git
and deployment uploads. This snapshot will not include later local changes.
Take a fresh backup and pause local writes when performing the final migration.

1. Create an empty hosted PostgreSQL database, preferably PostgreSQL 18 to match
   the local server. Obtain its direct connection URL for migration and its
   pooled connection URL for the application. Preserve the provider's TLS options.
2. Restore the backup using PostgreSQL 18 `pg_restore`. Supply the destination
   connection string through `DATABASE_MIGRATION_URL` in your local environment.
   From the repository root in PowerShell:

   ```powershell
   & 'C:\Program Files\PostgreSQL\18\bin\pg_restore.exe' --dbname=$env:DATABASE_MIGRATION_URL --no-owner --no-acl --exit-on-error --single-transaction '.\database\backups\career-compass-20261011-113657.dump'
   ```

   Use an empty application database. The command does not drop existing tables;
   conflicts abort the restore. Do not initialize tables before restoring.
   If the host uses an older PostgreSQL version, check compatibility before import.
3. Verify table row counts and a sample of related records after restoring.
   Set Vercel's `DATABASE_URL` to the hosted provider's pooled URL.

`database/schema.sql` alone is insufficient to preserve the current database:
it contains no existing records, and the live model also includes video resources.

## Vercel project settings

Import this repository into your Vercel account. Use these settings:

| Setting | Value |
| --- | --- |
| Root Directory | Repository root (leave the directory override empty) |
| Framework Preset | **Services** |
| Build/install/output overrides | Use `vercel.json` |

The Services preset and the `services` key in `vercel.json` are both required.
The configuration builds `frontend` with `npm ci` and a Vercel-only
`VITE_API_BASE_URL=/api` override. Normal local builds retain the existing
single-address setup on port 8000. FastAPI uses `backend/vercel_app.py` and
Python 3.12. Public `/api/*` requests are routed to the mounted backend.

## Environment variables

Configure these in the Vercel project's environment settings before deploying.
Use Production values for production deployments; configure Preview separately
if previews are required. Secrets belong in server environment variables.

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | Hosted pooled PostgreSQL URL with TLS, including `sslmode=require` or the provider's stronger setting |
| `DATABASE_AUTO_CREATE` | `false` (also the default when Vercel sets `VERCEL=1`) |
| `FIREBASE_CREDENTIALS_JSON` | Complete contents of the existing Firebase service-account JSON file |
| `OPENROUTER_API_KEY` | Existing backend OpenRouter key |
| `OPENROUTER_MODEL` | `nvidia/nemotron-3.5-lightning:free` |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` |
| `CHATBOT_TIMEOUT_SECONDS` | `20` |
| `CHATBOT_MAX_TOKENS` | `700` |
| `APP_SITE_URL` | Final HTTPS Vercel/custom domain |
| `APP_NAME` | `Career Compass AI` |
| `YOUTUBE_API_KEY` | Existing backend value, if using YouTube search |

For `FIREBASE_CREDENTIALS_JSON`, paste the JSON object without wrapping it in extra
quotes; preserve escaped newlines inside its private key. The cloud deployment
does not use the local `FIREBASE_CREDENTIALS_PATH`. Never prefix these secrets with
`VITE_`; Vite variables become public browser code. The `/api` frontend setting
is supplied by the build command automatically.

Vercel disables automatic schema creation by default. Future schema changes must
be applied explicitly once to the hosted database. The backend uses the provider's
pooler without retaining its own idle connections in each serverless instance.

## Firebase and launch checks

In Firebase Console for `career-compass-ai-c058c`, open **Authentication → Settings
→ Authorized domains** and add the final Vercel hostname (without `https://`).
Keep the existing Firebase project and enabled sign-in providers.

Deploy, then check:

- `/api/health` returns `{"status":"ok"}`.
- `/api/db-test` returns a successful database connection result.
- Sign-in works, existing profiles and saved careers appear, and chat replies work.
- Refreshing a frontend route such as `/login` loads the React app.

Local tests and builds do not verify the deployed Linux function or its dependency
bundle. Confirm Vercel's build logs and the live checks before announcing launch.

References: [Services configuration](https://vercel.com/docs/services/config-reference),
[FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi),
[PostgreSQL backup tools](https://www.postgresql.org/docs/current/app-pgdump.html).
