import imaplib
import email
import json
from email.message import Message
from openai import OpenAI
import requests
import jsonlines
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# === Load config ===
with open("config.json", "r") as f:
    config = json.load(f)

EMAIL = config["email"]
APP_PASSWORD = config["app_password"]
USE_OPENAI = config.get("use_openai", True)
OPENAI_API_KEY = config.get("openai_api_key")
OLLAMA_URL = config.get("ollama_base_url")
DELETE_PROCESSED = config.get("delete_processed", False)
RECIPIENTS = config.get("recipients", [EMAIL])

# === Connect to Gmail ===
mail = imaplib.IMAP4_SSL("imap.gmail.com")
mail.login(EMAIL, APP_PASSWORD)
mail.select('"[Gmail]/Spam"')

# === Fetch all spam email IDs ===
result, data = mail.search(None, "ALL")
email_ids = data[0].split()
print(f"Found {len(email_ids)} spam emails")

OUTPUT_FILE = "spam_analysis_results.jsonl"
all_results = []  # Collect all analysis for email


# === Save analysis to JSONL ===
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


# === AI analysis function ===
def analyze_email(body: str) -> str:
    system_prompt = "You're a spam detection system. \
        Classify the following email content as 'Spam' or 'Not Spam' and explain briefly why."

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
        payload = {
            "model": "llama3.2:latest",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": body}
            ]
        }
        response = requests.post(f"{OLLAMA_URL}/chat/completions",
                                 headers={"Content-Type": "application/json"},
                                 json=payload)
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()


# === Email sender ===
def send_email(subject, body, recipients):
    msg = MIMEMultipart()
    msg["From"] = EMAIL
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, APP_PASSWORD)
        server.sendmail(EMAIL, recipients, msg.as_string())


# === Process emails ===
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

    subject = msg["subject"] or "[No subject]"
    analysis = analyze_email(body)
    save_to_jsonl(eid, subject, analysis)
    all_results.append(f"Email: {subject}\nAnalysis:\n{analysis}\n{'-'*40}")

# === Send collected analysis in one email ===
email_body = "\n\n".join(all_results)
send_email("Spam Folder Analysis Results", email_body, RECIPIENTS)

# === Optional deletion ===
if DELETE_PROCESSED:
    for eid in email_ids:
        mail.store(eid, '+FLAGS', '\\Deleted')
    mail.expunge()

mail.logout()
print("All spam emails analyzed and emailed. Deletion flag:", DELETE_PROCESSED)
