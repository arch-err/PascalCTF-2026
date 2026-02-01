# Keep Scripting!

## Description
> *I always loved bombare, but my friend Elia challenged me to finish this level in 1 minute! It's impossible!!!1!*

**Connection:** `nc scripting.ctf.pascalctf.it 6004`

**Files:** [KeepTalkingAndNobodyExplodes-BombDefusalManual-v1.pdf](./orig/KeepTalkingAndNobodyExplodes-BombDefusalManual-v1.pdf)

## Solution
**TL;DR**: Automate solving 100 KTANE (Keep Talking and Nobody Explodes) modules in under 60 seconds using socket programming.

1. Connect to the server and parse bomb info (serial number, batteries, labels, ports)
2. Implement solvers for each module type: Wires, Button, Keypads, Complicated Wires, Simon Says, Who's on First, Memory, Morse Code, Wire Sequences, Passwords
3. Handle the Button "hold" case which requires providing a release digit based on strip color
4. For Complicated Wires, send individual "cut"/"skip" decisions for each wire interactively
5. For Keypads, map the Unicode symbols to KTANE manual columns and determine press order
6. Solve all 100 modules within the time limit

### Flag
> `pascalCTF{H0w_4r3_Y0u_s0_g0Od_4t_BOMBARE?}`
