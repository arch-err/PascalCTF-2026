# YetAnotherNoteTaker

## Description
> *I've read too many notes recently, I can't take it anymore...*

**Connection:** `nc notetaker.ctf.pascalctf.it 9002`

**Files:** [notetaker.zip](./orig/notetaker.zip)

## Solution
**TL;DR**: Format string vulnerability with libc 2.23 heap exploitation
1. Binary has format string vulnerability in note read/write functions
2. Input at stack position 8 reflects back
3. Uses old libc 2.23 (included in challenge) - classic heap exploit
4. Can leak stack addresses: `%p` outputs show heap and stack locations
5. **Status: UNSOLVED** - Need GOT overwrite or other exploitation technique

### Vulnerability Details
- Service: `nc notetaker.ctf.pascalctf.it 9002`
- Format string at stack position 8
- Heap pointer leakable
- libc 2.23 allows various heap attacks (fastbin dup, etc.)

### Flag
> `UNSOLVED - Format string + heap exploitation required`
