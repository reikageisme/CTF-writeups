# Dog-Bark-None-Bite - Pwn Challenge Writeup

## Analysis
The binary checks if we are the "President" to give us the flag.
1. `scanf("%32s", buf)` reads up to 32 bytes into a buffer at `rbp-0x30`.
2. It checks if the byte at `rbp-0x11` (index 31 of our input) is non-zero.
3. It copies the buffer to `rbp-0x50` using `strcpy`.
4. It compares the copy with the string "President".

## Vulnerability
Logic conflict:
- `strcmp` requires the string to be exactly "President" (9 chars).
- The zero-check requires the char at index 31 to be non-zero (implying the string is at least 32 chars long).

Solution:
`scanf` treats null bytes (`\x00`) as normal characters (unlike `strcpy` or `gets`).
`strcpy` stops copying at the first null byte.

We can send "President" followed by a null byte, then padding up to 32 bytes.
- `scanf` reads the full 32 bytes (including the null and the padding).
- `buf[31]` becomes 'A' (non-zero), satisfying the check.
- `strcpy` encounters the null byte after "President" and stops, so `dest` becomes just "President".
- `strcmp` matches "President".

## Exploit
```python
from pwn import *

p = remote("14.225.212.104", 9010)

# "President" (9) + "\x00" (1) + Padding (22) = 32 bytes
payload = b"President\x00" + b"A" * 22

p.sendlineafter(b"name: \n", payload)
print(p.recvall().decode())
```

## Flag
`VSL{NU11_8Y73_N0N3_8173_N17}`
