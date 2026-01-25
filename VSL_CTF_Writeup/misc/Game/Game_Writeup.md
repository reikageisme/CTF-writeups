# Game Writeup

## Challenge Description
**Name:** Game
**Category:** Misc / Reverse Engineering
**Description:** 
> Just a funny game with basic rule : Connect to server by client.exe, enter server IP and Port. Kill the monster in silent, NOT SLAY IT. Trust me bro, you don't want to wake him up...

**Server:** 14.225.212.104:9999

## Analysis

We are provided with `client.exe` and `string.h` (which contains source code strings). The goal is to kill the monster "silently".

### 1. Initial Reconnaissance
Running the client connects to the server. The interface shows:
- **Monster HP**: 10
- **Gun [1]**: Damage 1, Ammo 10.
- **Bomb [2]**: Damage 1337, Ammo 1.

The description warns "NOT SLAY IT" and "don't wake him up". 
- Using the **Bomb** deals 1337 damage. This likely triggers the bad ending (Satan wakes up).
- Using the **Gun** 10 times deals exactly 10 damage. This kills the monster, but depletes all ammo. The client then displays: `"Out of bullet !? I think you should find another way !"`.

### 2. Reverse Engineering `client.exe`
We analyzed the binary to understand the communication protocol.

#### Handshake via `valid_user`
By examining the `main` function (approximate address `0x140001d2c`) and `valid_user` function (`0x140001c35`), we can see how the client authenticates:

1.  `main` initializes four variables:
    *   `0x9` (9) - Likely Bullets.
    *   `0x1` (1) - Likely Gun Damage.
    *   `0x1` (1) - Likely Bomb Count.
    *   `0x539` (1337) - Likely Bomb Damage.

2.  `valid_user` takes these values and formats them into a string using `sprintf` with the pattern `%d %d %d %d`.
3.  It sends this string to the server (e.g., `9 1 1 1337`).
4.  The server responds with `valid` if accepted.

#### Game Loop via `send_damage`
When the player selects an option, the client calls `send_damage`.
This function simply converts the damage integer to a string (using `itoa`) and sends it to the server.

### 3. The Exploit
The "Out of bullets" message is purely client-side logic. The server trusts the client to tell it how much damage is dealt.

To kill the monster "silently":
1.  We must deal enough damage to kill it (HP 10).
2.  We must **not** deal 1337 damage (which triggers Satan).
3.  We want to do it efficiently or bypass the ammo check.

Since we control the packets, we can simply write a Python script to:
1.  Perform the handshake (`9 1 1 1337\x00`).
2.  Send a custom damage packet with value `10` (`10\x00`). 

Sending `10` damage kills the monster instantly (10 - 10 = 0) but is not the specific "loud" value of 1337.

## Solution Script

```python
import socket
import time

HOST = '14.225.212.104'
PORT = 9999

def solve():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((HOST, PORT))
        print(f"[+] Connected to {HOST}:{PORT}")
        
        # 1. Perform Handshake
        # Protocol: "Bullets GunDmg BombCnt BombDmg"
        # Values found in binary: 9 1 1 1337
        payload = b"9 1 1 1337"
        print(f"[*] Sending handshake: {payload}")
        s.sendall(payload + b"\x00") # Client sends null-terminated string
        
        # 2. Check validity
        resp = s.recv(4096)
        if b"valid" in resp:
            print("[+] Handshake accepted.")
            
            # 3. Send "Silent Kill" Damage
            # We skip the menu logic and just tell server we did 10 damage.
            # 10 kills the monster (HP 10) without triggering "Satan" (which requires 1337 damage).
            damage_payload = b"10"
            print(f"[*] Sending custom damage: {damage_payload}")
            s.sendall(damage_payload + b"\x00")
            
            # 4. Read Flag
            s.settimeout(5)
            while True:
                data = s.recv(4096)
                if not data: break
                print(data.decode('utf-8', errors='ignore'), end='')
        else:
            print("[-] Handshake failed.")
            
    except Exception as e:
        print(f"[-] Error: {e}")
    finally:
        s.close()

if __name__ == "__main__":
    solve()
```

## Flag
`VSL{D0_Y0U_H4V3_FUN_W1tH_iT_?}`
