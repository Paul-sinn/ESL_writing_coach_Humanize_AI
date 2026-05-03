# CLAUDE.md — pj-1: ESL Academic Writing Coach

---

## Business Strategy

### Product Positioning
**This is an ESL Academic Writing Coach, NOT an AI detector bypass tool.**

Core value proposition:
> "An AI writing coach for ESL college students who want clearer, more natural essays in their own voice."

**Safe positioning (USE):**
- Improve clarity and natural English
- Reduce generic AI-like writing patterns
- Strengthen personal voice
- Help ESL students revise ethically
- Support academic integrity

**Forbidden positioning (NEVER USE):**
- AI detector bypass / Turnitin bypass
- Undetectable essay generator
- Guarantee passing AI detectors
- Helping students submit AI-generated work as their own

**Forbidden phrases:** "bypass AI detectors", "beat Turnitin", "undetectable AI", "100% human score", "never get flagged", "AI detector guarantee"

---

### Target Market
ESL college students / international students in the U.S. who struggle with academic writing and sounding natural in English. Start narrow, then expand to: general college students → high school → job seekers → professionals → international workers → writing centers.

### Target Persona — Kim, 25 (updated)
Korean international student taking English classes. Struggles with academic writing due to language barrier. Needs a writing coach to improve clarity and naturalness — not a cheat tool.

---

### Agent Workflow
```
Input Essay
→ Policy Guard Agent       # block cheat requests, redirect to ethical use
→ Writing Analyzer Agent   # find AI-like patterns, vague claims, robotic tone
→ ESL Voice Coach Agent    # keep student's voice, suggest natural college English
→ Revision Suggestion Agent # sentence/paragraph suggestions, not full rewrites
→ Academic Integrity Agent  # ensure student's ideas remain, generate disclosure
→ Final Feedback Report
```

---

### MVP Features
1. Paste essay / paragraph
2. Select assignment type: Discussion post / Reflection essay / Research essay / Personal statement / General academic paragraph
3. Select writing level: ESL beginner / Intermediate / Advanced
4. System returns: generic/AI-like sections, unnatural phrases, robotic sentences, missing personal examples, clarity/structure issues, revision suggestions
5. Revision suggestions only — do NOT fully rewrite the essay
6. Academic integrity guidance + optional AI-use disclosure statement

---

### Pricing
| Plan | Price | Credits |
|---|---|---|
| Free | $0 | 1 analysis/day, 300 words max |
| Starter | $7/mo | 20K credits |
| Student Plus | $12/mo | 60K credits (most popular) |
| Pro | $19/mo | 150K credits |
| Credit Pack S | $5 | 25K credits |
| Credit Pack M | $10 | 60K credits |
| Credit Pack L | $20 | 150K credits |

**Credit costs:** Basic analysis = 1 cr/word · Deep feedback = 2 cr/word · Revision suggestions = 3 cr/word · Multi-agent full review = 5 cr/word

**Always protect API costs:** monthly balance caps, word limits, daily free limits, abuse guardrails, Stripe subscription + one-time purchase, cancellation button, refund policy.

---

### Legal Requirements
Must include: Terms of Service, Privacy Policy, Academic Integrity Policy, Refund Policy, disclaimer (no AI detector guarantee), user content deletion option, statement that writing is not used for model training, warning to follow school AI policy.

---

### Immediate Tasks
1. Landing page copy
2. MVP user flow
3. Pricing page
4. System prompts for each agent
5. Prototype: essay input + assignment type dropdown + writing level dropdown + analyze button + feedback report
6. Test with 10 ESL/international students
7. Measure: value understanding, real-use intent, willingness to pay $7–$12/mo, most useful feedback, trust

---

## Security
** If I showed my API keys from like terminal log or something you must let me know that i putted api keys and say "remove api keys and renew it" to me
** 내가 실수로 apikey를 너한테 보여줬을때 터미널로그나 어떤식으로든 너는 나한테 무조건 알려줘야하고 지우고 다시 발급받으라고 경고해야돼.

---

## Stack

- **Backend**: FastAPI + LangGraph + OpenAI API (Python 3.13)
- **Frontend**: React 18 + Vite 5

---

## Running

### Backend
```bash
cd pj-1
uvicorn main:app --reload
# Runs on http://127.0.0.1:8000
```

### Frontend
```bash
cd pj-1/frontend
npm install
npm run dev
# Dev server: http://127.0.0.1:5173, proxies /api/* → port 8000
```

Build frontend (`npm run build`) → FastAPI serves `frontend/dist/` at `/`.

### Tests
```bash
cd pj-1
pytest                                          # all tests
pytest tests/test_graphs.py                     # single file
pytest tests/test_graphs.py::test_name          # single test
```

---

## Configuration

Settings loaded from `.env` via `backend/app/config.py` (Pydantic Settings, `lru_cache`).

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | `None` | LLM calls — all services fall back to heuristics if unset |
| `standard_analysis_model` | `gpt-4` | Basic analysis model |
| `advanced_analysis_model` | `gpt-5` | Advanced analysis model |
| `humanize_model` | `gpt-5` | Humanize rewrite model |
| `max_word_limit` | `1200` | Input word cap (validated in schemas + graph) |
| `pro_monthly_credits` | `1000` | Credits seeded to demo-pro account |
| `advanced_credit_cost` | `50` | Credits per advanced scan |
| `humanize_credit_cost` | `250` | Credits per humanize |

Frontend: `VITE_API_BASE` overrides default `http://127.0.0.1:8000`.

---

## Architecture

### Request flow
`main.py` routes are thin shims — they extract `X-User-Id` / `client_ip`, call `graph.invoke(state)`, and return `result["response"]`. All business logic lives in `graphs.py`.

### API Endpoints (`backend/app/main.py`)
- `POST /api/coach` — ESL writing coaching (main endpoint)
- `GET /api/billing/status` — Credit balance
- `POST /api/billing/checkout` — Generate checkout URL
- `GET /{full_path}` — SPA fallback (served only when `frontend/dist/` exists)

### LangGraph Graphs (`backend/app/graphs.py`)
Both graphs are compiled at module load time as module-level singletons.

- **`coach_graph`** — `load_user_context` → `validate_coach_input` → `resolve_coach_cost` → `check_coach_entitlement` → `run_policy_guard` → `run_coaching_analysis` → `run_academic_integrity` → `deduct_coach_credits` → `format_coach_response`
- **`billing_graph`** — resolve offer → build options → format redirect

**Error routing:** Nodes write sentinel strings to `state["error"]`. Allowed sentinels: `"INSUFFICIENT_CREDITS"`, `"FREE_LIMIT_REACHED"`, `"FREE_WORD_LIMIT"`, `"POLICY_BLOCKED"`. These route to `route_to_billing` or directly to `format_coach_response` and produce a `billing_redirect` payload. Any other non-nil error raises `ValueError`.

**Graph node contract:** Every node returns `dict[str, Any]` with only the keys it updates. LangGraph merges into state.

**Credit cost model:** `basic` = 1 cr/word · `deep` = 2 cr/word · `full_review` = 5 cr/word. Free tier users are rate-limited (1/day, 300 words max) with no credit deduction.

### Services (module-level singletons — no persistence)
- `billing_service` — `dict[user_id, UserAccount]`; pre-seeded with `demo-free` (0 cr), `demo-starter` (20K), `demo-plus` (60K), `demo-pro` (150K); resets on process restart
- `coaching_service` — wraps `OpenAI.chat.completions.create()` with `response_format={"type":"json_object"}`; falls back to keyword heuristic when key is absent
- `rate_limit_service` — `defaultdict[(ip, date)]`; 2 free coaching sessions/IP/day; `"unknown"` is treated as a valid key (all unknown-IP requests share one bucket)

### Demo Billing Headers (for API testing)
```
X-User-Id: demo-free      # free plan, 0 credits
X-User-Id: demo-starter   # starter plan, 20K credits
X-User-Id: demo-plus      # student plus, 60K credits
X-User-Id: demo-pro       # pro plan, 150K credits
```

---

## Implementation Notes

- **Tests run fully offline.** `OPENAI_API_KEY` is not required — `coaching_service` falls back to heuristics automatically.
- **Test isolation.** `conftest.py` has an `autouse=True` fixture that resets `billing_service._accounts` and clears `rate_limit_service._attempts` before every test. Adding new demo accounts requires updating `conftest.py` in addition to `billing.py`.
- **`lru_cache` on settings.** `get_settings()` is cached for the process lifetime. Changing `.env` at runtime has no effect without restarting.

---

## Key Files

| Path | Role |
|---|---|
| `backend/app/main.py` | FastAPI app, CORS, routes, SPA fallback |
| `backend/app/graphs.py` | All LangGraph workflow logic |
| `backend/app/config.py` | Settings / env loading (`lru_cache`) |
| `backend/app/schemas.py` | Pydantic request/response models + word-limit validator |
| `backend/app/services/coaching.py` | ESL coaching with policy guard, analyzer, integrity; heuristic fallback |
| `backend/app/services/billing.py` | In-memory accounts & credit management |
| `backend/app/services/rate_limits.py` | IP-based daily rate limiting |
| `backend/app/utils/text.py` | Word count, sentence split, requirement parsing |
| `frontend/src/App.jsx` | Single-file React UI — all state, API calls, and rendering |
| `tests/conftest.py` | autouse fixture that resets billing + rate limit singletons per test |
