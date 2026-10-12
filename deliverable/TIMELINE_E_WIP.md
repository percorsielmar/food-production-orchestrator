# Food Production Orchestrator — Timeline e stato WIP

Fonte: `git log` del branch `master` (nessuna stima inventata).

## Metriche oggettive
| Metrica | Valore |
|---|---|
| Finestra temporale | 2026-07-12 → 2026-07-13 |
| Commit totali | 3 (2 di sviluppo + 1 merge PR #1) |
| Giorni attivi di sviluppo | 2 |
| Autori | `Devin AI` (bot `devin-ai-integration[bot]`, 158243242+devin-ai-integration[bot]@users.noreply.github.com): 2 commit · `percorsielmar`: 1 merge |

## Cronologia
| Data | Commit | Contenuto |
|---|---|---|
| 2026-07-12 | `feat: orchestratore LLM con Tool Use, WebSocket e client Blocco 1` | Prima versione: FastAPI, WebSocket `/ws/chat`, loop tool-calling, client Blocco 1, stub di sviluppo, test |
| 2026-07-12 | `Integrazione Blocco 2 con Blocco 1: payload predict, CORS, config default` | Allineamento payload `/api/v1/predict` al Blocco 1 reale, CORS, default di configurazione |
| 2026-07-13 | Merge PR #1 (`devin/integrazione-blocco1`) | Integrazione nel branch principale |
| 2026-10 | Pacchetto Docker (questo deliverable) | `Dockerfile` con `uv sync --frozen`, `docker-compose.yml`, `.env.example` aggiornato, documentazione |

Dopo il 2026-07-13 lo sviluppo è proseguito nel monorepo `food-production-saas` (`blocco2-orchestratore/`, primo commit 2026-07-13).

## Stato WIP
- **Completato (prototipo)**: chat WebSocket, tool `simulate_scenario`, provider Anthropic/OpenAI/Mock, stub Blocco 1, containerizzazione.
- **Test**: suite `tests/` → **6/6 passati**. Nel pacchetto Docker sono stati riallineati al contratto del
  Blocco 1 reale (`samples`/`n_scenarios`/`noise_std`/`category_map` → `scenarios`), introdotto dal commit di
  integrazione del 2026-07-12, sia lo stub `dev/block1_stub.py` (prima rispondeva 422 e la chat mostrava rischi `N/A`)
  sia il test `tests/test_block1_client.py::test_predict_success` (si aspettava ancora il vecchio campo `cliente`).
- **Non presente in questo repo** (evoluto nel monorepo): RBAC, Financial Intelligence, integrazioni meteo/ERP, frontend.

## Nota sulla stima dell'effort
I commit di sviluppo sono autorati dal bot **`devin-ai-integration[bot]`** (agente AI Devin) e le
modifiche sono raggruppate in pochi commit. **Una stima ore/uomo affidabile non è derivabile dal solo
git**: numero di commit e giorni attivi sono riportati solo come proxy oggettivi dell'attività.
