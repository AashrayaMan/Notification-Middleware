from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json
import hmac
import hashlib
import base64
import uuid
import logging
from requests.exceptions import RequestException
import subprocess
import sys
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

def run_client_script(transaction_details):
    script_path = os.path.join(os.path.dirname(__file__), 'client.py')
    
    args = [
        sys.executable,
        script_path,
        transaction_details['merchantId'],
        transaction_details['amount'],
        transaction_details['mobileNumber'],
        transaction_details['properties']['email'],
        transaction_details['properties']['commission']
    ]
    
    subprocess.Popen(args)
    logger.info(f"Launched client.py for transaction: {transaction_details['uniqueId']}")

class FonepayNotificationAPI:
    def __init__(self, base_url, api_key, api_secret):
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret

    def generate_signature(self, nonce, body):
        signature_data = f" {self.api_key} {nonce} {body} "
        hmac_obj = hmac.new(self.api_secret.encode(), signature_data.encode(), hashlib.sha512)
        return base64.b64encode(hmac_obj.digest()).decode()

    def send_notification(self, payload):
        url = f"{self.base_url}/notification/send"
        
        body = json.dumps(payload, separators=(',', ':'))
        nonce = str(uuid.uuid4())
        signature = self.generate_signature(nonce, body)
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'HmacSHA512 {self.api_key}:{nonce}:{signature}'
        }
        
        try:
            response = requests.post(url, data=body, headers=headers, timeout=10)
            response.raise_for_status()
            logger.info(f"Send Notification Status Code: {response.status_code}")
            logger.info(f"Send Notification Response: {response.text}")
            
            if response.status_code == 200:
                run_client_script(payload)
            
            return response.json()
        except RequestException as e:
            logger.error(f"An error occurred while sending notification: {e}")
            return None

    def get_last_5_transactions(self, merchant_id, terminal_id):
        url = f"{self.base_url}/callback"
        
        payload = {
            "merchantId": merchant_id,
            "terminalId": terminal_id
        }
        
        body = json.dumps(payload, separators=(',', ':'))
        nonce = str(uuid.uuid4())
        signature = self.generate_signature(nonce, body)
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'HmacSHA512 {self.api_key}:{nonce}:{signature}'
        }
        
        try:
            response = requests.post(url, data=body, headers=headers, timeout=10)
            response.raise_for_status()
            logger.info(f"Callback Status Code: {response.status_code}")
            logger.info(f"Callback Response: {response.text}")
            return response.json()
        except RequestException as e:
            logger.error(f"An error occurred while getting transactions: {e}")
            return None

# Initialize API
base_url = "http://localhost:5000"  # Our mock server URL
api_key = "test@test.com.np"  # Must match the mock server
api_secret = "testApiSecret"  # Must match the mock server

api = FonepayNotificationAPI(base_url, api_key, api_secret)

class NotificationPayload(BaseModel):
    mobileNumber: str
    remark1: str
    retrievalReferenceNumber: str
    amount: str
    merchantId: str
    terminalId: str
    type: str
    uniqueId: str
    properties: dict

@app.post("/send_notification")
async def send_notification(payload: NotificationPayload):
    notification_response = api.send_notification(payload.dict())
    if notification_response:
        logger.info(f"Notification sent successfully: {notification_response}")
        return {
            "status": "success",
            "message": "Notification sent successfully",
            "response": notification_response
        }
    else:
        logger.error("Failed to send notification")
        raise HTTPException(status_code=500, detail="Failed to send notification")

@app.get("/get_transactions/{merchant_id}/{terminal_id}")
async def get_transactions(merchant_id: str, terminal_id: str):
    transactions_response = api.get_last_5_transactions(merchant_id, terminal_id)
    if transactions_response:
        logger.info(f"Transactions retrieved successfully: {transactions_response}")
        return {
            "status": "success",
            "message": "Transactions retrieved successfully",
            "full_response": transactions_response,
            "transaction_details": transactions_response.get('transactionNotificationDetails', [])
        }
    else:
        logger.error("Failed to retrieve transactions")
        raise HTTPException(status_code=500, detail="Failed to retrieve transactions")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)