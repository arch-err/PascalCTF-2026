# Keep Scripting! - Full Writeup

## Challenge Overview

**Category:** Misc
**Connection:** `nc scripting.ctf.pascalctf.it 6004`
**Description:** Automate solving 100 KTANE (Keep Talking and Nobody Explodes) bomb modules in under 60 seconds.

## Initial Analysis

### Server Protocol

Upon connecting to the server, we receive bomb information:

```
╔═══════════════════════════════════════════════════════════════════╗
║                    BOMB DEFUSAL SIMULATOR                          ║
╚═══════════════════════════════════════════════════════════════════╝

📋 BOMB INFORMATION:
  Serial Number: 123456
  Batteries: 2
  Label: FRK
  Ports: Parallel, Serial

⏱️ You have 60 seconds to defuse 100 modules!
(press Enter):
```

After pressing Enter, modules are presented one at a time with their data in Python dict format:

```
🔧 Module: Wires
Data: {'amount': 5, 'colors': ['Red', 'Blue', 'White', 'Black', 'Yellow']}

📝 Enter your solution for Wires:
Which wire to cut (enter wire number):
```

### Key Observations

1. **Time limit:** 60 seconds for 100 modules = 0.6 seconds per module average
2. **Module types:** Wires, Button, Keypads, Complicated Wires, Simon Says, Who's on First, Memory, Morse Code, Wire Sequences, Passwords
3. **Interactive modules:** Complicated Wires requires individual cut/skip responses per wire; Button "hold" option requires a release digit
4. **Unicode symbols:** Keypad module uses Unicode characters that map to KTANE manual symbols

## Module Solving Logic

### 1. Wires Module

Based on wire count and colors, following KTANE manual rules:

**3 Wires:**
- No red wires → cut 2nd
- Last wire is white → cut last
- More than one blue → cut last blue
- Otherwise → cut last

**4 Wires:**
- More than one red AND serial odd → cut last red
- Last is yellow AND no red → cut 1st
- Exactly one blue → cut 1st
- More than one yellow → cut last
- Otherwise → cut 2nd

**5 Wires:**
- Last is black AND serial odd → cut 4th
- Exactly one red AND more than one yellow → cut 1st
- No black wires → cut 2nd
- Otherwise → cut 1st

**6 Wires:**
- No yellow AND serial odd → cut 3rd
- Exactly one yellow AND more than one white → cut 4th
- No red → cut last
- Otherwise → cut 4th

### 2. Button Module

**Initial decision (press=1, hold=2):**
- Blue button with "Abort" → hold
- More than 1 battery AND "Detonate" → press
- White button AND CAR indicator → hold
- More than 2 batteries AND FRK indicator → press
- Yellow button → hold
- Red button with "Hold" → press
- Otherwise → hold

**If holding, release when timer shows:**
- Blue strip → 4
- Yellow strip → 5
- Other → 1

### 3. Keypads Module

The server uses Unicode symbols that map to KTANE manual columns. Through sample collection, the correct mappings were determined:

```python
KEYPAD_COLUMNS = [
    ['Ϙ', 'Ѧ', 'ƛ', 'Ϟ', 'Ѭ', 'ϗ', 'Ͽ'],           # Column 1
    ['Ӭ', 'Ϙ', 'Ͽ', 'Ҩ', '☆', 'ϗ', '¿'],           # Column 2
    ['©', 'Ѽ', 'Ҩ', 'Җ', 'Ԇ', 'ƛ', '☆'],           # Column 3
    ['б', '¶', 'ƀ', 'Ѭ', 'Җ', '¿', 'ټ'],           # Column 4
    ['ψ', 'ټ', 'ƀ', 'Ͼ', '¶', 'Ѯ', '★'],           # Column 5
    ['б', 'Ӭ', '҂', 'æ', 'ψ', 'Ҋ', 'Ω'],           # Column 6
]
```

Find the column containing all 4 symbols, then return button positions in column order.

### 4. Complicated Wires Module

Each wire has properties: red, blue, star, LED. The decision table:

| Red | Blue | Star | LED | Action |
|-----|------|------|-----|--------|
| ❌ | ❌ | ❌ | ❌ | Cut |
| ✓ | ❌ | ❌ | ❌ | Serial even → Cut |
| ❌ | ✓ | ❌ | ❌ | Serial even → Cut |
| ❌ | ❌ | ✓ | ❌ | Cut |
| ❌ | ❌ | ❌ | ✓ | Don't cut |
| ✓ | ✓ | ❌ | ❌ | Serial even → Cut |
| ✓ | ❌ | ✓ | ❌ | Cut |
| ✓ | ❌ | ❌ | ✓ | 2+ batteries → Cut |
| ❌ | ✓ | ✓ | ❌ | Don't cut |
| ❌ | ✓ | ❌ | ✓ | Parallel port → Cut |
| ❌ | ❌ | ✓ | ✓ | 2+ batteries → Cut |
| ✓ | ✓ | ✓ | ❌ | Parallel port → Cut |
| ✓ | ✓ | ❌ | ✓ | Serial even → Cut |
| ✓ | ❌ | ✓ | ✓ | 2+ batteries → Cut |
| ❌ | ✓ | ✓ | ✓ | Parallel port → Cut |
| ✓ | ✓ | ✓ | ✓ | Don't cut |

Server expects interactive "cut" or "skip" for each wire.

### 5. Simon Says Module

Color mapping based on serial vowels and strikes:

**With vowel in serial:**
| Strikes | Red→ | Blue→ | Green→ | Yellow→ |
|---------|------|-------|--------|---------|
| 0 | Blue | Red | Yellow | Green |
| 1 | Yellow | Green | Blue | Red |
| 2 | Green | Red | Yellow | Blue |

**Without vowel:**
| Strikes | Red→ | Blue→ | Green→ | Yellow→ |
|---------|------|-------|--------|---------|
| 0 | Blue | Yellow | Green | Red |
| 1 | Red | Blue | Yellow | Green |
| 2 | Yellow | Green | Blue | Red |

### 6. Who's on First Module

**Step 1:** Map display word to button position:
```python
WHOS_STEP1 = {
    "": "bottom left", "blank": "middle right", "c": "top right",
    "yes": "middle left", "nothing": "middle left", "led": "middle left",
    # ... (full mapping in solution)
}
```

**Step 2:** Read the button at that position, then find first matching word from priority list.

### 7. Memory Module

Track positions and labels across 5 stages. Rules vary by stage and display number.

### 8. Morse Code Module

Word-to-frequency lookup:
```python
MORSE_WORDS = {
    'shell': '3.505', 'halls': '3.515', 'slick': '3.522', 'trick': '3.532',
    'boxes': '3.535', 'leaks': '3.542', 'strobe': '3.545', 'bistro': '3.552',
    'flick': '3.555', 'bombs': '3.565', 'break': '3.572', 'brick': '3.575',
    'steak': '3.582', 'sting': '3.592', 'vector': '3.595', 'beats': '3.600',
}
```

### 9. Wire Sequences Module

Track occurrence count per color. Cut if destination letter is in valid set for that occurrence:

```python
WIRE_SEQ = {
    'red':   ['C', 'B', 'A', 'AC', 'B', 'AC', 'ABC', 'AB', 'B'],
    'blue':  ['B', 'AC', 'B', 'A', 'B', 'BC', 'C', 'AC', 'A'],
    'black': ['ABC', 'AC', 'B', 'AC', 'B', 'BC', 'AB', 'C', 'C'],
}
```

### 10. Passwords Module

Match column letters against word list:
```python
PASSWORDS = ['about', 'after', 'again', 'below', 'could', 'every', 'first',
             'found', 'great', 'house', 'large', 'learn', 'never', 'other',
             'place', 'plant', 'point', 'right', 'small', 'sound', 'spell',
             'still', 'study', 'their', 'there', 'these', 'thing', 'think',
             'three', 'water', 'where', 'which', 'world', 'would', 'write']
```

## Implementation Challenges

### 1. Timing Issues
- Initial socket implementation had timeout issues causing missed modules
- Solution: Used pwntools for better socket handling with appropriate timeouts

### 2. Button Hold Interaction
- When choosing "hold" (option 2), server asks for release digit based on strip color
- Solution: After sending "2", wait for digit prompt and respond with appropriate digit

### 3. Complicated Wires Interaction
- Server expects individual "cut"/"skip" responses, not a combined answer
- Solution: Send each decision separately in a loop

### 4. Keypad Unicode Mapping
- Server uses Unicode characters that don't directly match KTANE manual images
- Solution: Collected samples with correct answers to reverse-engineer mappings

### 5. False BOOM Detection
- Word "timer" in Button prompt contains "TIME" substring
- Solution: Check for "TIME'S UP" specifically, not just "TIME"

## Final Solution

```python
#!/usr/bin/env python3
from pwn import *
import re
import ast

context.log_level = 'error'

HOST = 'scripting.ctf.pascalctf.it'
PORT = 6004

def parse_bomb_info(data):
    info = {}
    serial_match = re.search(r'Serial Number:\s*(\w+)', data)
    if serial_match:
        info['serial'] = serial_match.group(1)
        info['serial_last_odd'] = int(info['serial'][-1]) % 2 == 1
        info['serial_has_vowel'] = any(c in info['serial'].upper() for c in 'AEIOU')
    batteries_match = re.search(r'Batteries:\s*(\d+)', data)
    info['batteries'] = int(batteries_match.group(1)) if batteries_match else 0
    label_match = re.search(r'Label:\s*(\w+)', data)
    info['label'] = label_match.group(1).upper() if label_match else ''
    ports_match = re.search(r'Ports:\s*(.*)', data)
    if ports_match:
        info['has_parallel'] = 'parallel' in ports_match.group(1).lower()
    else:
        info['has_parallel'] = False
    return info

# ... (all module solving functions)

def main():
    r = remote(HOST, PORT)

    data = r.recvuntil(b'press Enter):').decode()
    bomb_info = parse_bomb_info(data)
    r.sendline(b'')

    for module_num in range(1, 101):
        # Receive module data
        data = r.recvuntil([b'Choose action', b'Sequence (e.g.',
                           b'Wire 1:', b'wire number):', ...]).decode()

        # Parse and solve module
        module_type = re.search(r'Module:\s*(\w+(?:\s+\w+)*)', data).group(1)
        module_data = ast.literal_eval(re.search(r"Data:\s*(\{.*?\})", data).group(1))
        answer = solve_module(module_type, module_data, bomb_info)

        # Send answer (handle special cases for CW and Button hold)
        r.sendline(answer.encode())

        # Wait for confirmation and press Enter
        response = r.recvuntil([b'press Enter', b'Wrong', b'BOOM']).decode()
        if 'press Enter' in response:
            r.sendline(b'')

    r.close()

if __name__ == '__main__':
    main()
```

## Execution

```bash
$ python3 solve.py
[+] s=875013, b=2, l=CAR, p=True
[1] CW -> SCSS
[2] CW -> SC
...
[99] Keypads -> 4 3 1 2
[100] CW -> SC
Connection closed after 100 modules
Remaining data: ✅ Module defused successfully!

🎉 CONGRATULATIONS! 🎉
🏆 You successfully defused the bomb!
🚀 Well done, here's your flag: pascalCTF{H0w_4r3_Y0u_s0_g0Od_4t_BOMBARE?}
```

## Flag

```
pascalCTF{H0w_4r3_Y0u_s0_g0Od_4t_BOMBARE?}
```
