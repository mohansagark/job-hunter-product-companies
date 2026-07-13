## 1. Scoring output: hard-constraint booleans

- [x] 1.1 Extend `SCORE_PROMPT` in `job_hunt/scanner.py` to require three booleans per job — `india_doable`, `has_required_skills`, `role_matches` — with the D2 definitions embedded in the prompt
- [x] 1.2 Update the JSON example/schema in `SCORE_PROMPT` so the model returns the three booleans alongside `score`/`employer`/`title`/`stack`/`reason`
- [x] 1.3 Parse the three booleans from the scored response; default a missing field to `true` and log a warning (fail-open, per D3)

## 2. Post-scoring eligibility filter

- [x] 2.1 Add a filter so a job qualifies as a match only when `score >= min_score` AND `india_doable` AND `has_required_skills` AND `role_matches`
- [x] 2.2 Keep non-matching jobs in the CSV/state record for transparency, but exclude them from `top_jobs` / Telegram

## 3. Config

- [x] 3.1 Sharpen `candidate.seeking` and `candidate.not_suitable` in `config.actions.json` to state India-remote/IST, missing-skill exclusions, and target role families precisely
- [x] 3.2 Raise `candidate.min_score` from 60 to 75

## 4. Tests

- [x] 4.1 Unit tests: filter keeps an eligible job and drops each single-constraint violation (geo-restricted, missing skill, off-target role)
- [x] 4.2 Unit test: a scored job missing a boolean is treated as eligible (fail-open) and warns
- [x] 4.3 Test that `SCORE_PROMPT` requests the three constraint fields
- [x] 4.4 ruff + mypy + pytest green with the 85% coverage gate held

## 5. Local validation

- [ ] 5.1 Run a single-shard scan locally over a small company subset; confirm scored output carries the booleans and the filter drops EU-only / Go-required / full-stack jobs

## 6. Mirror to remote-boards

- [x] 6.1 Apply the same `SCORE_PROMPT` + filter change to the remote-boards repo (`autopilot-jobhunt-forked`); run its tests green

## 7. Real-run validation

- [ ] 7.1 Trigger a product-companies run; verify the digest's matches are India-doable, skill-matched, and on-target; tune `min_score` if too strict or loose
