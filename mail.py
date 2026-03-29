import os
import re
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = r"c:/Users/jackc/Downloads/canyon app/credentials.json"
TOKEN_FILE = r"c:/Users/jackc/Downloads/canyon app/token.json"
INVESTOPEDIA_URL = "https://auth.investopedia.com/realms/investopedia/protocol/openid-connect/auth?client_id=finance-simulator&redirect_uri=https%3A%2F%2Fwww.investopedia.com%2Fsimulator%2Fportfolio&state=3f9d47e0-160b-479e-9883-da019923a926&response_mode=fragment&response_type=code&scope=openid&nonce=12702430-5d9a-49ec-a423-a9133b9d9e4c&code_challenge=uwdjB1YT5bk6t1gvaEtPRs-Zc4-0i33urVRtEOUAgLs&code_challenge_method=S256"
EMAIL = "jack.castrission@gmail.com"

def get_gmail_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def get_magic_link():
    service = get_gmail_service()

    # Wait up to 30 seconds for the email to arrive
    for attempt in range(15):
        print(f"📧 Checking for email... attempt {attempt + 1}")
        results = service.users().messages().list(
            userId="me",
            q="from:investopedia newer_than:1d",
            maxResults=1
        ).execute()

        messages = results.get("messages", [])
        if messages:
            msg = service.users().messages().get(
                userId="me",
                id=messages[0]["id"],
                format="full"
            ).execute()

            parts = msg["payload"].get("parts", [])
            body = ""
            if parts:
                for part in parts:
                    if part["mimeType"] == "text/plain":
                        data = part["body"]["data"]
                        body = base64.urlsafe_b64decode(data).decode("utf-8")
                        break
            else:
                data = msg["payload"]["body"]["data"]
                body = base64.urlsafe_b64decode(data).decode("utf-8")

            # Extract the magic link
            match = re.search(r'https://auth\.investopedia\.com\S+', body)
            if match:
                link = match.group().strip()
                print(f"✅ Found magic link!")
                return link

        time.sleep(2)

    print("⚠️ No email found after 30 seconds")
    return None

def login():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # Step 1 - submit email on Investopedia
        driver.get(INVESTOPEDIA_URL)
        time.sleep(3)
        driver.find_element(By.ID, "username").send_keys(EMAIL)
        driver.find_element(By.ID, "login").click()
        print("📧 Email submitted! Waiting for magic link...")
        time.sleep(5)

        # Step 2 - grab magic link from Gmail
        link = get_magic_link()

        if link:
            # Step 3 - open the magic link in the browser
            driver.get(link)
            time.sleep(3)
            print("✅ Logged in to Investopedia!")
            input("Press Enter to close the browser...")
        else:
            print("⚠️ Could not get magic link")

    except Exception as e:
        print(f"⚠️ Error: {e}")
    finally:
        driver.quit()

login()