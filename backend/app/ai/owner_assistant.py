import anthropic

from app.config import settings

client = anthropic.Anthropic(
    api_key=settings.anthropic_api_key
)

response = client.messages.create(
    model=settings.anthropic_model,
    max_tokens=1000,
    messages=[
        {
            "role": "user",
            "content": "Show me my charging station details."
        }
    ]
)

print(response.content[0].text)