from pydantic import BaseModel, Field, EmailStr, field_validator
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
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import re
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

def run_client_script(transaction_details):
    script_path = os.path.join(os.path.dirname(__file__), 'receiver.py')
    
    properties = transaction_details.get('properties', {})
    
    args = [
        sys.executable,
        script_path,
        transaction_details['merchantId'],
        transaction_details['amount'],
        transaction_details['mobileNumber'],
        properties.get('email', ''),
        properties.get('commission', '')
    ]
    
    try:
        subprocess.Popen(args)
        logger.info(f"Launched client.py for transaction: {transaction_details['uniqueId']}")
    except Exception as e:
        logger.error(f"Error launching client script: {str(e)}")

def run_koili_ipn(amount):
    script_path = os.path.join(os.path.dirname(__file__), 'koili_ipn.py')
    
    args = [
        sys.executable,
        script_path,
        str(amount)
    ]
    
    try:
        subprocess.Popen(args)
        logger.info(f"Launched koili_ipn.py with amount: {amount}")
    except Exception as e:
        logger.error(f"Error launching koili_ipn script: {str(e)}")

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
base_url = os.getenv('FONEPAY_API_URL')
api_key = os.getenv('FONEPAY_API_KEY')
api_secret = os.getenv('FONEPAY_API_SECRET')

api = FonepayNotificationAPI(base_url, api_key, api_secret)

class Properties(BaseModel):
    txnDate: Optional[str] = None
    secondaryMobileNumber: Optional[str] = None
    email: Optional[EmailStr] = None
    sessionSrlNo: Optional[str] = None
    commission: Optional[str] = None
    initiator: Optional[str] = None

    @field_validator('secondaryMobileNumber')
    @classmethod
    def validate_secondary_mobile_number(cls, v):
        if v and not re.match(r'^\d{10}$', v):
            raise ValueError('secondaryMobileNumber must be a 10-digit number')
        return v

    @field_validator('commission')
    @classmethod
    def validate_commission(cls, v):
        if v is not None:
            if not isinstance(v, str):
                raise ValueError('commission must be a string')
            try:
                float_value = float(v)
                if float_value < 0:
                    raise ValueError('commission must be a non-negative number')
            except ValueError:
                raise ValueError('commission must be a valid number string')
        return v

class NotificationPayload(BaseModel):
    mobileNumber: str = Field(..., min_length=10, max_length=10)
    remark1: str = Field(..., min_length=1)
    retrievalReferenceNumber: str = Field(..., min_length=1)
    amount: str = Field(..., min_length=1)
    merchantId: str = Field(..., min_length=1)
    terminalId: str = Field(..., min_length=1)
    uniqueId: str = Field(..., min_length=1)
    type: Optional[str] = Field(None, pattern='^(otp|alert)$')
    properties: Optional[Properties] = None

    @field_validator('mobileNumber')
    @classmethod
    def validate_mobile_number(cls, v):
        if not v.isdigit():
            raise ValueError('mobileNumber must contain only digits')
        return v

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if not isinstance(v, str):
            raise ValueError('amount must be a string')
        try:
            float_value = float(v)
            if float_value <= 0:
                raise ValueError('amount must be a positive number')
        except ValueError:
            raise ValueError('amount must be a valid number string')
        return v

class TransactionRequest(BaseModel):
    merchant_id: str
    terminal_id: str

def validate_notification_payload(payload: NotificationPayload):
    return payload

@app.post("/send_notification")
async def send_notification(payload: NotificationPayload):
    try:
        logger.info(f"Received payload: {payload.model_dump_json()}")
        notification_response = api.send_notification(payload.model_dump())
        
        if notification_response:
            logger.info(f"Notification sent successfully: {notification_response}")
            
            # Run koili_ipn.py with the amount from the transaction details
            amount = payload.amount
            run_koili_ipn(amount)
            
            # Run the client script
            run_client_script(payload.model_dump())
            
            return {
                "status": "success",
                "message": "Notification sent successfully",
                "response": notification_response
            }
        else:
            logger.error("Failed to send notification")
            raise HTTPException(status_code=500, detail="Failed to send notification")
    
    except HTTPException as he:
        logger.error(f"HTTPException: {str(he)}")
        raise he
    except ValueError as ve:
        logger.error(f"ValueError: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@app.post("/get_transactions")
async def get_transactions(
    request: TransactionRequest,
    payload: NotificationPayload = Depends(validate_notification_payload)
):
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