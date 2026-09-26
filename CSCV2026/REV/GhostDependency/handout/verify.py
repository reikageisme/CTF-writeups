#!/usr/bin/env python3

import argparse, base64, hashlib, hmac, json, sys
from pathlib import Path

def _canon(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()

def _commit(proof, payload):
    c = _canon(proof)
    if payload is not None:
        c += b"|" + hashlib.sha256(payload).digest()
    return c

def _key(c):
    prk = hmac.new(b"CSCV2026:extract", c, hashlib.sha256).digest()
    return hmac.new(prk, b"CSCV2026:v2", hashlib.sha256).digest()

def _open_flag(flag_path, proof, payload=None):
    lines = Path(flag_path).read_bytes().splitlines()
    if not lines or lines[0] != b"CSCV-ENC-2":
        return None
    raw = base64.b64decode(lines[1])
    nonce, tag, ct = raw[:16], raw[16:48], raw[48:]
    k = _key(_commit(proof, payload))
    if not hmac.compare_digest(hmac.new(k, nonce + ct, hashlib.sha256).digest(), tag):
        return None
    out = bytearray()
    for i in range(0, len(ct), 32):
        ks = hmac.new(k, nonce + (i // 32).to_bytes(8, "big"), hashlib.sha256).digest()
        out += bytes(a ^ b for a, b in zip(ct[i:i + 32], ks))
    return bytes(out).decode()


import json, sys
if len(sys.argv) != 2: raise SystemExit("usage: verify.py proof.json")
proof = json.load(open(sys.argv[1], encoding="utf-8"))
payload = None

flag = _open_flag(str(Path(__file__).parent / 'flag.enc'), proof, payload)
if flag is None:
    sys.stderr.write('invalid proof\n')
    raise SystemExit(1)
sys.stdout.write(flag + '\n')
