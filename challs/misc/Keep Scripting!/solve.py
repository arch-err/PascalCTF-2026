#!/usr/bin/env python3
import socket
import re
import ast

HOST = 'scripting.ctf.pascalctf.it'
PORT = 6004

def recv_until(sock, until):
    """Receive data until a specific string is found"""
    data = b''
    while until.encode() not in data:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
    return data.decode(errors='ignore')

def parse_bomb_info(data):
    """Parse bomb configuration from initial output"""
    info = {}

    serial_match = re.search(r'Serial Number:\s*(\w+)', data)
    if serial_match:
        info['serial'] = serial_match.group(1)
        info['serial_last_odd'] = int(info['serial'][-1]) % 2 == 1
        info['serial_has_vowel'] = any(c in info['serial'].upper() for c in 'AEIOU')

    batteries_match = re.search(r'Batteries:\s*(\d+)', data)
    if batteries_match:
        info['batteries'] = int(batteries_match.group(1))

    label_match = re.search(r'Label:\s*(\w+)', data)
    if label_match:
        info['label'] = label_match.group(1)

    ports_match = re.search(r'Ports:\s*(.*)', data)
    if ports_match:
        ports_str = ports_match.group(1).strip().lower()
        info['ports'] = [p.strip() for p in ports_str.split(',') if p.strip()]
        info['has_parallel'] = 'parallel' in ports_str
    else:
        info['ports'] = []
        info['has_parallel'] = False

    return info

def solve_wires(data, bomb_info):
    """Solve the Wires module"""
    colors = data['colors']
    amount = data['amount']
    serial_odd = bomb_info['serial_last_odd']

    if amount == 3:
        if 'Red' not in colors:
            return 2
        elif colors[-1] == 'White':
            return amount
        elif colors.count('Blue') > 1:
            # Find last blue wire
            for i in range(amount - 1, -1, -1):
                if colors[i] == 'Blue':
                    return i + 1
        else:
            return amount

    elif amount == 4:
        if colors.count('Red') > 1 and serial_odd:
            for i in range(amount - 1, -1, -1):
                if colors[i] == 'Red':
                    return i + 1
        elif colors[-1] == 'Yellow' and 'Red' not in colors:
            return 1
        elif colors.count('Blue') == 1:
            return 1
        elif colors.count('Yellow') > 1:
            return amount
        else:
            return 2

    elif amount == 5:
        if colors[-1] == 'Black' and serial_odd:
            return 4
        elif colors.count('Red') == 1 and colors.count('Yellow') > 1:
            return 1
        elif 'Black' not in colors:
            return 2
        else:
            return 1

    elif amount == 6:
        if 'Yellow' not in colors and serial_odd:
            return 3
        elif colors.count('Yellow') == 1 and colors.count('White') > 1:
            return 4
        elif 'Red' not in colors:
            return amount
        else:
            return 4

    return 1

def solve_button(data, bomb_info):
    """Solve the Button module"""
    color = data['color'].lower()
    text = data['text'].lower()
    batteries = bomb_info['batteries']
    label = bomb_info.get('label', '').upper()

    # Rule 1: Blue button saying "Abort" -> hold
    if color == 'blue' and text == 'abort':
        return 'hold'

    # Rule 2: More than 1 battery and button says "Detonate" -> press
    if batteries > 1 and text == 'detonate':
        return 'press'

    # Rule 3: White button and lit indicator CAR -> hold
    if color == 'white' and label == 'CAR':
        return 'hold'

    # Rule 4: More than 2 batteries and lit indicator FRK -> press
    if batteries > 2 and label == 'FRK':
        return 'press'

    # Rule 5: Yellow button -> hold
    if color == 'yellow':
        return 'hold'

    # Rule 6: Red button saying "Hold" -> press
    if color == 'red' and text == 'hold':
        return 'press'

    # Rule 7: Otherwise -> hold
    return 'hold'

# Keypad symbol columns (from manual)
KEYPAD_COLUMNS = [
    ['Q', 'A', 'lambda', 'lightning', 'kitty', 'h', 'c-back'],  # Column 1
    ['e-dots', 'Q', 'c-back', 'at', 'star-outline', 'h', 'question'],  # Column 2
    ['copyright', 'pumpkin', 'at', 'zh', 'not-equal', 'ae', 'star-outline'],  # Column 3
    ['six', 'paragraph', 'bt', 'kitty', 'zh', 'question', 'smiley'],  # Column 4
    ['psi', 'smiley', 'bt', 'c', 'paragraph', 'dragon', 'star'],  # Column 5
    ['six', 'e-dots', 'not-equal', 'ae', 'psi', 'n-tilde', 'omega'],  # Column 6
]

def solve_keypad(data, bomb_info):
    """Solve the Keypad module"""
    symbols = data['symbols']

    # Find which column contains all 4 symbols
    for col in KEYPAD_COLUMNS:
        if all(s in col for s in symbols):
            # Return symbols in order they appear in column
            ordered = [s for s in col if s in symbols]
            return ','.join(ordered)

    # Fallback - return as-is
    return ','.join(symbols)

# Simon Says color mappings
SIMON_VOWEL = {
    0: {'red': 'blue', 'blue': 'red', 'green': 'yellow', 'yellow': 'green'},
    1: {'red': 'yellow', 'blue': 'green', 'green': 'blue', 'yellow': 'red'},
    2: {'red': 'green', 'blue': 'red', 'green': 'yellow', 'yellow': 'blue'},
}

SIMON_NO_VOWEL = {
    0: {'red': 'blue', 'blue': 'yellow', 'green': 'green', 'yellow': 'red'},
    1: {'red': 'red', 'blue': 'blue', 'green': 'yellow', 'yellow': 'green'},
    2: {'red': 'yellow', 'blue': 'green', 'green': 'blue', 'yellow': 'red'},
}

def solve_simon_says(data, bomb_info):
    """Solve Simon Says module"""
    sequence = data.get('sequence', data.get('flashes', []))
    strikes = data.get('strikes', 0)
    has_vowel = bomb_info['serial_has_vowel']

    mapping = SIMON_VOWEL[strikes] if has_vowel else SIMON_NO_VOWEL[strikes]

    result = []
    for flash in sequence:
        result.append(mapping[flash.lower()])

    return ','.join(result)

# Who's on First lookup tables
WHOS_STEP1 = {
    "": "bottom left", "blank": "middle right", "c": "top right",
    "cee": "bottom right", "display": "bottom right", "first": "top right",
    "hold on": "bottom right", "lead": "bottom right", "led": "middle left",
    "leed": "bottom left", "no": "bottom right", "nothing": "middle left",
    "okay": "top right", "read": "middle right", "red": "middle right",
    "reed": "bottom left", "says": "bottom right", "see": "bottom right",
    "their": "middle right", "there": "bottom right", "they are": "middle left",
    "they're": "bottom left", "ur": "top left", "yes": "middle left",
    "you": "middle right", "you are": "bottom right", "you're": "middle right",
    "your": "middle right"
}

WHOS_STEP2 = {
    "ready": ["yes", "okay", "what", "middle", "left", "press", "right", "blank", "ready", "no", "first", "uhhh", "nothing", "wait"],
    "first": ["left", "okay", "yes", "middle", "no", "right", "nothing", "uhhh", "wait", "ready", "blank", "what", "press", "first"],
    "no": ["blank", "uhhh", "wait", "first", "what", "ready", "right", "yes", "nothing", "left", "press", "okay", "no", "middle"],
    "blank": ["wait", "right", "okay", "middle", "blank", "press", "ready", "nothing", "no", "what", "left", "uhhh", "yes", "first"],
    "nothing": ["uhhh", "right", "okay", "middle", "yes", "blank", "no", "press", "left", "what", "wait", "first", "nothing", "ready"],
    "yes": ["okay", "right", "uhhh", "middle", "first", "what", "press", "ready", "nothing", "yes", "left", "blank", "no", "wait"],
    "what": ["uhhh", "what", "left", "nothing", "ready", "blank", "middle", "no", "okay", "first", "wait", "yes", "press", "right"],
    "uhhh": ["ready", "nothing", "left", "what", "okay", "yes", "right", "no", "press", "blank", "uhhh", "middle", "wait", "first"],
    "left": ["right", "left", "first", "no", "middle", "yes", "blank", "what", "uhhh", "wait", "press", "ready", "okay", "nothing"],
    "right": ["yes", "nothing", "ready", "press", "no", "wait", "what", "right", "middle", "left", "uhhh", "blank", "okay", "first"],
    "middle": ["blank", "ready", "okay", "what", "nothing", "press", "no", "wait", "left", "middle", "right", "first", "uhhh", "yes"],
    "okay": ["middle", "no", "first", "yes", "uhhh", "nothing", "wait", "okay", "left", "ready", "blank", "press", "what", "right"],
    "wait": ["uhhh", "no", "blank", "okay", "yes", "left", "first", "press", "what", "wait", "nothing", "ready", "right", "middle"],
    "press": ["right", "middle", "yes", "ready", "press", "okay", "nothing", "uhhh", "blank", "left", "first", "what", "no", "wait"],
    "you": ["sure", "you are", "your", "you're", "next", "uh huh", "ur", "hold", "what?", "you", "uh uh", "like", "done", "u"],
    "you are": ["your", "next", "like", "uh huh", "what?", "done", "uh uh", "hold", "you", "u", "you're", "sure", "ur", "you are"],
    "your": ["uh uh", "you are", "uh huh", "your", "next", "ur", "sure", "u", "you're", "you", "what?", "hold", "like", "done"],
    "you're": ["you", "you're", "ur", "next", "uh uh", "you are", "u", "your", "what?", "uh huh", "sure", "done", "like", "hold"],
    "ur": ["done", "u", "ur", "uh huh", "what?", "sure", "your", "hold", "you're", "like", "next", "uh uh", "you are", "you"],
    "u": ["uh huh", "sure", "next", "what?", "you're", "ur", "uh uh", "done", "u", "you", "like", "hold", "you are", "your"],
    "uh huh": ["uh huh", "your", "you are", "you", "done", "hold", "uh uh", "next", "sure", "like", "you're", "ur", "u", "what?"],
    "uh uh": ["ur", "u", "you are", "you're", "next", "uh uh", "done", "you", "uh huh", "like", "your", "sure", "hold", "what?"],
    "what?": ["you", "hold", "you're", "your", "u", "done", "uh uh", "like", "you are", "uh huh", "ur", "next", "what?", "sure"],
    "done": ["sure", "uh huh", "next", "what?", "your", "ur", "you're", "hold", "like", "you", "u", "you are", "uh uh", "done"],
    "next": ["what?", "uh huh", "uh uh", "your", "hold", "sure", "next", "like", "done", "you are", "ur", "you're", "u", "you"],
    "hold": ["you are", "u", "done", "uh uh", "you", "ur", "sure", "what?", "you're", "next", "hold", "uh huh", "your", "like"],
    "sure": ["you are", "done", "like", "you're", "you", "hold", "uh huh", "ur", "sure", "u", "what?", "next", "your", "uh uh"],
    "like": ["you're", "next", "u", "ur", "hold", "done", "uh uh", "what?", "uh huh", "you", "like", "sure", "you are", "your"],
}

def solve_whos_on_first(data, bomb_info):
    """Solve Who's on First module"""
    display = data.get('display', '').lower().strip()
    buttons = [b.lower().strip() for b in data.get('buttons', [])]

    # Step 1: Find which button to read based on display
    position = WHOS_STEP1.get(display, "middle left")

    # Map position to index
    pos_map = {
        "top left": 0, "top right": 1,
        "middle left": 2, "middle right": 3,
        "bottom left": 4, "bottom right": 5
    }

    idx = pos_map.get(position, 2)
    if idx >= len(buttons):
        idx = 0

    button_label = buttons[idx]

    # Step 2: Find first button that appears in the list
    order = WHOS_STEP2.get(button_label, [])

    for word in order:
        if word in buttons:
            return word

    return buttons[0] if buttons else ""

# Memory module state
memory_state = {'positions': [], 'labels': []}

def solve_memory(data, bomb_info):
    """Solve Memory module"""
    global memory_state

    stage = data.get('stage', 1)
    display = data.get('display', 1)
    buttons = data.get('buttons', [1, 2, 3, 4])

    if stage == 1:
        memory_state = {'positions': [], 'labels': []}
        if display == 1:
            pos = 2
        elif display == 2:
            pos = 2
        elif display == 3:
            pos = 3
        else:  # 4
            pos = 4

    elif stage == 2:
        if display == 1:
            # Press button labeled "4"
            pos = buttons.index(4) + 1
        elif display == 2:
            pos = memory_state['positions'][0]
        elif display == 3:
            pos = 1
        else:  # 4
            pos = memory_state['positions'][0]

    elif stage == 3:
        if display == 1:
            # Same label as stage 2
            label = memory_state['labels'][1]
            pos = buttons.index(label) + 1
        elif display == 2:
            # Same label as stage 1
            label = memory_state['labels'][0]
            pos = buttons.index(label) + 1
        elif display == 3:
            pos = 3
        else:  # 4
            pos = buttons.index(4) + 1

    elif stage == 4:
        if display == 1:
            pos = memory_state['positions'][0]
        elif display == 2:
            pos = 1
        elif display == 3:
            pos = memory_state['positions'][1]
        else:  # 4
            pos = memory_state['positions'][1]

    elif stage == 5:
        if display == 1:
            label = memory_state['labels'][0]
            pos = buttons.index(label) + 1
        elif display == 2:
            label = memory_state['labels'][1]
            pos = buttons.index(label) + 1
        elif display == 3:
            label = memory_state['labels'][3]
            pos = buttons.index(label) + 1
        else:  # 4
            label = memory_state['labels'][2]
            pos = buttons.index(label) + 1
    else:
        pos = 1

    # Record position and label for future stages
    memory_state['positions'].append(pos)
    memory_state['labels'].append(buttons[pos - 1])

    return str(pos)

# Morse code lookup
MORSE_WORDS = {
    'shell': '3.505',
    'halls': '3.515',
    'slick': '3.522',
    'trick': '3.532',
    'boxes': '3.535',
    'leaks': '3.542',
    'strobe': '3.545',
    'bistro': '3.552',
    'flick': '3.555',
    'bombs': '3.565',
    'break': '3.572',
    'brick': '3.575',
    'steak': '3.582',
    'sting': '3.592',
    'vector': '3.595',
    'beats': '3.600',
}

def solve_morse_code(data, bomb_info):
    """Solve Morse Code module"""
    word = data.get('word', '').lower()
    freq = MORSE_WORDS.get(word, '3.500')
    return freq

def solve_complicated_wires(data, bomb_info):
    """Solve Complicated Wires module"""
    wires = data.get('wires', [])
    serial_even = not bomb_info['serial_last_odd']
    has_parallel = bomb_info['has_parallel']
    batteries = bomb_info['batteries']

    cuts = []
    for i, wire in enumerate(wires):
        has_red = 'red' in wire.get('colors', []) or wire.get('red', False)
        has_blue = 'blue' in wire.get('colors', []) or wire.get('blue', False)
        has_star = wire.get('star', False)
        led_on = wire.get('led', False)

        # Determine action from Venn diagram
        # No properties: C (cut)
        # Red only: S (serial even)
        # Blue only: S (serial even)
        # Star only: C (cut)
        # LED only: D (don't cut)
        # Red+Blue: S (serial even)
        # Red+Star: C (cut)
        # Red+LED: B (2+ batteries)
        # Blue+Star: D (don't cut)
        # Blue+LED: P (parallel port)
        # Star+LED: B (2+ batteries)
        # Red+Blue+Star: P (parallel port)
        # Red+Blue+LED: S (serial even)
        # Red+Star+LED: B (2+ batteries)
        # Blue+Star+LED: P (parallel port)
        # All four: D (don't cut)

        cut = False
        if not has_red and not has_blue and not has_star and not led_on:
            cut = True  # C
        elif has_red and not has_blue and not has_star and not led_on:
            cut = serial_even  # S
        elif not has_red and has_blue and not has_star and not led_on:
            cut = serial_even  # S
        elif not has_red and not has_blue and has_star and not led_on:
            cut = True  # C
        elif not has_red and not has_blue and not has_star and led_on:
            cut = False  # D
        elif has_red and has_blue and not has_star and not led_on:
            cut = serial_even  # S
        elif has_red and not has_blue and has_star and not led_on:
            cut = True  # C
        elif has_red and not has_blue and not has_star and led_on:
            cut = batteries >= 2  # B
        elif not has_red and has_blue and has_star and not led_on:
            cut = False  # D
        elif not has_red and has_blue and not has_star and led_on:
            cut = has_parallel  # P
        elif not has_red and not has_blue and has_star and led_on:
            cut = batteries >= 2  # B
        elif has_red and has_blue and has_star and not led_on:
            cut = has_parallel  # P
        elif has_red and has_blue and not has_star and led_on:
            cut = serial_even  # S
        elif has_red and not has_blue and has_star and led_on:
            cut = batteries >= 2  # B
        elif not has_red and has_blue and has_star and led_on:
            cut = has_parallel  # P
        elif has_red and has_blue and has_star and led_on:
            cut = False  # D

        if cut:
            cuts.append(str(i + 1))

    return ','.join(cuts) if cuts else 'none'

# Wire sequences tracking
wire_sequence_counts = {'red': 0, 'blue': 0, 'black': 0}

WIRE_SEQ_RED = ['C', 'B', 'A', 'AC', 'B', 'AC', 'ABC', 'AB', 'B']
WIRE_SEQ_BLUE = ['B', 'AC', 'B', 'A', 'B', 'BC', 'C', 'AC', 'A']
WIRE_SEQ_BLACK = ['ABC', 'AC', 'B', 'AC', 'B', 'BC', 'AB', 'C', 'C']

def solve_wire_sequences(data, bomb_info):
    """Solve Wire Sequences module"""
    global wire_sequence_counts

    if data.get('reset', False):
        wire_sequence_counts = {'red': 0, 'blue': 0, 'black': 0}

    wires = data.get('wires', [])
    cuts = []

    for wire in wires:
        color = wire.get('color', '').lower()
        dest = wire.get('destination', '').upper()

        count = wire_sequence_counts.get(color, 0)

        if color == 'red':
            valid = WIRE_SEQ_RED[count] if count < 9 else ''
        elif color == 'blue':
            valid = WIRE_SEQ_BLUE[count] if count < 9 else ''
        elif color == 'black':
            valid = WIRE_SEQ_BLACK[count] if count < 9 else ''
        else:
            valid = ''

        if dest in valid:
            cuts.append(str(wire.get('position', wire.get('index', 0)) + 1))

        wire_sequence_counts[color] = count + 1

    return ','.join(cuts) if cuts else 'none'

# Maze definitions (from manual)
MAZES = [
    # Maze 1: markers at (0,1) and (5,2)
    {'markers': [(0,1), (5,2)]},
    # Maze 2: markers at (4,1) and (1,3)]
    {'markers': [(4,1), (1,3)]},
    # ... etc
]

def solve_maze(data, bomb_info):
    """Solve Maze module - returns direction sequence"""
    # This would need BFS/pathfinding, simplified here
    return data.get('solution', 'up')

# Password word list
PASSWORDS = [
    'about', 'after', 'again', 'below', 'could',
    'every', 'first', 'found', 'great', 'house',
    'large', 'learn', 'never', 'other', 'place',
    'plant', 'point', 'right', 'small', 'sound',
    'spell', 'still', 'study', 'their', 'there',
    'these', 'thing', 'think', 'three', 'water',
    'where', 'which', 'world', 'would', 'write'
]

def solve_password(data, bomb_info):
    """Solve Password module"""
    columns = data.get('columns', [])

    for word in PASSWORDS:
        valid = True
        for i, col in enumerate(columns):
            if i < len(word) and word[i] not in [c.lower() for c in col]:
                valid = False
                break
        if valid:
            return word

    return 'about'

def solve_module(module_type, data, bomb_info):
    """Route to appropriate solver"""
    module_type = module_type.lower().strip()

    if 'wire' in module_type and 'sequence' in module_type:
        return solve_wire_sequences(data, bomb_info)
    elif 'wire' in module_type and 'complicated' in module_type:
        return solve_complicated_wires(data, bomb_info)
    elif 'wire' in module_type:
        return solve_wires(data, bomb_info)
    elif 'button' in module_type:
        return solve_button(data, bomb_info)
    elif 'keypad' in module_type:
        return solve_keypad(data, bomb_info)
    elif 'simon' in module_type:
        return solve_simon_says(data, bomb_info)
    elif 'who' in module_type or 'first' in module_type:
        return solve_whos_on_first(data, bomb_info)
    elif 'memory' in module_type:
        return solve_memory(data, bomb_info)
    elif 'morse' in module_type:
        return solve_morse_code(data, bomb_info)
    elif 'maze' in module_type:
        return solve_maze(data, bomb_info)
    elif 'password' in module_type:
        return solve_password(data, bomb_info)
    else:
        print(f"Unknown module type: {module_type}")
        return "1"

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    sock.settimeout(30)

    # Get initial banner and bomb info
    data = recv_until(sock, 'press Enter):')
    print(data)

    bomb_info = parse_bomb_info(data)
    print(f"\n[+] Bomb Info: {bomb_info}")

    # Press enter to start
    sock.send(b'\n')

    for module_num in range(1, 101):
        try:
            # Receive module info
            data = recv_until(sock, ':')
            print(f"\n[Module {module_num}]")
            print(data[-500:] if len(data) > 500 else data)

            # Parse module type
            type_match = re.search(r'Module:\s*(\w+(?:\s+\w+)*)', data)
            if type_match:
                module_type = type_match.group(1)
            else:
                module_type = "unknown"

            # Parse data
            data_match = re.search(r"Data:\s*(\{.*?\})", data, re.DOTALL)
            if data_match:
                try:
                    module_data = ast.literal_eval(data_match.group(1))
                except:
                    module_data = {}
            else:
                module_data = {}

            print(f"[+] Type: {module_type}, Data: {module_data}")

            # Solve
            answer = solve_module(module_type, module_data, bomb_info)
            print(f"[+] Answer: {answer}")

            # Send answer
            sock.send(f"{answer}\n".encode())

            # Check for next module prompt or success
            response = recv_until(sock, ':')
            print(response[-300:] if len(response) > 300 else response)

            if 'flag' in response.lower() or 'ptm{' in response.lower() or 'congratulations' in response.lower():
                print("\n" + "="*50)
                print("FLAG FOUND!")
                print(response)
                break

            # Press enter for next module if needed
            if 'press Enter' in response:
                sock.send(b'\n')

        except Exception as e:
            print(f"Error on module {module_num}: {e}")
            import traceback
            traceback.print_exc()

    # Get any remaining output
    try:
        remaining = sock.recv(4096).decode()
        print(remaining)
    except:
        pass

    sock.close()

if __name__ == '__main__':
    main()
