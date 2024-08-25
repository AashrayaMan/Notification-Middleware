from fastapi import FastAPI, HTTPException, Depends, Header, Request
from pydantic import BaseModel, Field, EmailStr, validator, ValidationError
from typing import List, Optional
from datetime import datetime
import hmac
import hashlib
import base64
import logging
import json
import os
from dotenv import load_dotenv
import email_validator
from service_check import get_device_data, check_enabled_services
from email_sender import email_alert

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Load API credentials from environment variables
API_KEY = os.getenv('FONEPAY_API_KEY')
API_SECRET = os.getenv('FONEPAY_API_SECRET')

class Properties(BaseModel):
    commission: Optional[float] = None
    sessionSrlNo: Optional[str] = None
    txnDate: Optional[datetime] = None
    secondaryMobileNumber: Optional[str] = None
    email: Optional[str] = None
    initiator: Optional[str] = None

    @validator('secondaryMobileNumber')
    def validate_secondary_mobile_number(cls, v):
        if v and (not v.isdigit() or len(v) != 10):
            raise ValueError('Payload Invalid')
        return v

    @validator('txnDate', pre=True)
    def parse_datetime(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValueError("Payload Invalid")
        return v

    @validator('email')
    def validate_email(cls, v):
        if v:
            try:
                email_validator.validate_email(v)
            except email_validator.EmailNotValidError:
                raise ValueError("Payload Invalid")
        return v

    @validator('commission')
    def validate_commission(cls, v):
        if v is not None:
            try:
                float(v)
            except ValueError:
                raise ValueError("Payload Invalid")
        return v

class SendNotificationRequest(BaseModel):
    mobileNumber: str = Field(..., pattern=r'^\d{10}$')
    merchantId: str
    terminalId: str
    retrievalReferenceNumber: str
    amount: str
    remark1: str
    type: Optional[str] = None
    uniqueId: str
    properties: Optional[Properties] = None

    @validator('amount')
    def validate_amount(cls, v):
        if not v.replace('.', '').isdigit():
            raise ValueError('Payload Invalid')
        return v

    @validator('type')
    def validate_type(cls, v):
        if v and v not in ['alert', 'otp']:
            raise ValueError('Payload Invalid')
        return v

    @validator('mobileNumber')
    def validate_mobile_number(cls, v):
        if not v.isdigit() or len(v) != 10:
            raise ValueError('Payload Invalid')
        return v

class SendNotificationResponse(BaseModel):
    status: bool
    message: str
    code: str
    data: dict
    httpStatus: int

def generate_signature(api_key: str, api_secret: str, nonce: str, body: str) -> str:
    message = f" {api_key} {nonce} {body} "
    signature = base64.b64encode(
        hmac.new(api_secret.encode(), message.encode(), hashlib.sha512).digest()
    ).decode()
    return signature

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

        body = await request.body()
        body_str = body.decode()
        logger.debug(f"Request body: {body_str}")

        expected_signature = generate_signature(API_KEY, API_SECRET, nonce, body_str)
        
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

    try:
        # Check enabled services
        device_data = get_device_data(request.uniqueId)  # Assuming uniqueId is the device ID
        if device_data is None:
            raise HTTPException(status_code=404, detail="Device not found")

        enabled_services = device_data.get('enabledServices', [])

        # Prepare notification content
        subject = f"Transaction Notification for {request.merchantId}"
        body = f"Amount: {request.amount}\nMobile: {request.mobileNumber}\nRemark: {request.remark1}"

        # Send email notification if enabled and email is provided
        if 'EMAIL' in enabled_services and request.properties and request.properties.email:
            try:
                email_alert(subject, body, request.properties.email)
                logger.info(f"Email sent to {request.properties.email}")
            except Exception as e:
                logger.error(f"Failed to send email: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to send email notification")
        else:
            logger.info("Email notification not sent: Either EMAIL service not enabled or email not provided")

        response = SendNotificationResponse(
            status=True,
            message="Notification processed successfully",
            code="0",
            data={
                "mobileNumber": request.mobileNumber,
                "msgId": f"MN-{int(datetime.now().timestamp())}"
            },
            httpStatus=200
        )

        return response

    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail="Payload Invalid")
    except Exception as e:
        logger.error(f"Error processing notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/")
async def root():
    return {"message": "Notification API for Acquirers is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)