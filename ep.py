import requests
import json
import hmac
import hashlib
import base64
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API endpoint
url = "http://localhost:8000/notification/send"

# API credentials
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')

# Check if API credentials are loaded
if not API_KEY or not API_SECRET:
    print("Error: API_KEY or API_SECRET not found in environment variables.")
    print("Please make sure you have a .env file with API_KEY and API_SECRET defined.")
    exit(1)

# Request body
payload = {
    "mobileNumber": "9849669934",
    "remark1": "Message to send",
    "retrievalReferenceNumber": "70112545",
    "amount": "40.0",
    "merchantId": "987654321000987654",
    "terminalId": "9876543210900876543",
    "type": "otp",
    "uniqueId": "202307201141001",
    "properties": {
        "txnDate": "2023-07-22 01:00:10",
        "secondaryMobileNumber": "9012932645",
        "email": "pokharelsamir246@gmail.com",
        "sessionSrlNo": "69",
        "commission": "0.0",
        "initiator": "98xxxxxxxx"
    }
}

def generate_signature(api_secret: str, nonce: str, api_key: str, body: str) -> str:
    message = f" {api_key} {nonce} {body} "
    signature = base64.b64encode(
        hmac.new(api_secret.encode(), message.encode(), hashlib.sha512).digest()
    ).decode()
    return signature

# Convert payload to JSON string
body = json.dumps(payload)

# Generate nonce (you might want to use a more sophisticated method in production)
nonce = str(int(datetime.now().timestamp() * 1000))

# Generate signature
signature = generate_signature(API_SECRET, nonce, API_KEY, body)

# Prepare headers
headers = {
    "Content-Type": "application/json",
    "Authorization": f"HmacSHA512 {API_KEY}:{nonce}:{signature}"
}

# Send POST request
try:
    response = requests.post(url, headers=headers, data=body)
    
    # Check the response
    if response.status_code == 200:
        result = response.json()
        print(f"Status Code: {response.status_code}")
        print(f"Response: {result}")
    else:
        print(f"Error: Status Code {response.status_code}")
        print(f"Response: {response.text}")

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")

   
#this is just for funV