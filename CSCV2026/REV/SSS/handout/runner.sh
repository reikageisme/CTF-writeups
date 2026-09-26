#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
[ "$#" -eq 2 ] || { echo "usage: runner.sh proof.json proof.mod" >&2; exit 2; }
"${PYTHON:-python3}" - "$SCRIPT_DIR/flag.enc" "$1" "$2" <<'PY'
import base64, hashlib, hmac, json, sys
from pathlib import Path

def _canon(obj): return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",",":")).encode()
def _commit(proof, payload):
    c = _canon(proof)
    if payload is not None:
        c += b"|" + hashlib.sha256(payload).digest()
    return c
def _key(c):
    prk = hmac.new(b"CSCV2026:extract", c, hashlib.sha256).digest()
    return hmac.new(prk, b"CSCV2026:v2", hashlib.sha256).digest()

flag_path, proof_path, payload_path = sys.argv[1], sys.argv[2], sys.argv[3]
proof = json.load(open(proof_path, encoding="utf-8"))
payload = Path(payload_path).read_bytes()
lines = Path(flag_path).read_bytes().splitlines()
raw = base64.b64decode(lines[1]); nonce, tag, ct = raw[:16], raw[16:48], raw[48:]
k = _key(_commit(proof, payload))
if not hmac.compare_digest(hmac.new(k, nonce + ct, hashlib.sha256).digest(), tag):
    sys.stderr.write("rejected\n"); sys.exit(1)
out = bytearray()
for i in range(0, len(ct), 32):
    ks = hmac.new(k, nonce + (i // 32).to_bytes(8, "big"), hashlib.sha256).digest()
    out += bytes(a ^ b for a, b in zip(ct[i:i + 32], ks))
sys.stdout.write(bytes(out).decode() + "\n")
PY
