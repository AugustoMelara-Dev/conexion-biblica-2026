# Conexión Bíblica 2026 Multi-Bank Design

## Goal

Evolve the existing offline React application without replacing V1. Add the canonical 3,558-question V2 bank, a virtual mixed selection, persistent coverage cycles, separated analytics, resumable rounds, compatible backups, and offline availability.

## Architecture

`BankDefinition` describes stable bank behavior. Existing imported banks belong to the protected `legacy-v1` profile; the canonical master JSON belongs to `master-v2`. `mixed` is a `BankSelection`, never a stored or duplicated bank.

Both formats are adapted into the existing `Question` engine contract. V2 additionally retains original difficulty, normalized difficulty band, answer mode, canonical answer text, fact identifiers, and a lossless metadata object. Persistent identity remains `${bankId}:${questionId}`.

The master JSON remains at the repository root. Vite exposes it as a hashed asset through `new URL(..., import.meta.url)`, and application startup fetches, validates, adapts, stores, and runtime-caches that asset. A V2 failure is isolated so V1 can still open.

## Session selection

All filtering and selection flows through a pure selector service. Strategies are:

- `coverage-cycle`: deterministic pool key, shuffled unseen queue, no repeats before exhaustion, explicit reset.
- `random-balanced`: Fisher-Yates buckets with injected RNG and balanced bank/material/chapter output.
- `sequential-blocks`: stable ordering and explicit block cursor.
- `adaptive`: preserves existing error/difficulty/mastery scoring while preventing internal duplicates and immediate retries.

Coverage state is stored in IndexedDB by pool key. Selecting a session atomically advances the cycle; the chosen question keys and quiz cursor are stored as an active round so reload resumes the exact queue.

## Persistence and compatibility

IndexedDB is upgraded transactionally. Existing stores and records are retained. New stores hold coverage cycles and the active round. Legacy progress keys already contain a bank ID in the current application; migration only namespaces genuinely unqualified historic keys with `legacy-v1` when encountered.

Backup schema 2.0 includes cycles and active round. Schema 1.0 remains valid and is migrated in memory before restore. V1 data is never cleared as part of an upgrade.

## UI

The dashboard receives compact V1, V2, and Mixto cards matching the current visual language. The selected profile scopes the builder, dashboard, statistics, review, and history views. V2 shows its native difficulty labels; mixed mode uses normalized bands. Results clearly distinguish repeating the same batch from selecting the next non-repeating batch.

## Validation

Automated tests protect V1 behavior, validate all V2 counts and metadata, exercise corrected historical answers, prove the 100/50/50 and 120/50/50/20 coverage cases, verify IndexedDB persistence and backup migration, and check mixed pools. Final verification runs tests, lint, typecheck, build, and browser smoke flows including reload and offline behavior.
