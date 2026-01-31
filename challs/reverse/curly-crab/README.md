# curly-crab

## Description
> *A crab stole my json schema...*

**Files:** [curly-crab](./orig/curly-crab)

## Solution
**TL;DR**: Reverse engineer the Rust binary to find the hidden flag in the symbol table

1. The binary is a Rust program using serde_json to deserialize JSON into nested structs
2. Running `strings` reveals the struct hierarchy: Top, Crab, Claww, Ocean, Rusty, Shell, Termm, Abysss, Crabby, Oceann, Prawnn, Rustyy, Shelll, Shrimp, Ferriss, Lobstah, Lobster, Shrimppy
3. Several red herring strings exist in the rodata section:
   - `extern "shrimppyl0bst3rd` at offset 0x6440 (fake extern ABI)
   - `crabZeros4f3`, `r3vv1ng_Deadlock`, and leetspeak field names
4. The actual flag is hidden in the symbol table section at offset 0x8631a
5. Running `strings -n 20 curly-crab | grep -E "^[a-z0-9]+$"` reveals the flag content: `ay1je5uw7soca0mpxasj1sp36`

### Flag
> `pascalCTF{ay1je5uw7soca0mpxasj1sp36}`
