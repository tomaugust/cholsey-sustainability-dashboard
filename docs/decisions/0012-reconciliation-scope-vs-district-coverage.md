# 0012. P3.8's reconciliation test can't literally cover "all parishes in the district" given ADR-0003's 9-parish scope — drop that line, rely on the other three checks

- **Status:** Accepted — Tom answered Q-012 (STATUS.md, 2026-10-03) with option (b): drop the literal district-wide reconciliation line as out of scope, rely on P3.8's other three checks plus the already-passing district-vs-publisher check.
- **Date:** 2026-10-02 (raised); 2026-10-03 (answered and actioned)
- **Deciders:** Phase 3 exit-criteria review raised it; decision by Tom (Q-012)
- **Related:** P3.8; development-plan.md §3 Phase 3 "Tests of success" (reconciliation line); ADR-0003 (comparator parish selection); `pipeline/src/cholsey_pipeline/validate/data_quality.py`

## Context

development-plan.md's Phase 3 "Tests of success" (reconciliation bullet) reads:

> *Automated (reconciliation):* district-level values computed by our pipeline match the publisher's own district figure within 0.5% where the publisher provides one (DESNZ does). **Summed apportioned meter counts across all parishes in the district match the district total within 1%.**

The first sentence is already satisfied and tested: South Oxfordshire's district rows for electricity/gas are DESNZ's own published district-level figures (`method=direct`), not apportioned, so there's nothing to reconcile — they already match the publisher's figure by construction.

The second sentence is the real problem. South Oxfordshire has over 60 constituent parishes. This project's scope (ADR-0003, Q-009: "use all 8 comparators") only ever built apportioned rows for Cholsey plus its 8 chosen comparators — 9 of 60+. Summing just those 9 parishes' apportioned meter counts will **always** fall far short of South Oxfordshire's real total meter count, not because of any error in the apportionment, but because the other 50+ parishes were never in scope to begin with. There is no way to satisfy this line literally without either (a) building out full apportioned rows for every remaining South Oxfordshire parish — a large, unscoped expansion directly contradicting ADR-0003's deliberate 9-parish choice — or (b) reinterpreting what "reconciliation" means for this check.

## Decision

**Drop the literal "all parishes in the district" reconciliation line from P3.8's scope.** Tom's answer (option b) treats this specific test-of-success bullet as superseded by ADR-0003's scope decision, not something P3.8 needs to build. Data quality for metrics 3/4 (electricity/gas) is instead covered by:

1. The first reconciliation sentence above (district row == publisher's own district figure), already true by construction for every `method=direct` district row.
2. P3.8's other three real, built checks (`validate/data_quality.py`): range validation, year-on-year change limits, and the completeness matrix — all passing against the real `metrics.csv`.
3. P3.10's golden-value tests (`pipeline/tests/golden/`), which independently re-derive Cholsey's own apportioned electricity/gas figures by hand from the raw DESNZ LSOA sheets and P1.5's real weights — a different, real correctness check on the apportionment math itself, just not a district-wide sum.

**Not built, and not needed:** a `reconcile_with`-style check that sums all 9 in-scope parishes' meters/consumption and compares to anything district-wide. Summing only 9 of 60+ parishes against the full district total would always "fail" by a predictable, scope-driven margin — a check that can never pass isn't a quality gate, it's noise. A narrower version (summing just the 9 in-scope parishes' own weights for internal consistency, option a from Q-012) was considered but not chosen; Tom's answer was explicit about relying on the existing three checks instead.

## Consequences

- Phase 3's exit criteria ("all core metrics... pass every automated check in CI") is now achievable without further reconciliation work — the three built P3.8 checks plus P3.10's golden values are what "every automated check" means for this project, not the literal district-wide sum.
- `config/metrics.yaml`'s documented-but-unused `reconcile_with` field (mentioned in `docs/development-plan.md` §5.2) stays unused for metrics 3/4. If a future phase ever does expand comparator coverage to the full district (unlikely, given ADR-0003's deliberate curation), this ADR should be revisited rather than silently building the check against newly-available data.
- No code change: `validate/data_quality.py` is unchanged by this decision — it already didn't implement a district-wide reconciliation check, so this ADR formalizes that as the project's considered position, not a gap.
