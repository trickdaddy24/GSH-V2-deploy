from datetime import datetime
from typing import Dict, List, Tuple
from config import DATE_FORMAT, RISK_HIGH, RISK_MAX_LATE, RISK_GENERAL_MIN, RISK_ENHANCED_MIN, RISK_IMMINENT_DAYS


def calculate_risk_score(customer: Dict) -> Tuple[int, List[str]]:
    now = datetime.now()
    days = (customer["due_date"] - now).days
    score, reasons = 0, []

    if days <= 7:
        score += min(max(7 - days, 1), 7)
        label = f"{days} day(s)" if days >= 0 else f"{abs(days)} day(s) overdue"
        reasons.append(f"Due in {label}")

    if customer["late_payments"] > 0:
        score += 3 * min(customer["late_payments"], RISK_MAX_LATE)
        reasons.append(f"{customer['late_payments']} late payment(s)")

    if customer["grace_period_used"]:
        score += 2
        reasons.append("Used grace period")

    return score, reasons


def suggest_actions(customer: Dict, score: int) -> List[str]:
    actions: List[str] = []
    if score >= RISK_HIGH:
        actions.append("Send urgent reminder via email or Telegram")
        if customer.get("email"):
            actions.append(f"Email: {customer['email']}")
        if customer.get("phone"):
            actions.append(f"Call: {customer['phone']}")
    else:
        actions.append("Send friendly reminder via Telegram")
    return actions


def run_general_risk(customers: List[Dict]) -> Dict:
    predictions = []
    for customer in customers:
        score, reasons = calculate_risk_score(customer)
        if score < RISK_GENERAL_MIN:
            continue
        risk_level = "high" if score >= RISK_HIGH else "medium"
        predictions.append({
            "id": customer["id"],
            "username": customer["username"],
            "risk_score": score,
            "risk_level": risk_level,
            "reasons": reasons,
            "suggested_actions": suggest_actions(customer, score),
            "due_date": customer["due_date"].strftime(DATE_FORMAT),
            "due_in_days": (customer["due_date"] - datetime.now()).days,
        })

    high = sum(1 for p in predictions if p["risk_level"] == "high")
    return {
        "predictions": predictions,
        "generated_at": datetime.now().strftime(f"{DATE_FORMAT} %H:%M:%S"),
        "total": len(predictions),
        "high_count": high,
        "medium_count": len(predictions) - high,
    }


def run_enhanced_risk(customers: List[Dict]) -> Dict:
    now = datetime.now()
    predictions = []

    for customer in customers:
        days = (customer["due_date"] - now).days
        if days > RISK_IMMINENT_DAYS:
            continue

        score, reasons = 0, []
        score += max(5 - days, 0)
        reasons.append(f"Due in {days} day(s)")

        if customer["late_payments"] > 0:
            score += 2 * min(customer["late_payments"], RISK_MAX_LATE)
            reasons.append(f"{customer['late_payments']} late payment(s)")

        if customer["grace_period_used"]:
            score += 1
            reasons.append("Used grace period")

        if score < RISK_ENHANCED_MIN:
            continue

        risk_level = "high" if score >= RISK_HIGH else "medium"
        predictions.append({
            "id": customer["id"],
            "username": customer["username"],
            "risk_score": score,
            "risk_level": risk_level,
            "reasons": reasons,
            "suggested_actions": [
                "Urgent personal contact needed" if risk_level == "high" else "Send payment reminder"
            ],
            "due_date": customer["due_date"].strftime(DATE_FORMAT),
            "due_in_days": days,
        })

    high = sum(1 for p in predictions if p["risk_level"] == "high")
    return {
        "predictions": sorted(predictions, key=lambda x: (x["due_in_days"], -x["risk_score"])),
        "generated_at": datetime.now().strftime(f"{DATE_FORMAT} %H:%M:%S"),
        "total": len(predictions),
        "high_count": high,
        "medium_count": len(predictions) - high,
    }
