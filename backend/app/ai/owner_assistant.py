from anthropic import Anthropic
from groq import AsyncGroq
from app.config import settings

api_key = settings.groq_api_key.strip()

if not api_key:
    raise RuntimeError(
        "GROQ_API_KEY is missing. "
        "Check your backend/.env file."
    )

client = Anthropic(api_key=api_key)

response = client.messages.create(
    model=settings.anthropic_model,
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "Hello, introduce yourself as ChargeMate AI Owner Assistant."
        }
    ]
)

for block in response.content:
    if block.type == "text":
        print(block.text)