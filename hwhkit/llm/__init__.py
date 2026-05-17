"""hwhkit.llm — litellm-backed LLM provider.

Public surface::

    from hwhkit.llm import LlmProvider, LlmConfig
"""

from hwhkit.llm.config import LlmConfig
from hwhkit.llm.provider import LlmProvider

__all__ = ["LlmConfig", "LlmProvider"]
