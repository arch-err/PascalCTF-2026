# wordy

## Description
> *Bored in class? Try this cryptic Wordle twist and crack the next word! 🧩🔐*

**Connection:** `nc wordy.ctf.pascalctf.it 5005`

**Files:** [service.py](./orig/service.py)

## Solution
**TL;DR**: MT19937 state recovery from partial outputs using z3 constraint solving.

1. The service implements a Wordle game using MT19937 PRNG with a 16-letter alphabet (a-p) and 5-letter words
2. Each secret word is generated from `rng.next_u32() & 0xFFFFF` (lower 20 bits of PRNG output)
3. We can recover each secret by playing Wordle (using feedback to filter candidates)
4. Collect 1248 observations (624 + 624) to fully constrain two complete state arrays
5. Use z3 to solve for the MT19937 internal state by:
   - Constraining lower 20 bits of tempered outputs 0-623 against first state array
   - Modeling the twist operation symbolically
   - Constraining lower 20 bits of tempered outputs 624-1247 against second state array
6. Clone the recovered state and predict the next 5 outputs to win

### Flag
> `pascalCTF{Y0ur_l1k3_a_3ncycl0p3d14_0f_r4nd0m_w0rds!}`
