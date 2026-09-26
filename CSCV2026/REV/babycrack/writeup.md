---
title: "BabyCrackMe"
ctf: "CSCV"
date: 2026-09-26
category: reverse
difficulty: unknown
points: 100
flag_format: "CSCV2026{...}"
author: "unknown"
---

# BabyCrackMe

![Challenge](challenge.png)

## Summary

The outer PE hides an embedded PE and constructs an 80-byte verifier blob in code. Recovering those bytes reveals an AES-encrypted target password; reversing the bit permutation recovers the password, which then decrypts the supplied PNG containing the flag.

## Solution

### Recover the password and decrypt the flag image

The solver extracts immediate values from the outer binary's `mov dword ptr [rbp+disp8], imm32` instructions. It splits the blob into an AES-256 key and ciphertext, derives the CBC IV from the key nibbles, and decrypts the target. The checker transform moves one bit from each input byte into each output byte; the script inverts that permutation and confirms its result by applying the forward transform again.

The accepted password's SHA-256 digest is the AES key for `extracted/flag.png.enc`. The decrypted bytes are checked for the PNG header and trailer before being written to `extracted/flag.png`.

The handout archive is password-protected with `infected`. Extract it into `extracted/`, then run from this directory with Python 3 and `cryptography` installed:

```powershell
7z x .\BabyCrackme.7z -pinfected -oextracted
python .\solve_baby.py
```

The recovered image contains the flag.

## Flag

```text
CSCV2026{n0_IAT_HuH???}
```
