# SCT-FenrirGuard

SCT-FenrirGuard is a Viking-inspired AI tool from **Social Climate Tech SocialLab** that analyzes your Gmail spam folder and classifies emails as **Spam** or **Not Spam** using AI. Instead of manually checking your spam, let the AI do the work and deliver a concise summary to your inbox.

This tool supports **OpenAI API** or a fully **local Ollama setup**, works on Mac, Linux, and Windows, and follows our **Open Code principles** for ethical AI: [Social Climate Tech Open Code](https://socialclimate.tech/open_code).

SocialLab collaboration link: [https://socialclimate.tech/sociallab](https://socialclimate.tech/sociallab)

---

## **Repository Structure**

```text
sct-fenrirguard/
├── README.md             ← This file
├── CONTRIBUTORS.md       ← Credits and contributors
├── ETHICS.md             ← Ethics & responsible AI
├── config.example.json   ← Example configuration
├── config.json           ← Your local config (not committed)
├── daily_spam_analysis.py← The main script
└── requirements.txt      ← Python dependencies

```

## Setup
1. Clone the repository
```bash
git clone https://github.com/yourusername/sct-fenrirguard.git
cd sct-fenrirguard

```
2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Configure
Copy the example config:
```bash
cp config.example.json config.json
Edit config.json with your values:
```
```json
{
    "email": "your.email@gmail.com",
    "app_password": "your_gmail_app_password",
    "use_openai": true,
    "openai_api_key": "YOUR_OPENAI_API_KEY",
    "ollama_base_url": "http://localhost:11434",
    "delete_processed": false,
    "recipients": ["your.email@gmail.com"]
}
```

use_openai – Set to true for OpenAI API, false for Ollama local.

delete_processed – Set to true to remove analyzed spam from Gmail.

recipients – List of email addresses to receive the analysis.

Gmail App Passwords: You must enable 2FA and generate an App Password: Google Account Security

Using Ollama Locally (Offline Mode)
Ollama allows running large language models entirely on your machine.

Install Ollama: https://ollama.ai

Pull a model (example):
```bash
ollama pull llama3.2
```
Start Ollama (usually http://localhost:11434)

Set "use_openai": false in config.json

## How it Works
Connects to Gmail and fetches all emails in the Spam folder.

Extracts plain text from each email.

Sends the text to AI for analysis (Spam / Not Spam + explanation).

Collects all analyses and sends a single email with the results.

Optionally deletes the processed emails if delete_processed is true.

Saves structured output to spam_analysis_results.jsonl.

You can tweak the AI prompt inside daily_spam_analysis.py to adjust classification logic.

Running Automatically
Mac/Linux – Cronjob
```bash
crontab -e
```
```bash

0 8,20 * * * /usr/bin/python3 /path/to/sct-fenrirguard/daily_spam_analysis.py
```

Windows – Task Scheduler

Open Task Scheduler → Create Basic Task

Set triggers for morning and evening

Action: Run python with full path to daily_spam_analysis.py

## Contributing
See CONTRIBUTORS.md for guidelines. We welcome bug reports, improvements, or new features.

## Ethics
SCT-FenrirGuard follows Open Code principles:

Only accesses public information (your Gmail spam folder)

Does not bypass security or privacy restrictions

Promotes transparency in AI classification

Read more in ETHICS.md.

## Links
Social Climate Tech: https://socialclimate.tech/

SocialLab: https://socialclimate.tech/sociallab

Open Code Principles: https://socialclimate.tech/open_code

---

## **requirements.txt**

```txt
# HTTP requests
requests>=2.30.0

# OpenAI API client
openai>=1.27.0

# JSONL support for structured output
jsonlines>=3.3.0
Notes:

imaplib, email, smtplib, json, email.message are built-in Python libraries.

```
Pin versions if you want consistent behavior across environments.
