# BabyREV Writeup

## Challenge Overview
**Category**: Reverse Engineering  
**Objective**: Reverse engineer the `babyrev` binary to find the correct flag.

## Initial Analysis
The challenge provided a 64-bit ELF executable `babyrev`.

```bash
$ file babyrev
babyrev: ELF 64-bit LSB pie executable, x86-64 ...
```

Running `strings` revealed prompts like "Enter flag:", "Nope.", and "Nice work, that's the flag!".

Executing the binary:
```bash
$ ./babyrev
Enter flag: VSL{test}
Nope.
```

## Static Analysis (GDB & Disassembly)
We used GDB and `objdump` to analyze the binary's logic.

1.  **Input Verification**:
    *   The program reads a line of input.
    *   It checks the length (expected 60 characters total).
    *   It checks for the prefix `VSL{` and the suffix `}` at index 59.
    *   The core flag content has a length of **55 characters**.

2.  **Transformation Loop**:
    The main verification logic is a loop that iterates 55 times (indices 0 to 54).

    *   **Permutation**: The input at standard index `i` is written to a permuted index in a buffer. Code analysis and dynamic debugging revealed the destination index formula:
        ```c
        dest_idx = (i * 7) % 55;
        ```
    
    *   **State Machine**:
        The transformation maintains a complex internal state using registers `ESI`, `R9D`, and `R10D`. These values are updated in every iteration based on the current character of the flag.

    *   **Bitwise Logic**:
        The transformation involves:
        *   Addition with constants (updating `R9D`).
        *   XOR operations mixing the character and state.
        *   Circular bit shifts (`ROL`) where the shift amount depends on the loop index (`cl = (i % 13) + 1`).
        *   A final XOR check against a hardcoded constant `0xffffffa5` and `R10D`.

3.  **Target Buffer**:
    The transformed bytes are compared against a hardcoded byte array stored in the `.rodata` section. We extracted these 55 bytes using a Python script.

## Solution Strategy
Since the internal state (`ESI`) for iteration `i` depends on the result of iteration `i-1` and the character chosen at `i-1`, we cannot simply reverse the math for each byte independently. The state "flows" through the string.

### Solver Implementation
We implemented a **backtracking solver** in Python:
1.  **Simulation**: We re-implemented the assembly logic (ROL, XOR, ADD) in Python to simulate the state updates exactly.
2.  **Search**: The solver tries printable ASCII characters for the current position `i`.
3.  **Validation**: For a chosen character, it calculates the transformed byte and checks if it matches the byte at `target[(i * 7) % 55]`.
4.  **Recursion**: If valid, it recursively proceeds to `i+1`. If invalid, it backtracks.

### Key Logic Snippet (Python)
```python
def backtrack(i, r9d, esi, r10d, path):
    if i == 55:
        return "".join(path)

    dest_idx = (i * 7) % 55
    target_byte = target[dest_idx]
    cl = (i % 13) + 1 # Dynamic shift amount

    for c in range(32, 127):
        # Emulate binary logic
        curr_esi = esi
        curr_esi = (curr_esi ^ (c + r9d)) & 0xFFFFFFFF
        curr_esi = rol(curr_esi, cl)
        curr_esi = (curr_esi - 0x61c8864f) & 0xFFFFFFFF
        
        # Calculate resulting byte
        val = (curr_esi >> 17) ^ (curr_esi >> 3)
        term2 = ( (i+3) * c ) & 0xFFFFFFFF
        val = val ^ term2 ^ r10d ^ 0xffffffa5
        
        if (val & 0xFF) == target_byte:
             # Recursive call
             res = backtrack(i+1, next_r9d, curr_esi, next_r10d, path + [chr(c)])
             if res: return res
```

## Result
The solver successfully reconstructed the flag content.

**Flag**: `VSL{medium_reverse_fun_with_layered_checks_and_twists_12345}`
