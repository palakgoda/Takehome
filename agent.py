import os
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai import errors

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

class InvoiceRequest(BaseModel):
    client_name: str
    description: str
    amount: str        # e.g. "250.00"
    currency: str      # e.g. "USD"
    due_days: int      # days from today

PROMPT = """Extract invoice details from the freelancer's message.
- amount must be a plain number string like "250.00" (no symbols)
- currency is a 3-letter code; default to USD if not stated
- due_days defaults to 7 if not stated
- description should be short and professional
Message: {message}"""

async def parse_invoice_request(message: str) -> InvoiceRequest:
    response = await generate_with_retry(PROMPT.format(message=message), InvoiceRequest)
    return response.parsed

class ReminderDraft(BaseModel):
    subject: str
    note: str

async def draft_reminder(amount: str, currency: str, due_date: str,
                         days_overdue: int, tone: str = "friendly") -> ReminderDraft:
    prompt = f"""Write a short payment reminder email from a freelancer to a client.
Amount: {amount} {currency}. Due date: {due_date}. Days overdue: {days_overdue} (0 or less means not overdue yet).
Tone: {tone}. Keep it polite, professional, under 60 words, no placeholders like [Name].
Return a subject and a note."""
    response = await generate_with_retry(prompt, ReminderDraft)
    return response.parsed

async def generate_with_retry(prompt: str, schema, retries: int = 4):
    for attempt in range(retries):
        try:
            return await client.aio.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
        except errors.ServerError:
            if attempt == retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
