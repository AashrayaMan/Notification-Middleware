from pydantic import BaseModel, Field
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
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

def run_client_script(transaction_details):
    script_path = os.path.join(os.path.dirname(__file__), 'new_client.py')
    
    properties = transaction_details.get('properties', {})
    
    args = [
        sys.executable,
        script_path,
        transaction_details['merchantId'],
        transaction_details['amount'],
        transaction_details['mobileNumber'],
        properties.get('email', ''),  # Use an empty string if 'email' is not present
        properties.get('commission', '')  # Use an empty string if 'commission' is not present
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

class Properties(BaseModel):
    txnDate: Optional[str] = None
    secondaryMobileNumber: Optional[str] = None
    email: Optional[str] = None
    sessionSrlNo: Optional[str] = None
    commission: Optional[str] = None
    initiator: Optional[str] = None

class NotificationPayload(BaseModel):
    mobileNumber: str = Field(..., min_length=1)
    remark1: str = Field(..., min_length=1)
    retrievalReferenceNumber: str = Field(..., min_length=1)
    amount: str = Field(..., min_length=1)
    merchantId: str = Field(..., min_length=1)
    terminalId: str = Field(..., min_length=1)
    uniqueId: str = Field(..., min_length=1)
    type: Optional[str] = None
    properties: Optional[Properties] = None

class TransactionRequest(BaseModel):
    merchant_id: str
    terminal_id: str

@app.post("/send_notification")
async def send_notification(payload: NotificationPayload):
    try:
        # Validate mandatory fields
        mandatory_fields = [
            "mobileNumber", "remark1", "retrievalReferenceNumber", 
            "amount", "merchantId", "terminalId", "uniqueId"
        ]
        
        for field in mandatory_fields:
            if not getattr(payload, field):
                raise ValueError(f"{field} is mandatory and cannot be empty")
        
        # If we reach this point, all mandatory fields are present and non-empty
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
    
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@app.post("/get_transactions")
async def get_transactions(request: TransactionRequest):
    transactions_response = api.get_last_5_transactions(request.merchant_id, request.terminal_id)
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