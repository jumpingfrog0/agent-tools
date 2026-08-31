# Payment attempt lifecycle

Load this reference only for payment/result/receipt/retry/change-channel/context/identity/cleanup/logout/late-callback work. Apply it to task-relevant paths, not as a universal matrix.

## Identity and context ownership

Inventory each identity field named by the requirement, current carrier, or confirmed semantic. At minimum consider trace identifiers, transaction token/identifier, application order identifier, SDK/server order identifier, style/business type, page/statistics trace, product/cid, channel, and callback expand when present. Preserve or intentionally replace each applicable field across start, retry, option/channel change, result routing, and cleanup; “complete context” is not evidence that a field survived.

Determine from exact source whether each path uses a shared legacy context or an attempt-keyed context. Do not exchange their save/read/clear APIs, infer concurrency safety from a pointer, choose an arbitrary pending attempt, or treat similarly named order identifiers as equivalent.

## Stages and result authority

Trace applicable stages separately:

```text
eligibility/config → order creation → Apple or Web handoff → StoreKit callback → receipt/JWS report → payment-stage result → CurrencyCharge/credited state → business entitlement/reward → terminal cleanup
```

Do not merge stages because they occur close together. Identify the authoritative completion signal for the task's business type and current path. Review only applicable result states, but never collapse success, cancel, failure, timeout, unknown, risk-control, frozen/blocked, credited arrival, or entitlement completion when source distinguishes them.

## Retry, change, and handoff

- Same-attempt retry reuses its frozen applicable context and identity.
- Explicit channel/tier/option change revalidates fields whose applicability changed while preserving transaction identity that still belongs to the attempt.
- Selected coupon, package, reward, promotion, or channel is scoped to its eligible business type and attempt; reject or clear it before an out-of-scope transition.
- For replacement or external handoff, prove the order: validate replacement input → save replacement context → narrowly clear obsolete state → start the external action. Invalid URL/channel/config or a rejected handoff must leave safe retry context intact.

Derive retry/change/contact/no-safe-action from current user capability, available channels, and exact result semantics. Do not invent recovery behavior from generic product wording.

## Cleanup, logout, and late callbacks

Enumerate task-relevant terminal and nonterminal paths. Verify cleanup key/cardinality, display owner versus pending owner, UI removal versus Flow finish, account switch/logout, abandoned attempts, delayed callbacks, duplicated callbacks, and result arrival after presentation disappears. Narrow cleanup must never delete another transaction or a newly saved replacement context.

For historical replay, an unavailable wire field name does not erase a behavior explicitly required by the task. Describe a guarded adapter/parser seam and keep the unresolved identifier/shape as a contract prerequisite; stop only when no safe reversible candidate exists or an owner decision is required.

## Lifecycle closure

Map every applicable lifecycle clause to a candidate action and static validation. R3 remains a hard edit gate. Reject a patch that loses identity, routes a callback by weak similarity, treats payment success as credited/entitled without authority, clears state before a handoff is valid, makes a late callback claim without evidence, or changes a disputed result/notification policy without owner decision.
