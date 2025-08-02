import os.path
import base64
import re

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

# === Step 1: Gmail API Authentication ===
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service():
    creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=4243)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

# === Step 2: Fetch Latest Email ===
import base64

def get_email_by_prompt(service, user_prompt):
    # Let Gmail handle the query parsing
    result = service.users().messages().list(userId='me', q=user_prompt, labelIds=['INBOX'], maxResults=1).execute()
    messages = result.get('messages', [])
    profile = service.users().getProfile(userId='me').execute()
    user_email = profile['emailAddress']
    print(f"User email: {user_email}")
    if not messages:
        return "No matching emails found.", None

    message = service.users().messages().get(userId='me', id=messages[0]['id'], format='full').execute()
    payload = message['payload']
    headers = payload.get('headers', [])

    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')

    parts = payload.get('parts', [])
    body = ""
    if parts:
        for part in parts:
            if part['mimeType'] == 'text/plain':
                data = part['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
                break
    else:
        data = payload['body']['data']
        body = base64.urlsafe_b64decode(data).decode('utf-8')

    return f"From: {sender}\nSubject: {subject}\n\n{body.strip()}", message


# === Step 3: Generate Email Reply using LangChain ===
def generate_reply(email_content: str):
    prompt = ChatPromptTemplate.from_template("""
You are an email assistant. Read the following email:

---EMAIL START---
{email_content}
---EMAIL END---

Write a concise, professional reply. Start with "Subject:" and then "Body:".
""")
    
    messages = prompt.format_messages(email_content=email_content)
    llm = ChatGroq(
    temperature=0.3,
    model_name="llama3-8b-8192",  # or "mixtral-8x7b-32768", etc.
    groq_api_key="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"  # or set via environment variable
     )
    
    return llm(messages).content

# === Step 4: Send Email Reply ===
import base64

def create_reply_draft(service, original_message, reply_subject, reply_body):
    message_id = original_message['id']
    thread_id = original_message['threadId']
    to_email = "mohithsai309@gmail.com"

    message = f"To: {to_email}\n" \
              f"Subject: {reply_subject}\n" \
              f"In-Reply-To: {message_id}\n" \
              f"References: {message_id}\n\n" \
              f"{reply_body}"

    encoded_message = base64.urlsafe_b64encode(message.encode("utf-8")).decode("utf-8")

    draft_body = {
        'message': {
            'raw': encoded_message,
            'threadId': thread_id
        }
    }

    return service.users().drafts().create(userId="me", body=draft_body).execute()

# === Step 5: Main ===
if __name__ == '__main__':
    service = get_gmail_service()
    email_text, full_msg = get_email_by_prompt(service,"get me the latest email")
    print("Latest Email:\n", email_text)

    reply = generate_reply(email_text)
    print("\nGenerated Reply:\n", reply)

    subject_match = re.search(r"Subject:\s*(.*)", reply)
    body_match = re.search(r"Body:\s*(.*)", reply, re.DOTALL)

    subject = subject_match.group(1).strip() if subject_match else "Re:"
    body = body_match.group(1).strip() if body_match else reply.strip()

    create_reply(service, full_msg, subject, body)
    print("\n✅ Email reply sent.")

