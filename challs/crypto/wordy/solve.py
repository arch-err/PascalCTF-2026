#!/usr/bin/env python3
from pwn import *
from z3 import *
from collections import defaultdict
import sys

ALPHABET = "abcdefghijklmnop"
K = 16
L = 5
N_WORDS = K ** L

print("[*] Precomputing word table...", file=sys.stderr)
ALL_WORDS = []
for idx in range(N_WORDS):
    digits = []
    x = idx
    for _ in range(L):
        digits.append(x % K)
        x //= K
    ALL_WORDS.append("".join(ALPHABET[d] for d in reversed(digits)))

def word_to_index(word):
    x = 0
    for ch in word:
        x = x * K + ALPHABET.find(ch)
    return x

def compute_feedback(guess, secret):
    res = 0
    counts = [0] * K
    fb = [0] * L

    for i in range(L):
        if guess[i] == secret[i]:
            fb[i] = 2
        else:
            counts[ALPHABET.find(secret[i])] += 1

    for i in range(L):
        if fb[i] == 2:
            continue
        gi = ALPHABET.find(guess[i])
        if counts[gi] > 0:
            fb[i] = 1
            counts[gi] -= 1

    for i in range(L):
        res = res * 3 + fb[i]
    return res

INIT_GUESSES = ["aceik", "bdfhl", "gjmnp"]

print("[*] Precomputing feedback tables...", file=sys.stderr)
feedback_tables = []
for g in INIT_GUESSES:
    table = defaultdict(list)
    for idx in range(N_WORDS):
        fb = compute_feedback(g, ALL_WORDS[idx])
        table[fb].append(idx)
    feedback_tables.append(dict(table))

print("[*] Precomputation done!", file=sys.stderr)

def solve_wordle_fast(io):
    def guess(word):
        io.sendline(f"GUESS {word}".encode())
        resp = io.recvline().decode().strip()
        if not resp.startswith("FEEDBACK "):
            return None
        fb_str = resp.split()[1]
        if fb_str == "GGGGG":
            return ("DONE", word)
        fb = 0
        for c in fb_str:
            fb = fb * 3 + '_YG'.index(c)
        return fb

    result = guess(INIT_GUESSES[0])
    if isinstance(result, tuple):
        return result[1]
    fb1 = result

    result = guess(INIT_GUESSES[1])
    if isinstance(result, tuple):
        return result[1]
    fb2 = result

    result = guess(INIT_GUESSES[2])
    if isinstance(result, tuple):
        return result[1]
    fb3 = result

    s1 = set(feedback_tables[0].get(fb1, []))
    s2 = set(feedback_tables[1].get(fb2, []))
    s3 = set(feedback_tables[2].get(fb3, []))
    candidates = list(s1 & s2 & s3)

    for _ in range(17):
        if len(candidates) == 1:
            return ALL_WORDS[candidates[0]]
        if len(candidates) == 0:
            return None

        g = ALL_WORDS[candidates[0]]
        result = guess(g)
        if isinstance(result, tuple):
            return result[1]
        fb = result

        candidates = [c for c in candidates if compute_feedback(g, ALL_WORDS[c]) == fb]

    return ALL_WORDS[candidates[0]] if candidates else None

def temper(y):
    y ^= (y >> 11)
    y ^= ((y << 7) & 0x9D2C5680)
    y ^= ((y << 15) & 0xEFC60000)
    y ^= (y >> 18)
    return y & 0xFFFFFFFF

class MT19937:
    def __init__(self, state, index=0):
        self.mt = state[:]
        self.index = index

    def twist(self):
        old = self.mt[:]
        for i in range(624):
            y = (old[i] & 0x80000000) | (old[(i+1) % 624] & 0x7FFFFFFF)
            self.mt[i] = old[(i + 397) % 624] ^ (y >> 1) ^ (0x9908B0DF if (y & 1) else 0)
        self.index = 0

    def next_u32(self):
        if self.index >= 624:
            self.twist()
        y = self.mt[self.index]
        self.index += 1
        return temper(y)

def symbolic_temper(y):
    y = y ^ LShR(y, 11)
    y = y ^ ((y << 7) & 0x9D2C5680)
    y = y ^ ((y << 15) & 0xEFC60000)
    y = y ^ LShR(y, 18)
    return y

def solve_state_z3_with_twist(observations):
    """Solve with full second state array constrained"""
    print(f"[*] Solving for state from {len(observations)} observations...")

    MT_N = 624
    MT_M = 397
    MATRIX_A = 0x9908B0DF
    UPPER_MASK = 0x80000000
    LOWER_MASK = 0x7FFFFFFF

    s = Solver()

    # First state array (observations 0-623)
    mt = [BitVec(f'mt_{i}', 32) for i in range(MT_N)]

    for i in range(min(MT_N, len(observations))):
        tempered = symbolic_temper(mt[i])
        s.add(Extract(19, 0, tempered) == observations[i])

    if len(observations) > MT_N:
        print("[*] Modeling twist and second state array...")
        new_mt = []
        for i in range(MT_N):
            y = (mt[i] & UPPER_MASK) | (mt[(i + 1) % MT_N] & LOWER_MASK)
            twist_val = mt[(i + MT_M) % MT_N] ^ LShR(y, 1) ^ If((y & 1) == 1, BitVecVal(MATRIX_A, 32), BitVecVal(0, 32))
            new_mt.append(twist_val)

        n_post_twist = min(len(observations) - MT_N, MT_N)
        print(f"[*] Constraining {n_post_twist} post-twist observations...")
        for i in range(n_post_twist):
            tempered = symbolic_temper(new_mt[i])
            s.add(Extract(19, 0, tempered) == observations[MT_N + i])

    print("[*] Running z3...")
    if s.check() == sat:
        model = s.model()
        state = [model.eval(mt[i], model_completion=True).as_long() for i in range(MT_N)]
        print("[+] State found!")
        return state
    print("[-] No solution")
    return None

def main():
    context.log_level = 'warn'

    io = remote("wordy.ctf.pascalctf.it", 5005)
    io.recvuntil(b"READY")
    io.recvline()

    observations = []
    # 624 + 624 = 1248 to fully constrain both state arrays
    # Max is 1300 rounds, need 5 for FINAL, so 1295 max observations
    NUM_ROUNDS = 1248

    print(f"[*] Playing {NUM_ROUNDS} Wordle rounds...")

    for r in range(NUM_ROUNDS):
        io.sendline(b"NEW")
        io.recvline()

        secret = solve_wordle_fast(io)
        if not secret:
            print(f"[-] Round {r} failed")
            break

        observations.append(word_to_index(secret))

        if (r + 1) % 200 == 0:
            print(f"[*] Round {r+1}/{NUM_ROUNDS}")

    print(f"[+] Got {len(observations)} observations")

    state = solve_state_z3_with_twist(observations)
    if not state:
        io.close()
        return

    rng = MT19937(state, 0)

    # Quick verification of a sample
    print("[*] Verifying sample observations...")
    test_indices = [0, 100, 500, 623, 624, 625, 1000, 1200, 1247]
    for idx in test_indices:
        if idx >= len(observations):
            continue
        # Reset and advance
        rng2 = MT19937(state, 0)
        for _ in range(idx):
            rng2.next_u32()
        out = rng2.next_u32()
        pred = out & 0xFFFFF
        if pred != observations[idx]:
            print(f"[-] Mismatch at {idx}: got {pred}, expected {observations[idx]}")
        else:
            print(f"[+] Match at {idx}: {pred}")

    # Advance our RNG to position len(observations)
    for _ in range(len(observations)):
        rng.next_u32()

    print(f"[*] RNG index: {rng.index}")

    print("[*] Predicting next 5...")
    flag = None
    for i in range(5):
        out = rng.next_u32()
        pred_idx = out & 0xFFFFF
        pred = ALL_WORDS[pred_idx]
        print(f"[*] Prediction {i}: {pred}")
        io.sendline(f"FINAL {pred}".encode())
        resp = io.recvline().decode().strip()
        print(f"[*] Response: {resp}")
        if "pascalCTF{" in resp:
            flag = resp.split()[-1]
            print(f"[+] FLAG: {flag}")

    if flag:
        with open("flag.txt", "w") as f:
            f.write(flag + "\n")

    io.close()

if __name__ == "__main__":
    main()
