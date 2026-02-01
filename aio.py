print("\033[38;5;88m" + r"""
                    ▓█████▄  ▄▄▄       ███▄ ▄███▓▓█████  ███▄    █
                    ▒██▀ ██▌▒████▄    ▓██▒▀█▀ ██▒▓█   ▀  ██ ▀█   █
                    ░██   █▌▒██  ▀█▄  ▓██    ▓██░▒███   ▓██  ▀█ ██▒
                    ░▓█▄   ▌░██▄▄▄▄██ ▒██    ▒██ ▒▓█  ▄ ▓██▒  ▐▌██▒
                    ░▒████▓  ▓█   ▓██▒▒██▒   ░██▒░▒████▒▒██░   ▓██░
                     ▒▒▓  ▒  ▒▒   ▓▒█░░ ▒░   ░  ░░░ ▒░ ░░ ▒░   ▒ ▒ 
                     ░ ▒  ▒   ▒   ▒▒ ░░  ░      ░ ░ ░  ░░ ░░   ░ ▒░
                     ░ ░  ░   ░   ▒   ░      ░      ░      ░   ░ ░ 
                       ░          ░  ░       ░      ░  ░         ░ 
                     ░                                             
""")

import requests
import secrets
import string
import sys
import os
import json
import re
from datetime import datetime
from typing import List, Optional, Tuple

BASE_URL = ""
DOMAIN = ""
API_KEY = ""
OUTPUT_BASE_DIR = "mailcow_output"

RESET = "\033[0m"
GRAY = "\033[1;90m"
RED = "\033[1;91m"
GREEN = "\033[1;92m"
YELLOW = "\033[1;93m"
BLUE = "\033[1;94m"
MAGENTA = "\033[1;95m"
CYAN = "\033[1;96m"
WHITE = "\033[1;97m"


def now():
    return datetime.now().strftime("%H:%M:%S")


def create_output_dir():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(OUTPUT_BASE_DIR, timestamp)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def scan_output_for_latest_number(prefix: str) -> int:
    max_num = 0
    
    if not os.path.exists(OUTPUT_BASE_DIR):
        return 0
    
    pattern = re.compile(rf'{re.escape(prefix)}_(\d+)@')
    
    for root, dirs, files in os.walk(OUTPUT_BASE_DIR):
        for file in files:
            if file.endswith('.txt'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        for line in f:
                            match = pattern.search(line)
                            if match:
                                max_num = max(max_num, int(match.group(1)))
                except:
                    pass
    
    return max_num


def generate_password(length=16):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    pwd = ''.join(secrets.choice(chars) for _ in range(length))
    
    if not any(c.isupper() for c in pwd):
        pwd = pwd[:-1] + secrets.choice(string.ascii_uppercase)
    if not any(c.islower() for c in pwd):
        pwd = pwd[:-2] + secrets.choice(string.ascii_lowercase) + pwd[-1]
    if not any(c.isdigit() for c in pwd):
        pwd = pwd[:-3] + secrets.choice(string.digits) + pwd[-2:]
    
    return pwd


class MailcowAPI:
    def __init__(self, api_key: str, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def create_mailbox(self, username: str, password: str) -> Tuple[bool, str]:
        url = f"{self.base_url}/api/v1/add/mailbox"
        
        data = {
            "local_part": username,
            "domain": DOMAIN,
            "name": username,
            "password": password,
            "password2": password,
            "quota": 1024,
            "active": 1
        }
        
        try:
            response = self.session.post(url, json=data, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if isinstance(result, list) and len(result) > 0:
                    if result[0].get('type') == 'success':
                        return True, "Created successfully"
                    else:
                        msg = result[0].get('msg', 'Unknown error')
                        return False, msg
                else:
                    return False, "Invalid response format"
            else:
                return False, f"HTTP {response.status_code}"
                
        except Exception as e:
            return False, str(e)
    
    def get_all_mailboxes(self) -> List[dict]:
        url = f"{self.base_url}/api/v1/get/mailbox/all"
        
        try:
            response = self.session.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'data' in data:
                return data['data']
            else:
                return []
                
        except Exception as e:
            print(f"{GRAY}{now()} » {RED}ERROR {WHITE}• Failed to fetch mailboxes ➔ {RED}{e}{RESET}")
            return []
    
    def delete_mailbox(self, mailbox: str) -> Tuple[bool, str]:
        url = f"{self.base_url}/api/v1/delete/mailbox"
        
        formats_to_try = [
            [mailbox],
            {"items": [mailbox]},
            mailbox,
            {"username": mailbox},
        ]
        
        for payload in formats_to_try:
            try:
                response = self.session.post(url, json=payload, headers=self.headers, timeout=30)
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    if isinstance(response_data, list):
                        for item in response_data:
                            if isinstance(item, dict) and item.get('type') == 'success':
                                return True, "Deleted successfully"
                    elif isinstance(response_data, dict) and response_data.get('type') == 'success':
                        return True, "Deleted successfully"
                        
            except Exception as e:
                continue
        
        return False, "All API formats failed"
    
    def change_password(self, email: str, new_password: str) -> Tuple[bool, str]:
        url = f"{self.base_url}/api/v1/edit/mailbox"
        
        payload = {
            "attr": {
                "password": new_password,
                "password2": new_password
            },
            "items": [email]
        }
        
        try:
            response = self.session.post(url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result and isinstance(result, list) and len(result) > 0:
                if result[0].get("type") == "success":
                    return True, "Password changed"
                else:
                    return False, result[0].get("msg", "Unknown error")
            return False, "Unexpected response"
            
        except Exception as e:
            return False, str(e)


def feature_create_emails(api: MailcowAPI):
    prefix = input(f"{CYAN}Enter email prefix: {RESET}").strip()
    if not prefix:
        print(f"{GRAY}{now()} » {RED}ERROR {WHITE}• No prefix provided{RESET}")
        return
    
    start_num = scan_output_for_latest_number(prefix) + 1
    print(f"{GRAY}{now()} » {YELLOW}NOTICE {WHITE}• Starting from {CYAN}{prefix}_{start_num}{RESET}")
    
    try:
        count = int(input(f"{CYAN}How many emails: {RESET}"))
        if count <= 0:
            print(f"{GRAY}{now()} » {RED}ERROR {WHITE}• Invalid count{RESET}")
            return
    except ValueError:
        print(f"{GRAY}{now()} » {RED}ERROR {WHITE}• Invalid number{RESET}")
        return
    
    output_dir = create_output_dir()
    output_file = os.path.join(output_dir, f"created_{prefix}.txt")
    log_file = os.path.join(output_dir, f"creation_log_{prefix}.json")
    
    print(f"{GRAY}{now()} » {BLUE}INFO {WHITE}• Creating {count} emails ➔ {output_dir}{RESET}")
    
    created = []
    failed = []
    log_entries = []
    
    for i in range(count):
        num = start_num + i
        username = f"{prefix}_{num}"
        email = f"{username}@{DOMAIN}"
        password = generate_password()
        
        success, message = api.create_mailbox(username, password)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "email": email,
            "status": "success" if success else "failed",
            "message": message
        }
        log_entries.append(log_entry)
        
        if success:
            created.append(f"{email}:{password}")
            with open(output_file, 'a') as f:
                f.write(f"{email}:{password}\n")
            print(f"{GRAY}{now()} » {GREEN}SUCCESS {WHITE}• Created ➔ {GREEN}{email}{RESET}")
        else:
            failed.append(f"{email} - {message}")
            print(f"{GRAY}{now()} » {RED}FAILED {WHITE}• {email} ➔ {RED}{message}{RESET}")
    
    with open(log_file, 'w') as f:
        json.dump(log_entries, f, indent=2)
    
    print(f"{GRAY}{now()} » {BLUE}SUMMARY {WHITE}• Total: {count} | Created: {GREEN}{len(created)}{WHITE} | Failed: {RED}{len(failed)}{RESET}")



def feature_list_emails(api: MailcowAPI):
    print(f"{GRAY}{now()} » {BLUE}INFO {WHITE}• Fetching mailboxes{RESET}")
    
    mailboxes = api.get_all_mailboxes()
    
    if not mailboxes:
        print(f"{GRAY}{now()} » {YELLOW}NOTICE {WHITE}• No mailboxes found{RESET}")
        return
    
    output_dir = create_output_dir()
    output_file = os.path.join(output_dir, "mailbox_list.txt")
    
    active_emails = []
    inactive_emails = []
    
    for mailbox in mailboxes:
        if isinstance(mailbox, dict) and 'username' in mailbox:
            email = mailbox['username']
            active = mailbox.get('active', '1')
            
            if active == '1' or active == 1:
                active_emails.append(email)
            else:
                inactive_emails.append(email)
    
    with open(output_file, 'w') as f:
        f.write("=== ACTIVE MAILBOXES ===\n")
        for email in sorted(active_emails):
            f.write(f"{email}\n")
        
        if inactive_emails:
            f.write("\n=== INACTIVE MAILBOXES ===\n")
            for email in sorted(inactive_emails):
                f.write(f"{email}\n")
    
    print(f"{GRAY}{now()} » {GREEN}ACTIVE {WHITE}• {len(active_emails)} mailboxes{RESET}")
    for email in sorted(active_emails)[:10]:
        print(f"{GRAY}{now()} » {WHITE}{email}{RESET}")
    if len(active_emails) > 10:
        print(f"{GRAY}{now()} » {YELLOW}NOTICE {WHITE}• {len(active_emails) - 10} more not shown{RESET}")
    
    if inactive_emails:
        print(f"{GRAY}{now()} » {YELLOW}INACTIVE {WHITE}• {len(inactive_emails)} mailboxes{RESET}")
    
    print(f"{GRAY}{now()} » {BLUE}INFO {WHITE}• Saved ➔ {output_file}{RESET}")



def feature_delete_emails(api: MailcowAPI):
    print(f"{WHITE}1.{RESET} Delete ALL mailboxes")
    print(f"{WHITE}2.{RESET} Delete by keyword")
    print(f"{WHITE}3.{RESET} Delete from file")
    
    mode = input(f"{CYAN}Select (1/2/3): {RESET}").strip()
    
    mailboxes_to_delete = []
    
    if mode == "1":
        confirm = input(f"{RED}Type 'YES' to delete ALL: {RESET}").strip()
        if confirm != "YES":
            print(f"{GRAY}{now()} » {YELLOW}NOTICE {WHITE}• Cancelled{RESET}")
            return
        
        all_mailboxes = api.get_all_mailboxes()
        mailboxes_to_delete = [mb['username'] for mb in all_mailboxes if 'username' in mb]
        
    elif mode == "2":
        keyword = input(f"{CYAN}Enter keyword: {RESET}").strip()
        if not keyword:
            print(f"{GRAY}{now()} » {RED}ERROR {WHITE}• No keyword{RESET}")
            return
        
        all_mailboxes = api.get_all_mailboxes()
        keyword_lower = keyword.lower()
        mailboxes_to_delete = [
            mb['username'] for mb in all_mailboxes 
            if 'username' in mb and keyword_lower in mb['username'].lower()
        ]
        
        print(f"{GRAY}{now()} » {YELLOW}NOTICE {WHITE}• Found {len(mailboxes_to_delete)} matching '{keyword}'{RESET}")
        
    elif mode == "3":
        file_path = input(f"{CYAN}Enter file path: {RESET}").strip()
        if not os.path.exists(file_path):
            print(f"{GRAY}{now()} » {RED}ERROR {WHITE}• File not found{RESET}")
            return
        
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and ':' in line:
                    email = line.split(':', 1)[0].strip()
                    mailboxes_to_delete.append(email)
                elif line and '@' in line:
                    mailboxes_to_delete.append(line)
    
    else:
        print(f"{GRAY}{now()} » {RED}ERROR {WHITE}• Invalid mode{RESET}")
        return
    
    if not mailboxes_to_delete:
        print(f"{GRAY}{now()} » {YELLOW}NOTICE {WHITE}• Nothing to delete{RESET}")
        return
    
    output_dir = create_output_dir()
    log_file = os.path.join(output_dir, "deletion_log.json")
    
    print(f"{GRAY}{now()} » {BLUE}INFO {WHITE}• Deleting {len(mailboxes_to_delete)} mailboxes{RESET}")
    
    deleted = []
    failed = []
    log_entries = []
    
    for email in mailboxes_to_delete:
        success, message = api.delete_mailbox(email)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "email": email,
            "status": "deleted" if success else "failed",
            "message": message
        }
        log_entries.append(log_entry)
        
        if success:
            deleted.append(email)
            print(f"{GRAY}{now()} » {GREEN}DELETED {WHITE}• {email}{RESET}")
        else:
            failed.append(f"{email} - {message}")
            print(f"{GRAY}{now()} » {RED}FAILED {WHITE}• {email} ➔ {RED}{message}{RESET}")
    
    with open(log_file, 'w') as f:
        json.dump(log_entries, f, indent=2)
    
    print(f"{GRAY}{now()} » {BLUE}SUMMARY {WHITE}• Total: {len(mailboxes_to_delete)} | Deleted: {GREEN}{len(deleted)}{WHITE} | Failed: {RED}{len(failed)}{RESET}")



def feature_change_passwords(api: MailcowAPI):
    file_path = input(f"{CYAN}Enter file path: {RESET}").strip()
    
    if not os.path.exists(file_path):
        print(f"{GRAY}{now()} » {RED}ERROR {WHITE}• File not found{RESET}")
        return
    
    emails = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and ':' in line:
                email = line.split(':', 1)[0].strip()
                emails.append(email)
    
    if not emails:
        print(f"{GRAY}{now()} » {YELLOW}NOTICE {WHITE}• No emails found{RESET}")
        return
    
    output_dir = create_output_dir()
    output_file = os.path.join(output_dir, "changed_passwords.txt")
    log_file = os.path.join(output_dir, "password_change_log.json")
    
    print(f"{GRAY}{now()} » {BLUE}INFO {WHITE}• Changing {len(emails)} passwords{RESET}")
    
    changed = []
    failed = []
    log_entries = []
    
    for email in emails:
        new_password = generate_password()
        success, message = api.change_password(email, new_password)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "email": email,
            "status": "changed" if success else "failed",
            "message": message
        }
        log_entries.append(log_entry)
        
        if success:
            changed.append(f"{email}:{new_password}")
            with open(output_file, 'a') as f:
                f.write(f"{email}:{new_password}\n")
            print(f"{GRAY}{now()} » {GREEN}CHANGED {WHITE}• {email}{RESET}")
        else:
            failed.append(f"{email} - {message}")
            print(f"{GRAY}{now()} » {RED}FAILED {WHITE}• {email} ➔ {RED}{message}{RESET}")
    
    with open(log_file, 'w') as f:
        json.dump(log_entries, f, indent=2)
    
    print(f"{GRAY}{now()} » {BLUE}SUMMARY {WHITE}• Total: {len(emails)} | Changed: {GREEN}{len(changed)}{WHITE} | Failed: {RED}{len(failed)}{RESET}")



def main():
    os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)
    
    print(f"\n{MAGENTA}MAILCOW MANAGER{RESET}\n")
    
    api = MailcowAPI(API_KEY)
    
    while True:
        print(f"\n{WHITE}1.{RESET} Create Emails")
        print(f"{WHITE}2.{RESET} List Emails")
        print(f"{WHITE}3.{RESET} Delete Emails")
        print(f"{WHITE}4.{RESET} Change Passwords")
        print(f"{WHITE}5.{RESET} Exit")
        
        choice = input(f"\n{CYAN}Select: {RESET}").strip()
        
        if choice == "1":
            feature_create_emails(api)
        elif choice == "2":
            feature_list_emails(api)
        elif choice == "3":
            feature_delete_emails(api)
        elif choice == "4":
            feature_change_passwords(api)
        elif choice == "5":
            print(f"{GRAY}{now()} » {BLUE}INFO {WHITE}• Exiting{RESET}\n")
            sys.exit(0)
        else:
            print(f"{GRAY}{now()} » {RED}ERROR {WHITE}• Invalid option{RESET}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{GRAY}{now()} » {YELLOW}NOTICE {WHITE}• Cancelled{RESET}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{GRAY}{now()} » {RED}FATAL {WHITE}• {e}{RESET}\n")
        sys.exit(1)
