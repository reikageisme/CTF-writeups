# Compress Server Writeup

## Challenge Overview
- **Name:** Compress Server
- **Category:** Web
- **Description:** A Node.js web application that allows users to upload archives (Zip/Tar) to be extracted. It has an Admin functionality protected by a secret Key and Password.

## Vulnerabilities

### 1. Arbitrary File Read via Symlink (Tar Slip / Symlink)
The application uses the `tar` library to extract uploaded `.tar` files. The extraction logic does not properly validate or sanitize symbolic links within the tar archive.
We can create a malicious Tar file containing a symbolic link pointing to `../../../logs/<session_id>/login.logs` or `../../../data/users.json`. When verified via the `/api/file` endpoint (which serves file content), the server follows the symlink and returns the target file's content.

### 2. Information Leak via Logging (Crypto Oracle)
The Admin Login endpoint (`/api/login`) checks a secret `adminKey` fetched from an internal service.
The validation logic is:
```javascript
if (hash_func(xor(Buffer.from(adminKeyInp), Buffer.from(adminKey))) !== TARGET_HASH) {
    await logAdminLogin(...); // Logs the COMPLETED hash to a file
}
```
The `xor` function uses `Math.min(length1, length2)`, meaning if we send a short input, the XOR operation is truncated to that length.
Since `a ^ 0 = a`, sending null bytes `\x00` allows us to "leak" the hash of the Key's prefix.
By increasing the input length byte-by-byte (1 byte, 2 bytes...), we can bruteforce the Key one character at a time by matching the logged SHA256 hash.

## Exploitation Steps

1.  **Arbitrary File Read Primitive:**
    *   Create a valid session.
    *   Trigger an error or log entry to ensure the log file exists (or target `users.json`).
    *   Construct a `tar` file with a symlink `link -> ../../../logs/<sid>/login.logs`.
    *   Upload the tar. The server extracts it.
    *   Access `/api/file?extractionId=...&file=link` to read the log file.

2.  **Admin Key Recovery:**
    *   We targeted the `admin` login with a fake Key input.
    *   We sent `\x00` * N as `adminKeyInp`.
    *   The server computed `SHA256(Key[0...N] ^ \x00)`.
    *   It logged this hash to `login.logs` because the login failed.
    *   We read `login.logs` using the Symlink primitive.
    *   We locally computed `SHA256(Candidate ^ \x00)` to find the matching character.
    *   Repeated for all 32 bytes of the hex-string key.
    *   Recovered Key: `8f9795b5e8b9401fea05e6c322910069`

3.  **Admin Password Recovery:**
    *   The server also checks the password from `users.json`.
    *   We used the Symlink primitive to read `../../../data/users.json`.
    *   Found Admin Password: `Sup3rp4s5w0rdy0un3v3rkn0wn1t1fy0ukn0wy0ukn0w`

4.  **Flag Capture:**
    *   Logged in as `admin` with the recovered Key and Password.
    *   Accessed `/admin` to get the flag.

**Flag:** `VSL{81ee58a307bc02cf74d366f26e7b4610}`
