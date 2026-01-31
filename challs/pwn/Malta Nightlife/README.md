# Malta Nightlife

## Description
> *You've never seen drinks this cheap in Malta, come join the fun! 🍹*

**Connection:** `nc malta.ctf.pascalctf.it 9001`

**Files:** [malta.zip](./orig/malta.zip)

## Solution
**TL;DR**: Integer overflow vulnerability - buy drinks with negative quantity to gain money
1. Connect to the service and notice the Flag drink costs 1000000000 € but you only have 100 €
2. The program doesn't validate negative numbers for quantity
3. Buy any drink with quantity -999999999 to overflow the price calculation (price * quantity)
4. This gives you a huge balance due to integer overflow: 100 - (-1705032698) = 1705032798 €
5. Now you can afford the Flag drink (10) for 1000000000 €

### Flag
> `pascalCTF{St0p_dR1nKing_3ven_1f_it5_ch34p}`
