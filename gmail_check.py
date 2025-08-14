import imaplib
import email
import json
from email.message import Message
from openai import OpenAI
import requests
import jsonlines

# === Load config ===
with open("config.json", "r") as f:
    config = json.load(f)

EMAIL = config["email"]
APP_PASSWORD = config["app_password"]
USE_OPENAI = config.get("use_openai", True)
OPENAI_API_KEY = config.get("openai_api_key")
OLLAMA_URL = config.get("ollama_base_url")

# === Connect to Gmail ===
mail = imaplib.IMAP4_SSL("imap.gmail.com")
mail.login(EMAIL, APP_PASSWORD)
mail.select('"[Gmail]/Spam"')

# === Fetch all spam email IDs ===
result, data = mail.search(None, "ALL")
email_ids = data[0].split()
print(f"Found {len(email_ids)} spam emails")

OUTPUT_FILE = "spam_analysis_results.jsonl"


def save_to_jsonl(email_id, subject, analysis_result):
    classification, reason = "Unknown", analysis_result
    if "not spam" in analysis_result.lower():
        classification = "Not Spam"
    elif "spam" in analysis_result.lower():
        classification = "Spam"

    with jsonlines.open(OUTPUT_FILE, mode='a') as writer:
        writer.write({
            "email_id": email_id.decode() if isinstance(email_id, bytes) else str(email_id),
            "subject": subject,
            "classification": classification,
            "reason": reason
        })


# === Define summarization/analyzer function ===
def analyze_email(body: str) -> str:
    system_prompt = "You're a spam detection system. Classify the following email content as \
        'Spam' or 'Not Spam' and explain briefly why."

    if USE_OPENAI:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": body}
            ]
        )
        return response.choices[0].message.content.strip()

    else:
        # Use Ollama/OpenLLaMA via OpenAI-compatible interface
        payload = {
            "model": "llama3.2:latest",  # or whatever model name your Ollama server uses
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": body}
            ]
        }
        response = requests.post(
            f"{OLLAMA_URL}/chat/completions",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()


# === Loop through emails ===
for eid in email_ids:
    result, message_data = mail.fetch(eid, "(RFC822)")
    msg: Message = email.message_from_bytes(message_data[0][1])

    # Extract plain text
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition")):
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode(errors="replace")
                    break
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body = payload.decode(errors="replace")

    if not body:
        body = "[No readable plain text body found.]"

    print("🔍 Analyzing email...")
    subject = msg["subject"] or "[No subject]"
    result = analyze_email(body)
    save_to_jsonl(eid, subject, result)
    print(f"Result:\n{result}\n{'-'*40}")

# === Delete all processed emails ===
for eid in email_ids:
    mail.store(eid, '+FLAGS', '\\Deleted')

mail.expunge()
mail.logout()
print("All spam emails analyzed and deleted.")
