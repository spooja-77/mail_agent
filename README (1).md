# Groq Email Agent

A minimal agentic AI that reads a natural-language request, decides to send an
email, writes the subject/body itself, and sends it via SMTP — all through
Groq's fast LLM inference with tool (function) calling.

## Setup in VS Code

1. **Open the folder** `mail-agent` in VS Code.

2. **Create a virtual environment** (open a terminal in VS Code: `` Ctrl+` ``):
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your `.env` file:**
   ```bash
   cp .env.example .env
   ```
   Then fill in:
   - `GROQ_API_KEY` — get a free key at https://console.groq.com/keys
   - `SMTP_USER` / `SMTP_PASS` — your email + an **app password** (see below)

   > **Gmail users:** you can't use your normal password. Enable 2-Step
   > Verification on your Google account, then generate an "App Password" at
   > https://myaccount.google.com/apppasswords and use that as `SMTP_PASS`.

5. **Run it:**
   ```bash
   python agent.py
   ```

## Example session

```
📧 Groq Email Agent — type 'exit' to quit

You: email raj@example.com and tell him the client meeting moved to 4pm today
🔧 Agent is sending an email to raj@example.com...
   → SUCCESS: Email sent to raj@example.com with subject 'Meeting Time Change'.

Agent: Done! I let Raj know the client meeting has been moved to 4pm today.
```

## How it works

- `agent.py` — the agent loop. Sends your message + a tool schema to Groq;
  if the model decides to call `send_email`, we execute it and feed the
  result back so the model can confirm in natural language.
- `email_tool.py` — the actual SMTP sending logic (works with Gmail, Outlook,
  Yahoo, or any SMTP provider — just change the host/port in `.env`).

## Extending this

Ideas for next steps:
- Add a `read_emails` tool (via IMAP) so the agent can also check inbox
- Add a `list_contacts` tool backed by a small JSON/CSV file, so you can say
  "email the marketing team" and it resolves names to addresses
- Add a confirmation step before sending (print the drafted email and ask
  y/n) if you want a human-in-the-loop safety check
- Swap the CLI loop for a Flask/FastAPI endpoint or a Slack bot trigger

## Note on safety

This agent will actually send real emails once you run it and give it an
instruction — there's no dry-run mode by default. If you want a safety net,
add a confirmation prompt in `agent.py` before calling `send_email`.
