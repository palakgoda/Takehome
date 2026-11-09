# TakeHome

**Describe a job in one sentence. TakeHome invoices your client through PayPal and shows what you'll actually receive in rupees.**

Built for the PayPal AI Hackathon with the PayPal Developer Platform (Invoicing API, sandbox) and AI (Google Gemini).

>Live demo: https://takehome-ycf0.onrender.com/app
>Demo login: username judge (any username works), password takehome2026
>Demo video: https://www.youtube.com/watch?v=Uh3NkCnLXxQ
>License: MIT

---

## The problem

Indian freelancers who bill international clients lose time and money in three places:

1. **Invoicing is tedious.** Filling in forms for every small job.
2. **Nobody knows what will land in their bank.** PayPal's fees and currency conversion markup make the final rupee amount hard to predict.
3. **Chasing payments is awkward.** Writing the right reminder, in the right tone, at the right time.

## What TakeHome does

| Feature | How it works |
|---|---|
| **Text to invoice** | Type "Invoice Acme Corp $250 for the landing page design, due in 10 days". Gemini extracts the client, amount, currency, description and due date. |
| **Take-home estimate in INR** | Before anything is sent, you see roughly how many rupees you'll receive after PayPal's fee, GST on the fee, and the currency conversion markup. All rates are configurable. |
| **Approve before it sends** | The AI only drafts and previews. Nothing is sent to a client until you press **Send invoice**. |
| **Live payment status** | The dashboard checks PayPal every 15 seconds. When a client pays, the row highlights and a notification appears, with no manual refresh. |
| **AI reminder drafts** | For unpaid or overdue invoices, Gemini writes a reminder in a tone that fits how late the payment is. You edit and approve it before it goes out. |
| **Client reliability** | From each client's payment history, TakeHome shows who pays early, who pays late, and which invoices to chase first. |

## How it works

```
Browser (index.html)
   │  sentence
   ▼
FastAPI backend ──► Gemini API      (parse sentence, draft reminders)
   │
   ├──► fees.py                     (INR take-home estimate, live exchange rate)
   │
   └──► PayPal Invoicing API v2     (create, send, list, remind)
              (Sandbox)
```

**Stack:** Python, FastAPI, httpx, Google Gemini (`google-genai`), PayPal Invoicing REST API (v2), plain HTML/CSS/JavaScript for the dashboard.

**Project layout**

```
takehome/
├── main.py            # FastAPI routes
├── paypal_client.py   # PayPal auth, invoices, reminders
├── agent.py           # Gemini: parse invoices, draft reminders, retry on busy
├── fees.py            # INR take-home estimate
├── insights.py        # Client reliability and "chase first"
├── index.html         # Dashboard UI
├── requirements.txt
└── .env               # Your secrets (never committed)
```

## Design decisions

- **Human in the loop.** An AI that can send payment requests on its own is a risk. TakeHome splits "understand" from "act": `/preview` only reads and estimates, and `/confirm-invoice` is the only route the dashboard uses to send.
- **Honest estimates.** The rupee figure is labelled as an estimate, shows the conversion rate used, and every rate can be changed in `.env` if your PayPal account has different terms.
- **Resilient AI calls.** If Gemini is busy (HTTP 503), the backend retries with backoff instead of failing.
- **Real error messages.** PayPal and Gemini errors are passed through to the UI instead of a generic "something went wrong".

## Run it locally

**Requirements:** Python 3.11+, a PayPal developer account, a Gemini API key.

### 1. Clone and install

```bash
git clone <your-repo-url>
cd takehome
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

### 2. Set up PayPal Sandbox

1. Sign in at [developer.paypal.com](https://developer.paypal.com) and switch to **Sandbox**.
2. Go to **Apps & Credentials → Sandbox → Default Application** and copy the **Client ID** and **Secret**.
3. Go to **Testing Tools → Sandbox Accounts**. Use the default **Business** account as the freelancer.
4. Create a **Personal** account with the country set to **United States** to act as the client (see the note below).

> **Why a US client?** PayPal does not allow sending invoices to customers within India, so a sandbox client created with country India fails with `INR_FOREIGN_CURRENCY_BLOCKED`. TakeHome is built for Indian freelancers billing clients abroad, which is the case PayPal supports.

### 3. Create `.env`

```
PAYPAL_CLIENT_ID=your_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_sandbox_secret
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com
PAYPAL_BUSINESS_EMAIL=sb-xxxx@business.example.com
PAYPAL_PERSONAL_EMAIL=sb-xxxx@personal.example.com
GEMINI_API_KEY=your_gemini_key

# Optional
GEMINI_MODEL=gemini-3.8-flash
PAYPAL_FEE_PCT=4.4
PAYPAL_FIXED_FEE=0.30
PAYPAL_FX_MARKUP_PCT=3.0
GST_ON_FEES_PCT=18
USD_INR_FALLBACK=87
```

### 4. Start the app

```bash
uvicorn main:app --reload
```

Open **http://127.0.0.1:8000/app**.

### 5. Try it

1. Type or pick an example sentence and press **Preview invoice**.
2. Check the take-home estimate, then press **Send invoice**.
3. In another tab, sign in at `sandbox.paypal.com` with the Personal sandbox account and pay the invoice.
4. Watch the dashboard update on its own within about 15 seconds.

## API routes

| Route | Purpose |
|---|---|
| `GET /app` | Dashboard |
| `GET /dashboard` | Invoices and insights in one call |
| `POST /preview` | Parse a sentence and estimate take-home in INR (sends nothing) |
| `POST /confirm-invoice` | Create and send the invoice |
| `GET /reminder-draft/{invoice_id}` | AI-drafted reminder |
| `POST /send-reminder` | Send an approved reminder |
| `GET /estimate?amount=250&currency=USD` | Standalone INR estimate |
| `GET /invoices`, `GET /insights` | Raw invoice list and client insights |

## Limitations

- **Sandbox only.** Nothing here moves real money.
- **Estimates are indicative.** Fees, GST treatment and the conversion markup depend on your PayPal account terms. Check them before relying on the numbers.
- **Polling, not webhooks.** Payments show up within about 15 seconds. Instant updates would need PayPal webhooks and a public URL.
- **Single user, no login.** The dashboard has no authentication and is meant to run locally.
- **International clients only.** See the note about Indian clients above.

## What's next

- PayPal webhooks for instant payment detection
- Sign-in and multiple freelancer accounts
- Recurring invoices for retainer clients
- Scheduled reminders that wait for approval in a queue

## Security notes

- Secrets live in `.env`, which is git-ignored. Use separate keys for Sandbox and Live.
- The Client Secret is only used on the server and never reaches the browser.
- All text shown in the dashboard is escaped before rendering.

## Author

Palak Goda · KSD's Model College · https://youtu.be/Uh3NkCnLXxQ
