# A pipeline of tools (`finmodel.pipeline`)

Every module in this toolkit already exposes the same shape: a `from_dict(d) -> dict` entry point that both
its own CLI command and its own tests call directly. That shared shape means chaining modules together
doesn't need a new execution model — it needs a small amount of glue that runs a list of `from_dict()` calls
in order and lets a later call reference an earlier one's real, computed output. `finmodel.pipeline` is that
glue: a step is `{"name", "module", "inputs"}`, and any input value that is exactly `"${step_name.path.to.
value}"` gets replaced with the actual value at that path in an earlier step's result before that step runs.

This is deliberately scoped as a **pipeline** (a strict, ordered list — the same word CI/CD tools and this
doc's title both use), not a general workflow engine: no parallel branches, no conditional steps, no
scheduler. That scope match is why the whole implementation is ~60 lines: a dotted-path resolver
(`${step.key1.key2.3.key4}`, where a segment that parses as an integer indexes into a list and anything else
looks up a dict key) and a loop that runs each step's `from_dict()` against its resolved inputs. Only a
whole-string value is treated as a placeholder — a value keeps its real type (a number stays a number)
rather than being stringified into a template, which matters here because pipeline steps pass real
numbers (loan balances, forecast values) forward, not text.

## The worked example: a retail-lending origination-to-risk pipeline

`examples/pipeline_retail_lending_demo.json` chains three genuinely different modules into one coherent
loan lifecycle, each step depending on the previous step's REAL computed output rather than a repeated
literal:

1. **`eligibility`** (`finmodel.retail_loans.loan_eligibility_foir`) — a borrower's FOIR-based maximum
   eligible loan principal, from their income and existing EMI obligations.
2. **`schedule`** (`finmodel.retail_loans.amortization_schedule`) — the full amortization schedule for
   EXACTLY that eligible principal (`${eligibility.loan_eligibility_foir.max_eligible_principal}`), not a
   hand-picked round number.
3. **`delinquency`** (`finmodel.npa_classification.npa_provisioning`) — what the bank would need to provision
   if this SPECIFIC loan turned 120 days past due after 24 months of payments, using the loan's own real
   outstanding balance at that point (`${schedule.amortization_schedule.schedule.23.closing_balance}`) rather
   than an illustrative round number.

Running it (`finmodel pipeline examples/pipeline_retail_lending_demo.json --json-out out.json`) produces a
real, internally consistent answer chain: an eligible principal, the exact balance remaining on that specific
loan after 24 EMIs, and the exact provision the bank would hold against it if it became a Sub-standard NPA at
that point — three modules, one coherent story, with every number flowing from the one before it instead of
being independently made up.

## What was deliberately left out

- **A dependency graph with parallel execution** — real pipeline tools (Airflow, Dagster, GitHub Actions)
  build a DAG and run independent steps concurrently; this toolkit's own modules are pure, fast Python
  functions with no I/O to overlap, so a scheduler would add real complexity (cycle detection, worker pools)
  for no real performance benefit here. Steps run strictly in list order, which is sufficient for chaining
  finance calculations.
- **Conditional branching** (e.g. "run step C only if step B's DSCR falls below 1.2x") — a real and useful
  extension, but the placeholder syntax would need to grow into a small expression language to support it,
  which is a materially bigger design (and testing) surface than the linear reference-passing this version
  covers. Left for a real use case that specifically needs it.
- **A registry validating which modules are "pipeline-safe"** — every module's `from_dict()` is a pure
  function of its input dict already (no shared mutable state, no filesystem writes except the CLI's own
  optional `--json-out`), so any module can already be used as a pipeline step; a separate allowlist would
  just be maintenance overhead duplicating what's already true.

## Test coverage

`tests/test_pipeline.py` (7 tests) checks a single-step pipeline against a known hand-verified example
already used elsewhere in this suite, checks a two-step pipeline for BOTH real placeholder-resolution paths
(a dict-key lookup and a list-index lookup) into an actual earlier-step output, checks the full three-module
retail-lending example end to end (confirming the amortized balance is genuinely lower than the original
principal, and that the exact same number reaches the provisioning step), and checks the pipeline's own error
handling: a duplicate step name, a module with no `from_dict()`, and a reference path that doesn't exist in
the referenced step's actual output.
