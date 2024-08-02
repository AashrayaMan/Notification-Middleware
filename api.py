from fastapi import FastAPI
from pydantic import BaseModel
 
app = FastAPI(title="User Information API", description="API for managing user information")
 
class UserInfo(BaseModel):
    value: str
 
@app.post("/name", response_model=UserInfo)
async def set_name(user_info: UserInfo):
    return user_info
 
@app.post("/title", response_model=UserInfo)
async def set_title(user_info: UserInfo):
    return user_info
 
@app.post("/location", response_model=UserInfo)
async def set_location(user_info: UserInfo):
    return user_info
 
@app.post("/email", response_model=UserInfo)
async def set_email(user_info: UserInfo):
    return user_info
 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)