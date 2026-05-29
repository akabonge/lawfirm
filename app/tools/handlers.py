"""
Tool execution dispatcher for Vera's agentic loop.
"""
from datetime import date, timedelta
from app.tools.mock_db import (
    schedule_consultation,
    check_consultation,
    get_practice_area_info,
)

# Virginia statutes of limitations in days
_VA_SOL = {
    "personal_injury": 730,
    "car_accident": 730,
    "slip_and_fall": 730,
    "wrongful_death": 730,
    "medical_malpractice": 730,
    "property_damage": 1825,
    "breach_of_contract": 1825,
}


def _assess_case(case_type: str, incident_date: str, description: str) -> dict:
    from datetime import datetime

    try:
        incident = datetime.strptime(incident_date, "%Y-%m-%d").date()
    except ValueError:
        return {
            "error": "Could not parse incident_date. Use YYYY-MM-DD format.",
            "example": "2024-11-15",
        }

    today = date.today()
    if incident > today:
        return {"error": "Incident date is in the future. Please verify the date."}

    days_elapsed = (today - incident).days
    key = case_type.lower().replace(" ", "_").replace("-", "_")
    sol_days = next((v for k, v in _VA_SOL.items() if k in key or key in k), 730)
    days_remaining = sol_days - days_elapsed
    deadline = (incident + timedelta(days=sol_days)).isoformat()

    if days_remaining <= 0:
        return {
            "viable": False,
            "case_type": case_type,
            "incident_date": incident_date,
            "sol_days": sol_days,
            "days_elapsed": days_elapsed,
            "days_remaining": 0,
            "deadline": deadline,
            "urgency": "expired",
            "assessment": (
                f"The statute of limitations appears to have expired "
                f"({abs(days_remaining)} days ago). The filing deadline was {deadline}. "
                "An attorney should still be consulted — certain exceptions (discovery rule, "
                "fraudulent concealment, minority tolling) may apply."
            ),
            "recommendation": "Schedule a consultation immediately to explore any applicable exceptions.",
        }

    if days_remaining <= 30:
        urgency = "critical"
        urgency_note = f"CRITICAL: Only {days_remaining} days before the statute of limitations expires on {deadline}. Act immediately."
    elif days_remaining <= 90:
        urgency = "high"
        urgency_note = f"HIGH PRIORITY: {days_remaining} days remaining before SOL deadline ({deadline}). Schedule consultation this week."
    elif days_remaining <= 180:
        urgency = "moderate"
        urgency_note = f"Moderate urgency: {days_remaining} days remaining (deadline: {deadline})."
    else:
        urgency = "normal"
        urgency_note = f"{days_remaining} days remaining before the {sol_days // 365}-year SOL deadline ({deadline})."

    return {
        "viable": True,
        "case_type": case_type,
        "incident_date": incident_date,
        "sol_days": sol_days,
        "days_elapsed": days_elapsed,
        "days_remaining": days_remaining,
        "deadline": deadline,
        "urgency": urgency,
        "urgency_note": urgency_note,
        "virginia_code": "Va. Code § 8.01-243" if sol_days == 730 else "Va. Code § 8.01-243(B)",
        "recommendation": "Schedule a free consultation to evaluate your claim." if urgency == "normal"
                          else "Schedule your free consultation as soon as possible.",
        "contributory_negligence_warning": (
            "Note: Virginia is a contributory negligence state. If you are found even 1% at fault, "
            "you may be barred from recovery. An attorney evaluation is important."
        ) if "injury" in key or "accident" in key or "fall" in key else None,
    }


def execute_tool(name: str, inputs: dict) -> dict:
    if name == "assess_case":
        return _assess_case(
            inputs.get("case_type", ""),
            inputs.get("incident_date", ""),
            inputs.get("description", ""),
        )
    if name == "schedule_consultation":
        return schedule_consultation(
            name=inputs.get("name", ""),
            email=inputs.get("email", ""),
            phone=inputs.get("phone", ""),
            case_type=inputs.get("case_type", ""),
            preferred_date=inputs.get("preferred_date", ""),
            preferred_time=inputs.get("preferred_time", ""),
            case_summary=inputs.get("case_summary", ""),
            opposing_party=inputs.get("opposing_party", ""),
            urgency=inputs.get("urgency", "normal"),
            sol_deadline=inputs.get("sol_deadline", ""),
        )
    if name == "check_consultation":
        return check_consultation(inputs.get("lookup", ""))
    if name == "get_practice_area_info":
        return get_practice_area_info(inputs.get("area", ""))
    return {"error": f"Unknown tool: {name}"}
