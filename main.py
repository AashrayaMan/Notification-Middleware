from fastapi import FastAPI, HTTPException, Depends, Header, Request
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import hmac
import hashlib
import base64
import logging
import json
import subprocess
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Simulated API key and secret (replace with secure storage in production)
API_KEY = os.getenv('FONEPAY_API_KEY')
API_SECRET = os.getenv('FONEPAY_API_SECRET')

class Properties(BaseModel):
    commission: Optional[str] = None
    sessionSrlNo: Optional[str] = None
    txnDate: Optional[str] = None
    secondaryMobileNumber: Optional[str] = None
    email: Optional[str] = None
    initiator: Optional[str] = None

class SendNotificationRequest(BaseModel):
    mobileNumber: str
    merchantId: str
    terminalId: str
    retrievalReferenceNumber: str
    amount: str
    remark1: str
    type: Optional[str] = None
    uniqueId: str
    properties: Optional[Properties] = None

class SendNotificationResponse(BaseModel):
    status: bool
    message: str
    code: str
    data: dict
    httpStatus: int

class CallbackRequest(BaseModel):
    merchantId: str
    terminalId: str

class TransactionNotificationDetail(BaseModel):
    mobileNumber: str
    merchantId: str
    terminalId: str
    retrievalReferenceNumber: str
    amount: str
    remark1: str
    type: Optional[str] = None
    uniqueId: str
    properties: Optional[Properties] = None

class CallbackResponse(BaseModel):
    transactionNotificationDetails: List[TransactionNotificationDetail]

async def verify_hmac(request: Request, authorization: str = Header(...)):
    logger.debug(f"Received authorization header: {authorization}")
    try:
        auth_type, auth_data = authorization.split(" ", 1)
        if auth_type != "HmacSHA512":
            raise HTTPException(status_code=403, detail="Invalid authorization type")

        api_key, nonce, signature = auth_data.split(":")
        logger.debug(f"Parsed auth data - API Key: {api_key}, Nonce: {nonce}")
        
        if api_key != API_KEY:
            raise HTTPException(status_code=403, detail="Invalid API key")

        # In a real implementation, you would validate the nonce here

        # Get the request body
        body = await request.body()
        body_str = body.decode()
        logger.debug(f"Request body: {body_str}")

        # Verify the signature
        message = f" {API_KEY} {nonce} {body_str} "
        expected_signature = base64.b64encode(
            hmac.new(API_SECRET.encode(), message.encode(), hashlib.sha512).digest()
        ).decode()
        
        logger.debug(f"Expected signature: {expected_signature}")
        logger.debug(f"Received signature: {signature}")

        if signature != expected_signature:
            raise HTTPException(status_code=403, detail="Invalid signature")

    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=403, detail="Invalid authorization data")

@app.post("/notification/send", response_model=SendNotificationResponse)
async def send_notification(request: SendNotificationRequest, authorized: bool = Depends(verify_hmac)):
    logger.info(f"Received notification request for mobile number: {request.mobileNumber}")
    # Implement your notification sending logic here
    # This is a mock response
    response = SendNotificationResponse(
        status=True,
        message="SMS delivered successfully",
        code="0",
        data={
            "mobileNumber": request.mobileNumber,
            "msgId": f"MN-{int(datetime.now().timestamp())}"
        },
        httpStatus=200
    )

    # If the notification was successful, call receiver.py
    if response.status:
        receiver_script = os.path.join(os.path.dirname(__file__), 'receiver.py')
        message = json.dumps({
            'amount': request.amount,
            'mobileNumber': request.mobileNumber,
            'email': request.properties.email if request.properties else None,
            'merchantId': request.merchantId,
            'commission': request.properties.commission if request.properties else None
        })
        subprocess.Popen([sys.executable, receiver_script, message])
        logger.info(f"Called receiver.py with message: {message}")

    return response

@app.post("/callback", response_model=CallbackResponse)
async def callback(request: CallbackRequest, authorized: bool = Depends(verify_hmac)):
    logger.info(f"Received callback request for merchant: {request.merchantId}")
    # Implement your logic to fetch last 5 transactions here
    # This is a mock response
    mock_transaction = TransactionNotificationDetail(
        mobileNumber="98xxxxxxxx",
        merchantId=request.merchantId,
        terminalId=request.terminalId,
        retrievalReferenceNumber="701125454",
        amount="400",
        remark1="Message to send",
        type="alert",
        uniqueId="202307201141001",
        properties=Properties(
            txnDate="2023-07-22 01:00:10",
            secondaryMobileNumber="9012325645",
            email="cn@fpay.com",
            sessionSrlNo="69",
            commission="10.00",
            initiator="98xxxxxxxx"
        )
    )
    return CallbackResponse(transactionNotificationDetails=[mock_transaction] * 5)

@app.get("/")
async def root():
    return {"message": "Notification API for Acquirers is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)