import imaplib
import email
from email.header import decode_header
from google import genai

import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

# Setting gemini 
client = genai.Client(api_key=GEMINI_API_KEY)

def connect_to_gmail():
    """Connect to Gmail from IMAP"""
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
    print("✅ Connect to Gmail!")
    return mail

def decode_email_subject(subject):
    """Decode email subject"""
    decoded_parts = decode_header(subject)
    decoded_subject = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            decoded_subject += part.decode(encoding or "utf-8", errors="ignore")
        else:
            decoded_subject += part
    return decoded_subject

def get_email_body(msg):
    """Extract text from email"""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                try:
                    body = part.get_payload(decode=True).decode("utf-8", 
                    errors="ignore")
                    break
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
        except:
            body = "Can`t decoded"
    return body

def get_emails(mail, max_emails=5):
    """Get last email"""
    try:
        mail.select("INBOX")

        status, messages = mail.search(None, "All")
        email_ids = messages[0].split()

        email_ids = email_ids[-max_emails:]

        emails = []

        for email_id in reversed(email_ids):
            status, msg_data = mail.fetch(email_id, "(RFC822)")

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])

                    subject = decode_email_subject(msg.get("Subject", "Without subject"))
                    sender = msg.get("From", "No name")
                    date = msg.get("Date", "Unknown date")
                    body = get_email_body(msg)

                    emails.append({
                        "subject": subject,
                        "from": sender,
                        "date": date,
                        "body": body[:500]
                    })
        return emails


    except Exception as e:
        print(f"Error with getting email: {e}")
        return []

def analyze_emails_with_ai(emails):
    """Analyze emails from Gemini AI"""
    if not emails:
        print("No emails")
        return
    print(f"\nFoFound {len(emails)} emails. Analyze....")

    for i, email_data in enumerate(emails, 1):
        print(f"{'=' * 70}")
        print(f"Email #{i}")
        print(f"{'=' * 70}")
        print(f"From: {email_data['from']}")
        print(f"Subect: {email_data['subject']}")
        print(f"Date: {email_data['date']}")
        print(f"\nStart email: \n{email_data['body'][:200]}....")
# Analyze from AI
        prompt = f"""
        Проаналізуй цей email українською мовою:
        
        Від: {email_data['from']}
        Тема: {email_data['subject']}
        Текст: {email_data['body']}
        
        Надай коротку відповідь:
        1. Про що лист (1 речення)
        2. чи потрібна дія від мене? (так/ні, яка)
        3. Пріоритет (низький/середній/високий)
        """
        try:
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt
            )
            print(f"\nAnalyze from AI:\n{response.text}")
        except Exception as e:
            print(f"Error from AI: {e}")

        print(f"{'=' * 70}")


def main():
    print("Start Email Agent....")

    mail = connect_to_gmail()
    if not mail:
        return

    print ("\nGetting emails....")
    emails = get_emails(mail, max_emails=5)

    mail.close()
    mail.logout()

    # print(emails) #Without AI
    analyze_emails_with_ai(emails)

    print("\nWell done!!!")

if __name__ == "__main__":
    main()


        
                            










