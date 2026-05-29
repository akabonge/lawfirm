"""
Anthropic tool_use schema definitions for Vera — Billie Jean Law intake specialist.
"""

TOOLS = [
    {
        "name": "assess_case",
        "description": (
            "Assess whether a potential civil case is within Virginia's statute of limitations "
            "and flag urgency level. Use this when a client describes a personal injury, "
            "property damage, malpractice, or other time-sensitive civil claim. "
            "Returns SOL deadline, days remaining, urgency level, and recommended next steps."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "case_type": {
                    "type": "string",
                    "description": "Type of case: personal_injury, car_accident, slip_and_fall, wrongful_death, medical_malpractice, property_damage, breach_of_contract",
                },
                "incident_date": {
                    "type": "string",
                    "description": "Date of the incident in YYYY-MM-DD format.",
                },
                "description": {
                    "type": "string",
                    "description": "Brief description of what happened.",
                },
            },
            "required": ["case_type", "incident_date", "description"],
        },
    },
    {
        "name": "schedule_consultation",
        "description": (
            "Book a free 30-minute consultation at Billie Jean Law. "
            "Use this once you have collected: the client's name, email, phone, case type, "
            "preferred date, preferred time window, and ideally the opposing party name for a conflict check. "
            "The system automatically routes to the right attorney based on case type."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Client's full name."},
                "email": {"type": "string", "description": "Client's email address."},
                "phone": {"type": "string", "description": "Client's best phone number."},
                "case_type": {
                    "type": "string",
                    "description": "Practice area: personal_injury, family_law, criminal_defense, estate_planning, or specific type like dui, divorce, custody.",
                },
                "preferred_date": {
                    "type": "string",
                    "description": "Preferred consultation date in YYYY-MM-DD format.",
                },
                "preferred_time": {
                    "type": "string",
                    "description": "Preferred time window: morning (9 AM-12 PM) or afternoon (1-5 PM).",
                },
                "case_summary": {
                    "type": "string",
                    "description": "Brief summary of the client's legal situation.",
                },
                "opposing_party": {
                    "type": "string",
                    "description": "Name of the opposing party, insurance company, or defendant for conflict of interest check.",
                },
                "urgency": {
                    "type": "string",
                    "enum": ["normal", "high", "critical"],
                    "description": "Urgency level based on SOL deadline or court date proximity.",
                },
                "sol_deadline": {
                    "type": "string",
                    "description": "Statute of limitations deadline in YYYY-MM-DD format, if known.",
                },
            },
            "required": ["name", "email", "phone", "case_type", "preferred_date", "preferred_time"],
        },
    },
    {
        "name": "check_consultation",
        "description": (
            "Look up an existing consultation by client name, phone number, email, or ticket ID. "
            "Use this when someone asks about an appointment they already scheduled."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "lookup": {
                    "type": "string",
                    "description": "Search term: client name, phone number, email address, or ticket ID (e.g. BJL-A3F2B1).",
                },
            },
            "required": ["lookup"],
        },
    },
    {
        "name": "get_practice_area_info",
        "description": (
            "Get detailed information about a specific practice area at Billie Jean Law — "
            "including fee structure, assigned attorney, typical timeline, what to bring, "
            "Virginia-specific legal notes, and statute of limitations. "
            "Use this when a client asks about costs, process, timelines, or what to expect."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "area": {
                    "type": "string",
                    "description": "Practice area: personal_injury, family_law, criminal_defense, or estate_planning.",
                },
            },
            "required": ["area"],
        },
    },
]
