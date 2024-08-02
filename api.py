from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import random
import time
import hmac
import hashlib
import base64

app = FastAPI()

SECRET_KEY = "7de9fd42a0b0403ea0e5c73b8deb673b"

class RandomData(BaseModel):
    number: int
    string: str
    boolean: bool
    email: str

def verify_signature(method: str, path: str, timestamp: str, payload: str, signature: str):
    string_to_sign = f"{method}\n{path}\n{timestamp}\n{payload}"
    print(f"Server string to sign: {string_to_sign}")  # Debug print
    expected_signature = base64.b64encode(
        hmac.new(
            SECRET_KEY.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha512
        ).digest()
    ).decode('utf-8')
    return hmac.compare_digest(expected_signature, signature)

@app.get("/random")
async def get_random_data(
    x_timestamp: str = Header(...),
    x_signature: str = Header(...)
):
    if not verify_signature("GET", "/random", x_timestamp, "", x_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    random_data = RandomData(
        number=random.randint(1, 100),
        string=''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=10)),
        boolean=random.choice([True, False]),
        email="aashraya11@gmail.com"
    )
    return random_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)