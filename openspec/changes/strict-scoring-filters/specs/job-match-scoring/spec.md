## ADDED Requirements

### Requirement: Hard eligibility gate
The system SHALL report a discovered job as a match only when its LLM score is at
or above `min_score` AND all three hard-constraint booleans (`india_doable`,
`has_required_skills`, `role_matches`) are true. A job failing any hard constraint
SHALL be excluded from Telegram notification regardless of its numeric score.

#### Scenario: High score but geo-restricted
- **WHEN** a job scores 90 but `india_doable` is false
- **THEN** the job is excluded from the reported matches

#### Scenario: Eligible and above threshold
- **WHEN** a job scores at or above `min_score` and `india_doable`, `has_required_skills`, and `role_matches` are all true
- **THEN** the job is included in the reported matches

### Requirement: India-doable location constraint
The scorer SHALL set `india_doable` to false for any role restricted to a region or
country that excludes India, requiring relocation, or requiring in-country work
authorization; and true for roles performable remotely from India (IST-compatible
or async), including "remote" roles with no geographic exclusion.

#### Scenario: EU-only remote role
- **WHEN** a job description states the role is "Remote (EU only)" or "must reside in the EU"
- **THEN** `india_doable` is false

#### Scenario: Globally remote role
- **WHEN** a job is "Remote (global)" or "Remote" with no geographic restriction
- **THEN** `india_doable` is true

### Requirement: Required-skills constraint
The scorer SHALL set `has_required_skills` to false when a PRIMARY required skill of
the job is a language or stack the candidate does not have (e.g. Go, Rust, Java,
C++, .NET). Nice-to-have skills SHALL NOT affect the value.

#### Scenario: Go required as core skill
- **WHEN** a job requires Go as a primary/must-have skill
- **THEN** `has_required_skills` is false

#### Scenario: Candidate stack matches
- **WHEN** a job's core requirements are React, Next.js, TypeScript, Python, or LLM/GenAI
- **THEN** `has_required_skills` is true

### Requirement: Target role-type constraint
The scorer SHALL set `role_matches` to true only for roles in the candidate's target
families (AI/ML engineering, AI-driven/GenAI frontend, or frontend) and false for
pure backend, full-stack without an AI or frontend focus, data/ML-ops, SRE/DevOps,
non-React mobile, or management roles.

#### Scenario: Pure backend role
- **WHEN** a job is a backend engineer role with no AI or frontend focus
- **THEN** `role_matches` is false

#### Scenario: AI frontend role
- **WHEN** a job is an AI-driven frontend or GenAI engineer role
- **THEN** `role_matches` is true

### Requirement: Missing-constraint fail-open
When the LLM omits a hard-constraint boolean from its output, the system SHALL
default that constraint to true (fail-open) and log a warning, so a single
malformed field cannot suppress all matches; `min_score` remains the backstop.

#### Scenario: LLM omits a boolean
- **WHEN** a scored job is missing the `india_doable` field
- **THEN** the system treats `india_doable` as true and logs a warning
