"""
agent.py
An agentic AI assistant (powered by Groq) that can send emails on your behalf.

How it works:
1. You type a natural-language request, e.g.
   "Email raj@example.com and tell him the meeting moved to 4pm"
2. Groq's LLM decides whether to call the `send_email` tool, and with what
   arguments (to, subject, body) — it writes the email content itself.
3. If it calls the tool, we actually send the email via SMTP and report the
   result back to the model, which then confirms to you in plain language.
"""

import os
import json
from dotenv import load_dotenv
from groq import Groq

from email_tool import send_email

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

# Tool schema Groq's model uses to decide when/how to send an email
tools = [
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email to a recipient. Use this whenever the user "
                            "asks to email, message, or notify someone via email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient's email address."
                    },
                    "subject": {
                        "type": "string",
                        "description": "A concise, relevant subject line."
                    },
                    "body": {
                        "type": "string",
                        "description": "The full email body, written in a clear, "
                                        "professional tone based on the user's request."
                    },
                },
                "required": ["to", "subject", "body"],
            },
        },
    }
]

SYSTEM_PROMPT = (
    "You are an email assistant agent. When the user asks you to email someone, "
    "compose an appropriate subject and body yourself, then call the send_email "
    "tool. Confirm with the user in plain language once it's done. If the user's "
    "request has no recipient email address, ask for it before doing anything else."
)


def run_agent():
    print("📧 Groq Email Agent — type 'exit' to quit\n")
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            break

        messages.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        msg = response.choices[0].message
        messages.append(msg)

        # Did the model decide to call a tool?
        if msg.tool_calls:
            for tool_call in msg.tool_calls:
                if tool_call.function.name == "send_email":
                    args = json.loads(tool_call.function.arguments)
                    print(f"\n🔧 Agent is sending an email to {args.get('to')}...")
                    result = send_email(
                        to=args.get("to"),
                        subject=args.get("subject"),
                        body=args.get("body"),
                    )
                    print(f"   → {result}\n")

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result,
                        }
                    )

            # Get the model's final natural-language confirmation
            followup = client.chat.completions.create(
                model=MODEL,
                messages=messages,
            )
            final_msg = followup.choices[0].message
            messages.append(final_msg)
            print(f"Agent: {final_msg.content}\n")
        else:
            print(f"Agent: {msg.content}\n")


if __name__ == "__main__":
    run_agent()
