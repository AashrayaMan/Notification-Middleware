from flask import Flask, request, jsonify
import hmac
import hashlib
import base64
import json

app = Flask(__name__)

# Replace these with your actual API key and secret
API_KEY = "test@test.com.np"
API_SECRET = "your_api_secret_here"

def verify_hmac(api_key, nonce, signature, body):
    # Reconstruct the signature data
    signature_data = f" {api_key} {nonce} {body} "
    
    # Generate HMAC
    hmac_obj = hmac.new(API_SECRET.encode(), signature_data.encode(), hashlib.sha512)
    expected_signature = base64.b64encode(hmac_obj.digest()).decode()
    
    return hmac.compare_digest(signature, expected_signature)

@app.route('/notification/send', methods=['POST'])
def send_notification():
    # Check content type
    if request.headers.get('Content-Type') != 'application/json':
        return jsonify({"error": "Content-Type must be application/json"}), 400

    # Parse authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('HmacSHA512 '):
        return jsonify({"error": "Invalid Authorization header"}), 401

    auth_parts = auth_header[11:].split(':')
    if len(auth_parts) != 3:
        return jsonify({"error": "Invalid Authorization header format"}), 401

    api_key, nonce, signature = auth_parts

    # Verify API key
    if api_key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 401

    # Get request body as a string
    body = request.data.decode('utf-8')

    # Verify HMAC signature
    if not verify_hmac(api_key, nonce, signature, body):
        return jsonify({"error": "Invalid signature"}), 401

    # Parse and validate request body
    try:
        data = json.loads(body)
        required_fields = ['mobileNumber', 'remark1', 'retrievalReferenceNumber', 'amount', 'merchantId', 'terminalId', 'type', 'uniqueId', 'properties']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        required_properties = ['txnDate', 'secondaryMobileNumber', 'email', 'sessionSrlNo', 'commission', 'initiator']
        for prop in required_properties:
            if prop not in data['properties']:
                return jsonify({"error": f"Missing required property: {prop}"}), 400
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON in request body"}), 400

    # Process the notification (implement your logic here)
    # For this example, we'll just return a success message
    return jsonify({"message": "Notification sent successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)