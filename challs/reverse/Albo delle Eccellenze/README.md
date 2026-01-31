# Albo delle Eccellenze

## Description
> *One of our former Blaisone CTF Team members 🚩 has just earned a medal in the Cyberchallenge.IT contest 🥳.*
>
> *He's now wondering whether he also received a prize 🏆, could you help him find out?*

**Connection:** `nc albo.ctf.pascalctf.it 7004`

**Files:** [albo.zip](./orig/albo.zip)

## Solution
**TL;DR**: The check logic is inverted - any input works.

1. Reverse engineering the binary reveals:
   - The program generates an Italian "Codice Fiscale"-like code from user input (name, surname, date of birth, sex, place of birth)
   - The `check` function (at `0x004023eb`) validates the code by:
     - Checking if it's 16 characters
     - Performing 64 iterations of XOR (with `0x5e`) and adjacent swaps
     - Comparing against `"A11D612LPSCBLS37"`

2. There are two bugs in the implementation:
   - **Buffer overflow**: The swap loop accesses index 16 of a 16-character string (out of bounds), corrupting the string with null bytes
   - **Inverted logic**: In `main` at `0x004026f2`, the result is XORed with 1 before the branch check, meaning success is triggered when the comparison *fails*

3. Due to these bugs, the corrupted string never matches the target, causing `check` to return 0, which the inverted logic interprets as success.

4. Solution: Enter any valid input format:
   ```
   nc albo.ctf.pascalctf.it 7004
   Name: anything
   Surname: anything
   Date of birth: 01/01/2000
   Sex: M
   Place of birth: anywhere
   ```

### Flag
> `pascalCTF{g00d_luck_g3tt1ng_your_pr1zes_n0w}`
