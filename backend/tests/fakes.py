
import json
from types import SimpleNamespace

from app.llm.client import LLMError


def build_completion(content=None, tool_calls=None):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=content,
                    tool_calls=tool_calls,
                )
            )
        ]
    )


def build_tool_call(call_id, name, arguments):
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(
            name=name,
            arguments=json.dumps(arguments) if isinstance(arguments, dict) else arguments,
        ),
    )


class FakeLLMClient:
    """Scriptable stand-in for OpenRouterClient."""

    def __init__(
        self,
        chat_replies=None,
        completions=None,
        completion_factory=None,
        chat_errors=None,
    ):
        self.chat_calls = []
        self.complete_calls = []
        self._chat_replies = list(chat_replies or [])
        self._completions = list(completions or [])
        self._completion_factory = completion_factory
        self._chat_errors = list(chat_errors or [])

    async def chat(self, messages, **kwargs):
        self.chat_calls.append(messages)

        if self._chat_errors:
            error = self._chat_errors.pop(0)

            if error is not None:
                raise error

        if self._chat_replies:
            return self._chat_replies.pop(0)

        return "Default reply"

    async def complete(self, messages, **kwargs):
        self.complete_calls.append(messages)

        if self._completion_factory is not None:
            return self._completion_factory()

        if self._completions:
            return self._completions.pop(0)

        return build_completion(content="done")


class FakeToolRegistry:
    """Scriptable stand-in for the MCP tool registry."""

    def __init__(self, tools=None, results=None, error_tools=None):
        self.tools = list(tools or [])
        self.results = dict(results or {})
        self.error_tools = set(error_tools or set())
        self.invocations = []

    def list_tools(self, role):
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": f"Test tool {name}",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            }
            for name in self.tools
        ]

    async def invoke_tool(self, role, name, arguments, context):
        self.invocations.append(
            {
                "role": role,
                "name": name,
                "arguments": arguments,
                "context": context,
            }
        )

        if name in self.error_tools:
            raise RuntimeError("boom")

        if name in self.results:
            return self.results[name]

        return {"status": "ok", "data": {"echo": arguments}}


def build_initial_state(**overrides):
    state = {
        "user_id": "11111111-1111-1111-1111-111111111111",
        "role": "owner",
        "conversation_id": "22222222-2222-2222-2222-222222222222",
        "current_request": "Show me my stations",
        "messages": [],
        "tool_results": [],
        "rag_context": [],
        "pending_confirmation": None,
        "confirmation_action": None,
        "response": "",
    }

    state.update(overrides)

    return state


def llm_error():
    return LLMError("provider down")
