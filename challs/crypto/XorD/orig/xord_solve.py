#!/usr/bin/env python
import random

enc = bytes.fromhex(open('output.txt').read().strip())

# rebuild the keystream
rng = random.Random(1337)
stream = [rng.randint(0, 255) for _ in range(len(enc))]

# decrypt
flag = bytes([c ^ k for c, k in zip(enc, stream)])
print(flag.decode())
