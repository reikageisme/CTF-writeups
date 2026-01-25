# R4um4n1a-Uni Challenge Writeup

## Analysis

We are given a C source file `chall.c` and a remote service running it.
The core logic resides in `math_func` which validates 4 inputs (`x`, `y`, `z`, `t`) against 4 equations derived from global variables.

### Variables

```c
unsigned int out_put_0 = 6442450944; // 0x180000000 -> Wraps to 0x80000000 (2147483648)
unsigned int out_put_1 = 192096208;
unsigned int out_put_2 = 111120240;
unsigned int out_put_3 = 286156338;
```

Note that `out_put_0` is initialized with a value larger than `UINT_MAX` (32-bit). It wraps modulo $2^{32}$:
$$6442450944 \pmod{2^{32}} = 2147483648 \text{ (0x80000000)}$$

### Equations

The code implements the following checks:

**Equation 1:**
`1 * x + 3 * y + 3 * z - 7 * t != (unsigned long long) (out_put_0 * 2)`
The RHS calculation `out_put_0 * 2` happens in `unsigned int` arithmetic before casting:
$$0x80000000 \times 2 = 0x100000000 \xrightarrow{\text{u32 wrap}} 0$$
So, $x + 3y + 3z - 7t = 0$.

**Equation 2:**
`1 * x + 1 * y + 1 * z + 1 * t != (unsigned long long) (out_put_1 / 24012026)`
$192096208 / 24012026 = 8$
So, $x + y + z + t = 8$.

**Equation 3:**
`3 * x - 1 * y + 1 * z + 1 * t != (unsigned long long) (out_put_2 / 11112024)`
$111120240 / 11112024 = 10$
So, $3x - y + z + t = 10$.

**Equation 4:**
`1 * x + 1 * y + 2 * z + 2 * t != (unsigned long long) (out_put_3 / 22012026)`
$286156338 / 22012026 = 13$
So, $x + y + 2z + 2t = 13$.

## Solving the System

We have:
1. $x + 3y + 3z - 7t = 0$
2. $x + y + z + t = 8$
3. $3x - y + z + t = 10$
4. $x + y + 2(z + t) = 13$

**Step 1:** Subtract Eq 2 from Eq 3:
$(3x - y + z + t) - (x + y + z + t) = 10 - 8$
$2x - 2y = 2 \implies x - y = 1 \implies x = y + 1$

**Step 2:** Isolate $(z+t)$ in Eq 2 and substitute into Eq 4:
From Eq 2: $(x+y) + (z+t) = 8$
From Eq 4: $(x+y) + 2(z+t) = 13$
Let $A = x+y$ and $B = z+t$.
$A + B = 8$
$A + 2B = 13$
Subtracting first from second: $B = 5$.
So $z + t = 5$.
Then $A = 3 \implies x + y = 3$.

**Step 3:** Solve x and y:
$x - y = 1$
$x + y = 3$
Adding them: $2x = 4 \implies x = 2$.
Then $y = 1$.

**Step 4:** Solve z and t using Eq 1:
$x + 3y + 3z - 7t = 0$
$2 + 3(1) + 3z - 7t = 0$
$5 + 3z - 7t = 0$
$3z - 7t = -5$
We also know $z = 5 - t$.
$3(5-t) - 7t = -5$
$15 - 3t - 7t = -5$
$15 - 10t = -5$
$20 = 10t \implies t = 2$.
$z = 5 - 2 = 3$.

**Solution:**
Code: `2 1 3 2`

## Flag
Running the exploit script against the remote target:
`VSL{r4um4n14_n3v3r_d13_h1h1_@@_j4f}`
