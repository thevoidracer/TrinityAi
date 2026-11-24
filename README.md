# Trinity AI Gateway

Your own AI API, built to be dropped into any of your apps. It's an OpenAI-style
HTTP gateway you own: your apps call *it* (with *your* API key), and behind the
scenes it answers using Claude (strong, general-purpose), or a local open-weight
model via Ollama (free, offline, no API costs), plus retrieval over your own
documents (RAG) so it knows things specific to your app.

## Why this shape

A small local model alone cannot match Claude/GPT/Gemini on general reasoning,
coding, or broad knowledge — no amount of prompting fixes that. This gateway
gives you a single stable API that can use Claude when you want real
capability, and a local model when you want it free/offline/for simple stuff.
Your other apps never change — only `DEFAULT_BACKEND` does.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env: set GATEWAY_API_KEY and ANTHROPIC_API_KEY
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Optional, for a free local model:

```bash
# install Ollama (https://ollama.com), then:
ollama pull llama3.1:8b
```

## Calling it from your other apps

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer <GATEWAY_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
        "messages": [{"role": "user", "content": "What can you do?"}]
      }'
```

Pass `"model": "local"` in the body to force the free local model instead of
Claude for that one request. `DEFAULT_BACKEND=auto` in `.env` makes the
gateway pick automatically (short/simple messages → local, everything else →
Claude).

The response shape mirrors OpenAI's chat completions, so most existing
OpenAI-client code in your apps works by just pointing the base URL here (swap
in your own thin client if you'd rather not bend an OpenAI SDK to a custom
auth header).

## Teaching it about your app (RAG)

```bash
curl -X POST http://localhost:8000/v1/ingest \
  -H "Authorization: Bearer <GATEWAY_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"text": "Our app'\''s refund policy is ..."}'
```

Anything ingested here gets pulled into context automatically on relevant
questions. This is how you make it "know" your product/business without any
training.

## If you still want to fine-tune a model later

Fine-tuning (even LoRA) needs a GPU, which this container doesn't have. The
practical path: rent one (RunPod, Lambda, Vast.ai — often under $1/hr) or use
a free Colab GPU, train a LoRA adapter on an open base model (e.g. Llama 3.1
8B or Qwen2.5-7B) with a tool like Unsloth or Axolotl, then point
`OLLAMA_MODEL` at the resulting model once it's loaded into Ollama. Ask and
I'll write the training script when you're ready for that step.
