import os, time, httpx

FEE_PCT = float(os.getenv("PAYPAL_FEE_PCT", "4.4"))
FIXED_FEE = float(os.getenv("PAYPAL_FIXED_FEE", "0.30"))      # USD value, varies by currency
FX_MARKUP_PCT = float(os.getenv("PAYPAL_FX_MARKUP_PCT", "3.0"))
GST_PCT = float(os.getenv("GST_ON_FEES_PCT", "18"))
FALLBACK_USD_INR = float(os.getenv("USD_INR_FALLBACK", "87"))

_cache = {}

async def get_inr_rate(currency: str):
    cached = _cache.get(currency)
    if cached and time.time() - cached[1] < 3600:
        return cached[0], "live"
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"https://open.er-api.com/v6/latest/{currency}")
            rate = r.json()["rates"]["INR"]
            _cache[currency] = (rate, time.time())
            return rate, "live"
    except Exception:
        if currency == "USD":
            return FALLBACK_USD_INR, "fallback"
        raise

async def estimate_inr(amount: float, currency: str = "USD"):
    rate, source = await get_inr_rate(currency)
    fee = amount * FEE_PCT / 100 + FIXED_FEE
    gst = fee * GST_PCT / 100
    after_fees = amount - fee - gst
    paypal_rate = rate * (1 - FX_MARKUP_PCT / 100)
    net_inr = after_fees * paypal_rate
    mid_inr = amount * rate
    return {
        "invoice_amount": amount,
        "currency": currency,
        "paypal_fee": round(fee, 2),
        "gst_on_fee": round(gst, 2),
        "mid_market_rate": round(rate, 2),
        "paypal_rate_after_markup": round(paypal_rate, 2),
        "rate_source": source,
        "you_receive_inr": round(net_inr),
        "lost_to_fees_inr": round(mid_inr - net_inr),
        "lost_percent": round((mid_inr - net_inr) / mid_inr * 100, 1),
        "note": "Estimate only. Actual fees depend on your PayPal account terms.",
    }
    