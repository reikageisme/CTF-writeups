# Piano Cipher (KeyGame) Challenge Solution

## Overview
The challenge is a web game "Piano Cipher" where the user must follow a random path of 40 steps. The server enforces strict verification:
1.  **HMAC Signature:** Each move requires a hash `md5($SECRET_KEY | $step | $side)`.
2.  **Random Path:** The server generates a random path stored in the session. One wrong move resets the path.

## Reconnaissance
We discovered that the environment installed the `libjs-jquery-jfeed` package.
Fuzzing revealed the existence of `/javascript/jquery-jfeed/proxy.php`.
This file is vulnerable to Local File Inclusion (LFI) / SSRF via the `url` parameter.

## Exploitation
1.  **Leak Secret Key:**
    Using the LFI, we read `/var/www/secret_key.txt`.
    Payload: `/javascript/jquery-jfeed/proxy.php?url=file:///var/www/secret_key.txt`
    Result: `4d55c523-329f-4a06-a050-a1e1516c147b`

2.  **Leak Session Data:**
    The random path is generated securely (`random_int`) and stored in the PHP session.
    Since we can't predict the path, we use the LFI to *read* the session file directly.
    Session Path: `/var/lib/php/sessions/sess_<PHPSESSID>`
    Payload: `/javascript/jquery-jfeed/proxy.php?url=file:///var/lib/php/sessions/sess_<PHPSESSID>`

3.  **Automated Solver:**
    A Python script was written to:
    - Start a game (`?act=respawn`) to get a Session ID.
    - Retrieve the session content via LFI.
    - Parse the serialized path array (`[0, 1, 0, ...]`).
    - Use the secret key to generate valid move signatures.
    - Submit all 40 moves to the server.

## Flag
`VSL{LFI_v1a_jFeed_Proxy_is_D4ngerous!}`
