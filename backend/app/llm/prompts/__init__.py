"""Shared LLM configuration conventions (Member 4, lane A).

Prompt conventions:
- Prompts live in ``app/llm/prompts`` as Python constants/modules, kept separate
  from business logic and graph nodes.
- Every prompt states the assistant's role boundary explicitly so role confusion
  and prompt-injection attempts are resisted in the instruction text itself.
- Domain rules (pricing, bookings, ownership) must NOT be encoded in prompts;
  they belong in Member 2/3 services. Prompts only describe *how to ask* for
  those capabilities and *how to report* their results.
"""
