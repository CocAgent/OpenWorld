# Session and Source Register

**Last review:** 2026-10-28  
**Purpose:** Track the provenance of OpenWorld planning decisions and previous conversations without treating inaccessible links as read transcripts.

## A. External conversation URLs supplied by the project owner

The first request supplied two **unique** URLs, with the first repeated. Subsequent requests supplied two further **distinct** share URLs. Attempts to read their full transcripts via the available reader were unsuccessful. No complete transcript was independently verified.

| Source ID | Shared link | Status | Eligible for transcript-derived claims? |
|---|---|---|---|
| CHAT-SHARE-001 | https://chatgpt.com/s/t_6ae211da5b6481918229efe3a872998c | **PENDING_ACCESS** — content not retrievable | **No** |
| CHAT-SHARE-002 | https://chatgpt.com/s/t_6ae2123fe370819195aff2f1f75b60ff | **PENDING_ACCESS** — content not retrievable | **No** |
| CHAT-SHARE-003 | https://chatgpt.com/share/6ae21436-a858-83ec-b90e-c55e0f507b06 | **PENDING_ACCESS** — full transcript unreadable; owner-supplied mathematical excerpt available separately | **No** |
| CHAT-SHARE-004 | https://chatgpt.com/share/6ae214d5-8860-83ec-b076-f7834ec8a002 | **PENDING_ACCESS** — full transcript unreadable; active OpenWorld discussion visible independently | **No** |

A duplicate occurrence of CHAT-SHARE-001 is not a third source. The owner's visible selected mathematical excerpt for CHAT-SHARE-003 and the visible OpenWorld discussion relevant to CHAT-SHARE-004 are **not verified full transcript exports**. Do not infer unseen topics, participants, decisions or progress from any URL.

## B. Sources actually used in this synthesis

| Source ID | Source | Coverage and evidence strength |
|---|---|---|
| OPENWORLD-CURRENT-CONVERSATION | OpenWorld project working conversation visible in the active task | Design discussions and reported prototype results; not independent evidence |
| GITHUB-MAIN | https://github.com/CocAgent/OpenWorld | Tracked source, contracts and repository history |
| GITHUB-PR-007 | https://github.com/CocAgent/OpenWorld/pull/7 | Initial public bootstrap |
| GITHUB-PR-008 | https://github.com/CocAgent/OpenWorld/pull/8 | Proposed RFC-006 contracts |
| GITHUB-PR-009 | https://github.com/CocAgent/OpenWorld/pull/9 | HM-P1e code and authored tests |
| GITHUB-PR-010 | https://github.com/CocAgent/OpenWorld/pull/10 | W5 benchmark and authored tests |
| GITHUB-GATE-011 | https://github.com/CocAgent/OpenWorld/issues/11 | Pending independent merged-main verification |
| GITHUB-PR-014 | https://github.com/CocAgent/OpenWorld/pull/14 | RFC-007 mathematical research |
| GITHUB-W2-P0-015 | https://github.com/CocAgent/OpenWorld/issues/15 | Bounded MathKernel P0 implementation |
| GITHUB-PR-017 | https://github.com/CocAgent/OpenWorld/pull/17 | Experimental compositional fixture, merged separately from acceptance gates |

## C. Safe import procedure for an unavailable shared transcript

1. Obtain an authorized export/text of the exact conversation or a genuinely accessible shared page.
2. Verify title, authorship/source identity, date and completeness.
3. Screen private or proprietary data, credentials, tool/system content and third-party rights.
4. Extract decisions into the [Decision Ledger](DECISION-LEDGER.md) with exact source IDs.
5. Deduplicate and resolve contradictions instead of silently choosing a newer statement.
6. Preserve unverified claims and negative results with explicit limitations.
7. Submit a reviewed English PR before incorporating any additional transcript-derived claims.

**Current result:** Four distinct shared URLs are recorded as pending-access; their complete transcripts have **not** been ingested. Only actually visible excerpts, discussions, and checked repository files informed the corresponding proposals and research fixture.
