import streamlit as st
import re
import base64
import json
from tempfile import NamedTemporaryFile
from gmail_langchain_reply import get_email_by_prompt, generate_reply, create_reply_draft
from google_auth_oauthlib.flow import InstalledAppFlow

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# -------------------
# STEP 1: Upload credentials and authenticate
# -------------------
def authenticate_gmail_from_upload(uploaded_json_str):
    creds = None
    try:
        # flow = InstalledAppFlow.from_client_config(
        #     json.loads(uploaded_json_str),
        #     scopes=SCOPES,
        #     redirect_uri='http://localhost:8501'
        # )
        # creds = flow.run_console()
        # # creds = flow.run_local_server(port=0)
      flow = InstalledAppFlow.from_client_config(
      json.loads(uploaded_json_str),
      scopes=SCOPES,
      redirect_uri="https://your-app.streamlit.app/oauth2callback")
auth_url, _ = flow.authorization_url(prompt='consent')
 st.markdown(f"[Click here to login]({auth_url})")

    except Exception as e:
        st.error(f"Authentication failed: {e}")
        return None
    return [build('gmail', 'v1', credentials=creds), creds]

uploaded_file = st.file_uploader("Upload your credentials.json", type="json")

if uploaded_file and "gmail_service" not in st.session_state:
    uploaded_json_str = uploaded_file.read().decode("utf-8")
    st.title("📧 Gmail Assistant")
    st.title("✉️ Smart Gmail Reply Draft with Groq")
    st.info("You'll be redirected to log in via browser after clicking below button. After granting access, copy and paste the auth code back into the terminal if prompted.")
    if st.button("🔐 Login with Gmail"):
        x = authenticate_gmail_from_upload(uploaded_json_str)
        print(x, "x logging")
        if x[0]:
            st.session_state.gmail_service = x[0]
            st.session_state.gmail_creds = x[1].to_json()  # store safely
            st.success("✅ Gmail authenticated successfully!")

# -------------------
# STEP 2: Fetch email by prompt
# -------------------
if "gmail_service" in st.session_state:
    user_prompt = st.text_input("🔍 Enter what you're looking for in your emails (e.g. 'invoice from:boss')")

    if st.button("📩 Search Email"):
        if user_prompt.strip():
            service = st.session_state.gmail_service
            email_text, full_msg = get_email_by_prompt(service, user_prompt)
            st.session_state.full_msg = full_msg
            st.session_state.email_text = email_text
            st.text_area("📧 Email Result", email_text, height=200)
        else:
            st.warning("Please enter something to search.")

# -------------------
# STEP 3: Generate reply from fetched email
# -------------------
if "email_text" in st.session_state:
    if st.button("💡 Generate Reply"):
        reply = generate_reply(st.session_state.email_text)

        subject_match = re.search(r"Subject:\s*(.*)", reply)
        body_match = re.search(r"Body:\s*(.*)", reply, re.DOTALL)
        subject = subject_match.group(1).strip() if subject_match else ""
        body = body_match.group(1).strip() if body_match else reply

        st.session_state.reply_subject = subject
        st.session_state.reply_body = body

# -------------------
# STEP 4: Display editable reply and draft it
# -------------------
if "reply_subject" in st.session_state and "reply_body" in st.session_state:
    subject = st.text_input("✏️ Subject", st.session_state.reply_subject)
    body = st.text_area("📝 Body", st.session_state.reply_body)

    if st.button("📤 Make a Draft Email"):
        create_reply_draft(
            st.session_state.gmail_service,
            st.session_state.full_msg,
            subject,
            body
        )
        st.success("✅ Draft created successfully!")



# import streamlit as st
# import os
# import re
# import base64
# from tempfile import NamedTemporaryFile
# from gmail_langchain_reply import get_gmail_service, get_email_by_prompt, generate_reply, create_reply_draft
# import shutil
# from google_auth_oauthlib.flow import InstalledAppFlow
# import pickle
# from googleapiclient.discovery import build
# SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# def authenticate_gmail():
#     creds = None
#     # if os.path.exists("token.pkl"):
#     #     with open("token.pkl", "rb") as token:
#     #         creds = pickle.load(token)
#     if not creds or not creds.valid:
#         flow = InstalledAppFlow.from_client_secrets_file("credentials1.json", SCOPES)
#         creds = flow.run_local_server(port=0)
#         with open("token.pkl", "wb") as token:
#             pickle.dump(creds, token)
#     return build('gmail', 'v1', credentials=creds)


# # STEP 1: Upload credentials
# uploaded_file = st.file_uploader("Upload your credentials.json", type="json")

# if uploaded_file and "gmail_service" not in st.session_state:
#     with NamedTemporaryFile(delete=False, suffix=".json") as tmp:
#         tmp.write(uploaded_file.read())
#         cred_path = tmp.name

#     shutil.copy(cred_path, "credentials1.json") # This will overwrite if exists
#     st.title("📧 Gmail Assistant")
#     st.title("✉️ Smart Gmail Reply Draft with Groq")
#     if st.button("🔐 Login with Gmail"):
#         service = authenticate_gmail()
#         st.session_state.gmail_service = service
#         st.success("✅ Gmail authenticated successfully!")

# # if st.button("🔐 Login with Gmail"):
# #     service = authenticate_gmail()
# #     st.session_state.gmail_service = service
# #     st.success("Successfully authenticated with Gmail!")
# # STEP 2: Fetch latest email
# if "gmail_service" in st.session_state:
#     # Input box for user's email search prompt
#     user_prompt = st.text_input("🔍 Enter what you're looking for in your emails (e.g. 'invoice from:boss', 'meeting subject', etc.)")

#     if st.button("📩 Search Email"):
#         if user_prompt.strip():
#             service = st.session_state.gmail_service
#             email_text, full_msg = get_email_by_prompt(service, user_prompt)
#             st.session_state.full_msg = full_msg
#             st.session_state.email_text = email_text
#             st.text_area("📧 Email Result", email_text, height=200)
#         else:
#             st.warning("Please enter something to search.")

# # STEP 3: Generate reply
# if "email_text" in st.session_state:
#     if st.button("💡 Generate Reply"):
#         reply = generate_reply(st.session_state.email_text)

#         # Extract subject and body from reply
#         subject_match = re.search(r"Subject:\s*(.*)", reply)
#         body_match = re.search(r"Body:\s*(.*)", reply, re.DOTALL)
#         subject = subject_match.group(1).strip() if subject_match else ""
#         body = body_match.group(1).strip() if body_match else reply

#         st.session_state.reply_subject = subject
#         st.session_state.reply_body = body

# # STEP 4: Display and send reply
# if "reply_subject" in st.session_state and "reply_body" in st.session_state:
#     subject = st.text_input("✏️ Subject", st.session_state.reply_subject)
#     body = st.text_area("📝 Body", st.session_state.reply_body)

#     if st.button("📤 Make a Draft Email"):
#         create_reply_draft(
#             st.session_state.gmail_service,
#             st.session_state.full_msg,
#             subject,
#             body
#         )
#         st.success("✅ Email sent successfully!")
