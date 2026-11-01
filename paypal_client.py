import os, httpx
from dotenv import load_dotenv
from datetime import date, timedelta
from fastapi import HTTPException


load_dotenv()
BASE = os.getenv("PAYPAL_BASE_URL")

async def get_token():
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{BASE}/v1/oauth2/token",
            auth=(os.getenv("PAYPAL_CLIENT_ID"), os.getenv("PAYPAL_CLIENT_SECRET")),
            data={"grant_type": "client_credentials"},
        )
        r.raise_for_status()
        return r.json()["access_token"]
    
async def create_invoice(client_email: str, description: str, amount: str,
                         currency: str = "USD", due_days: int = 7):
    token = await get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    due = (date.today() + timedelta(days=due_days)).isoformat()
    body = {
        "detail": {
            "currency_code": currency,
            "note": "Created by TakeHome",
            "payment_term": {"due_date": due},
        },
        "invoicer": {"email_address": os.getenv("PAYPAL_BUSINESS_EMAIL")},
        "primary_recipients": [{"billing_info": {"email_address": client_email}}],
        "items": [{
            "name": description,
            "quantity": "1",
            "unit_amount": {"currency_code": currency, "value": amount},
        }],
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE}/v2/invoicing/invoices", json=body, headers=headers)
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        invoice_id = r.json()["href"].split("/")[-1]
        s = await client.post(
            f"{BASE}/v2/invoicing/invoices/{invoice_id}/send",
            json={"send_to_recipient": True, "send_to_invoicer": False},
            headers=headers,
        )
        if s.status_code >= 400:
            raise HTTPException(status_code=s.status_code, detail=s.text)
        return {"invoice_id": invoice_id, "status": "sent", "due_date": due}

async def list_invoices():
    token = await get_token()
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BASE}/v2/invoicing/invoices",
            params={"page": 1, "page_size": 20, "total_required": "true"},
            headers=headers,
        )
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        data = r.json()

    today = date.today().isoformat()
    result = []
    for inv in data.get("items", []):
        status = inv.get("status")
        due = inv.get("detail", {}).get("payment_term", {}).get("due_date")
        overdue = status in ("SENT", "UNPAID", "PARTIALLY_PAID") and due and due < today
        result.append({
            "id": inv.get("id"),
            "status": "OVERDUE" if overdue else status,
            "due_date": due,
            "amount": inv.get("amount", {}).get("value"),
            "currency": inv.get("amount", {}).get("currency_code"),
        })
    return result

async def get_invoice(invoice_id: str):
    token = await get_token()
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE}/v2/invoicing/invoices/{invoice_id}", headers=headers)
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()

async def send_reminder(invoice_id: str, subject: str, note: str):
    token = await get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    body = {"subject": subject, "note": note, "send_to_invoicer": False}
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE}/v2/invoicing/invoices/{invoice_id}/remind",
                              json=body, headers=headers)
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return {"invoice_id": invoice_id, "status": "reminder_sent"}
    