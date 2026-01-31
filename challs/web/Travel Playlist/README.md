# Travel Playlist

## Description
> *Nel mezzo del cammin di nostra vita*
> *mi ritrovai per una selva oscura,*
> *ché la diritta via era smarrita.*
>
> *The flag can be found here `/app/flag.txt`*

**URL:** https://travel.ctf.pascalctf.it

## Solution
**TL;DR**: Path traversal or LFI to read /app/flag.txt
1. Web app has API endpoint `/api/get_json` that reads files from `static/` directory
2. API accepts POST with JSON `{"index": N}` to read `static/N` files
3. Error messages reveal path structure: `static/{index}`
4. Path traversal attempts (`../`) are filtered/blocked
5. **Status: UNSOLVED** - Need to bypass path sanitization

### Findings
- API requires `Content-Type: application/json`
- Error on `{"index": "."}` shows: `[Errno 21] Is a directory: 'static/.'`
- Basic path traversal returns "File not found" (sanitized)
- Flag location: `/app/flag.txt`

### Flag
> `UNSOLVED - Path traversal blocked`
