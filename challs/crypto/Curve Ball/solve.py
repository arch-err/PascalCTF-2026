#!/usr/bin/env sage
from pwn import *
import re

p = 1844669347765474229
a = 0
b = 1
n = 1844669347765474230
Gx = 27
Gy = 728430165157041631

# Connect to the server
io = remote('curve.ctf.pascalctf.it', 5004)

# Read banner and get Q
data = io.recvuntil(b'> ').decode()
print(data)

# Parse Q from output
match = re.search(r'Q = \((\d+), (\d+)\)', data)
Qx, Qy = int(match.group(1)), int(match.group(2))
print(f"[*] Q = ({Qx}, {Qy})")

# Use SageMath to solve the discrete log
# For supersingular curves with n = p + 1, this is efficient
E = EllipticCurve(GF(p), [a, b])
G = E(Gx, Gy)
Q = E(Qx, Qy)

print(f"[*] Curve order: {E.order()}")
print(f"[*] Solving discrete log...")

# SageMath handles supersingular curves efficiently
secret = discrete_log(Q, G, operation='+')
print(f"[+] Secret: {secret}")
print(f"[+] Secret (hex): {hex(secret)}")

# Submit the secret
io.sendline(b'1')
io.recvuntil(b'secret (hex): ')
io.sendline(hex(secret).encode())

# Get flag
response = io.recvall(timeout=2).decode()
print(response)

io.close()
