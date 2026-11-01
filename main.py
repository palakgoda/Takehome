import os
from datetime import date

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from paypal_client import (
    get_token,
    create_invoice,
    list_invoices,
    get_invoice,
    send_reminder,
)
from agent import parse_invoice_request, draft_reminder
from fees import estimate_inr
from insights import build_insights
from fastapi.responses import FileResponse

load_dotenv()
app = FastAPI()

class TextRequest(BaseModel):
    message: str
    client_email: str | None = None

class ReminderSend(BaseModel):
    invoice_id: str
    subject: str
    note: str

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
    
@app.get("/invoices")
async def invoices():
    return await list_invoices()

@app.get("/reminder-draft/{invoice_id}")
async def reminder_draft(invoice_id: str, tone: str = "friendly"):
    inv = await get_invoice(invoice_id)
    due = inv["detail"].get("payment_term", {}).get("due_date")
    days_overdue = (date.today() - date.fromisoformat(due)).days if due else 0
    amount = inv["amount"]["value"]
    currency = inv["amount"]["currency_code"]
    draft = await draft_reminder(amount, currency, due or "not set", days_overdue, tone)
    return {"invoice_id": invoice_id, "days_overdue": days_overdue, "draft": draft}

@app.post("/send-reminder")
async def send_reminder_route(req: ReminderSend):
    return await send_reminder(req.invoice_id, req.subject, req.note)

@app.get("/estimate")
async def estimate(amount: float, currency: str = "USD"):
    try:
        return await estimate_inr(amount, currency.upper())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")

@app.post("/preview")
async def preview(req: TextRequest):
    parsed = await parse_invoice_request(req.message)
    est = await estimate_inr(float(parsed.amount), parsed.currency)
    return {"parsed": parsed, "estimate": est}

@app.get("/insights")
async def insights():
    return build_insights(await list_invoices())

class ConfirmRequest(BaseModel):
    description: str
    amount: str
    currency: str = "USD"
    due_days: int = 7
    client_email: str | None = None

@app.get("/app")
def dashboard_page():
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))

@app.get("/dashboard")
async def dashboard():
    invs = await list_invoices()
    return {"invoices": invs, "insights": build_insights(invs)}

@app.post("/confirm-invoice")
async def confirm_invoice(req: ConfirmRequest):
    email = req.client_email or os.getenv("PAYPAL_PERSONAL_EMAIL")
    return await create_invoice(email, req.description, req.amount, req.currency, req.due_days)
def guard(request: Request,
          creds: HTTPBasicCredentials = Depends(HTTPBasic(auto_error=False))):
    pw = os.getenv("DEMO_PASSWORD")
    if not pw or request.url.path == "/":
        return          # no password set (local dev), or the "/" health check
    if not creds or not secrets.compare_digest(creds.password.encode(), pw.encode()):
        raise HTTPException(401, "Password required", headers={"WWW-Authenticate": "Basic"})

app = FastAPI(dependencies=[Depends(guard)])