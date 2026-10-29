---
name: drama-ios-recharge-expert
description: Use for drama-ios work involving recharge, wallet, insufficient balance, coins, IAP, StoreKit, Turnover, payment results, receipt reporting, credited-currency arrival, coupons, currency exchange, packages, H5 or RN payment, payment notifications, payment context, traceId, transaction token, or orderId. Load the personal recharge knowledge kernel directly, gather categorized read-only evidence, classify R0-R3 risk, and produce a compact change contract before implementation.
---

# Drama iOS Recharge Expert

Keep recharge work inside the current responsibility, identity, and lifecycle boundaries. Source is the current implementation fact; the personal kernel is the reviewed semantic authority. This skill orchestrates evidence and decisions and must not duplicate business facts from the kernel.

## Resident gates

Run the current gate sequence in order. The sequence is an operational structure, not a permanent target count. Keep the working set limited to the current requirement; do not build an object graph or preload all recharge code.

### 1. Authority and release gate

1. Resolve two roots independently. The **source repository root** is the Git root of the business worktree being investigated. Resolve the **workbench root** in this order: the first ancestor of this `SKILL.md` containing `knowledge/recharge-kernel/manifest.yaml`; the `AGENT_WORKBENCH_ROOT` environment variable; then the installation convention `$HOME/Documents/Github/agent-workbench`. Validate the marker file after resolution. If no candidate is valid, stop explicitly; never fall back to a Kernel inside the source repository. Never infer one root from the other or persist the resolved absolute path.
2. From the workbench root read `knowledge/recharge-kernel/README.md`, `active-semantics.yaml`, and `manifest.yaml`. This is the only personal authority for recharge knowledge; source-repository instructions may separately require general project context. Load `architecture.md` only for R2/R3, routing, result, arrival, context, notification, or login/logout work.
3. Before using kernel claims, verify that `repo_commit` equals the source repository HEAD being inspected, the manifest supports only confirmed active semantics, and the recorded SHA-256 values match README, architecture, and active semantics. The manifest intentionally has no self-hash.
4. If the authority is absent, incompatible, hash-mismatched, or requires tracked assets that are unavailable, stop explicitly. Do not silently fall back to stale knowledge.
5. For the current working tree, record both HEAD and whether uncommitted source is being inspected. For historical replay, bind all source evidence to the requested revision and treat later kernel claims only as leads until revalidated there; never import a later class, owner, state, or route into an older baseline.

Start a loading receipt and keep it current:

```text
repo_revision: <HEAD or replay commit; note WORKTREE when applicable>
kernel_release_id: <manifest release_id>
skill_hash_or_release: <runtime SHA-256/release when available, otherwise unavailable + reason>
loaded_references: []
loaded_research_decisions: []
source_revision: <revision used for source evidence>
risk: R0 | R1 | R2 | R3 | pending
index_queries: []
```

Evaluation V2 绑定完整 Skill package 时，快照包含 `SKILL.md`、`agents/`、`references/`、`scripts/` 下的实际文件，排除 `__pycache__`、`.pyc`、`.pyo`。对每个文件计算 SHA-256，生成按 repo-relative POSIX path 排序的 `path sha256\n` 列表，再对该 UTF-8 列表计算 SHA-256；不得用入口文件哈希代替完整包 digest，也不得写入本机绝对路径。

### 2. Evidence gate

- Prefer current exact source reads and direct control/data-flow evidence. Rank evidence: exact symbol/key/literal and event producer/consumer/declaration first; historical co-change only as an investigation lead; name similarity only as a low-confidence appendix.
- Separate current code facts, historical facts with commits, kernel constraints, inference, conflicts, and unknowns. Cite a repo-relative path and symbol for important conclusions.
- Weak evidence cannot promote a semantic, prove ownership/dependency, create a blocker, or prove that a dynamic caller/subscriber does not exist. When a search has no result, report revision, scope, and query instead of claiming absence.
- For an as-of task, use `git grep <rev>`/`git show <rev>:<path>` or `source_index.py --rev <rev>` and forbid forward knowledge.

### 3. Risk and conflict gate

Apply knowledge type before implementation:

- Kernel `confirmed`: may constrain the change after its scope and evidence still match.
- Research `provisional`: requires current evidence and cannot constrain implementation or become an invariant by repetition.
- Research `disputed`: stop the intersecting behavior and request the exact owner decision, even if safe local work exists.

The research area is not part of the Kernel and is not loaded by default. From the workbench root read `knowledge/recharge-research/open-decisions.yaml` only when the task changes popup scene exclusion/display overlap, independent Apple versus legacy notification isolation, or empty-expand/active-trace concurrent or late-callback correlation. Record only the matching decision in `loaded_research_decisions`; other research items remain out of the working set.

Assign the highest applicable risk:

- R0: docs/comments or pure Debug support disconnected from production entry points.
- R1: leaf UI/formatting or pure models without routing or payment-state effects.
- R2: entry, routing, configuration, analytics, Bridge, or cross-file propagation.
- R3: ordering, IAP/Web results, receipt, arrival, idempotency, notification payload, payment identity/context, cleanup/logout/late callback, or payment state.

R3 is a hard edit gate: obtain explicit personal-owner or payment-owner confirmation before changing code. Also stop on a source/kernel conflict or a high-risk unknown that leaves no safe reversible boundary action. Name the conflicting source/semantic and the precise decision needed.

### 4. Requirement and runtime-host gate

Build a minimal behavior ledger with one row per explicit requirement or preservation clause:

```text
requirement/condition | exact evidence or external-contract unknown | current runtime host/owner | candidate action | static validation
```

Resolve product-role words to exact runtime hosts through live registration, construction, presentation, handoff, and ownership call sites. Class/directory names and superficial similarity are not proof. Treat named path families and exclusions as hard scope, and close every ledger row into both an action and validation. Read only paths needed for those rows; do not fill a universal impact matrix when the task does not require it.

### 5. Conditional checklist gate

Load no reference by default. Load at most the references whose trigger matches the task (maximum three), record them in the receipt, and apply only the relevant sections:

- Entry, route, runtime host, UI, notification, or cross-path propagation: [references/runtime-path-coverage.md](references/runtime-path-coverage.md).
- Payment/result/receipt/retry/change-channel/context/identity/cleanup/logout/late-callback lifecycle: [references/payment-attempt-lifecycle.md](references/payment-attempt-lifecycle.md).
- Server configuration/model/schema/parser, channel/coupon/package/reward scope, or selected/account state: [references/server-driven-state.md](references/server-driven-state.md).

Specialized checks are allowed only behind these triggers. A rule may enter the resident gates only when it is a cross-task mechanism or a critical invariant.

### 6. Evidence-gap and index gate

Use direct exact reads first. Run the read-only index only for a named ledger gap involving cross-file callers, event producers/consumers, Bridge parity, or path discovery. Use one to three exact identifiers, never broad topic words:

```bash
python3 <skill-dir>/scripts/source_index.py \
  --repo <source-repository-root> \
  --query <symbol-or-key> --query <event-or-path-token> \
  --max-results 60 --max-chars 12000
```

The default output is exact/event evidence only. Request bounded co-change with `--history-limit <n>` or name similarity with `--include-name-similarity` only after exact/event evidence leaves a recorded gap. Consume truncated output as incomplete, record every query and source revision in the loading receipt, and follow results into source before drawing conclusions. There is no index-only default arm: an index result alone is not an implementation contract or completeness proof.

### 7. Compact contract and validation gate

Before editing, output a compact contract:

```text
Goal:
Change scope and responsible layer:
Layers/paths that must not change:
Affected runtime hosts and Apple/Web/H5/RN paths:
Invariants:
Candidate changes (mapped to ledger rows):
Known risks / unknowns / conflicts:
Static validation:
Risk: R0 | R1 | R2 | R3
Required confirmation:
Stopped: true | false (exact reason when true)
```

Hard-fail or escalate any proposal that could duplicate ordering/credited feedback; merge payment, arrival, or entitlement stages; merge distinct result states; lose or confuse transaction identity; clear another attempt's context; bypass established Component/Module ownership; reverse an included/excluded runtime host; break a named legacy/new/black-user/wallet/H5/RN path; prefer stale knowledge; rely on weak evidence; or choose user-visible payment behavior without confirmation.

After editing, inspect the actual diff and re-run task-proportional static checks. Close the ledger against the diff; verify responsibility boundaries, every requested path, narrow cleanup and late-callback behavior, and whether a confirmed semantic's evidence or invalidation condition is now stale. Report remaining unknowns and hard failures explicitly.

## Overfitting and evaluation boundary

Task-specific specialization is useful only when conditionally activated. Old question types, candidate schemas, scoring expectations, and historical exam exceptions belong in Evaluation V2, not this skill or its references. Do not justify a resident rule because it improved the old 12 tasks. Rule value must be established by unseen tasks or real shadow use; byte/check-count budgets are complexity guardrails, not evidence of effectiveness.
