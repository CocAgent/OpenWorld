# Session and Source Register

**Last review:** 2026-10-28  
**Purpose:** Track the provenance of OpenWorld planning decisions and previous conversations without treating inaccessible links as read transcripts.

## A. External conversation URLs supplied by the project owner

Two **unique** URLs were supplied; the first was repeated. An attempt to open each shared ChatGPT URL through the available web retrieval tool returned a fetch-disabled error, and a targeted prior-conversation lookup did not recover either transcript.

| Source ID | Shared link | Status | Eligible for transcript-derived claims? |
|---|---|---|---|
| CHAT-SHARE-001 | https://chatgpt.com/s/t_6ae211da5b6481918229efe3a872998c | **PENDING_ACCESS** — content not retrievable | **No** |
| CHAT-SHARE-002 | https://chatgpt.com/s/t_6ae2123fe370819195aff2f1f75b60ff | **PENDING_ACCESS** — content not retrievable | **No** |

The duplicate of CHAT-SHARE-001 must not be counted as a third independent working session. Do not infer the topics, participants, decisions or progress of these two sessions from their URLs or from nearby project discussions.

## B. Sources actually used in this synthesis

| Source ID | Source | Coverage and evidence strength |
|---|---|---|
| OPENWORLD-CURRENT-CONVERSATION | OpenWorld project working conversation visible in the current task | Historical design discussion and previously *reported* prototype results; not automatically independent evidence |
| GITHUB-MAIN | https://github.com/CocAgent/OpenWorld | Current repository identity, tracked files, contracts and written code |
| GITHUB-PR-007 | https://github.com/CocAgent/OpenWorld/pull/7 | Initial public repository bootstrap |
| GITHUB-PR-008 | https://github.com/CocAgent/OpenWorld/pull/8 | RFC-006 proposed contracts |
| GITHUB-PR-009 | https://github.com/CocAgent/OpenWorld/pull/9 | HM-P1e code and authored tests |
| GITHUB-PR-010 | https://github.com/CocAgent/OpenWorld/pull/10 | Independent W5 benchmark and authored tests |
| GITHUB-GATE-011 | https://github.com/CocAgent/OpenWorld/issues/11 | Pending independent merged-main verification |

## C. Safe import procedure for an unavailable shared transcript

1. Obtain an authorized export/text of the exact conversation from the owner, or a genuinely accessible shared page.
2. Verify title, authorship/source identity, date and that the export is complete.
3. Exclude credentials, personally identifying information, hidden system/tool content and unrelated projects from public artifacts.
4. Extract decisions into the [Decision Ledger](DECISION-LEDGER.md) with exact source identifiers and status.
5. Deduplicate against existing OpenWorld decisions and GitHub Issues. Resolve contradictions explicitly instead of silently choosing one.
6. Preserve unresolved claims with `UNVERIFIED` status; do not fabricate test passes or deployment records.
7. Submit an English PR with a clear change log and owner review before merge.

**Current result:** The repository now records both references and integrates only content that was actually available; **the two linked transcripts have not been ingested**.
