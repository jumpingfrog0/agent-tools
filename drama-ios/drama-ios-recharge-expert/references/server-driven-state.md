# Server-driven state

Load this reference only for server configuration/model/schema/parser work, scoped channel/coupon/package/reward propagation, or selected/account state. Do not turn repository guesses into a wire contract.

## Configuration states

When behavior depends on server configuration, model the applicable states separately:

1. configuration absent or not ready;
2. configuration present and allowing;
3. configuration present and forbidding.

Derive the absent-state default from current behavior or an explicit external contract. Do not silently equate absence with denial or permission. Put the state rule in both candidate action and validation, including refresh, invalidation, nil/default, and account-switch behavior when relevant.

## Scoped propagation

Treat channel, coupon, package/product, reward, promotion, selection, and eligibility data as scoped values. Record their producer, authoritative model/owner, selection state, attempt carrier, business-type applicability, consumers, and clear/revalidation point. A selection valid for one business type, account, channel, or attempt must not leak into another.

Trace requested values through reads and writes on every named path. A server model or preselected configuration may be the producer even without a dedicated selection UI. Do not mark a path inapplicable after finding only one producer shape.

## Authority and schema adapter

Locate the domain owner that current consumers already read before adding state. Extend that mapping chain rather than copying a new server label into a convenient cache, singleton, view model, or persistence layer unless exact source proves it is already authoritative.

If the task names a field, message, reward, callback, or schema but the baseline lacks its exact wire identifier/shape, use a contract-supplied matcher or narrow adapter seam at the authoritative boundary. The closest protobuf field, numeric type, JSON leaf, message class, or handler is only an investigation lead. Do not invent generated SDK types or duplicate storage from product wording.

## Parser and presentation validity

At an applicable parser/adapter boundary:

- validate runtime container and field types;
- trim user-visible strings before non-empty checks;
- validate positivity/range and eligibility where the contract requires them;
- fail closed at the narrow boundary without corrupting prior valid attempt state;
- clear stale presentation on an invalid refresh when current ownership requires refreshed truth;
- keep parsing, selection, presentation, persistence, and payment completion responsibilities separate.

These are conditional parser checks, not resident requirements for unrelated tasks.

## AccountState and selected-state cardinality

Identify whether each state is per account, attempt/trace, business scene, page/view instance, or exposure. Do not replace user-scoped first-time policy with a page-session boolean, or extend one query generation guard to unrelated callbacks/state. Keep page exposure deduplication separate from user/account policy and keep account switch/logout semantics with the authoritative owner.

Close each applicable state transition into a ledger action and validation. Unknown server combinations remain explicit external-contract/runtime unknowns; static source cannot prove production configuration values or rollout combinations.
