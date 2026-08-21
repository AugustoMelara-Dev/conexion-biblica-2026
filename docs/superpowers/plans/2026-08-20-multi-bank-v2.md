# Multi-Bank V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add protected V1, canonical V2, mixed sessions, persistent non-repeating selection, scoped analytics, compatible backups, and offline support.

**Architecture:** Bank profiles and adapters feed one question engine. Pure strategy functions produce selections; IndexedDB repositories persist cycles and active rounds. UI scopes existing components by bank selection rather than cloning the app.

**Tech Stack:** React 19, TypeScript 6, Vite 8, IndexedDB, Vitest, Testing Library, service worker.

**Spec:** `docs/superpowers/specs/2026-08-20-multi-bank-v2-design.md`

## Global Constraints

- Preserve all V1 questions, IDs, progress, features, and visual language.
- Preserve the canonical master JSON byte-for-byte and retain every V2 metadata field.
- V2 must normalize exactly 3,558 unique questions: 2,211 Daniel, 1,347 PR, 888 historical, 2,670 generated.
- Mixed mode is virtual and never duplicates progress or question records.
- No server, cloud, telemetry, or runtime Excel dependency.
- Use test-first red/green cycles for every production behavior.
- This workspace has no active Git repository, so commit steps are unavailable.

---

### Task 1: Bank profiles and master adapter

**Files:**
- Create: `src/domain/banks.ts`
- Create: `src/domain/master-bank.ts`
- Create: `src/domain/master-bank.test.ts`
- Modify: `src/domain/types.ts`

**Interfaces:**
- Produces `BankSelection`, `BankDefinition`, `MasterQuestionRaw`, `adaptMasterBank(raw)`, `validateMasterBank(raw)` and `getQuestionKey(question)`.
- The adapter returns a normal `Bank` with `bankId: "master-v2"` and lossless V2 metadata.

- [ ] Write tests loading the real JSON and asserting literal totals, unique IDs, sources, corrected answers, fact IDs, and all supported type mappings.
- [ ] Run `npm test -- src/domain/master-bank.test.ts` and verify failure because the adapter does not exist.
- [ ] Implement bank definitions, extended question fields, validation, type/difficulty mapping, and canonical textual-answer representation.
- [ ] Run the focused test and the existing domain tests until green.

### Task 2: Selection strategies and pool keys

**Files:**
- Create: `src/domain/session-selection.ts`
- Create: `src/domain/session-selection.test.ts`
- Modify: `src/domain/session-selector.ts`
- Modify: `src/domain/types.ts`

**Interfaces:**
- Produces `buildPoolKey(config)`, `selectCoverageCycle(input)`, `selectBalancedRandom(input)`, `selectSequentialBlock(input)`, and `selectAdaptive(input)`.
- All strategy inputs accept an injected `rng`; outputs contain questions plus updated strategy state.

- [ ] Write the exact 100/50/50 and 120/50/50/20 failing acceptance tests, plus uniqueness, pool-key, sequential cursor, balance, mixed fallback, reset, and fact-spacing property tests.
- [ ] Run the focused tests and confirm failures are caused by missing strategy behavior.
- [ ] Implement deterministic serialization, seeded Fisher-Yates, balanced bucket selection, cycle reconciliation, sequential blocks, adaptive delegation, and spacing constraints.
- [ ] Replace the old `slice(0, target)` path with the central strategy API and run selector/domain tests.

### Task 3: IndexedDB migration, cycles, and active rounds

**Files:**
- Modify: `src/storage/db.ts`
- Modify: `src/storage/storage.test.ts`
- Modify: `src/domain/types.ts`

**Interfaces:**
- Adds `repositories.coverage`, `repositories.activeRound`, and schema-version migration helpers.
- Active round stores question keys, config, cursor, answers, timestamps, and strategy context.

- [ ] Write failing fake-IndexedDB tests proving a V1 record survives the version upgrade, cycles survive reopen, reset changes cycle ID, and active round resumes exact question keys.
- [ ] Upgrade the DB transactionally and add repositories without clearing existing stores.
- [ ] Run storage tests twice against fresh and upgraded databases.

### Task 4: Backup 2.0 compatibility

**Files:**
- Modify: `src/domain/backup.ts`
- Modify: `src/domain/backup.test.ts`
- Modify: `src/domain/types.ts`
- Modify: `src/app/app-state.tsx`

**Interfaces:**
- `createBackupPayload` emits 2.0 with cycles/active round.
- `migrateBackupPayload` accepts 1.0 and returns a validated 2.0 payload.

- [ ] Write failing tests for 2.0 round-trip, 1.0 migration, unqualified V1 key namespacing, and malformed backup rejection.
- [ ] Implement non-destructive migration and repository restore.
- [ ] Run backup and storage tests.

### Task 5: Application state and scoped analytics

**Files:**
- Modify: `src/app/app-state.tsx`
- Modify: `src/lib/statistics.ts`
- Modify: `src/lib/statistics.test.ts`
- Modify: `src/App.tsx`

**Interfaces:**
- Context exposes selected bank profile, scoped questions/statistics, cycle status, active-round actions, and next-batch/reset operations.

- [ ] Write failing tests for V1/V2/combined analytics and origin-correct progress.
- [ ] Load V2 independently, isolate V2 startup errors, scope derived state, persist selection, and persist every active-round transition.
- [ ] Route all session creation through the strategy service and verify focused tests.

### Task 6: Bank-aware UI and result actions

**Files:**
- Modify: `src/components/dashboard-page.tsx`
- Modify: `src/components/session-builder-page.tsx`
- Modify: `src/components/statistics-page.tsx`
- Modify: `src/components/results-page.tsx`
- Modify: `src/components/history-page.tsx`
- Modify: `src/components/review-page.tsx`
- Modify: `src/components/app-shell.tsx`

**Interfaces:**
- Accessible controls select V1, V2, or Mixto and strategy; results expose same batch, next unseen batch, random batch, same configuration, and new configuration.

- [ ] Write component tests for keyboard-accessible selection, native V2 difficulty labels, cycle counts, and distinct result actions.
- [ ] Implement compact cards and controls using existing components and styles.
- [ ] Run UI tests and inspect desktop/mobile browser rendering.

### Task 7: Offline asset and documentation

**Files:**
- Modify: `src/app/app-state.tsx`
- Modify: `public/sw.js`
- Modify: `README.md`

**Interfaces:**
- Vite asset URL references the unchanged root JSON; runtime cache stores it after successful load and service-worker fetch fallback serves it offline.

- [ ] Add a failing loader test for cached fallback and isolated V2 validation failure.
- [ ] Implement asset loading/cache fallback and bump the shell cache version.
- [ ] Document bank profiles, update flow, cycles, keys, backup versions, and verification commands.

### Task 8: Final verification

**Files:**
- Review every modified file and generated `dist` output.

- [ ] Run `npm test` and record test/file counts.
- [ ] Run `npm run lint`, `npm run typecheck`, and `npm run build`; fix every introduced failure.
- [ ] Start the app and exercise V1, V2, Mixto, coverage next batch, reload resume, backup restore, and offline reload in a real browser.
- [ ] Re-run the full verification suite after browser-driven fixes and report remaining limitations precisely.
