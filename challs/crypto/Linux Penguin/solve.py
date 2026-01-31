#!/usr/bin/env python3
from pwn import *

words = [
    "biocompatibility", "biodegradability", "characterization", "contraindication",
    "counterbalancing", "counterintuitive", "decentralization", "disproportionate",
    "electrochemistry", "electromagnetism", "environmentalist", "internationality",
    "internationalism", "institutionalize", "microlithography", "microphotography",
    "misappropriation", "mischaracterized", "miscommunication", "misunderstanding",
    "photolithography", "phonocardiograph", "psychophysiology", "rationalizations",
    "representational", "responsibilities", "transcontinental", "unconstitutional"
]

# Connect to remote
r = remote("penguin.ctf.pascalctf.it", 5003)

# Wait for initial prompt
r.recvuntil(b"16 chars):")

# Build ciphertext -> plaintext mapping by encrypting all 28 words in 7 rounds of 4
ct_to_word = {}

for i in range(7):
    batch = words[i*4:(i+1)*4]

    for j, word in enumerate(batch):
        r.recvuntil(f"Word {j+1}: ".encode())
        r.sendline(word.encode())

    r.recvuntil(b"Encrypted words: ")
    encrypted = r.recvline().decode().strip().split()

    for word, ct in zip(batch, encrypted):
        ct_to_word[ct] = word

    # Skip to next round prompt if not last
    if i < 6:
        r.recvuntil(b"16 chars):")

# Get the challenge ciphertext
r.recvuntil(b"Ciphertext: ")
ciphertext = r.recvline().decode().strip().split()

log.info(f"Received {len(ciphertext)} encrypted words to guess")

# Guess each word
for i, ct in enumerate(ciphertext):
    word = ct_to_word[ct]
    log.info(f"Word {i+1}: {word}")
    r.recvuntil(f"Guess the word {i+1}: ".encode())
    r.sendline(word.encode())

# Get the flag
r.recvuntil(b"Correct guess:")
flag = r.recvall(timeout=2).decode()
print(flag)
