# CornHub Challenge Solution

## Overview
CornHub challenge consists of a Node.js frontend and a Python FastAPI backend. The frontend proxies requests to the backend with some filtering and valid session management. The backend has "Internal Only" endpoints and checks for JWT authentication on some endpoints.

## Authenticated Bypass via Request Smuggling
The `/debug` endpoint in the frontend takes a `headers` JSON object from the request body and merges it into the headers sent to the backend. This allows injecting headers like `Content-Length`.

We exploited this to perform **HTTP Request Smuggling**:
1. Sent a request to `/debug` with `headers: {"Content-Length": "0"}` and a body containing a second, smuggled HTTP request (`POST /auth/forgot_password ...`).
2. The backend sees `Content-Length: 0`, processes the debug request (empty body), and leaves the rest of the payload in the buffer.
3. The backend then processes the next bytes as a new request: `/auth/forgot_password` for `admin@cornhub.com`.

## Account Takeover
The `forgot_password` endpoint generates a reset token based on:
`sha256(email + username + dob + timestamp_minute_precision)`
We knew all these values (Default admin created in `db.py`: `admin`, `admin@cornhub.com`, `2005-08-05`).
We brute-forced the timestamp (minute precision) to generate the valid token.

Using the valid token, we smuggled a request to `/auth/update_password` (also Internal Only) to reset the admin password.
Then we logged in legitimately via the frontend `/login` to get a valid JWT.

## Flag 1: LFI via `$HOME`
The `/documents` endpoint allows reading files but filters `..` and `startswith("/")`.
It uses `os.path.expandvars()`.
We used `file_name="$HOME/flag_1.txt"`.
`$HOME` expands to `/home/appuser` (absolute path).
`os.path.join("/cornhub", "/home/appuser/...")` results in `/home/appuser/...`.
This bypassed the filter and read the flag.

## Flag 2: Frontend Filter Bypass
The frontend blocks requests containing `flag_2.txt` in the body.
The check was: `if (req.path === '/documents') ...`
We bypassed this by sending the request to `/documents/` (trailing slash).
Express routing treats `/documents/` and `/documents` as the same route handler, but `req.path` is `/documents/`, failing the exact match check.
We then used the same `$HOME` trick to read `flag_2.txt`.

## Flags
Flag 1: `VSL{why_50_w34k?50_w34k?`
Flag 2: `50_w34k?1ccb825f90f9a5a3}`

Combined: `VSL{why_50_w34k?50_w34k?50_w34k?1ccb825f90f9a5a3}`
