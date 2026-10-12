# Timeline e WIP — food-production-orchestrator

> **Avvertenza:** le ore/uomo riportate in questo documento sono una **STIMA (approssimazione ingegneristica)**, non un dato misurato. Vedi la sezione "Metodologia e avvertenze".

Repository: `percorsielmar/food-production-orchestrator` — branch `master`.
Dati ricalcolati con `git log origin/master --date=short --pretty='%ad %h %an | %s'`.

## Dati oggettivi (da Git)

| Metrica | Valore |
|---|---|
| Commit totali | 3 (2 non-merge + 1 merge) |
| Autori | 2 `Devin AI` (`devin-ai-integration[bot]`), 1 merge `percorsielmar` via GitHub |
| Giorni attivi di sviluppo | 2 (di fatto 1: il codice è del 2026-07-12, il 2026-07-13 contiene solo il merge) |
| Intervallo date | 2026-07-12 → 2026-07-13 |
| PR mergiate | 1 (#1, `devin/integrazione-blocco1`) |

### Commit

| Data | Commit | Autore | Contenuto |
|---|---|---|---|
| 2026-07-12 | `f035ec4` | Devin AI | Orchestratore LLM con Tool Use, WebSocket e client Blocco 1 |
| 2026-07-12 | `c5a59ed` | Devin AI | Integrazione Blocco 2 con Blocco 1: payload predict, CORS, config default |
| 2026-07-13 | `d8a4def` | percorsielmar | Merge pull request #1 |

## Stima effort (STIMA, non dato misurato)

| Metrica | Valore |
|---|---|
| Giorni attivi | 2 (1 effettivo di sviluppo) |
| Assunzione | 6 ore effettive equivalenti per giorno attivo |
| Valore puntuale (1 × 6 h + revisione/merge) | ~6 ore |
| **Intervallo stimato** | **~6–10 ore/uomo equivalenti** |

Motivazione dell'intervallo: prototipo standalone completo (FastAPI, WebSocket, tool loop LLM, client Blocco 1, stub di sviluppo, test) realizzato in un giorno, più revisione e merge il giorno successivo.

## Fasi / WIP

1. **Prototipo orchestratore (2026-07-12)** — orchestratore LLM con Tool Use, WebSocket chat, client verso Blocco 1, integrazione payload `predict`.
2. **Merge (2026-07-13, PR #1)** — integrazione su `master`.
3. **Assorbimento in food-production-saas** — dal 2026-07-13 il codice prosegue nel monorepo `food-production-saas` come `blocco2-orchestratore`; l'evoluzione successiva (provider LLM, RBAC, hardening) è contabilizzata in quel repository.

**WIP fuori da `master` (escluso dai conteggi):** il branch `devin/1783949603-windsurf-provider` contiene 1 commit del 2026-07-13 (provider windsurf, endpoint OpenAI-compatibile via `LLM_BASE_URL`) non mergiato.

## Metodologia e avvertenze

- **Git NON misura ore/uomo umane.** I timestamp dei commit indicano *quando* il lavoro è stato pushato, non *quanto* è durato. Non esiste in Git alcuna informazione sul tempo effettivamente speso.
- **Giorni attivi di sviluppo** = date di calendario distinte (`%ad`, formato `--date=short`) con almeno un commit sul branch principale.
- **Sessioni** = PR mergiate dove visibili (merge commit `Merge pull request #N`); in assenza di PR, cluster di commit nello stesso giorno.
- **Convenzione di stima:** 1 giorno di sviluppo focalizzato ≈ **6 ore effettive equivalenti**, applicate ai *giorni attivi* (non allo span wall-clock tra primo e ultimo commit).
- Le colonne oggettive (commit, giorni attivi, PR, intervalli di date) sono **fatti** ricavati da `git log`; la colonna ore/uomo è una **STIMA** (approssimazione ingegneristica) basata sull'assunzione 6 h/giorno-attivo. L'intervallo riportato tiene conto della diversa intensità dei giorni (giorni con 1 commit vs. giorni con 10+ commit).
- Per numeri più precisi l'unica fonte affidabile sono i **log ACU/runtime delle sessioni Devin** o i **registri tempi del cliente**.
- Commit presenti solo su branch non mergiati sono esclusi dai conteggi.
- In questo repository entrambi i commit di codice sono autorati da `devin-ai-integration[bot]`; l'unico commit umano è il merge della PR.

## Riepilogo complessivo sui tre repository

| Repository | Branch | Commit (totali) | Giorni attivi | PR mergiate | Intervallo date | Effort stimato (ore/uomo equivalenti) |
|---|---|---:|---:|---:|---|---:|
| food-production-saas | `main` | 46 | 11 | 0 (commit diretti) | 2026-07-13 → 2026-08-25 | ~55–75 (STIMA) |
| pascale-dashboard | `master` | 98 (71 non-merge + 27 merge) | 19 | 24 (#1–#24) | 2026-05-21 → 2026-07-30 | ~90–130 (STIMA) |
| food-production-orchestrator | `master` | 3 (2 non-merge + 1 merge) | 2 (codice in 1) | 1 (#1) | 2026-07-12 → 2026-07-13 | ~6–10 (STIMA) |
| **Totale** | | **147** | **28** date distinte (32 sommando per repo) | **25** | 2026-05-21 → 2026-08-25 | **~150–215 (STIMA)** |
