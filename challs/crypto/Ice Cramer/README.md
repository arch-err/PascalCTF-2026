# Ice Cramer

## Description
> *Elia's swamped with algebra but craving a new ice-cream flavor, help him crack these equations so he can trade books for a cone!*

**Connection:** `nc cramer.ctf.pascalctf.it 5002`

**Files:** [main.py](./orig/main.py)

## Solution
**TL;DR**: Solve system of linear equations using Cramer's rule / numpy
1. Connect to the server to receive a system of 28 linear equations
2. Each unknown `x_i` represents an ASCII character of the flag content
3. Parse the equations to extract coefficient matrix A and result vector b
4. Solve the system `Ax = b` using linear algebra (numpy.linalg.solve)
5. Round solutions to integers and convert to ASCII characters

### Flag
> `pascalCTF{0h_My_G0DD0_too_much_m4th_:O}`
