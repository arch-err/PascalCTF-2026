# StrangeVM

## Description
> *A stranger once built a VM and hid the **Forbidden Key**, can you uncover it?*
>
> ***P.S.**: Keep all the files in the same directory for easier debugging and execution.*

**Files:** [vm](./orig/vm), [code.pascal](./orig/code.pascal)

## Solution
**TL;DR**: Reverse engineer custom VM bytecode - input transformed by position-based ADD/SUB

1. Binary runs `code.pascal` bytecode through a custom VM interpreter
2. VM has 6 opcodes: INP(5), SET(4), MOD(3), SUB(2), ADD(1), JZ(6)
3. For each character at position i:
   - If i is even: `mem[i] = input[i] + i`
   - If i is odd: `mem[i] = input[i] - i`
4. Result is compared against stored flag data at 0x4a0278
5. Reverse transformation: even positions subtract index, odd positions add index

### Bytecode Pattern (per character)
```
INP mem[i]           # read input char
SET mem[i+1], i      # temp = i
MOD mem[i+1], 2      # temp = i % 2
JZ mem[i+1], 12      # if even, skip SUB
SUB mem[i], i        # subtract index (odd positions)
JZ mem[1023], 6      # unconditional skip ADD
ADD mem[i], i        # add index (even positions)
```

### Solver
```python
flag_bytes = [86, 76, 117, 92, 56, 109, 57, 88, 108, 40, 62, 87, 123, 95, 63, 84,
              68, 91, 113, 32, 130, 27, 139, 80, 128, 70, 126, 21, 138, 87, 125,
              90, 80, 84, 129, 81, 140, 12, 148, 68]

flag = []
for i, b in enumerate(flag_bytes):
    if i % 2 == 0:
        flag.append(chr(b - i))
    else:
        flag.append(chr(b + i))
print(''.join(flag))  # VMs_4r3_d14bol1c4l_3n0ugh_d0nt_y0u_th1nk
```

### Flag
> `pascalCTF{VMs_4r3_d14bol1c4l_3n0ugh_d0nt_y0u_th1nk}`
