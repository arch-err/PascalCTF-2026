# Curve Ball

## Description
> *Our casino's new cryptographic gambling system uses elliptic curves for provably fair betting.*
>
> *We're so confident in our implementation that we even give you an oracle to verify points!*

**Connection:** `nc curve.ctf.pascalctf.it 5004`

**Files:** [curve.py](./orig/curve.py)

## Solution
**TL;DR**: Supersingular elliptic curve with n = p + 1, SageMath's `discrete_log` solves it instantly

1. The curve `y² = x³ + 1 (mod p)` has order `n = p + 1 = 1844669347765474230`, which is characteristic of a **supersingular elliptic curve**
2. For supersingular curves, the embedding degree is 2, making the **MOV attack** highly efficient
3. SageMath's `discrete_log` function handles this case automatically by using the Weil pairing to reduce ECDLP to DLP in F_{p²}
4. Connect to the server, parse `Q = secret * G`, solve the discrete log, and submit the secret

### Flag
> `pascalCTF{sm00th_0rd3rs_m4k3_3cc_n0t_s0_h4rd_4ft3r_4ll}`
