# AuraTester2000

## Description
> *Will you be able to gain enogh aura?*

**Connection:** `nc auratester.ctf.pascalctf.it 7001`

**Files:** [AuraTester2000.gyat](./orig/AuraTester2000.gyat)

## Solution
**TL;DR**: Reverse "brainrot" language encoding and answer questions to gain 500+ aura
1. The `.gyat` file is written in a "brainrot" language with Gen-Z slang as keywords:
   - `glaze` = import, `ahh` = as, `bop` = def, `mewing` = for, `huzz` = range
   - `chat is this real X twin Y` = if X == Y, `yo chat` = elif, `only in ohio` = else
   - `rizz=` = +=, `its giving` = return, `yap` = print
   - `sigma` = >, `beta` = <, `let him cook` = while True
2. Answer questions to maximize aura (need 500+): yes/no/yes/no gives 150+50+450+50 = 700
3. The encoder converts every `steps`-th character (not spaces) to its ASCII ordinal value
4. Decode by: finding consecutive digits and converting them to chr(int(digits))
5. Steps value is randomly 2-5; try each to find the correct phrase

### Flag
> `pascalCTF{Y0u_4r3_th3_r34l_4ur4_f1n4l_b0s5}`
