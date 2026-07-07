"""Provider abstraction for the LLM coach layer."""

from typing import Protocol

from app.coach.llm_models import LLMCoachDraft, LLMCoachPrompt


class LLMCoachProvider(Protocol):
    """A bounded text-generation provider; implementations live outside deterministic engines."""

    def generate(self, prompt: LLMCoachPrompt) -> LLMCoachDraft:
        """Generate a draft coaching message from an auditable prompt."""

