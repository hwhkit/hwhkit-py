# LLM

`hwhkit.llm.LlmProvider` is a thin wrapper over [litellm](https://github.com/BerriAI/litellm),
giving you `LlmClient` + `EmbeddingClient` contracts that dispatch to any
backend by model-name prefix.

## Install

```bash
hwhkit add llm
```

API keys come from the standard environment variables expected by each
provider — `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `DEEPSEEK_API_KEY`,
`OLLAMA_API_BASE`, etc. hwhkit doesn't reinvent them.

## Configuration

```bash
HWHKIT_LLM__DEFAULT_CHAT_MODEL=claude-sonnet-4-20250514
HWHKIT_LLM__DEFAULT_EMBEDDING_MODEL=text-embedding-3-small
HWHKIT_LLM__DEFAULT_TEMPERATURE=0.7
HWHKIT_LLM__REQUEST_TIMEOUT_SECONDS=60
```

## Chat

```python
from hwhkit.core.contracts import LlmClient
from hwhkit.core.contracts.llm import ChatMessage

llm: LlmClient = ctx.resolve(LlmClient)

resp = await llm.chat(
    [
        ChatMessage(role="system", content="You are concise."),
        ChatMessage(role="user", content="What is 2+2?"),
    ],
    model="anthropic/claude-sonnet-4-20250514",
)
print(resp.content)        # "4."
print(resp.usage)          # {"prompt_tokens": ..., "completion_tokens": ...}
```

## Streaming

```python
async for chunk in llm.chat_stream(messages, model="openai/gpt-4o-mini"):
    print(chunk, end="", flush=True)
```

## Embeddings

```python
from hwhkit.core.contracts import EmbeddingClient

emb: EmbeddingClient = ctx.resolve(EmbeddingClient)
vectors = await emb.embed(
    ["hello world", "foo bar"],
    model="openai/text-embedding-3-small",
)
```

## Multi-provider patterns

litellm chooses the backend from the model prefix:

| Prefix | Backend |
|---|---|
| `openai/...` | OpenAI |
| `anthropic/...` | Anthropic |
| `deepseek/...` | DeepSeek |
| `ollama/...` | local Ollama |
| `azure/...` | Azure OpenAI |
| `bedrock/...` | AWS Bedrock |

You can mix providers in one process — `llm.chat(..., model="openai/...")`
hits OpenAI, the next call with `anthropic/...` hits Anthropic. Each uses
the matching env-var API key.

## Cost tracking

litellm publishes per-call cost data in `resp.raw["response_cost"]` for
models with known pricing. Hook it into an OTel histogram:

```python
from hwhkit.observability.metrics import get_meter

llm_cost = get_meter().create_counter("llm.cost.usd", unit="usd")

resp = await llm.chat(...)
if cost := resp.raw.get("response_cost"):
    llm_cost.add(cost, {"model": resp.model})
```

## Testing

For unit tests, monkey-patch `litellm.acompletion` / `litellm.aembedding`
to async mocks:

```python
from unittest.mock import AsyncMock

provider._litellm.acompletion = AsyncMock(return_value={...})
```

(See `tests/unit/llm/test_provider.py` for examples.)
