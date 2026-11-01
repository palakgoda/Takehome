import os
from dotenv import load_dotenv
from fastapi import FastAPI
from paypal_client import get_token, create_invoice
from pydantic import BaseModel
from agent import parse_invoice_request
from fastapi import HTTPException

load_dotenv()
app = FastAPI()

class TextRequest(BaseModel):
    message: str
    client_email: str | None = None

@app.get("/")
def home():
    return {"status": "TakeHome running"}

@app.get("/test-token")
async def test_token():
    token = await get_token()
    return {"token_preview": token[:12] + "..."}

@app.get("/test-invoice")
async def test_invoice():
    return await create_invoice(os.getenv("PAYPAL_PERSONAL_EMAIL"), "Logo design", "100.00")

@app.post("/parse")
async def parse(req: TextRequest):
    try:
        return await parse_invoice_request(req.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")

@app.post("/create-from-text")
async def create_from_text(req: TextRequest):
    try:
        parsed = await parse_invoice_request(req.message)
        email = req.client_email or os.getenv("PAYPAL_PERSONAL_EMAIL")
        result = await create_invoice(email, parsed.description, parsed.amount,
                                      parsed.currency, parsed.due_days)
        return {"parsed": parsed, "invoice": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")
    