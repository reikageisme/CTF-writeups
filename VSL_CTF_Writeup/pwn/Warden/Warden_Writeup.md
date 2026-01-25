# Warden - Pwn Challenge Writeup

## Analysis
The binary `warden` is a 32-bit ELF with Canary, NX, and PIE enabled.
The function `tft` has two vulnerabilities:
1.  **Format String**: `printf(buf)` with user input.
2.  **Buffer Overflow**: `gets(buf)` into a 44-byte buffer (offset 0x2c).

The `win` function gives the flag but requires setting 3 global variables to specific values and passing `0x123` as an argument.
Functions `braum`, `ornn`, and `thress` sets these global variables.

## Exploitation Strategy
1.  **Leak Canary & PIE**:
    Use the format string vulnerability to leak the Canary (offset 15) and a return address (offset 19) to calculate the PIE base address.
2.  **ROP Chain**:
    Construct a ROP chain to call the setup functions in order (`braum`, `ornn`, `thress`) and finally `win`.
    Since arguments are passed on the stack in 32-bit, we need a ROP gadget (`pop ebp; ret`) to clean up the stack arguments after each function call so the next function in the chain receives the correct stack layout.

## Payload
-   **Padding**: 32 bytes (to reach Canary).
-   **Canary**: 4 bytes (leaked value).
-   **Padding**: 12 bytes (Saved Registers & EBP).
-   **ROP**: `braum -> pop_ret -> ornn -> pop_ret -> thress -> pop_ret -> win -> dummy_ret -> 0x123`

## Flag
`VSL{1b58255c85311dfd1ee315b4897e7505}`
