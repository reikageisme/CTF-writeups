---
title: "Ghost Dependency"
ctf: "CSCV"
date: 2026-09-26
category: reverse
difficulty: unknown
points: 100
flag_format: "CSCV2026{...}"
author: "unknown"
---

# Ghost Dependency

![Challenge](challenge.png)

## Summary

The challenge asks for the registry crate whose contents disagree with the SPDX inventory, the runtime host identity, and a hash-based activation value. The crate's malicious build script explains the ghost dependency.

## Solution

The entered component is `telemetry-core 0.8.1`. Its registry archive SHA-256 is `00ebb39a81290e16cd8c6c677ba2ce3265021f940c0a6c37894720f98abdd463`, which does not match the SPDX claim `80d433753b03c46eb8dd0c63ac60d7d22c2a3e91f2d652b5e9c073edf1e6d573`.

The hostile archive contains `telemetry-core-0.8.1/build.rs`, whose SHA-256 is `9158c8946f2c738740da4dd83634b7e07537975b74a0a0eb54698d7150a15f91`. The build script encodes `build-secret-rotation` with `hex::encode` and exports it as `EXFIL_PAYLOAD`, making the secret available to the compiled agent. The source crate has no declared dependency for `hex`; the build log nevertheless shows `hex v0.4.3` compiled. This is the supply-chain/build-environment inconsistency behind the ghost dependency.

Running the supplied Linux ELF under WSL prints the selected host identity `host-39113c02654a`. The activation value is the lowercase SHA-256 of the UTF-8 string `crate_sha256:host_id`:

```text
SHA256("00ebb39a81290e16cd8c6c677ba2ce3265021f940c0a6c37894720f98abdd463:host-39113c02654a")
= 0a7d8a886e765c8bf794c66bde6e0beb107ffa9ab829b7ab74b4a531da665e1a
```

The solution proof also commits to the malicious build-script snippet hash:

```json
{
  "activation_hex": "0a7d8a886e765c8bf794c66bde6e0beb107ffa9ab829b7ab74b4a531da665e1a",
  "crate_sha256": "00ebb39a81290e16cd8c6c677ba2ce3265021f940c0a6c37894720f98abdd463",
  "host_id": "host-39113c02654a",
  "malicious_snippet_sha256": "9158c8946f2c738740da4dd83634b7e07537975b74a0a0eb54698d7150a15f91"
}
```

The proof object is saved as `proof.json`. First unpack the supplied handout archive, then run the verifier from the challenge directory:

The handout's `FORMAT.md` specifies exactly three proof fields, while the accepted supplied proof includes `malicious_snippet_sha256` as a fourth field. Keep that fourth field when reproducing this checked-in solution: it is part of the canonical proof committed by the encrypted flag.

```sh
python3 -m zipfile -e download.zip .
python3 handout/verify.py proof.json
```

The verifier accepts the proof and recovers:

## Flag

```text
CSCV2026{pr0v3nanc3_b34ts_4_trust3d_n4m3}
```
