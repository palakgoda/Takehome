import os
from dotenv import load_dotenv
from pydantic import BaseModel
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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
    response = await client.aio.models.generate_content(
        model="gemini-3.8-flash",
        contents=PROMPT.format(message=message),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=InvoiceRequest,
        ),
    )
    return response.parsed
