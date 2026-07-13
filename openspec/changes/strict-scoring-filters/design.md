## Context

Scoring happens in `job_hunt/scanner.py`: `SCORE_PROMPT` feeds the candidate
profile + resume summary + a batch of jobs to the LLM, which returns a JSON array
of `{score, employer, title, stack, reason, ...}`. Only the numeric `score` gates
notification (via `min_score`). The candidate config already states India-remote
in `not_suitable`, but nothing enforces it — and the current scorer (qwen-7b) is
lenient (~92% of jobs score >= 60), so eligibility violations (EU-only roles,
Go-required roles, full-stack roles) slip through as "top matches".

## Goals / Non-Goals

**Goals:**
- Reported matches deterministically satisfy three hard constraints: doable from
  India, primary skills the candidate has, and a target role type.
- Enforcement does not depend on the LLM choosing to lower a fuzzy score.
- Fewer but genuinely eligible matches.

**Non-Goals:**
- No regex/rule engine parsing freeform JD text (the LLM handles nuance better).
- No change to sharding/consolidation, discovery, or keywords (already tightened).
- Not re-scoring historical results.

## Decisions

**D1 — LLM emits hard-constraint booleans; code enforces them.**
Add three booleans to each scored job in the LLM output: `india_doable`,
`has_required_skills`, `role_matches`. A deterministic post-scoring filter keeps a
job only if `score >= min_score` AND all three are true.
- Rationale: the LLM reads nuanced JD language ("must reside in the EU", "Go
  experience required") far better than regex, but asking it to merely *lower the
  score* is unreliable (proven lenient). Booleans + code enforcement gives nuanced
  judgment with deterministic gating.
- Alternatives rejected: (a) prompt-tune scores only — unreliable; (b) code parses
  location/stack from JD — brittle on freeform text; (c) raise `min_score` only —
  a Go/EU role can still score high on skill overlap.

**D2 — Constraint definitions (encoded in the prompt).**
- `india_doable`: performable remotely from India (IST-compatible or async);
  NOT restricted to a region/country that excludes India, no relocation or
  in-country work-authorization requirement. Ambiguous "Remote" with no exclusion
  counts as true; "Remote (US)"/"EU only"/"must reside in X" is false.
- `has_required_skills`: the job's PRIMARY required skills are among the
  candidate's (React, Next.js, React Native, TypeScript, JavaScript, Python,
  Node.js, LLM/GenAI). A core requirement in a language/stack the candidate lacks
  (Go, Rust, Java, C++, Scala, .NET, etc.) makes it false; nice-to-haves do not.
- `role_matches`: role is AI/ML engineering, AI-driven/GenAI frontend, or
  frontend. Pure backend, full-stack without an AI or frontend focus, data/ML-ops,
  SRE/DevOps, non-React mobile, or management makes it false.

**D3 — Missing-field handling: fail-open + backstop.**
If the LLM omits a boolean (parse gap), default it to `true` (fail-open) so a
malformed field cannot zero out the whole digest, but log a warning. The raised
`min_score` (D4) is the backstop when booleans are absent.

**D4 — Raise `min_score` 60 -> 75** as a quality backstop independent of the booleans.

**D5 — Mirror to remote-boards.** `scanner.py` is shared (separate copies per
repo); apply the same SCORE_PROMPT + filter change to the remote-boards repo.

## Risks / Trade-offs

- qwen-7b may not reliably emit the new booleans → keep paid llama-3.3-70b as
  fallback; fail-open + log on missing fields; a test asserts the prompt requests
  them. If unreliable in practice, force 70B for scoring.
- Over-strict `india_doable` could drop a mislabeled "Remote (global)" role →
  clear prompt definition + the `reason` field for auditability; tune after
  observing real runs.
- Fewer matches (intended) could become too few with 3 filters + min_score 75 →
  values are tunable; revisit after the first real run.

## Migration Plan

1. Implement in product-companies (`scanner.py` + `config.actions.json`), with unit
   tests over synthetic scored jobs (filter keeps/drops correctly).
2. Validate on one real run; inspect the digest for India/skill/role correctness.
3. Mirror the `scanner.py` change to remote-boards.
4. Rollback: revert the scanner.py + config commit(s).

## Open Questions

- Exact `min_score` (75 proposed) — confirm after first real run.
- Whether to hard-exclude all full-stack, or only non-AI/non-frontend full-stack
  (current decision: exclude only when neither AI nor frontend is the primary focus).
