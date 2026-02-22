# Environment Variable Checklist

Use this checklist when setting up `.env` for local development or configuring production environment variables.

> **Source of truth**: `service/project/settings.py` (backend) and `import.meta.env` references (frontend).
> The `.example.env` file documents intended variables but contains **three naming mismatches** (flagged below).

---

## 1. PostgreSQL Database

Local defaults match `docker-compose.yml`'s `db` service. No action needed for local dev.

| | Variable | Default | Recovery |
|---|---|---|---|
| [ ] | `DATABASE_NAME` | `diplicity` | Hardcoded in `docker-compose.yml` (`POSTGRES_DB`) |
| [ ] | `DATABASE_USER` | `postgres` | Hardcoded in `docker-compose.yml` (`POSTGRES_USER`) |
| [ ] | `DATABASE_PASSWORD` | `postgres` | Hardcoded in `docker-compose.yml` (`POSTGRES_PASSWORD`) |
| [ ] | `DATABASE_HOST` | `db` | Docker service name; use `localhost` outside Docker |
| [ ] | `DATABASE_PORT` | `5432` | Standard PostgreSQL port |

---

## 2. Django Core

| | Variable | Default | Recovery |
|---|---|---|---|
| [ ] | `DJANGO_DEBUG` | `False` | Set to `True` for local development |
| [ ] | `DJANGO_SUPERUSER_USERNAME` | _(none)_ | Choose any value; used by `createsuperuser --noinput` |
| [ ] | `DJANGO_SUPERUSER_EMAIL` | _(none)_ | Choose any value; used by `createsuperuser --noinput` |
| [ ] | `DJANGO_SUPERUSER_PASSWORD` | _(none)_ | Choose any value; used by `createsuperuser --noinput` |

---

## 3. Google OAuth

> **NAMING MISMATCH**: `.example.env` defines `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET`, but `settings.py` reads `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`. Google login will silently fail if you use the `.example.env` names. Use the corrected names below.

| | Variable | `.example.env` name | Default | Recovery |
|---|---|---|---|---|
| [ ] | `GOOGLE_CLIENT_ID` | `GOOGLE_OAUTH_CLIENT_ID` | _(none)_ | Google Cloud Console > `diplicity-django` project > APIs & Services > Credentials > "Diplicity Django Web" OAuth 2.0 Client ID |
| [ ] | `GOOGLE_CLIENT_SECRET` | `GOOGLE_OAUTH_CLIENT_SECRET` | _(none)_ | Same location as above, copy "Client Secret" |

---

## 4. Social Auth

> **NAMING MISMATCH**: `.example.env` defines `SOCIAL_SECRET`, but `settings.py` reads `SOCIAL_AUTH_PASSWORD`. If you use the `.example.env` name, the value is ignored and `default_social_password` is used instead.

| | Variable | `.example.env` name | Default | Recovery |
|---|---|---|---|---|
| [ ] | `SOCIAL_AUTH_PASSWORD` | `SOCIAL_SECRET` | `default_social_password` | Any random string; for local dev the default is fine |

---

## 5. Firebase Cloud Messaging

All values come from a Firebase service account JSON key file.

**Recovery**: Firebase Console > `diplicity-react` project > Project Settings (gear icon) > Service Accounts > Generate New Private Key. Use the downloaded JSON to fill in these values.

| | Variable | Default | Notes |
|---|---|---|---|
| [ ] | `FIREBASE_TYPE` | _(none)_ | Always `service_account` |
| [ ] | `FIREBASE_PROJECT_ID` | _(none)_ | `project_id` from JSON |
| [ ] | `FIREBASE_PRIVATE_KEY_ID` | _(none)_ | `private_key_id` from JSON |
| [ ] | `FIREBASE_PRIVATE_KEY` | _(none)_ | `private_key` from JSON; include `-----BEGIN/END-----` markers |
| [ ] | `FIREBASE_CLIENT_EMAIL` | _(none)_ | `client_email` from JSON |
| [ ] | `FIREBASE_CLIENT_ID` | _(none)_ | `client_id` from JSON |
| [ ] | `FIREBASE_AUTH_URI` | _(none)_ | Usually `https://accounts.google.com/o/oauth2/auth` |
| [ ] | `FIREBASE_TOKEN_URI` | _(none)_ | Usually `https://oauth2.googleapis.com/token` |
| [ ] | `FIREBASE_AUTH_PROVIDER_X509_CERT_URL` | _(none)_ | Usually `https://www.googleapis.com/oauth2/v1/certs` |
| [ ] | `FIREBASE_CLIENT_X509_CERT_URL` | _(none)_ | `client_x509_cert_url` from JSON |

---

## 6. Sentry Error Tracking

| | Variable | Default | Recovery |
|---|---|---|---|
| [ ] | `SENTRY_DSN` | _(none; Sentry disabled)_ | sentry.io > diplicity project > Settings > Client Keys (DSN) |
| [ ] | `VITE_SENTRY_DSN` | `""` _(disabled)_ | Same DSN or a separate frontend project DSN from sentry.io |

---

## 7. Honeycomb / OpenTelemetry

| | Variable | Default | Recovery |
|---|---|---|---|
| [ ] | `HONEYCOMB_API_KEY` | _(none; OTEL disabled)_ | Honeycomb > Team Settings > Environments & API Keys |
| [ ] | `OTEL_SERVICE_NAME` | `diplicity-service` | Identifies the backend service in traces |
| [ ] | `VITE_HONEYCOMB_API_KEY` | _(none; OTEL disabled)_ | Same key or separate key from Honeycomb |
| [ ] | `VITE_OTEL_SERVICE_NAME` | `diplicity-web` | Identifies the frontend in traces |

---

## 8. Frontend Configuration

| | Variable | Default | Recovery |
|---|---|---|---|
| [ ] | `VITE_GOOGLE_CLIENT_ID` | _(none)_ | Same value as `GOOGLE_CLIENT_ID` (see section 3) |
| [ ] | `VITE_DIPLICITY_API_BASE_URL` | _(none; falls back to `http://localhost:8000` in code)_ | `http://localhost:8000` for local dev; production URL in prod |
| [ ] | `VITE_MAINTENANCE_MODE` | _(none)_ | `false` for normal operation; `true` to show maintenance page |

---

## 9. Vars in `settings.py` NOT in `.example.env`

These variables are read by `settings.py` but are **not listed in `.example.env`**. Most have safe defaults for local development and are only needed in production.

| Variable | Default | Purpose | When needed |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | Insecure dev key | Django cryptographic signing | **Production only** — generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,service,allowed-health-check` | Hosts that Django will serve | Production — set to your domain |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Includes `localhost:8000`, `localhost:5173` | Origins allowed to make CSRF-protected requests | Production — set to your domain |
| `DJANGO_CORS_ALLOWED_ORIGINS` | Includes `localhost:3000`, `localhost:5173` | Origins allowed for CORS | Production — set to your frontend domain |
| `DATABASE_CONNECTION_STRING` | _(none)_ | Full database URL (takes priority over individual DB vars) | Production (Railway provides this) |
| `DATABASE_URL` | _(none)_ | Alternative full database URL (second priority) | Production (Railway provides this) |
| `ENVIRONMENT` | `development` | Labels the deployment environment | Production — set to `production` |
| `GIT_SHA` | `0.0.0` | Application version shown in health/version endpoints | Set by CI/CD pipeline |

---

## Summary of Naming Mismatches

These `.example.env` entries use **incorrect variable names** that don't match what `settings.py` actually reads. If copied verbatim, the values will be silently ignored.

| `.example.env` declares | `settings.py` reads | Impact if not corrected |
|---|---|---|
| `GOOGLE_OAUTH_CLIENT_ID` | `GOOGLE_CLIENT_ID` | Google OAuth login fails silently |
| `GOOGLE_OAUTH_CLIENT_SECRET` | `GOOGLE_CLIENT_SECRET` | Google OAuth login fails silently |
| `SOCIAL_SECRET` | `SOCIAL_AUTH_PASSWORD` | Falls back to `default_social_password` |

**Recommendation**: Update `.example.env` to use the correct variable names, or ensure your `.env` file uses the names that `settings.py` expects.
