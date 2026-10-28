# Session and Source Register

**Last review:** 2026-10-28  
**Purpose:** Track the provenance of OpenWorld planning decisions and previous conversations without treating inaccessible links as read transcripts.

## A. External conversation URLs supplied by the project owner

The first request supplied two **unique** URLs, with the first repeated. A later request supplied a **third distinct** share URL. Attempts to read these shared ChatGPT URLs via the available page reader were unsuccessful; none of the complete transcripts was verified.

| Source ID | Shared link | Status | Eligible for transcript-derived claims? |
|---|---|---|---|
| CHAT-SHARE-001 | https://chatgpt.com/s/t_6ae211da5b6481918229efe3a872998c | **PENDING_ACCESS** — content not retrievable | **No** |
| CHAT-SHARE-002 | https://chatgpt.com/s/t_6ae2123fe370819195aff2f1f75b60ff | **PENDING_ACCESS** — content not retrievable | **No** |
| CHAT-SHARE-003 | https://chatgpt.com/share/6ae21436-a858-83ec-b90e-c55e0f507b06 | **PENDING_ACCESS** — full transcript unreadable; owner-supplied mathematical excerpt available separately | **No** |

The repeated occurrence of CHAT-SHARE-001 is not an independent source. Do not infer unseen topics, participants, decisions or progress from any of the three share URLs. The verified owner-selected excerpt relevant to CHAT-SHARE-003 has been processed as an excerpt, not as a complete transcript.

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
| GITHUB-PR-014 | https://github.com/CocAgent/OpenWorld/pull/14 | RFC-007: selective mathematical foundation derived from visible excerpt, local prior RFC-004 and canonical documents |
| GITHUB-W2-P0-015 | https://github.com/CocAgent/OpenWorld/issues/15 | Next bounded executable MathKernel implementation |

## C. Safe import procedure for an unavailable shared transcript

1. Obtain an authorized export/text of the exact conversation from the owner, or a genuinely accessible shared page.
2. Verify title, authorship/source identity, date and that the export is complete.
3. Exclude credentials, personally identifying information, hidden system/tool content and unrelated projects from public artifacts.
4. Extract decisions into the [Decision Ledger](DECISION-LEDGER.md) with exact source identifiers and status.
5. Deduplicate against existing OpenWorld decisions and GitHub Issues. Resolve contradictions explicitly instead of silently choosing one.
6. Preserve unresolved claims with `UNVERIFIED` status; do not fabricate test passes or deployment records.
7. Submit an English PR with a clear change log and owner review before merge.

**Current result:** The repository now records all **three distinct** shared URLs. The full transcripts have **not been ingested**. Only the owner-visible mathematical excerpt associated with the third request, the earlier local RFC-004, and reviewed GitHub documents informed RFC-007.
