# Food Production Orchestrator — Descrizione del progetto

## Cos'è
Prototipo **standalone** dell'*Orchestratore LLM* per la produzione alimentare (pinse, fritti, 4ª gamma).
È un middleware FastAPI che fa da ponte tra le domande in linguaggio naturale dell'utente e il
microservizio analitico **Blocco 1** (motore DAE-O / Semi-Monte Carlo) per stimare rischio di
**stock-out** e rischio di **spreco/scadenza** al variare degli ordini.

> Stato: prototipo iniziale. Il codice è stato successivamente **assorbito nel monorepo
> `percorsielmar/food-production-saas`** come `blocco2-orchestratore/`, dove è evoluto
> (RBAC, Financial Intelligence, integrazioni Open-Meteo e Dylog, report PDF). Questo repository
> resta come versione di riferimento minimale.

## Architettura
```
Client (WebSocket /ws/chat)
        │  {"message": "..."}
        ▼
FastAPI orchestratore (porta 5000)
  ├─ ChatService ── loop tool-calling (max MAX_TOOL_TURNS)
  │     └─ LLM client: Anthropic | OpenAI | Mock
  └─ ToolExecutor ── tool `simulate_scenario`
                          └─ Block1Client ──HTTP──► Blocco 1  POST /api/v1/predict
                                                     (in Docker: stub dev/block1_stub.py :7000)
```

| Componente | File | Ruolo |
|---|---|---|
| App FastAPI | `src/orchestratore_llm/main.py` | `/health`, WebSocket `/ws/chat`, lifespan risorse, CORS |
| Configurazione | `src/orchestratore_llm/config.py` | `Settings` Pydantic da `.env` (provider, modelli, Blocco 1, porta) |
| Chat service | `src/orchestratore_llm/chat_service.py` | Orchestrazione messaggio → LLM → tool → risposta in italiano |
| LLM client | `src/orchestratore_llm/llm/client.py` | Adapter Anthropic / OpenAI / `MockLLMClient` (senza API key) |
| Tool | `src/orchestratore_llm/llm/tools.py` | Definizione `simulate_scenario` + dispatcher |
| System prompt | `src/orchestratore_llm/llm/system_prompt.py` | Persona "Consulente di Produzione Alimentare" |
| Schemi | `src/orchestratore_llm/schemas/prediction.py` | `PredictionRequest`/`PredictionResponse`, mapping verso Blocco 1 |
| Client Blocco 1 | `src/orchestratore_llm/services/block1_client.py` | Chiamata `/api/v1/predict`, *lazy training* su 409, aggregazione scenari |
| Stub Blocco 1 | `dev/block1_stub.py` | Blocco 1 fittizio per sviluppo/demo (euristica probabilistica) |
| Test | `tests/` | Client Blocco 1, chat service, WebSocket (pytest + pytest-asyncio) |

## Concetti chiave
- **Tool loop**: l'LLM non inventa numeri; ogni stima passa da `simulate_scenario` → Blocco 1.
- **Max tool turns**: limite di sicurezza alle invocazioni ricorsive dei tool.
- **Stock-out / Waste risk**: probabilità (P10/P50/P90) di mancata copertura della domanda o di scadenza (critico per la 4ª gamma).
- **Provider mock**: consente demo e test senza chiavi API.

## Stack
Python 3.10 (`.python-version`), FastAPI, Pydantic Settings, HTTPX, Uvicorn, uv (`uv.lock`), Pytest.

## Contenuto del pacchetto Docker
`Dockerfile`, `.dockerignore`, `docker-compose.yml` (orchestratore + stub Blocco 1), `.env.example`,
cartella `deliverable/` con questa documentazione, timeline e istruzioni Docker.
