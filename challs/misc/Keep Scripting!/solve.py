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

def solve_wires(data, bomb_info):
    colors = [c.lower() for c in data['colors']]
    amount = len(colors)
    serial_odd = bomb_info['serial_last_odd']
    if amount == 3:
        if 'red' not in colors: return "2"
        elif colors[-1] == 'white': return str(amount)
        elif colors.count('blue') > 1:
            for i in range(amount - 1, -1, -1):
                if colors[i] == 'blue': return str(i + 1)
        return str(amount)
    elif amount == 4:
        if colors.count('red') > 1 and serial_odd:
            for i in range(amount - 1, -1, -1):
                if colors[i] == 'red': return str(i + 1)
        elif colors[-1] == 'yellow' and 'red' not in colors: return "1"
        elif colors.count('blue') == 1: return "1"
        elif colors.count('yellow') > 1: return str(amount)
        return "2"
    elif amount == 5:
        if colors[-1] == 'black' and serial_odd: return "4"
        elif colors.count('red') == 1 and colors.count('yellow') > 1: return "1"
        elif 'black' not in colors: return "2"
        return "1"
    elif amount == 6:
        if 'yellow' not in colors and serial_odd: return "3"
        elif colors.count('yellow') == 1 and colors.count('white') > 1: return "4"
        elif 'red' not in colors: return str(amount)
        return "4"
    return "1"

def solve_button(data, bomb_info):
    color = data.get('color', '').lower()
    text = data.get('text', '').lower()
    batteries = bomb_info['batteries']
    label = bomb_info.get('label', '').upper()
    if color == 'blue' and text == 'abort': return '2'
    if batteries > 1 and text == 'detonate': return '1'
    if color == 'white' and label == 'CAR': return '2'
    if batteries > 2 and label == 'FRK': return '1'
    if color == 'yellow': return '2'
    if color == 'red' and text == 'hold': return '1'
    return '2'

KEYPAD_COLUMNS = [
    ['Ϙ', 'Ѧ', 'ƛ', 'Ϟ', 'Ѭ', 'ϗ', 'Ͽ'],
    ['Ӭ', 'Ϙ', 'Ͽ', 'Ҩ', '☆', 'ϗ', '¿'],
    ['©', 'Ѽ', 'Ҩ', 'Җ', 'Ԇ', 'ƛ', '☆'],
    ['б', '¶', 'ƀ', 'Ѭ', 'Җ', '¿', 'ټ'],
    ['ψ', 'ټ', 'ƀ', 'Ͼ', '¶', 'Ѯ', '★'],
    ['б', 'Ӭ', '҂', 'æ', 'ψ', 'Ҋ', 'Ω'],
]

def solve_keypad(data, bomb_info):
    symbols = data['symbols']
    for col in KEYPAD_COLUMNS:
        if all(s in col for s in symbols):
            positions = []
            for col_sym in col:
                for i, s in enumerate(symbols):
                    if s == col_sym and (i + 1) not in positions:
                        positions.append(i + 1)
                        break
            if len(positions) == 4:
                return ' '.join(map(str, positions))
    return '1 2 3 4'

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
    sequence = data.get('sequence', data.get('flashes', []))
    strikes = min(data.get('strikes', 0), 2)
    has_vowel = bomb_info['serial_has_vowel']
    mapping = SIMON_VOWEL[strikes] if has_vowel else SIMON_NO_VOWEL[strikes]
    return ' '.join(mapping[f.lower()] for f in sequence)

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
    display = data.get('display', '').lower().strip()
    buttons = [b.lower().strip() for b in data.get('buttons', [])]
    position = WHOS_STEP1.get(display, "middle left")
    pos_map = {"top left": 0, "top right": 1, "middle left": 2, "middle right": 3, "bottom left": 4, "bottom right": 5}
    idx = pos_map.get(position, 2)
    if idx >= len(buttons): idx = 0
    button_label = buttons[idx]
    order = WHOS_STEP2.get(button_label, [])
    for word in order:
        if word in buttons: return word
    return buttons[0] if buttons else ""

memory_state = {'positions': [], 'labels': []}

def solve_memory(data, bomb_info):
    global memory_state
    stage = data.get('stage', 1)
    display = data.get('display', 1)
    buttons = data.get('buttons', [1, 2, 3, 4])
    if stage == 1:
        memory_state = {'positions': [], 'labels': []}
        pos = {1: 2, 2: 2, 3: 3, 4: 4}[display]
    elif stage == 2:
        if display == 1: pos = buttons.index(4) + 1
        elif display in [2, 4]: pos = memory_state['positions'][0]
        else: pos = 1
    elif stage == 3:
        if display == 1: pos = buttons.index(memory_state['labels'][1]) + 1
        elif display == 2: pos = buttons.index(memory_state['labels'][0]) + 1
        elif display == 3: pos = 3
        else: pos = buttons.index(4) + 1
    elif stage == 4:
        if display == 1: pos = memory_state['positions'][0]
        elif display == 2: pos = 1
        else: pos = memory_state['positions'][1]
    elif stage == 5:
        label_idx = {1: 0, 2: 1, 3: 3, 4: 2}[display]
        pos = buttons.index(memory_state['labels'][label_idx]) + 1
    else:
        pos = 1
    memory_state['positions'].append(pos)
    memory_state['labels'].append(buttons[pos - 1])
    return str(pos)

MORSE_WORDS = {
    'shell': '3.505', 'halls': '3.515', 'slick': '3.522', 'trick': '3.532',
    'boxes': '3.535', 'leaks': '3.542', 'strobe': '3.545', 'bistro': '3.552',
    'flick': '3.555', 'bombs': '3.565', 'break': '3.572', 'brick': '3.575',
    'steak': '3.582', 'sting': '3.592', 'vector': '3.595', 'beats': '3.600',
}

def solve_morse_code(data, bomb_info):
    return MORSE_WORDS.get(data.get('word', '').lower(), '3.500')

def solve_complicated_wires(data, bomb_info):
    serial_even = not bomb_info['serial_last_odd']
    has_parallel = bomb_info['has_parallel']
    batteries = bomb_info['batteries']
    amount = data.get('amount', 0)
    colors = data.get('colors', [])
    leds = data.get('leds', [])
    stars = data.get('stars', [])
    decisions = []
    for i in range(amount):
        color_str = colors[i].lower() if i < len(colors) else ''
        has_red = 'red' in color_str
        has_blue = 'blue' in color_str
        has_star = stars[i] if i < len(stars) else False
        led_on = leds[i] if i < len(leds) else False
        key = (has_red, has_blue, has_star, led_on)
        rules = {
            (False, False, False, False): True,
            (True, False, False, False): serial_even,
            (False, True, False, False): serial_even,
            (False, False, True, False): True,
            (False, False, False, True): False,
            (True, True, False, False): serial_even,
            (True, False, True, False): True,
            (True, False, False, True): batteries >= 2,
            (False, True, True, False): False,
            (False, True, False, True): has_parallel,
            (False, False, True, True): batteries >= 2,
            (True, True, True, False): has_parallel,
            (True, True, False, True): serial_even,
            (True, False, True, True): batteries >= 2,
            (False, True, True, True): has_parallel,
            (True, True, True, True): False,
        }
        decisions.append('cut' if rules.get(key, False) else 'skip')
    return decisions

wire_sequence_counts = {'red': 0, 'blue': 0, 'black': 0}
WIRE_SEQ = {
    'red': ['C', 'B', 'A', 'AC', 'B', 'AC', 'ABC', 'AB', 'B'],
    'blue': ['B', 'AC', 'B', 'A', 'B', 'BC', 'C', 'AC', 'A'],
    'black': ['ABC', 'AC', 'B', 'AC', 'B', 'BC', 'AB', 'C', 'C'],
}

def solve_wire_sequences(data, bomb_info):
    global wire_sequence_counts
    if data.get('reset', False):
        wire_sequence_counts = {'red': 0, 'blue': 0, 'black': 0}
    cuts = []
    for wire in data.get('wires', []):
        color = wire.get('color', '').lower()
        dest = wire.get('destination', '').upper()
        count = wire_sequence_counts.get(color, 0)
        valid = WIRE_SEQ.get(color, [''])[count] if count < 9 else ''
        if dest in valid:
            cuts.append(str(wire.get('position', wire.get('index', 0)) + 1))
        wire_sequence_counts[color] = count + 1
    return ' '.join(cuts) if cuts else 'none'

PASSWORDS = ['about', 'after', 'again', 'below', 'could', 'every', 'first', 'found',
             'great', 'house', 'large', 'learn', 'never', 'other', 'place', 'plant',
             'point', 'right', 'small', 'sound', 'spell', 'still', 'study', 'their',
             'there', 'these', 'thing', 'think', 'three', 'water', 'where', 'which',
             'world', 'would', 'write']

def solve_password(data, bomb_info):
    columns = data.get('columns', [])
    for word in PASSWORDS:
        if all(word[i] in [c.lower() for c in columns[i]] for i in range(min(len(word), len(columns)))):
            return word
    return 'about'

def solve_module(module_type, data, bomb_info):
    mt = module_type.lower().strip()
    if 'wire' in mt and 'sequence' in mt:
        return solve_wire_sequences(data, bomb_info)
    elif 'complicated' in mt:
        return ('complicated', solve_complicated_wires(data, bomb_info))
    elif 'wire' in mt:
        return solve_wires(data, bomb_info)
    elif 'button' in mt:
        return solve_button(data, bomb_info)
    elif 'keypad' in mt:
        return solve_keypad(data, bomb_info)
    elif 'simon' in mt:
        return solve_simon_says(data, bomb_info)
    elif 'who' in mt or 'first' in mt:
        return solve_whos_on_first(data, bomb_info)
    elif 'memory' in mt:
        return solve_memory(data, bomb_info)
    elif 'morse' in mt:
        return solve_morse_code(data, bomb_info)
    elif 'password' in mt:
        return solve_password(data, bomb_info)
    return "1"

def main():
    r = remote(HOST, PORT)

    data = r.recvuntil(b'press Enter):').decode()
    bomb_info = parse_bomb_info(data)
    print(f"[+] s={bomb_info.get('serial')}, b={bomb_info.get('batteries')}, l={bomb_info.get('label')}, p={bomb_info.get('has_parallel')}")

    r.sendline(b'')

    for module_num in range(1, 101):
        try:
            try:
                data = r.recvuntil([b'Choose action', b'Sequence (e.g.', b'Wire 1:', b'wire number):',
                                   b'Solution:', b'word:', b'Frequency:', b'flag', b'ptm{',
                                   b"TIME'S UP", b'BOOM!'], timeout=3).decode()
            except Exception as recv_err:
                # Try to get any remaining data
                try:
                    data = r.recv(timeout=1).decode()
                    print(f"Timeout at {module_num}, got: {data[:300]}")
                except:
                    print(f"Timeout after {module_num} modules, no more data")
                print(f"Recv error: {recv_err}")
                break

            # Check for actual game over
            if "TIME'S UP" in data.upper() or 'BOOM!' in data or '💥' in data:
                print(f"GAME OVER after {module_num-1} modules!")
                print(data[-500:])
                break

            if 'flag' in data.lower() or 'ptm{' in data.lower():
                print("\n=== FLAG ===")
                print(data)
                try:
                    print(r.recvall(timeout=2).decode())
                except:
                    pass
                break

            type_match = re.search(r'Module:\s*(\w+(?:\s+\w+)*)', data)
            if not type_match:
                r.sendline(b'')
                continue

            module_type = type_match.group(1)
            data_match = re.search(r"Data:\s*(\{.*?\})", data, re.DOTALL)
            module_data = ast.literal_eval(data_match.group(1)) if data_match else {}

            answer = solve_module(module_type, module_data, bomb_info)

            if isinstance(answer, tuple) and answer[0] == 'complicated':
                decisions = answer[1]
                print(f"[{module_num}] CW -> {''.join('C' if d=='cut' else 'S' for d in decisions)}", flush=True)
                for decision in decisions:
                    r.sendline(decision.encode())
                response = r.recvuntil([b'press Enter', b'Wrong', b'BOOM', b'Correct'], timeout=5).decode()
            else:
                print(f"[{module_num}] {module_type[:8]} -> {answer}", flush=True)
                r.sendline(answer.encode())
                # For button with hold, we might need to provide release digit
                if 'button' in module_type.lower() and answer == '2':
                    # After choosing hold, server might ask for release digit based on strip color
                    strip_color = module_data.get('color_strip', '').lower()
                    if 'blue' in strip_color:
                        release_digit = '4'
                    elif 'yellow' in strip_color:
                        release_digit = '5'
                    else:
                        release_digit = '1'
                    try:
                        hold_response = r.recvuntil([b'digit', b'press Enter', b'Wrong', b'BOOM'], timeout=3).decode()
                        if 'digit' in hold_response.lower():
                            r.sendline(release_digit.encode())
                    except:
                        pass
                response = r.recvuntil([b'press Enter', b'Wrong', b'BOOM', b'Correct'], timeout=5).decode()

            if 'Wrong' in response or 'BOOM!' in response:
                print(f"  WRONG at {module_num}! {response[-300:]}")
                break

            if 'press Enter' in response:
                r.sendline(b'')
            else:
                print(f"  No 'press Enter' in response ({len(response)} bytes)")

        except EOFError:
            print(f"Connection closed after {module_num} modules")
            # Try to get any remaining data for flag
            try:
                remaining = r.recv(timeout=2)
                print(f"Remaining data: {remaining.decode()}")
            except:
                pass
            break
        except Exception as e:
            print(f"Error after {module_num} modules: {e}")
            import traceback
            traceback.print_exc()
            break

    r.close()

if __name__ == '__main__':
    main()
