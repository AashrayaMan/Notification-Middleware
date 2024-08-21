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
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import re
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(root_path="/api/v1")

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
        # Return the same response as the mock server
        return {
            "status": True,
            "message": "SMS delivered successfully",
            "code": "0",
            "data": {
                "mobileNumber": payload["mobileNumber"],
                "msgId": "MN-1553144161875"
            },
            "httpStatus": 200
        }

    def get_last_5_transactions(self, merchant_id, terminal_id):
        return {
            "transactionNotificationDetails": [
                {
                    "mobileNumber": "98xxxxxxxx",
                    "remark1": "Message to send",
                    "retrievalReferenceNumber": "701125454",
                    "amount": "400",
                    "merchantId": "99XXXXXXXXXX",
                    "terminalId": "222202XXXXXXXXXX",
                    "type": "alert",
                    "uniqueId": "202307201141001",
                    "properties": {
                        "txnDate": "2023-07-22 01:00:10",
                        "secondaryMobileNumber": "98xxxxxxxx",
                        "email": "random@gmail.com",
                        "sessionSrlNo": "69",
                        "commission": "10.00",
                        "initiator": "98xxxxxxxx"
                    }
                }
            ]
        }

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
    merchantId: str
    terminalId: str

@app.post("/notification/send")
async def send_notification(payload: NotificationPayload):
    try:
        logger.info("Received payload")
        notification_response = api.send_notification(payload.model_dump())
        
        if notification_response:
            logger.info(f"Notification sent successfully: {notification_response}")
            
            # Run koili_ipn.py with the amount from the transaction details
            amount = payload.amount
            run_koili_ipn(amount)
            
            # Run the client script
            run_client_script(payload.model_dump())
            
            return notification_response
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

@app.post("/callback")
async def callback(request: TransactionRequest):
    transactions_response = api.get_last_5_transactions(request.merchantId, request.terminalId)
    if transactions_response:
        logger.info(f"Transactions retrieved successfully: {transactions_response}")
        return transactions_response
    else:
        logger.error("Failed to retrieve transactions")
        raise HTTPException(status_code=500, detail="Failed to retrieve the transactions")

# To run in development mode, use the command:
# `fastapi dev`
# For production, you can use a command like:
# `fastapi run --host 0.0.0.0 --port 8000`