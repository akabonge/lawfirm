"""
MCP server for Billie Jean Law — exposes Vera's tools via stdio transport.
Run: python mcp_server.py
"""
import json
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from app.tools.mock_db import init_db
from app.tools.handlers import execute_tool, _assess_case
from app.tools.mock_db import (
    schedule_consultation,
    check_consultation,
    get_practice_area_info,
)

mcp = FastMCP("billie-jean-law")

init_db()


@mcp.tool()
def assess_case(case_type: str, incident_date: str, description: str) -> str:
    """
    Assess whether a Virginia civil case is within the statute of limitations.
    Returns SOL deadline, days remaining, urgency level, and recommendation.
    case_type: personal_injury | car_accident | slip_and_fall | wrongful_death | medical_malpractice | property_damage | breach_of_contract
    incident_date: YYYY-MM-DD format
    """
    result = _assess_case(case_type, incident_date, description)
    return json.dumps(result, indent=2)


@mcp.tool()
def book_consultation(
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
) -> str:
    """
    Book a free 30-minute consultation at Billie Jean Law.
    preferred_time: 'morning' or 'afternoon'
    urgency: 'normal' | 'high' | 'critical'
    Returns ticket ID and assigned attorney.
    """
    result = schedule_consultation(
        name=name,
        email=email,
        phone=phone,
        case_type=case_type,
        preferred_date=preferred_date,
        preferred_time=preferred_time,
        case_summary=case_summary,
        opposing_party=opposing_party,
        urgency=urgency,
        sol_deadline=sol_deadline,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
def lookup_consultation(lookup: str) -> str:
    """
    Find an existing consultation by client name, phone, email, or ticket ID (e.g. BJL-A3F2B1).
    """
    result = check_consultation(lookup)
    return json.dumps(result, indent=2)


@mcp.tool()
def practice_area_info(area: str) -> str:
    """
    Get detailed information about a Billie Jean Law practice area.
    area: personal_injury | family_law | criminal_defense | estate_planning
    Returns fee structure, assigned attorney, timeline, what to bring, Virginia-specific notes.
    """
    result = get_practice_area_info(area)
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
