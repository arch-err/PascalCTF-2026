# curly-crab

> [!WARNING]
> This challenge was **not solved** during the competition.

## Description
> *A crab stole my json schema...*

**Files:** [curly-crab](./orig/curly-crab)

## Analysis

### Binary Properties
- ELF 64-bit Rust binary using serde_json
- Prompts "Give me a JSONy flag!" and reads JSON input
- Outputs 🦀 on successful parse, 😔 on failure

### Struct Hierarchy
Running `strings` reveals nested struct definitions:
- Top, Crab, Claww, Ocean, Rusty, Shell, Termm, Abysss, Crabby, Oceann, Prawnn, Rustyy, Shelll, Shrimp, Ferriss, Lobstah, Lobster, Shrimppy

### Field Names (leetspeak)
- `s34_`, `g0t_`, `y0u_` (sea, got, you)
- `I_crabby`, `cr4bs`, `d33p_`, `oceann`, `w4v35`
- `ru5t_`, `rustyy`, `m3m0ry`, `sh3ll_`, `shelll`
- `l0v3_`, `d1v3r`, `sup3r_`, `c0d3_ftw`, `w3_`, `s34f00d`
- `cl4ws`, `shr1mp5`

### Red Herrings
- `extern "shrimppyl0bst3rd` at offset 0x6440
- `crabZeros4f3`, `r3vv1ng_Deadlock` in rodata
- `ay1je5uw7soca0mpxasj1sp36` in symbol table (FILE symbol) - doesn't decode to readable text

### What We Tried
1. Extracting `ay1je5uw7soca0mpxasj1sp36` from symbol table - **wrong flag**
2. Various XOR/cipher decoding of the string - produced gibberish
3. Attempting to construct valid JSON input - couldn't determine exact schema
4. Analyzing field names for patterns - spell "sea got you" but unclear how to use

### Key Insight (Unsolved)
The flag is likely revealed when you provide correctly-structured JSON that deserializes into the nested Rust structs. All other PascalCTF flags are readable leetspeak messages, suggesting `ay1je5uw7soca0mpxasj1sp36` is a red herring.

## Solution
*Not solved during the competition.*

### Flag
> *Not solved*
