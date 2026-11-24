# Trinity AI Gateway

Your own free AI API, built to be dropped into any of your apps. It's an
OpenAI-style HTTP gateway you own: your apps call *it* (with *your* API key),
and behind the scenes it runs **Qwen2.5-7B-Instruct** — a free, open-weight
model running entirely on your own hardware (CPU is fine), no per-token
billing, no vendor API key required. It also has permanent memory with
fact-checking, and optional Claude as a paid fallback if you ever want it.

## Why Qwen2.5-7B-Instruct

Apache 2.0 licensed (fully free, no usage restrictions), and it beats similarly
sized models like Llama 3.1 8B on most coding/math/instruction benchmarks —
so it needs the least additional fine-tuning to already feel capable. It runs
via [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) in-process
(no separate server/daemon to manage) from a quantized GGUF file.

## Setup

```bash
pip install -r requirements.txt

# Download the model weights (~4.4GB, one-time)
python3 -c "
from huggingface_hub import hf_hub_download
for fn in ['qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf', 'qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf']:
    hf_hub_download(repo_id='Qwen/Qwen2.5-7B-Instruct-GGUF', filename=fn, local_dir='models')
"

cp .env.example .env
# edit .env: set GATEWAY_API_KEY to something random
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

That's it — no Claude key needed, no separate model server. First request after
startup is slower (loads the model into memory); expect a few seconds per
reply on CPU.

## Calling it from your other apps

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer <GATEWAY_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
        "messages": [{"role": "user", "content": "What can you do?"}]
      }'
```

The response shape mirrors OpenAI's chat completions, so most existing
OpenAI-client code in your apps works by just pointing the base URL here (swap
in your own thin client if you'd rather not bend an OpenAI SDK to a custom
auth header).

### Optional: Claude as a paid fallback

If you ever want stronger general capability for specific requests, set
`ANTHROPIC_API_KEY` in `.env` and either pass `"model": "claude"` per-request,
set `DEFAULT_BACKEND=claude`, or `DEFAULT_BACKEND=auto` (short/simple messages
→ free local model, everything else → Claude, billed per token). None of this
is required — the gateway is fully functional and free without it.

## Permanent memory with fact-checking

Every chat turn runs a background check: it looks for a concrete fact worth
remembering (not small talk), and before saving it permanently, checks it
against Wikipedia. A fact is only marked **confirmed** if at least two
independent Wikipedia articles agree — a single page, which anyone can edit,
isn't enough. Disagreement gets stored as **unconfirmed** (kept, but flagged
as unverified); an outright contradiction is dropped.

You can also teach it something directly:

```bash
curl -X POST http://localhost:8000/v1/remember \
  -H "Authorization: Bearer <GATEWAY_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"text": "Our app'\''s refund policy is 30 days, no questions asked."}'
```

Or ingest a whole document without verification (for stuff you already trust,
like your own docs):

```bash
curl -X POST http://localhost:8000/v1/ingest \
  -H "Authorization: Bearer <GATEWAY_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"text": "Our app'\''s refund policy is ..."}'
```

Anything stored this way gets pulled into context automatically on relevant
future questions.

## If you want to fine-tune it later

"Basic training" on top of Qwen2.5-7B (LoRA) needs a GPU, which this
container doesn't have. The practical path: rent one (RunPod, Lambda,
Vast.ai — often under $1/hr) or use a free Colab GPU, train a LoRA adapter
with a tool like Unsloth, merge it, convert to GGUF, and point
`LOCAL_MODEL_PATH` at the new file. Ask and I'll write the training script
when you're ready for that step.
