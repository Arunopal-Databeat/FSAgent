import litellm
from fastapi import APIRouter
from google.adk.cli.utils.service_factory import create_local_session_service

router = APIRouter()

AGENT_DIR = "agents"
AGENT_APP_NAME = "FSAgent"

session_service = create_local_session_service(base_dir=AGENT_DIR, per_agent=True)

FOLLOW_QUESTIONS = [
    "Can you break that down by month?",
    "How does that compare to last year?",
    "Which accounts contributed the most to that number?",
]


async def _get_latest_conversation(user_id: str, session_id: str):
    session = await session_service.get_session(
        app_name=AGENT_APP_NAME, user_id=user_id, session_id=session_id
    )
    if not session:
        return []
    messages = []
    for event in session.events:
        if event.content and event.content.parts:
            text = "".join(part.text or "" for part in event.content.parts)
            if text:
                messages.append({"author": event.author, "text": text})
    return messages


async def _generate_follow_questions(conversation):
    transcript = "\n".join(f"{m['author']}: {m['text']}" for m in conversation)
    prompt = (
        "Based on the conversation below, generate exactly 3 relevant follow-up "
        "questions the user might ask next.\n\n"
        f"{transcript}\n\n"
        'Respond in EXACTLY this format and nothing else: ||"Q1"|"Q2"|"Q3"||'
    )
    response = await litellm.acompletion(
        model="anthropic/claude-sonnet-5",
        messages=[{"role": "user", "content": prompt}],
    )
    return response["choices"][0]["message"]["content"].strip()


@router.get("/follow_questions")
async def follow_questions(userId: str, sessionId: str):
    conversation = await _get_latest_conversation(userId, sessionId)
    if not conversation:
        return {"questions": FOLLOW_QUESTIONS}
    generated = await _generate_follow_questions(conversation)
    return {"questions": generated}
