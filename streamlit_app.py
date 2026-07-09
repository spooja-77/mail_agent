"""
streamlit_app.py
Streamlit web UI for the Groq-powered email agent.

Deploy on Streamlit Community Cloud by pushing this repo to GitHub and
adding GROQ_API_KEY, SMTP_USER, SMTP_PASS, SMTP_HOST, SMTP_PORT as
"Secrets" in the app settings (see README for details).
"""

import os
import json
from dotenv import load_dotenv
import streamlit as st
from groq import Groq

import httpx

from \email_tool (1) import send_email

# Load variables from .env into os.environ (needed for LOCAL runs).
# On Streamlit Cloud there is no .env file, so this simply does nothing there.
load_dotenv()

# ---------------------------------------------------------------------------
# Config — works both locally (.env via os.environ) and on Streamlit Cloud
# (st.secrets). We check st.secrets first, then fall back to env vars.
# ---------------------------------------------------------------------------
def get_config(key: str, default: str = None):
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, default)


# Push secrets into os.environ so email_tool (1).py (which reads os.environ) works
# unchanged whether running locally or on Streamlit Cloud.
for key in ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS"]:
    val = get_config(key)
    if val:
        os.environ[key] = str(val)

GROQ_API_KEY = get_config("GROQ_API_KEY")

st.set_page_config(page_title="Email Agent", page_icon="📧", layout="centered")
st.title("📧 RAISE - Agentic AI Assistant")
st.caption("Tell me whom to email and what to say — I'll draft and send the email for you.")

if not GROQ_API_KEY:
    st.error(
        "GROQ_API_KEY is not set. Add it to your `.env` file (local) or "
        "to Secrets (Streamlit Cloud), then restart the app."
    )
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

# =====================================================
# Local SSL Bypass (for office network only)
# Set SSL_VERIFY=false in your .env for local testing
# =====================================================

#SSL_VERIFY = get_config("SSL_VERIFY", "true").lower() == "true"

#http_client = httpx.Client(
#    verify=SSL_VERIFY,
#    timeout=60.0
#)

#client = Groq(
#    api_key=GROQ_API_KEY,
#    http_client=http_client
#)

tools = [
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email to one or more recipients. Use this whenever the "
                            "user asks to email, message, or notify someone (or a group) via "
                            "email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of recipient email addresses.",
                    },
                    "subject": {"type": "string", "description": "A concise, relevant subject line."},
                    "body": {
                        "type": "string",
                        "description": "The full email body, written in a clear, "
                                        "professional tone based on the user's request. "
                                        "If a feedback form link is provided in context, "
                                        "include it naturally in the body.",
                    },
                },
                "required": ["to", "subject", "body"],
            },
        },
    }
]


def build_system_prompt(form_link: str) -> str:
    base = (
        "You are an email assistant agent. When the user asks you to email one or more "
        "people, compose an appropriate subject and body yourself, then call the send_email "
        "tool with a list of recipient addresses. Confirm with the user in plain language "
        "once it's done. If the user's request has no recipient email address(es), ask for "
        "them before doing anything else."
    )
    if form_link:
        base += (
            f"\n\nWhen the user asks for a feedback-request email on some topic, include this "
            f"Google Form link in the body as the place to submit feedback: {form_link}. "
            f"Write a short line inviting the recipient to fill it out, tailored to the topic given."
        )
    return base


# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------
require_confirm = st.sidebar.checkbox("Ask me to confirm before sending", value=True)
feedback_form_link = st.sidebar.text_input(
    "Feedback Form link (optional)",
    placeholder="https://forms.gle/xxxxxxxx",
    help="If set, the agent will include this link in emails when you ask for feedback.",
)
st.sidebar.markdown("---")
st.sidebar.caption(
    "This app sends real emails via SMTP. Double-check recipients before confirming."
)

# ---------------------------------------------------------------------------
# Chat state
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": build_system_prompt(feedback_form_link)}
    ]
else:
    # Keep the system prompt in sync with the sidebar input on every rerun,
    # so changing the form link takes effect without restarting the chat.
    st.session_state.messages[0] = {
        "role": "system",
        "content": build_system_prompt(feedback_form_link),
    }

# Render chat history (skip system + tool messages from display)
for msg in st.session_state.messages:
    role = msg["role"] if isinstance(msg, dict) else msg.role
    if role in ("system", "tool"):
        continue
    content = msg["content"] if isinstance(msg, dict) else msg.content
    if not content:
        continue
    with st.chat_message("assistant" if role == "assistant" else "user"):
        st.markdown(content)

# ---------------------------------------------------------------------------
# Pending-send confirmation flow
# ---------------------------------------------------------------------------
if "pending_email" not in st.session_state:
    st.session_state.pending_email = None

if st.session_state.pending_email:
    pending = st.session_state.pending_email
    to_display = ", ".join(pending["to"]) if isinstance(pending["to"], list) else pending["to"]
    with st.chat_message("assistant"):
        st.markdown(
            f"**Ready to send:**\n\n"
            f"**To:** {to_display}\n\n"
            f"**Subject:** {pending['subject']}\n\n"
            f"**Body:**\n\n{pending['body']}"
        )
        col1, col2 = st.columns(2)
        if col1.button("✅ Send it"):
            result = send_email(pending["to"], pending["subject"], pending["body"])
            st.session_state.messages.append({"role": "assistant", "content": result})
            st.session_state.pending_email = None
            st.rerun()
        if col2.button("❌ Cancel"):
            st.session_state.messages.append(
                {"role": "assistant", "content": "Okay, I didn't send that email."}
            )
            st.session_state.pending_email = None
            st.rerun()

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------
user_input = st.chat_input("Let's write your next email together.")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("Thinking..."):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.messages,
            tools=tools,
            tool_choice="auto",
        )

    msg = response.choices[0].message
    st.session_state.messages.append(msg)

    if msg.tool_calls:
        for tool_call in msg.tool_calls:
            if tool_call.function.name == "send_email":
                args = json.loads(tool_call.function.arguments)

                if require_confirm:
                    # Stash for confirmation instead of sending immediately
                    st.session_state.pending_email = args
                    # Remove the tool_call message we just appended since we
                    # haven't actually executed it yet — we'll re-add once sent
                    st.session_state.messages.pop()
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": "I've drafted the email below — confirm to send it.",
                        }
                    )
                    st.rerun()
                else:
                    result = send_email(args.get("to"), args.get("subject"), args.get("body"))
                    st.session_state.messages.append(
                        {"role": "tool", "tool_call_id": tool_call.id, "content": result}
                    )
                    followup = client.chat.completions.create(
                        model="llama-3.3-70b-versatile", messages=st.session_state.messages
                    )
                    final_msg = followup.choices[0].message
                    st.session_state.messages.append(final_msg)
                    with st.chat_message("assistant"):
                        st.markdown(final_msg.content)
    else:
        with st.chat_message("assistant"):
            st.markdown(msg.content)
