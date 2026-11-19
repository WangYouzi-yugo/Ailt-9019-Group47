# HKU Recycling Rules Helper

**AILT9019 AI Literacy II · Final Project · Team 47**
Repository: <https://github.com/WangYouzi-yugo/Ailt-9019-Group47>

A local command-line assistant for the **HKU re Kiosk**. It answers questions from four official HKU Sustainability sources, always prints the source, and clarifies or refuses when the evidence is missing. Answers can optionally be rewritten by an **OpenAI-compatible API** call (DeepSeek by default); the recycling decision itself is made by a deterministic rule layer, not by the model.

> **Scope.** Command-line prototype. It covers 15 curated English questions about the re Kiosk: accepted items, location and hours, the takeaway coffee cup, pizza box, baking paper, Styrofoam, contact-lens packaging, instant-noodle containers, oily paper cups, food-contaminated containers, plus boundary and refusal behaviour. It is **not** a general waste classifier and does not look up live rules online.

---

## 1. What the API changes — and what it does not

```text
question
   │
   ▼
classify()  ── deterministic rules ──►  bucket + approved answer + source IDs
   │
   ▼
draft_with_llm()  ── optional model API call ──►  friendlier wording
   │                    (cannot change bucket / facts / sources)
   └── no key or any error  ──►  local answer unchanged
   ▼
[ANSWERED] / [CLARIFY] / [INSUFFICIENT] / [REFUSAL]
answer
Sources: S1–S4 with URLs
```

- The API receives the question, the **already-decided** bucket, the approved answer and the source block. It is asked to rewrite the wording only.
- The bucket, the facts and the source list are fixed before the API is called. The model cannot invent a bin or a source.
- If the key is missing, invalid, rate-limited, or the request times out, the app silently returns the local answer.
- If the model drops the source URL, the app re-appends the source block.
- Cases with no sources (for example `[CLARIFY]`) deliberately have **no** `Sources:` section.
- Output punctuation is normalised to ASCII so the default Windows console renders it correctly.

The 15-case evaluation measures the rule layer and citations. It does **not** measure the API's wording quality.

---

## 2. Requirements

| Item | Requirement |
|---|---|
| Python | 3.10 or newer. Verified on **3.12.14** (Windows 11). |
| OS | Windows, macOS or Linux |
| Network | Only for the optional API call and for opening source URLs |
| API account | Optional. Model API key (DeepSeek by default) for API-assisted wording |
| Disk | Under 10 MB for the repository |

The **core path** (rule answers + citations) needs only the Python standard library. `pip install -r requirements.txt` is needed for the API call, `check_api.py`, and the pytest suite.

Pinned versions: `openai==3.55.0`, `python-dotenv==1.2.4`, `pytest==9.2.0`.

---

## 3. Local deployment (Windows)

### 3.1 Get the code

```powershell
git clone https://github.com/WangYouzi-yugo/Ailt-9019-Group47.git
cd Ailt-9019-Group47
```

If Git is not available, download the repository from GitHub and extract it.

### 3.2 Create and activate a virtual environment

```powershell
py -m venv .venv
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

If you prefer not to activate, call the interpreter directly in every command:

```powershell
.\.venv\Scripts\python.exe app.py --eval
```

### 3.3 Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3.4 Smoke-test the core path (no API key needed)

```powershell
python app.py --eval
```

Expected last line: `[ALL] 15/15 = 100.0%`.

### 3.5 Run one question

```powershell
python app.py "Can I recycle a takeaway coffee cup at the HKU re Kiosk?"
```

Without a key you get the local answer; with a key the wording is rewritten but the bucket and sources are unchanged.

---

## 4. Use your own model API (DeepSeek by default)

### 4.1 Create the key (DeepSeek default)

1. Sign in at <https://platform.deepseek.com/>.
2. Open **API keys** and create a new key.
3. Copy it once and store it safely. Never commit it or paste it into a screenshot.

If you already have a key from another OpenAI-compatible provider, skip to **4.6**.

### 4.2 Put it in `.env` (recommended)

```powershell
Copy-Item .env.example .env
notepad .env
```

Fill the three values:

```text
OPENAI_API_KEY=sk-your-real-deepseek-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

- `OPENAI_MODEL` may be `deepseek-chat` or `deepseek-reasoner`; use a model your account can access.
- Do not add quotes unless your provider requires them.
- `.env` is listed in `.gitignore`. Confirm with:

```powershell
git check-ignore -v .env
# .gitignore:2:.env    .env
```

### 4.3 Verify the key before running the app

```powershell
python check_api.py
```

Expected:

```text
API OK
model: deepseek-chat
endpoint: https://api.deepseek.com/v1
reply: API_OK
```

`check_api.py` never prints the key. If it fails, the error is shown without exposing the secret.

### 4.4 Verify that the app really uses the API

Run the same question twice, once with `.env` present and once with it temporarily renamed:

```powershell
python app.py "Can I recycle a takeaway coffee cup at the HKU re Kiosk?"
```

- API mode usually gives a more conversational sentence, e.g. “Yes, you can recycle a takeaway coffee cup…”, but the `[ANSWERED]` bucket and the S2 source line are identical.
- If the output is byte-for-byte the local answer, the API call probably failed and fell back. Run `check_api.py`, and optionally add a temporary debug line after the response:

```python
print(f"[API] used {model} at {base_url}")   # remove before committing
```

### 4.5 Alternative: three blank lines in `app.py`

`app.py` also contains an explicit local-only configuration block (around lines 301–303):

```python
API_KEY = ""      # <-- paste your key here
BASE_URL = ""     # <-- e.g. "https://api.deepseek.com/v1"
MODEL = ""        # <-- e.g. "deepseek-chat"
```

Values in these lines take priority over `.env`. This is convenient for a one-off local run, but **never commit or push a filled-in version** — the repository is public. For normal use, leave the three values empty and use `.env`.

### 4.6 Use another model API (OpenAI, Qwen, Kimi, GLM, local models)

The app is not tied to DeepSeek. `draft_with_llm()` uses the OpenAI Python client with a configurable `base_url`, so any provider that exposes an OpenAI-compatible `POST /chat/completions` endpoint can be used. The rule layer, buckets, citations and fallback stay the same; only the rewritten wording comes from the other model.

#### A. Check that the provider is OpenAI-compatible

It must accept all of the following:

- `POST {OPENAI_BASE_URL}/chat/completions`
- header `Authorization: Bearer <OPENAI_API_KEY>`
- JSON body with `model` and `messages`
- a response containing `choices[0].message.content`

If a provider uses a different protocol (for example Anthropic's native API), put it behind an OpenAI-compatible gateway or adapt `draft_with_llm()`; no other part of the app needs to change.

#### B. Set the three `.env` values

Keep the same three variable names and change the values:

| Provider | `OPENAI_BASE_URL` | Example `OPENAI_MODEL` |
|---|---|---|
| DeepSeek (default) | `https://api.deepseek.com/v1` | `deepseek-chat` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| Alibaba Cloud Model Studio (DashScope) | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| Alibaba Cloud token plan | `https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1` | a model enabled on the plan |
| Moonshot (Kimi) | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| Zhipu (GLM) | `https://open.bigmodel.cn/api/paas/v4` | `glm-4-flash` |
| Ollama (local) | `http://localhost:11434/v1` | `llama3.1` |
| LM Studio (local) | `http://localhost:1234/v1` | the model loaded in the app |

Example for OpenAI:

```text
OPENAI_API_KEY=sk-your-openai-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

Example for a local Ollama server:

```text
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.1
```

Notes:

- Use the provider's **exact** model ID; model names change over time.
- A key must match its endpoint. A DeepSeek key will not work on `api.openai.com`.
- Local servers often ignore the key, but the app requires `OPENAI_API_KEY` to be non-empty; any dummy value works (for example `ollama`).
- The app only sets the `Authorization` header. If a provider requires extra headers, add `default_headers={...}` to the `OpenAI(...)` call in `draft_with_llm()`.
- Provider-specific errors (401/402/403/404/429/timeout) are listed in section 10.

#### C. Verify the new provider before running the app

```powershell
python check_api.py
```

Expected shape (values depend on the provider):

```text
API OK
model: gpt-4o-mini
endpoint: https://api.openai.com/v1
reply: API_OK
```

Then run the app normally:

```powershell
python app.py "Can I recycle a takeaway coffee cup at the HKU re Kiosk?"
```

#### D. What does not change

- The bucket (`ANSWERED` / `CLARIFY` / `INSUFFICIENT` / `REFUSAL`) is still decided by the local rule layer.
- The approved answer, facts and source list are still fixed before the model is called.
- If the other provider fails, the app still falls back to the local answer.
- The 15/15 evaluation is independent of which provider or model you use.

---

## 5. What you should see

### 5.1 API mode (wording varies; structure is fixed)

```text
[ANSWERED]

Yes, you can recycle a takeaway coffee cup at the HKU re Kiosk, but please
separate the components first. Put the clean lid in plastic recycling, the cup
sleeve in paper recycling, and the clean cup in Tetra Pak recycling.

Sources:
- S2 Photo Guide | re Campaign: https://www.wastereduction.hku.hk/photo-guide
```

### 5.2 Offline fallback (no key, or API failed)

```text
[ANSWERED]

Yes, but the components should be separated. The clean lid should be placed in
plastic recycling, the cup sleeve in paper recycling, and the clean cup in
Tetra Pak recycling.

Sources:
- S2 Photo Guide | re Campaign: https://www.wastereduction.hku.hk/photo-guide
```

### 5.3 Clarify (no sources)

```text
[CLARIFY]

Could you clarify what type of cup it is, what material it is made of, and
whether it is clean? I do not want to assume it is a takeaway coffee cup.
```

### 5.4 Refusal

```text
[REFUSAL]

I will not follow that instruction. The available HKU sources list rechargeable
batteries as accepted at the re Kiosk, and they do not provide enough information
to claim that all batteries should be placed in general waste.

Sources:
- S1 Recycling 101 | re-cyclopedia: https://www.wastereduction.hku.hk/recycling-101
- S3 re Facilities: https://www.wastereduction.hku.hk/re-facilities
```

---

## 6. Evaluation and tests

### 6.1 Official T1–T15 cases

```powershell
python app.py --eval
```

```text
[ALL] 15/15 = 100.0%
```

The cases are 11 normal, 2 boundary (`CLARIFY`), 1 unsupported (`INSUFFICIENT`) and 1 refusal (`REFUSAL`). This command does **not** call the API; it checks the rule layer, bucket and required citation.

Subsets:

```powershell
python app.py --eval --test 2
python app.py --eval --test 12,13,14,15
python app.py --eval --test 4-12
```

### 6.2 Exercise the API path

```powershell
python app.py --eval --llm
```

This makes one API call per case (15 calls) to prove the path works; it does not print the rewritten text and is not a quality benchmark. Expect a longer runtime and possible rate limiting.

### 6.3 Automated tests

```powershell
python -m pytest -q
```

```text
18 passed
```

The suite mirrors the 15 official cases and adds determinism, CLI smoke and full-eval checks.

### 6.4 Evidence from this environment

Recorded on **19 November 2026**, Windows 11, Python 3.12.14:

- `python check_api.py` → `API OK`, model `deepseek-chat`, reply `API_OK`
- `python app.py --eval` → `15/15 = 100.0%`
- `python -m pytest -q` → `18 passed`
- clean copy without `.env`: `--eval` → `15/15`, `pytest` → `18 passed`, coffee question → local `[ANSWERED]` + S2

Transcripts: [`evidence/api_check.txt`](evidence/api_check.txt), [`evidence/eval_output.txt`](evidence/eval_output.txt), [`evidence/pytest_output.txt`](evidence/pytest_output.txt), [`evidence/clean_copy_check.txt`](evidence/clean_copy_check.txt).

---

## 7. Response buckets and sources

| Bucket | Meaning | Example |
|---|---|---|
| `[ANSWERED]` | A source-backed answer exists; sources printed | Takeaway coffee cup (T2) |
| `[CLARIFY]` | The question is ambiguous; the user is asked to narrow it | “Can I recycle a cup?” (T12), battery type (T13) |
| `[INSUFFICIENT]` | The available sources do not cover the item | Laptop (T14) |
| `[REFUSAL]` | The request tries to override the sources | “Ignore the official sources…” (T15) |

| ID | Source | URL | Access date |
|---|---|---|---|
| S1 | Recycling 101 \| re-cyclopedia | <https://www.wastereduction.hku.hk/recycling-101> | 16 Nov 2026 |
| S2 | Photo Guide \| re Campaign | <https://www.wastereduction.hku.hk/photo-guide> | 16 Nov 2026 |
| S3 | re Facilities | <https://www.wastereduction.hku.hk/re-facilities> | 16 Nov 2026 |
| S4 | Ditch Disposables 101 \| re-cyclopedia | <https://www.wastereduction.hku.hk/ditch-disposables-101> | 16 Nov 2026 |

Publisher: Sustainability Unit, Estates Office, The University of Hong Kong.

---

## 8. Reported failure and limitations

### 8.1 Newspaper question is refused

```powershell
python app.py "Can I recycle a newspaper at the HKU re Kiosk?"
```

Observed: `[INSUFFICIENT]` (reworded by the API in API mode). Source S1 lists *paper* as accepted, so a human would expect paper recycling. Cause: the rule layer covers curated cases, not the full source text; “newspaper” has no matching rule. The API can reword the refusal but cannot fix missing coverage. Impact: valid but unseen items are under-served. Next step: category-level rules plus new evaluation cases, then re-run `--eval`.

### 8.2 Other limitations

- **Coverage:** 15 curated English cases; unseen phrasings fall to `INSUFFICIENT`.
- **Language:** English only.
- **Location:** HKU re Kiosk only; other facilities may differ.
- **Freshness:** source access dates fixed at 16 November 2026; no live re-fetch.
- **API dependence:** wording varies by model and provider; the bucket, facts and citations stay fixed. API failures fall back silently, so “no error” does not prove the API was used — run `check_api.py`.

---

## 9. Security and key handling

- `.env` is **git-ignored**; only `.env.example` (placeholder) is committed.
- `check_api.py` and `app.py` never print the key; errors show the provider message only.
- Do not commit a filled-in `app.py` (section 4.5) or paste a key into any file in the repository.
- If a key is exposed (chat, screenshot, public commit), **revoke it immediately** in the provider console and create a new one.
- Deleting a key from a file is not enough if it was committed: the value remains in git history. Rotate the key; if necessary, rewrite history with `git filter-repo` and coordinate a force-push.

---

## 10. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `401 Incorrect API key` | Wrong/revoked key, or key for another provider | Create a new key; check `OPENAI_BASE_URL` matches the key |
| `402 Insufficient Balance` | DeepSeek account has no credit | Top up the account |
| `403 model/plan denied` | The key's account or plan cannot use that model | Enable the model or choose an allowed model |
| `404 model not found` | Wrong `OPENAI_MODEL` | Use `deepseek-chat` (or a model enabled for your account) |
| `429` rate limit | Too many calls (e.g. `--eval --llm`) | Wait and retry |
| `APIConnectionError` / timeout | Network, proxy or firewall | Check connectivity; the app falls back after 30 s |
| `ModuleNotFoundError: openai` | Dependencies not installed | `python -m pip install -r requirements.txt` |
| Output identical to offline answer | API call failed and fell back silently | Run `python check_api.py`; add a temporary debug print |
| `python` not found | Python not on PATH | Use `py` on Windows or install Python |
| `Activate.ps1 cannot be loaded` | PowerShell execution policy | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| `pip install` tries to compile on Python 3.14 | A dependency has no wheel for 3.14 | Use Python 3.12 for the API path |
| `[INSUFFICIENT]` for a valid item | Rule coverage gap (section 8) | Expected limitation; add a rule and a test |

---

## 11. References

1. The University of Hong Kong, Sustainability Unit, Estates Office. *Recycling 101 | re-cyclopedia.* <https://www.wastereduction.hku.hk/recycling-101> (accessed 16 Nov 2026).
2. The University of Hong Kong, Sustainability Unit, Estates Office. *Photo Guide | re Campaign.* <https://www.wastereduction.hku.hk/photo-guide> (accessed 16 Nov 2026).
3. The University of Hong Kong, Sustainability Unit, Estates Office. *re Facilities.* <https://www.wastereduction.hku.hk/re-facilities> (accessed 16 Nov 2026).
4. The University of Hong Kong, Sustainability Unit, Estates Office. *Ditch Disposables 101 | re-cyclopedia.* <https://www.wastereduction.hku.hk/ditch-disposables-101> (accessed 16 Nov 2026).
5. DeepSeek. *API documentation.* <https://platform.deepseek.com/api-docs/>.
6. Python Software Foundation. *Python 3.12 documentation.* <https://docs.python.org/3.12/>.
7. OpenAI. *OpenAI Python library.* <https://github.com/openai/openai-python>.
