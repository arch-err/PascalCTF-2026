# ZazaStore

## Description
> *We dont take any responsibility in any damage that our product may cause to the user's health*

**URL:** https://zazastore.ctf.pascalctf.it

**Files:** [challenge.zip](./orig/challenge.zip)

## Solution
**TL;DR**: NaN bypass - add non-existent product to make total = NaN, bypassing balance check
1. Login with any credentials
2. Add "RealZa" to cart (costs $1000, you only have $100)
3. Add a fake product that doesn't exist in the prices object (e.g., "FakeProduct")
4. On checkout, the server calculates: `total = prices["RealZa"] * 1 + prices["FakeProduct"] * 1`
5. Since "FakeProduct" doesn't exist, `prices["FakeProduct"]` = undefined
6. `undefined * 1` = NaN, so `total = 1000 + NaN` = NaN
7. The check `if (total > req.session.balance)` fails because `NaN > 100` = false
8. Purchase succeeds, RealZa added to inventory with the flag

### Flag
> `pascalCTF{w3_l1v3_f0r_th3_z4z4}`
