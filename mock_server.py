from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import hmac
import hashlib
import base64

app = FastAPI()

# Mock API key and secret
API_KEY = "test@test.com.np"
API_SECRET = "testApiSecret"

def verify_signature(auth_header: str, body: bytes) -> bool:
    parts = auth_header.split()
    if len(parts) != 2 or parts[0] != "HmacSHA512":
        return False
    
    api_key, nonce, signature = parts[1].split(':')
    if api_key != API_KEY:
        return False
    
    expected_signature = generate_signature(nonce, body.decode())
    return signature == expected_signature

def generate_signature(nonce: str, body: str) -> str:
    signature_data = f" {API_KEY} {nonce} {body} "
    hmac_obj = hmac.new(API_SECRET.encode(), signature_data.encode(), hashlib.sha512)
    return base64.b64encode(hmac_obj.digest()).decode()

@app.post('/notification/send')
async def send_notification(request: Request):
    body = await request.body()
    if not verify_signature(request.headers.get('Authorization', ''), body):
        raise HTTPException(status_code=403, detail="Invalid authorization")
    
    # Mock successful response
    return JSONResponse({
        "status": True,
        "message": "SMS delivered successfully",
        "code": "0",
        "data": {
            "mobileNumber": "98xxxxxxxx",
            "msgId": "MN-1553144161875"
        },
        "httpStatus": 200
    })

@app.post('/callback')
async def callback(request: Request):
    body = await request.body()
    if not verify_signature(request.headers.get('Authorization', ''), body):
        raise HTTPException(status_code=403, detail="Invalid authorization")
    
    # Mock response with last 5 transactions
    return JSONResponse({
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
                    "email": "aashraya11@gmail.com",
                    "sessionSrlNo": "69",
                    "commission": "10.00",
                    "initiator": "98xxxxxxxx"
                }
            }
            
        ]
    })

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)