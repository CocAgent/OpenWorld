# Live Two-Agent Visual UI with Local Python Backend

This local research example connects an interactive 60fps HTML5 Canvas frontend ([`examples/web/two_agents_ui.html`](../../examples/web/two_agents_ui.html)) directly to a real Python OpenWorld HTTP backend ([`examples/two_agents_server.py`](../../examples/two_agents_server.py)).

No simulation math is faked in the browser: every negotiation message, W3 transfer, HMAC capability verification/revocation, `DonorBudget` reservation, SQLite `HyperMemoryP1e` update, and `verify_replay()` check runs in Python on the loopback interface (`127.0.0.1`).

## Run locally

From the repository root using Python 3.11+ (zero external dependencies):

```bash
python examples/two_agents_server.py --port 8765
```

Then open `http://127.0.0.1:8765` in a local browser.

## JSON API endpoints

| Method & Path | Purpose |
|---|---|
| `GET /` | Serves the offline-ready HTML/CSS/Canvas UI (`examples/web/two_agents_ui.html`) |
| `GET /api/state` | Authoritative session snapshot (balances, W3 fingerprint, `verify_replay`, SQLite `exact_events`, HM-P1e predictions, message log) |
| `POST /api/session/reset` | Starts a fresh W3 world, `CapabilityAuthority`, `DonorBudget`, and SQLite `HyperMemoryP1e` session for any scenario (`cooperative`, `hostile_refuse`, `hostile_liar`, `lost_notices`, `recovery`, `play_bob`) |
| `POST /api/round/step` | Executes one round in Python (or Phase 1 `PROPOSE` in `play_bob` interactive mode) |
| `POST /api/bob/reply` | Submits interactive Bob `accept` or `decline` (executes W3 Phase 2 + Phase 3 in Python) |
| `POST /api/bob/return` | Submits interactive Bob `return` or `lie` (executes W3 Phase 4 + Phase 5 verification in Python) |
| `POST /api/security/test` | Executes real negative controls (`cross_owner`, `wrong_token`, `spoof_verified`, `replay_id`, `toggle_revoke_alice`) against Python guards and reports the actual exception + unchanged W3 fingerprint |

## Verification

```bash
python -m unittest discover -s tests -p test_two_agents_server.py -v
python scripts/check_repository.py
```

## Boundaries, limitations, and rollback

- **Loopback single-user lab only:** Binds strictly to `127.0.0.1` / `localhost` using stdlib single-threaded `HTTPServer` (matching `HyperMemoryP1e`'s SQLite thread affinity). Never expose to untrusted networks.
- **Same-owner simulated scope:** No LLM, external API, cross-owner bilateral consent, or production authentication/TLS.
- **Rollback:** Delete `examples/two_agents_server.py`, `examples/web/two_agents_ui.html`, `tests/test_two_agents_server.py`, and this document. No shared `src/openworld_superkernel` contracts or existing examples are modified.
