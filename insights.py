from datetime import date

OPEN = {"SENT", "UNPAID", "PARTIALLY_PAID"}
PAID = {"PAID", "MARKED_AS_PAID"}

def build_insights(invoices):
    today = date.today()
    totals = {}   # per currency
    clients = {}
    chase = []

    for inv in invoices:
        raw, cur = inv["raw_status"], inv["currency"]
        amt = float(inv["amount"] or 0)
        email = inv["client_email"] or "unknown"
        due = date.fromisoformat(inv["due_date"]) if inv["due_date"] else None
        c = clients.setdefault(email, {"paid": 0, "late_days": [], "open": 0, "overdue": 0})
        t = totals.setdefault(cur, {"outstanding": 0.0, "due_this_week": 0.0, "overdue": 0.0})

        if raw in PAID and due and inv["paid_date"]:
            c["paid"] += 1
            c["late_days"].append((date.fromisoformat(inv["paid_date"]) - due).days)
        elif raw in OPEN:
            c["open"] += 1
            t["outstanding"] += amt
            if due:
                days_left = (due - today).days
                if days_left < 0:
                    c["overdue"] += 1
                    t["overdue"] += amt
                    chase.append({"id": inv["id"], "client": email, "days_overdue": -days_left,
                                  "reason": "overdue"})
                elif days_left <= 7:
                    t["due_this_week"] += amt

    summary = []
    for email, c in clients.items():
        avg = sum(c["late_days"]) / len(c["late_days"]) if c["late_days"] else None
        if avg is None:
            label = "no payment history yet"
        elif avg <= 0:
            label = "reliable (pays on time or early)"
        elif avg <= 5:
            label = "slightly late"
        else:
            label = "chase early"
        c["avg_days_late"] = round(avg, 1) if avg is not None else None
        c["label"] = label
        summary.append({"client": email, **{k: v for k, v in c.items() if k != "late_days"}})

    # open invoices from habitually late clients, even if not overdue yet
    late_clients = {s["client"] for s in summary if s["label"] == "chase early"}
    for inv in invoices:
        if inv["raw_status"] in OPEN and inv["client_email"] in late_clients \
           and inv["status"] != "OVERDUE":
            chase.append({"id": inv["id"], "client": inv["client_email"],
                          "days_overdue": 0, "reason": "client usually pays late"})

    chase.sort(key=lambda x: -x["days_overdue"])
    return {"totals": totals, "clients": summary, "chase_first": chase}