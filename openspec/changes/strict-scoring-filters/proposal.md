## Why

The product-companies scanner surfaces jobs that violate the candidate's hard
constraints: EU-only / geo-restricted roles that cannot be done from India,
roles requiring skills the candidate lacks (e.g. Go), and full-stack / off-target
roles outside the candidate's targets (AI, AI-driven frontend, frontend). The
LLM scorer (qwen-7b) rates ~92% of jobs at or above 60, so a fuzzy 0-100 score
alone does not enforce eligibility. Matches must pass hard eligibility filters,
not just clear a score threshold.

## What Changes

- Scoring output gains explicit **hard-constraint booleans** alongside the score:
  `india_doable`, `has_required_skills`, `role_matches`.
- A **deterministic post-scoring filter** drops any job where a hard constraint is
  false, regardless of its numeric score.
- The **SCORE_PROMPT and candidate profile** (`seeking` / `not_suitable`) are
  sharpened to define the constraints precisely: remote-from-India / IST-compatible
  and not geo-restricted to regions excluding India; primary required skills must
  be ones the candidate has; target role families only.
- `min_score` raised as a backstop (60 -> 75).
- The same scanner change is mirrored to the remote-boards scanner (shared code).

## Capabilities

### New Capabilities
- `job-match-scoring`: how a discovered job is scored against the candidate and
  hard-filtered for eligibility (location, skills, role type) before it can be
  reported as a match.

### Modified Capabilities
<!-- none: openspec/specs/ is empty; this is the first capability defined -->

## Impact

- `job_hunt/scanner.py`: `SCORE_PROMPT` (add hard-constraint fields + definitions),
  score-response parsing, and a post-scoring eligibility filter.
- `config.actions.json`: `candidate.profile` / `seeking` / `not_suitable` / `min_score`.
- Tests: `tests/test_scanner.py` (hard-filter behavior on synthetic scored jobs).
- Applies to both scanner repos (shared code): product-companies and remote-boards.
