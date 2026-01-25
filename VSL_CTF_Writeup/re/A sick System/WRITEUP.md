# CTF Writeup: Wow. A sick System 100

## Challenge Overview
**Category:** Reverse Engineering / WebAssembly  
**Goal:** Recover the flag hidden inside a WASM-based authentication system.

## 1. Initial Analysis
The challenge consists of a web interface powered by `challenge.js` and `challenge.wasm`. The JavaScript loads the WASM module which handles login and flag verification.

To analyze the logic effectively without a browser, I patched `challenge.js` to run in a Node.js environment, mocking necessary browser APIs (`window`, `TextEncoder`, etc.) and bypassing the `fetch` API to load the WASM from the local disk.

## 2. Authentication
By inspecting the strings inside the WASM binary or the behavior of the `login` function, valid credentials were found stored in plain text within the data section:
*   **Username:** `sup3rus3r`
*   **Password:** `s3cretp4ss`

Logging in with these credentials grants access to the `check_flag` function.

## 3. Reversing `check_flag`
The core difficulty lies in the `check_flag` function. 

### Side-Channel Analysis
Initial tests using side-channel analysis (monitoring the specific memory address returned by the function) revealed:
*   Return `1085` -> "Fail."
*   Return `1091` -> "Invalid length." (implied, or partial match)
*   Return `1076` -> "Success."

Brute-forcing the length confirmed the flag is exactly **30 characters** long.

### Logic Analysis
The function appeared to be stateful or destructive. When running the check, the input buffer in memory was modified. Comparing the input before and after execution revealed a transformation pattern.

Sending a known input (e.g., `AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA`) resulted in a specific output in the buffer. Changing one character in the input changed exactly one character in the output, but **at a mirrored position**.

The transformation logic was determined to be a **Reversed XOR Cipher**:
```javascript
Output_Buffer[29 - i] = Input_Buffer[i] ^ Key[i % 7]
```

### Key Recovery
By comparing the input `A` (0x41) with the resulting output bytes, I recovered the 7-byte XOR key:
**Key:** `0R0Dl4n`

## 4. Extracting the Flag
The `check_flag` function compares this transformed buffer against a hardcoded encrypted sequence in the WASM memory. 

Knowing the flag starts with `VSL{`, I calculated the encrypted bytes for this prefix using the derived key and logic:
*   `V` ^ `0` -> `0x66` (stored at end)
*   `S` ^ `R` -> `0x01`
*   `L` ^ `0` -> `0x7C`
*   `{` ^ `D` -> `0x3F`

Target sequence to find: `... 3F 7C 01 66`

Scanning the WASM memory for this sequence found a match at offset `1071`:
`2f451b4119314527451b051f1b0167435d593337010d445a042b3f7c0166`

## 5. Decryption
Reversing the cipher on the extracted bytes:

```javascript
Input[i] = Encrypted_Target[29 - i] ^ Key[i % 7]
```

**Decrypted Flag:**
`VSL{G04t_1s_m3s51_s1uuuuuuuuu}`
