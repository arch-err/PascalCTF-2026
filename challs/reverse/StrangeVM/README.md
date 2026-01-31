# StrangeVM

## Description
> *A 🧙🏻‍♂️ stranger once built a VM and hid the **Forbidden Key**🥀, can you uncover it?*
>
> ***P.S.**: Keep all the files in the same directory for easier debugging and execution.*

**Files:** [vm](./orig/vm), [code.pascal](./orig/code.pascal)

## Solution
**TL;DR**: Reverse engineer custom VM and XOR-encoded flag
1. Binary runs `code.pascal` bytecode through a custom VM
2. VM compares execution result with stored flag (XOR encrypted)
3. Flag data at 0x4a0270 in rodata, 40 bytes long
4. XOR keys found for "pascalCTF{": [38, 45, 6, 63, 89, 1, 122, 12, 42, 83]
5. Keys don't follow simple pattern (not sequential, not position-based)
6. **Status: UNSOLVED** - Need to find complete XOR key array or reverse VM opcodes

### Analysis
- Opcodes identified: 0-6, 12, 255 are most common
- Flag is XOR encrypted with position-dependent keys
- Last key is 57 (if last char is '}')

### Flag
> `UNSOLVED - XOR cipher with unknown key pattern`
