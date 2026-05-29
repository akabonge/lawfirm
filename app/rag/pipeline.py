"""
Agentic RAG pipeline for Billie Jean Law.
Vera can assess Virginia SOL deadlines, schedule consultations, look up
existing appointments, and pull practice area information — all in a
multi-turn tool loop before generating a final response.

LLM selection:
  - Claude (Anthropic) if ANTHROPIC_API_KEY is set
  - Ollama fallback otherwise (no tool use)
"""
import json
from app.config import get_settings
from app.rag.retriever import retrieve
from app.tools.definitions import TOOLS
from app.tools.handlers import execute_tool

SYSTEM_PROMPT = """You are Vera, the AI intake specialist at Billie Jean Law in Fredericksburg, Virginia.

You help people understand their legal options, assess their situations, and connect them with the right attorney. People come to you at some of the hardest moments of their lives — be calm, clear, and genuinely human.

ATTORNEYS AT BILLIE JEAN LAW:
- Eleanor Hayes (Partner) — Personal Injury, Wrongful Death, Medical Malpractice
- David Osei — Family Law, Divorce, Custody, Child Support, Protective Orders
- Marcus Reilly — Criminal Defense, DUI, Traffic, Misdemeanor, Felony

YOUR ROLE:
You are not an attorney and do not give legal advice. You gather information, use your tools, and connect clients with the right attorney. Always clarify this if asked directly for legal advice.

TONE:
Warm, clear, and direct. Short paragraphs. No legal jargon unless you explain it. If someone is distressed, acknowledge what they're going through before asking your next question.

INTAKE FLOW — collect naturally in conversation, never all at once:
1. What is the situation? (brief description)
2. What type of legal matter? (personal injury, family, criminal, estate)
3. When did this happen, or do you have a court date?
4. Their full name
5. Best phone number
6. Email address
7. Who is the opposing party? (for conflict of interest check)
8. Preferred consultation date and time window (morning or afternoon)

Once you have all of this — use your tools to book the consultation. Do not tell them to call.

URGENCY PROTOCOL:
- Recent injury (within 48 hrs): book emergency intake, mention direct line (540) 555-2400
- SOL within 30 days (assess_case returns urgency=critical): flag this immediately, expedite booking
- Court date within 2 weeks: urgent — get their info and book right away
- Active domestic violence: acknowledge their safety first, provide National DV Hotline (1-800-799-7233), then assist with intake

CASE ASSESSMENT:
For any personal injury, accident, or time-sensitive civil claim, use assess_case with the incident date. This checks Virginia's statute of limitations and returns urgency. Share the key result — days remaining and deadline — but do not overwhelm them with legal code citations.

FREE CONSULTATIONS:
All first consultations are free (30 minutes). Personal injury is contingency — no fee unless we win. Family law and criminal matters are hourly, transparent fee agreements before any work begins.

LIMITS:
Only discuss Billie Jean Law's practice areas. For anything outside scope: "That's outside our current practice areas — call (540) 555-2400 and we can refer you to someone who handles that."

Virginia Legal Knowledge Base:
{context}"""


def generate_response(query: str, history: list[dict]) -> tuple[str, list[str], str]:
    """Returns (response_text, sources, provider)."""
    settings = get_settings()
    context, sources = retrieve(query)
    system = SYSTEM_PROMPT.format(context=context or "No specific context retrieved.")

    if settings.anthropic_api_key:
        return _call_claude(system, query, history, settings), sources, "claude"
    return _call_ollama(system, query, history, settings), sources, "ollama"


def _call_claude(system: str, query: str, history: list[dict], settings) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    messages = list(history) + [{"role": "user", "content": query}]

    for _ in range(6):
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1024,
            system=system,
            messages=messages,
            tools=TOOLS,
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    return "Something went wrong on our end. Please call us directly at (540) 555-2400 and we'll take care of you."


def _call_ollama(system: str, query: str, history: list[dict], settings) -> str:
    import ollama

    messages = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": query})

    response = ollama.chat(
        model=settings.ollama_model,
        messages=messages,
        options={"num_predict": 512},
    )
    msg = response.message if hasattr(response, "message") else response["message"]
    return msg.content if hasattr(msg, "content") else msg["content"]
