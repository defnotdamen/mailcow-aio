# Mailcow Manager

## Features

- **Create Emails** - Bulk create mailboxes with auto-generated secure passwords
- **List Emails** - View all active and inactive mailboxes
- **Delete Emails** - Remove mailboxes by keyword, file, or all at once
- **Change Passwords** - Bulk update passwords for existing mailboxes

## Requirements

- Python 3.6+
- `requests` library

```bash
pip install requests
```

## Configuration

Edit the script to set your Mailcow instance details:

```python
BASE_URL = "https://mail.boostsync.cc"
DOMAIN = "boostsync.cc"
API_KEY = "your-api-key-here"
```

## Usage

Run the script:

```bash
python3 aio.py
```

Select from the interactive menu:

```
1. Create Emails    - Bulk create with prefix (e.g., user_1, user_2...)
2. List Emails      - Export all mailboxes to file
3. Delete Emails    - Remove by keyword, file, or all
4. Change Passwords - Update passwords from email list
5. Exit
```

## Output

All operations create timestamped folders in `mailcow_outputs/` containing:

- Credential files (`email:password` format)
- JSON logs with operation details
- Mailbox listings

## Security Notes

- Passwords are randomly generated (16 chars, mixed case, numbers, symbols)
- All credentials are saved locally - store securely
- API key should be kept private
