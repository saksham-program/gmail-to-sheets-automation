# gmail-to-sheets-automation

Author: Saksham Jagetiya
Purpose: Internship Assignment – Gmail to Google Sheets Automation

A Python 3 automation project that reads real unread emails from Gmail using the official Gmail API (not IMAP) and appends them into Google Sheets using the Google Sheets API.

It only scans:
- **Inbox** (`in:inbox`)
- **Unread** emails (`is:unread`)

After a message is successfully logged, it is **marked as read**.

## Architecture (text diagram)

```
+-------------------+       OAuth 2.0        +------------------------+
|   main.py         | <--------------------> | Google OAuth / Consent  |
| Orchestration     |                        +------------------------+
|                   |
| 1) Fetch unread   |      Gmail API         +------------------------+
| 2) Parse message  | <--------------------> | Gmail (users.messages) |
| 3) Append row     |                        +------------------------+
| 4) Mark as read   |
| 5) Persist state  |      Sheets API        +------------------------+
|                   | <--------------------> | Google Sheets          |
+-------------------+                        +------------------------+
                |
                v
          state.json (local)
```

## Folder structure

```
gmail-to-sheets/
├── src/
│   ├── gmail_service.py        # Gmail API authentication + fetching unread emails
│   ├── sheets_service.py       # Google Sheets API append logic
│   ├── email_parser.py         # Extract sender, subject, date, plain-text body
│   └── main.py                 # Orchestrates the full flow
├── credentials/
│   └── credentials.json        # OAuth file (DO NOT COMMIT)
├── config.py                   # Scopes, sheet ID, constants
├── requirements.txt
├── .gitignore
├── README.md
```

## Setup (Windows 10/11)

### 1) Create Google Cloud project + enable APIs

1. Go to Google Cloud Console.
2. Create a project (or reuse one).
3. Enable:
   - **Gmail API**
   - **Google Sheets API**
4. Configure the **OAuth consent screen**.

### 2) Create OAuth credentials (Desktop app flow)

1. In Google Cloud Console → **APIs & Services** → **Credentials**
2. Create credentials → **OAuth client ID**
3. Application type: **Desktop app**
4. Download the JSON and save it here:

```
credentials/credentials.json
```

Important: this project uses the **InstalledAppFlow (Desktop OAuth)**, not service accounts.

### 3) Prepare your Google Sheet

1. Create a spreadsheet.
2. Create a tab named (default): `InboxLog` (you can change `SHEET_NAME` in `config.py`).
3. Copy the Spreadsheet ID from the URL and paste it into `config.py`:

```python
SPREADSHEET_ID = "YOUR_SPREADSHEET_ID_HERE"
```

### 4) Install and run

```powershell
cd gmail-to-sheets
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

python -m src.main
```

On first run, a browser window opens for Google login/consent. After consent, the script caches tokens.

## OAuth flow explanation (what happens on first run)

- The script loads `credentials/credentials.json` (your downloaded OAuth client secret).
- It launches a **local server** on an ephemeral port and opens your default browser.
- After you approve consent, Google returns an authorization code to the local server.
- The script exchanges that code for access/refresh tokens and saves them to:

```
credentials/token.json
```

Next runs reuse `token.json` and refresh automatically when expired.

## Duplicate prevention logic

Duplicate prevention is handled at the **Gmail message ID** level.

- We fetch **only unread Inbox** messages.
- Before processing, we filter out message IDs already in `state.json`.
- Only *new* IDs are parsed and appended.
- After rows are appended successfully, those IDs are:
  1) marked as read (Gmail label UNREAD removed)
  2) added to the persisted state

This ensures running the script twice does not create duplicate rows.

## State persistence (what, where, why)

**What is stored?**
- A list of processed Gmail `message_id` values.

**Where is it stored?**
- In the project root:

```
state.json
```

**Why this approach?**
- Transparent and easy to audit.
- Works even if the Sheet is edited manually.
- Avoids expensive “read back the sheet to dedupe” calls.

If `state.json` is deleted, the script will treat currently unread emails as new again (and append them), so keep it safe.

## Real-world challenge + solution

### Challenge: email bodies are often multipart (plain text + HTML + attachments)
Gmail messages frequently contain nested MIME structures. If you only read `payload.body.data`, you’ll miss most content.

**Solution**
`src/email_parser.py` recursively walks message parts, prefers `text/plain`, and falls back to `text/html` with a lightweight HTML-to-text conversion.

## Limitations

- This project appends **raw** values; it does not apply formatting.
- The HTML → text conversion is intentionally dependency-free and simple (good enough for logging, not perfect for rendering).
- If you manually modify `state.json`, you can cause reprocessing or skipping.
- The script assumes the target sheet tab already exists.

## Proof of execution

The following proof artifacts were created and shared as part of submission:

- Gmail inbox screenshot with unread emails
- Google Sheet screenshot with populated rows
- OAuth consent screen screenshot
- 2–3 minute screen recording demonstrating:
   • Project flow
   • Gmail → Sheets data movement
   • Duplicate prevention
   • Script re-run behavior

(Proof files are not committed to this repository for security and privacy reasons.)

## Notes on security

- Do **not** commit `credentials/credentials.json` or `credentials/token.json`.
- `.gitignore` is configured to exclude credentials, tokens, and `state.json`.

---
