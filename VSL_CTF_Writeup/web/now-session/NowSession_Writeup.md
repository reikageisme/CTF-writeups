# Now-Session Challenge Writeup

## Analysis
The application is a Flask web app that allows users to "save" and "load" content.
It uses a custom `set_` function to merge JSON data into a python object (`Exploit` instance).

### Vulnerability: Class Pollution
The `set_` function (recursive merge) allows modifying attributes of objects if the key exists on the destination.
- Use `request.data` (JSON) to feed `set_`.
- `set_` traverses objects via `getattr` and sets via `setattr` or item assignment.

### Mitigation & Bypass
The application implements a blacklist:
```python
blacklist_raw = [
    "__", "globals", "init", ..., "application", "secret", "config", ...
]
```
Checks: `if any(b in lk for b in blacklist_raw): continue` where `lk = raw_k.lower()`.
Normalization: `k = unicodedata.normalize("NFKC", raw_k).translate(ZERO_WIDTH)`.

**Bypass Strategy:**
We can inject Zero Width Spaces (`\u200b`) *inside* the keywords.
Since the blacklist check happens on `raw_k` (before normalization), `glo\u200bbals` is NOT `globals` and bypasses the check.
The normalization then removes `\u200b`, restoring the key to `globals` for use in `getattr/setattr`.

### Exploit Path
We want to forge a session cookie to become `admin`.
To do this, we need the `SECRET_KEY`.
We can use Class Pollution to overwrite the `SECRET_KEY` in the running application to a known value (e.g., "pwned").

**Target:** `save.__func__.__globals__['application'].config['SECRET_KEY']`

**Payload Construction:**
- `__func__` -> `_\u200b_func_\u200b_`
- `__globals__` -> `_\u200b_glo\u200bbals_\u200b_` (Must break "globals" too!)
- `application` -> `appli\u200bcation`
- `secret_key` -> `secre\u200bt_key`
- `config` -> `con\u200bfig`
- `SECRET_KEY` -> `SECRE\u200bT_KEY`

### Execution
1. Send pollution payload to `/save_build`.
2. Forge a session cookie signed with secret key "pwned" containing `{"user": "admin"}`.
3. Access `/get_flag` with the forged cookie.

## Flag
`VSL{cl4ss_p0llut1on_v1a_sp3c_no3mar_asc11__l04d3r_bypass}`
