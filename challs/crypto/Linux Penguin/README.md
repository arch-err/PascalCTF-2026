# Linux Penguin

## Description
> *I've just installed Arch Linux and I couldn't be any happier :)*

**Connection:** `nc penguin.ctf.pascalctf.it 5003`

**Files:** [penguin.py](./orig/penguin.py)

## Solution
**TL;DR**: AES-ECB mode leaks plaintext equality - encrypt all dictionary words to build a lookup table.

1. The challenge uses AES-ECB which encrypts identical plaintexts to identical ciphertexts
2. All 28 dictionary words are exactly 16 characters (one AES block)
3. We get 7 rounds × 4 words = 28 encryptions, enough to encrypt the entire dictionary
4. Encrypt all words, build a ciphertext→plaintext mapping
5. Look up the 5 challenge ciphertexts in our mapping

### Flag
> `pascalCTF{why_4r3_th3_bl0ck_4lw4ys_th3_s4m3???}`
