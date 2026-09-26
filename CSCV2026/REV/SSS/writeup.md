---
title: "Signed, Sealed, Subverted"
ctf: "CSCV"
date: 2026-09-26
category: reverse
difficulty: unknown
points: 100
flag_format: "CSCV2026{...}"
author: "unknown"
---

# Signed, Sealed, Subverted

![Challenge](challenge.png)

## Summary

The updater has two separate objects in its install path: a signed base manifest and a patch record emitted at runtime. The signature covers the base manifest, while the patch can name a module that the signed manifest never committed to. I used the updater's own `emit` output as the minimal accepted patch, then supplied the proof and patch bytes to the challenge verifier.

## Solution

### 1. Compare what the signature covers with what gets installed

Start with `handout/signed-base.upd`, `handout/manifest.cddl`, `handout/policy.txt`, and the updater. The signed base manifest decodes to these three lines:

```text
CSCV-OTA-base-v7
root=/opt/recovery-root
version=7
```

The Ed25519 signature is valid for this manifest text. The manifest says which recovery root and version are trusted, but it has no module path, module digest, or build nonce. The policy protects `/etc` and `/usr/bin`; the install path used by the patch is `/opt/modules/proof.mod`, outside those protected paths.

That separates the two relevant questions: the signature proves who signed the base manifest, while the updater must still bind the installed module to that signed content. Here it does not. The patch record carries install instructions independently.

### 2. Ask the updater to emit its patch template

The AArch64 updater's `emit` mode prints the fields accepted by its patch parser. Run the supplied updater in its Linux/AArch64 challenge environment and save the output as `poc.upd`:

```text
CSCV-PATCH v1
nonce=be7f8504a8a5d232a6e88c67a4f47ecdab45d71427e11d653365ea34d147b15f
module=/opt/modules/proof.mod
len=0
```

The record is 121 bytes. `module` is the fixed path the updater installs, `nonce` is the updater's `buildNonce`, and `len=0` makes the module payload empty. The record still directs installation to `proof.mod`; the signed manifest never names or hashes that module.

### 3. Build the proof object

The verifier takes a JSON proof plus the patch file. The proof commits to the nonce and install path emitted above:

```json
{"build_nonce":"be7f8504a8a5d232a6e88c67a4f47ecdab45d71427e11d653365ea34d147b15f","module":"/opt/modules/proof.mod"}
```

The supplied `proof.json` contains exactly this object. The zero-byte `proof.mod` is not the patch; `poc.upd` is the 121-byte patch record passed as the verifier's payload.

### 4. Reproduce the verifier check

The challenge bundle is stored as `handout.zip`. Extract it and run the checked-in runner from the `SSS` directory:

```sh
python3 -m zipfile -e handout.zip handout
sh ./handout/runner.sh ./proof.json ./poc.upd
```

The runner's actual interface is `runner.sh proof.json proof.mod` (the second argument is read as a payload path). This differs from the challenge page's one-argument example `runner.sh poc.upd`. The runner itself does not launch the updater or modify `boot.qcow2`; it reads `handout/flag.enc`, the proof JSON, and the payload bytes.

The verifier canonicalizes the proof JSON by sorting keys and removing spacing. It appends `|` and the binary SHA-256 digest of `poc.upd`, derives a key with HMAC-SHA256 using the labels `CSCV2026:extract` and `CSCV2026:v2`, and authenticates the encrypted flag before decrypting it. This is why both files matter: changing a proof field or changing even one patch byte changes the verifier key and fails the authentication tag.

## Flag

```text
CSCV2026{v3rify_th3_s4m3_obj3ct_y0u_1nst4ll}
```
