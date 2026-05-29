"""
SQLite database for Billie Jean Law — consultations and attorneys.
"""
import sqlite3
import uuid
from datetime import datetime
from app.config import get_settings


def _conn():
    return sqlite3.connect(get_settings().db_path)


def init_db():
    with _conn() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS consultations (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id     TEXT UNIQUE NOT NULL,
                name          TEXT NOT NULL,
                email         TEXT NOT NULL,
                phone         TEXT NOT NULL,
                case_type     TEXT NOT NULL,
                preferred_date TEXT NOT NULL,
                preferred_time TEXT NOT NULL,
                case_summary  TEXT,
                opposing_party TEXT,
                urgency       TEXT DEFAULT 'normal',
                sol_deadline  TEXT,
                attorney_assigned TEXT,
                status        TEXT DEFAULT 'scheduled',
                created_at    TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS attorneys (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT NOT NULL,
                title           TEXT NOT NULL,
                practice_areas  TEXT NOT NULL,
                available_slots TEXT NOT NULL
            )
        """)
        # Seed attorneys if empty
        if db.execute("SELECT COUNT(*) FROM attorneys").fetchone()[0] == 0:
            attorneys = [
                (
                    "Eleanor Hayes",
                    "Partner",
                    "personal_injury,wrongful_death,medical_malpractice",
                    "Monday 9-12,Tuesday 9-12,Wednesday 2-5,Thursday 9-12,Friday 9-11",
                ),
                (
                    "David Osei",
                    "Associate Attorney",
                    "family_law,divorce,custody,child_support,protective_orders",
                    "Monday 1-5,Tuesday 2-5,Wednesday 9-12,Thursday 2-5,Friday 1-4",
                ),
                (
                    "Marcus Reilly",
                    "Associate Attorney",
                    "criminal_defense,dui,traffic,misdemeanor,felony",
                    "Monday 9-5,Tuesday 9-12,Wednesday 1-5,Thursday 9-5,Friday 9-12",
                ),
            ]
            db.executemany(
                "INSERT INTO attorneys (name, title, practice_areas, available_slots) VALUES (?,?,?,?)",
                attorneys,
            )
        # Seed sample consultations
        if db.execute("SELECT COUNT(*) FROM consultations").fetchone()[0] == 0:
            samples = [
                (
                    "BJL-001", "James Thornton", "j.thornton@email.com", "(540) 555-0101",
                    "personal_injury", "2026-06-02", "morning",
                    "Rear-end collision on I-95 southbound, significant neck and back injuries.",
                    "Progressive Insurance / Other Driver", "normal", "2027-03-15",
                    "Eleanor Hayes", "scheduled",
                ),
                (
                    "BJL-002", "Maria Santos", "m.santos@email.com", "(540) 555-0202",
                    "family_law", "2026-06-03", "afternoon",
                    "Contested divorce, two minor children, dispute over custody and marital home.",
                    "Roberto Santos", "normal", None,
                    "David Osei", "scheduled",
                ),
                (
                    "BJL-003", "Kevin Park", "k.park@email.com", "(540) 555-0303",
                    "criminal_defense", "2026-06-04", "morning",
                    "First-offense DUI, BAC 0.11, no accident, traffic stop on Route 1.",
                    "Commonwealth of Virginia", "high", None,
                    "Marcus Reilly", "scheduled",
                ),
            ]
            now = datetime.now().isoformat()
            for s in samples:
                db.execute(
                    """INSERT INTO consultations
                       (ticket_id,name,email,phone,case_type,preferred_date,preferred_time,
                        case_summary,opposing_party,urgency,sol_deadline,attorney_assigned,status,created_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (*s, now),
                )


def _route_attorney(case_type: str) -> str:
    ct = case_type.lower().replace(" ", "_")
    if any(k in ct for k in ("personal_injury", "car", "accident", "slip", "wrongful", "malpractice")):
        return "Eleanor Hayes"
    if any(k in ct for k in ("family", "divorce", "custody", "child", "domestic", "protective")):
        return "David Osei"
    if any(k in ct for k in ("criminal", "dui", "dwi", "traffic", "misdemeanor", "felony", "reckless")):
        return "Marcus Reilly"
    return "Eleanor Hayes"


def schedule_consultation(
    name: str,
    email: str,
    phone: str,
    case_type: str,
    preferred_date: str,
    preferred_time: str,
    case_summary: str = "",
    opposing_party: str = "",
    urgency: str = "normal",
    sol_deadline: str = "",
) -> dict:
    ticket_id = "BJL-" + str(uuid.uuid4())[:6].upper()
    attorney = _route_attorney(case_type)
    with _conn() as db:
        db.execute(
            """INSERT INTO consultations
               (ticket_id,name,email,phone,case_type,preferred_date,preferred_time,
                case_summary,opposing_party,urgency,sol_deadline,attorney_assigned,status,created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                ticket_id, name, email, phone, case_type,
                preferred_date, preferred_time, case_summary, opposing_party,
                urgency, sol_deadline or None, attorney, "scheduled",
                datetime.now().isoformat(),
            ),
        )
    return {
        "success": True,
        "ticket_id": ticket_id,
        "attorney_assigned": attorney,
        "confirmed_date": preferred_date,
        "confirmed_time": preferred_time,
        "message": (
            f"Consultation scheduled with {attorney}. "
            f"Confirmation: {ticket_id}. "
            "A team member will call to confirm within 1 business hour. "
            "Your first consultation is free — no obligation."
        ),
    }


def check_consultation(lookup: str) -> dict:
    lookup = lookup.strip().lower()
    with _conn() as db:
        rows = db.execute(
            """SELECT ticket_id,name,case_type,preferred_date,preferred_time,
                      attorney_assigned,status,urgency
               FROM consultations
               WHERE LOWER(name) LIKE ? OR LOWER(phone) LIKE ? OR LOWER(email) LIKE ?
                  OR LOWER(ticket_id) = ?
               ORDER BY created_at DESC LIMIT 3""",
            (f"%{lookup}%", f"%{lookup}%", f"%{lookup}%", lookup),
        ).fetchall()
    if not rows:
        return {"found": False, "message": "No consultation found. Please call (540) 555-2400 to verify."}
    results = []
    for r in rows:
        results.append({
            "ticket_id": r[0],
            "name": r[1],
            "case_type": r[2],
            "date": r[3],
            "time": r[4],
            "attorney": r[5],
            "status": r[6],
            "urgency": r[7],
        })
    return {"found": True, "consultations": results}


def get_practice_area_info(area: str) -> dict:
    area_map = {
        "personal_injury": {
            "name": "Personal Injury",
            "attorney": "Eleanor Hayes (Partner)",
            "fee_structure": "Contingency — no fee unless we win. Standard 33.3% of recovery.",
            "free_consultation": True,
            "typical_timeline": "6-18 months for settlement, 1-3 years if trial.",
            "what_to_bring": "Accident report, medical records, photos of injuries/scene, insurance info for all parties.",
            "common_cases": "Car accidents (I-95 corridor), truck accidents, slip and fall, wrongful death, medical malpractice.",
            "virginia_sol": "2 years from date of injury (Va. Code § 8.01-243)",
            "notes": "Virginia is a contributory negligence state — if you are even 1% at fault, you may be barred from recovery. This makes experienced representation critical.",
        },
        "family_law": {
            "name": "Family Law",
            "attorney": "David Osei (Associate Attorney)",
            "fee_structure": "Hourly. Transparent fee agreement before any work begins. Payment plans available.",
            "free_consultation": True,
            "typical_timeline": "Uncontested divorce: 3-6 months. Contested divorce: 1-2 years. Custody modifications: varies.",
            "what_to_bring": "Marriage certificate, financial documents (pay stubs, tax returns, bank statements), existing court orders, list of marital assets and debts.",
            "common_cases": "Divorce (fault and no-fault), child custody and visitation, child support, protective orders, property division.",
            "virginia_notes": "No-fault divorce requires 6-month separation (no minor children, with agreement) or 12 months. Virginia uses the Income Shares Model for child support calculation.",
            "notes": "Custody decisions in Virginia are based on the best interests of the child across 10 statutory factors.",
        },
        "criminal_defense": {
            "name": "Criminal Defense",
            "attorney": "Marcus Reilly (Associate Attorney)",
            "fee_structure": "Flat fee for most matters. Quoted upfront before representation begins.",
            "free_consultation": True,
            "typical_timeline": "Misdemeanor: 2-6 months. Felony: 6-18 months.",
            "what_to_bring": "Court date and case number, all paperwork from law enforcement, written account of the events.",
            "common_cases": "DUI/DWI, reckless driving (Class 1 misdemeanor in Virginia), traffic offenses, assault and battery, drug possession, felony charges.",
            "urgent_note": "If you have an upcoming court date, contact us immediately. Missing deadlines can severely limit your defense options.",
            "virginia_notes": "Virginia reckless driving (20+ mph over limit or any speed over 85 mph) is a Class 1 misdemeanor — same as DUI. A first-offense DUI carries up to 12 months jail and $2,500 fine.",
        },
        "estate_planning": {
            "name": "Estate Planning",
            "attorney": "Eleanor Hayes (Partner)",
            "fee_structure": "Flat fee packages. Simple will from $350. Full estate plan (will + trust + POA + healthcare directive) from $1,200.",
            "free_consultation": True,
            "typical_timeline": "Simple documents: 1-2 weeks. Complex trusts: 3-4 weeks.",
            "what_to_bring": "List of assets and intended beneficiaries, names of executor and healthcare proxy, any existing estate planning documents.",
            "common_cases": "Wills, revocable living trusts, durable power of attorney, healthcare directives, special needs trusts, guardianship.",
            "notes": "Without a will, Virginia intestacy law determines asset distribution — which may not match your wishes. Estate planning is especially important for military families near Quantico.",
        },
    }
    key = area.lower().replace(" ", "_").replace("-", "_")
    for k, v in area_map.items():
        if k in key or key in k:
            return v
    return {
        "available_areas": list(area_map.keys()),
        "message": "Practice area not found. Available: personal_injury, family_law, criminal_defense, estate_planning.",
    }
