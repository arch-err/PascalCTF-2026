# Packet Tracer 2

> [!WARNING]
> This challenge was **not solved** during the competition.

## Description
> *No way! They released a new version of my favorite software, Cisco Packet Tracer, now completely accessible by CLI!*

**Author:** Marco Balducci <`@Mark-74`>

**Connection:** `nc pt2.ctf.pascalctf.it 9005`

**Files:** [PT2](./orig/PT2), [libc.so.6](./orig/libc.so.6), [ld-linux-x86-64.so.2](./orig/ld-linux-x86-64.so.2), [env](./orig/env)

## Analysis

### Binary Properties
- ELF 64-bit PIE executable
- Has debug info, not stripped
- libc version: glibc 2.39
- Environment hint: `MALLOC_ARENA_MAX=1` (single heap arena)

### Program Structure
A network simulation tool with:
- Hosts (up to 30, indices 0-29)
- Routers (up to 5, indices 0-4)
- Interfaces for connections
- Routing tables
- Ping simulation

### Win Condition
A hidden `win_host` is created at startup:
- Stored at `hosts[30]` (inaccessible via normal menu)
- IP: 1.2.3.4/255.255.255.255
- Runs `win_host_thread` which checks every second if any router interface's `connected` field points to `win_host`
- If condition met, reads FLAG environment variable and prints it

### Key Structures
- Host: 0xa8 bytes (168)
- Router: 0x2e8 bytes (744)
- Packet: 0x409 bytes (1033)
- Route: 0x10 bytes (16)
- Interface: 0x90 bytes (144), has `connected` pointer at offset 0

### What We Tried
The MALLOC_ARENA_MAX=1 hint suggests heap exploitation is required. With glibc 2.39's tcache protections, we looked for:
- Double-free or UAF
- Type confusion
- Out-of-bounds access to write `win_host` pointer into a router interface

We needed to corrupt a router's interface `connected` pointer to point to `hosts[30]` (win_host).

### Unsolved Issues
- Couldn't find the exact vulnerability to exploit
- glibc 2.39 has strong heap protections (safe-linking, etc.)
- Time ran out before completing exploit

## Solution
*Not solved during the competition.*

### Flag
> *Not solved*
