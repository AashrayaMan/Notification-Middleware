from fastapi import FastAPI, HTTPException, Depends, Header, Request
from pydantic import BaseModel, Field, EmailStr, validator, ValidationError
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
import email_validator
from pymongo import MongoClient
from bson import ObjectId

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

app = FastAPI()

# Load API credentials from environment variables
API_SECRET = os.getenv('FONEPAY_API_SECRET')

# MongoDB connection
Mongodb_URL = MongoClient(os.getenv('DB_URL'))
db = Mongodb_URL[os.getenv('DB_NAME')]
collection = db['merchant-registry']
transaction_collection = db['transaction']

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

def generate_signature(api_secret: str, nonce: str, api_key: str, body: str) -> str:
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
            raise HTTPException(status_code=401, detail={"message": "Invalid authorization type", "code": "2"})

        api_key, nonce, signature = auth_data.split(":")
        logger.debug(f"Parsed auth data - API Key: {api_key}, Nonce: {nonce}")

        # Get the request body
        body = await request.body()
        body_str = body.decode()
        logger.debug(f"Request body: {body_str}")

        # Verify the signature
        expected_signature = generate_signature(API_SECRET, nonce, api_key, body_str)
        
        logger.debug(f"Expected signature: {expected_signature}")
        logger.debug(f"Received signature: {signature}")

        if signature != expected_signature:
            raise HTTPException(status_code=401, detail={"message": "Invalid signature", "code": "2"})

    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=401, detail={"message": "Invalid authorization data", "code": "2"})

def get_device_info(merchant_id: str, terminal_id: str):
    """
    Connect to MongoDB, check for merchantId and terminalId, 
    and retrieve enabled services and machine identifier.
    """
    device = collection.find_one({
        "fonepay.merchantId": merchant_id,
        "fonepay.terminalId": terminal_id
    })
    
    if not device:
        logger.error(f"No device found for merchantId: {merchant_id} and terminalId: {terminal_id}")
        return None, []
    
    machine_identifier = device.get('machineIdentifier')
    enabled_services = device.get('enabledServices', [])
    
    logger.info(f"Found device: {machine_identifier} with enabled services: {enabled_services}")
    return machine_identifier, enabled_services

@app.post("/notification/send", response_model=SendNotificationResponse)
async def send_notification(request: SendNotificationRequest, authorized: bool = Depends(verify_hmac)):
    logger.info(f"Received notification request for mobile number: {request.mobileNumber}")

    try:
        # Get device info
        machine_identifier, enabled_services = get_device_info(request.merchantId, request.terminalId)
        
        if not machine_identifier:
            raise HTTPException(status_code=402, detail={"message": "Device not found", "code": "3"})

        # Save transaction details to MongoDB
        transaction_details = request.dict()
        transaction_details['timestamp'] = datetime.now()
        transaction_collection.insert_one(transaction_details)

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

        if response.status:
            message = json.dumps({
                'amount': request.amount,
                'mobileNumber': request.mobileNumber,
                'email': request.properties.email if request.properties else None,
                'merchantId': request.merchantId,
                'terminalId': request.terminalId,
                'commission': request.properties.commission if request.properties else None,
                'machineIdentifier': machine_identifier,
                'enabledServices': enabled_services
            })
            
            receiver_script = os.path.join(os.path.dirname(__file__), 'receiver.py')
            subprocess.Popen([sys.executable, receiver_script, message], 
                     stdout=subprocess.DEVNULL, 
                     stderr=subprocess.DEVNULL)
            logger.info(f"Called receiver.py with message: {message}")

        return response

    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail={"message": "Payload Invalid", "code": "1"})

@app.post("/callback", response_model=CallbackResponse)
async def callback(request: CallbackRequest, authorized: bool = Depends(verify_hmac)):
    logger.info(f"Received callback request for merchant: {request.merchantId}")
    
    # Check if merchantId exists
    merchant = collection.find_one({"fonepay.merchantId": request.merchantId})
    if not merchant:
        raise HTTPException(status_code=403, detail={"message": "Invalid MerchantID", "code": "4"})

    # Check if terminalId exists
    terminal = collection.find_one({"fonepay.merchantId": request.merchantId, "fonepay.terminalId": request.terminalId})
    if not terminal:
        raise HTTPException(status_code=403, detail={"message": "Invalid TerminalID", "code": "4"})
    
    # Retrieve the last 5 transactions from MongoDB
    transactions = list(transaction_collection.find(
        {"merchantId": request.merchantId, "terminalId": request.terminalId}
    ).sort("timestamp", -1).limit(5))

    transaction_details = []
    for transaction in transactions:
        # Convert ObjectId to string for serialization
        transaction['_id'] = str(transaction['_id'])
        
        # Create TransactionNotificationDetail object
        detail = TransactionNotificationDetail(
            mobileNumber=transaction['mobileNumber'],
            merchantId=transaction['merchantId'],
            terminalId=transaction['terminalId'],
            retrievalReferenceNumber=transaction['retrievalReferenceNumber'],
            amount=transaction['amount'],
            remark1=transaction['remark1'],
            type=transaction.get('type'),
            uniqueId=transaction['uniqueId'],
            properties=Properties(**transaction['properties']) if transaction.get('properties') else None
        )
        transaction_details.append(detail)

    return CallbackResponse(transactionNotificationDetails=transaction_details)

@app.get("/")
async def root():
    return {"message": "Notification API for Acquirers is running"}