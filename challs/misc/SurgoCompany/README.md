# SurgoCompany

> [!WARNING]
> This challenge was **not solved** during the competition.

## Description
> ***SurgoCompany™** has just launched a brand-new online Customer Service platform 🧩. The system is still under development, and you've been asked to test it 😈.*
>
> *Simply enter your email, describe your issue, and optionally upload a file related to your problem 🤨.*
>
> *The source code of the challenge is saved somewhere on the filesystem... and rumor has it that a file named flag.txt is hiding in that very same folder 😜.*
>
> *Can you find a way to read it?*

**Connection:** `nc surgobot.ctf.pascalctf.it 6005`

**URLs:**
- Email box: https://surgo.ctf.pascalctf.it
- Email account generator: https://surgoservice.ctf.pascalctf.it

**Files:** [src.py](./orig/src.py)

## Analysis

### Vulnerability
The `check_attachment()` function has a clear code execution vulnerability:
```python
def check_attachment(filepath):
    with open(filepath, "r") as f:
        content = f.read()
    try:
        exec(content)  # <-- Arbitrary code execution!
    except Exception as e:
        print("The attachment passed the security check.")
```

### Attack Flow
1. Generate email credentials at the service
2. Connect to nc service and provide email address
3. Receive support email from the system
4. Reply with a Python file attachment containing: `print(open("flag.txt").read())`
5. The server executes the attachment and should print the flag

### What We Tried
- Created solve scripts to automate the email flow ([solve/](./solve/))
- Payload: `print(open("flag.txt").read())`
- Attempted various email formats and attachment types
- The email exchange seemed to work but flag was not returned

### Unsolved Issues
- Unclear if the email routing was working correctly
- Possible issues with email timing/synchronization
- May need different payload or file path

## Solution
*Not solved during the competition.*

### Flag
> *Not solved*
