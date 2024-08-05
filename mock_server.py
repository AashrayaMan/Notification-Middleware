from flask import Flask, request, jsonify
import hmac
import hashlib
import base64

app = Flask(__name__)

# Mock API key and secret
API_KEY = "test@test.com.np"
API_SECRET = "testApiSecret"

def verify_signature(auth_header, body):
    parts = auth_header.split()
    if len(parts) != 2 or parts[0] != "HmacSHA512":
        return False
    
    api_key, nonce, signature = parts[1].split(':')
    if api_key != API_KEY:
        return False
    
    expected_signature = generate_signature(nonce, body)
    return signature == expected_signature

def generate_signature(nonce, body):
    signature_data = f" {API_KEY} {nonce} {body} "
    hmac_obj = hmac.new(API_SECRET.encode(), signature_data.encode(), hashlib.sha512)
    return base64.b64encode(hmac_obj.digest()).decode()

@app.route('/notification/send', methods=['POST'])
def send_notification():
    if not verify_signature(request.headers.get('Authorization', ''), request.data.decode()):
        return jsonify({"error": "Invalid authorization"}), 403
    
    # Mock successful response
    return jsonify({
        "status": True,
        "message": "SMS delivered successfully",
        "code": "0",
        "data": {
            "mobileNumber": "98xxxxxxxx",
            "msgId": "MN-1553144161875"
        },
        "httpStatus": 200
    })

@app.route('/callback', methods=['POST'])
def callback():
    if not verify_signature(request.headers.get('Authorization', ''), request.data.decode()):
        return jsonify({"error": "Invalid authorization"}), 403
    
    # Mock response with last 5 transactions
    return jsonify({
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
                    "email": "fpaxxx@fpay.com",
                    "sessionSrlNo": "69",
                    "commission": "10.00",
                    "initiator": "98xxxxxxxx"
                }
            }
            # ... (repeat this structure 4 more times for 5 total transactions)
        ]
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)