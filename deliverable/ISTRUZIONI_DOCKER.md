# Food Production Orchestrator — Istruzioni Docker

## Prerequisiti
Docker Engine 24+ con Docker Compose v2.24+ (supporto `env_file.required`).

## Avvio rapido
```bash
cp .env.example .env          # LLM_PROVIDER=mock funziona senza chiavi API
docker compose up --build -d
docker compose ps             # orchestratore e block1-stub "healthy"
curl http://localhost:5000/health    # {"status":"ok"}
```
Chat WebSocket: `ws://localhost:5000/ws/chat`, messaggi JSON `{"message": "..."}` → risposta `{"type":"text","content":"..."}`.

Arresto: `docker compose down`.

## Servizi
| Servizio | Immagine | Porta | Note |
|---|---|---|---|
| `orchestratore` | `food-production-orchestrator:latest` (python:3.10-slim + uv) | host `${ORCHESTRATOR_PORT:-5000}` → 5000 | `uvicorn orchestratore_llm.main:app` |
| `block1-stub` | stessa immagine | solo rete interna, 7000 | `dev/block1_stub.py`, Blocco 1 fittizio |

L'immagine installa le dipendenze con `uv sync --frozen --no-dev` (versioni bloccate da `uv.lock`, Python da `.python-version`).

## Variabili (`.env`)
| Variabile | Default | Descrizione |
|---|---|---|
| `LLM_PROVIDER` | `mock` | `anthropic` \| `openai` \| `mock` |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | — | Chiave del provider scelto |
| `LLM_MODEL` | `claude-3-5-sonnet-20241022` | Modello |
| `LLM_MAX_TOKENS` / `LLM_TEMPERATURE` | `4096` / `0.2` | Parametri generazione |
| `BLOCK1_BASE_URL` | `http://block1-stub:7000` | URL Blocco 1 (stub interno o servizio reale) |
| `BLOCK1_API_KEY` | — | Bearer token verso Blocco 1 (opzionale) |
| `APP_LOG_LEVEL` | `INFO` | Livello log |
| `MAX_TOOL_TURNS` | `5` | Limite loop tool |
| `ORCHESTRATOR_PORT` | `5000` | Porta pubblicata sull'host |

`APP_HOST`/`APP_PORT` sono fissati nel compose a `0.0.0.0:5000` all'interno del container.

## Collegare un Blocco 1 reale
Impostare `BLOCK1_BASE_URL` (es. `http://<host-blocco1>:8000`) e riavviare: `docker compose up -d`.
Per il sistema completo (Blocco 1 + 2 + 3) usare il pacchetto `food-production-saas-docker.zip`.

## Test
```bash
uv sync --frozen && uv run pytest -q
# oppure in container:
docker run --rm -v "$PWD":/src -w /src ghcr.io/astral-sh/uv:python3.10-bookworm-slim sh -c "uv sync --frozen && uv run pytest -q"
```
Esito attuale: 5 passati, 1 fallito preesistente (vedi `TIMELINE_E_WIP.md`).
