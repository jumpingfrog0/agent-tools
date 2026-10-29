---
name: discuss-design-decisions
description: Use stepwise discussion for high-impact design decisions before implementation. Trigger only when the user explicitly asks to decide one by one, or when a large proposal has coupled, user-owned choices with no safe default and autonomous resolution risks major behavior, compatibility, ownership, API, lifecycle, or state consequences. Otherwise decide technical details autonomously and report the result. Do not trigger for ordinary plans, reviews, refactors, naming, local or reversible choices, one ambiguity, or requests for a direct or autonomous answer. Ask one focused question for one required clarification. Do not replace stricter formal workflows.
---

# Discuss Design Decisions

Guide a focused design conversation that produces explicit decisions without overwhelming the user.

## Decide whether to enter

Enter only when one of these conditions is true:

1. The user explicitly requests step-by-step or one-by-one decision discussion.
2. All of the following are true:
   - Multiple unresolved decisions materially depend on one another.
   - The choices belong to the user because they set product behavior, compatibility boundaries, ownership, public API semantics, lifecycle guarantees, state retention, or similarly consequential intent.
   - No safe default or clearly superior option can be established from current evidence.
   - Autonomous resolution could create substantial behavioral risk or costly rework.

Treat naming, code organization, private implementation, reversible local abstractions, and choices with a clear best practice as agent-owned. Resolve them autonomously even when the surrounding task is technically complex.

Do not enter this workflow solely because the user asks whether a proposal is overengineered. Evaluate it directly unless the activation gate is independently satisfied.

If only one specific material ambiguity remains, ask one focused confirmation question without activating this workflow.

Treat instructions such as “自主决策”, “直接给结论”, “不需要逐项确认”, “不要进入分步讨论”, or equivalent wording as an explicit opt-out from implicit activation. Make the technical decisions independently and summarize them afterward. This opt-out does not authorize inventing missing product requirements or overriding repository rules that require confirmation for a concrete behavior change.

## Establish the decision map

1. Inspect the available proposal, code, constraints, and prior decisions before recommending changes.
2. Separate facts about the current system from design choices.
3. Split the unresolved design into atomic decision points. Do not turn routine implementation details into user decisions.
4. Order the decisions by dependency so that later discussions can rely on earlier conclusions.
5. Present only the short ordered list first. Do not include the full solution unless the user asks for it.
6. Track each item internally as `pending`, `confirmed`, `deferred`, or `rejected`.
7. Track the workflow phase as `discussing`, `awaiting_implementation_approval`, or `implementing`.

## Discuss one decision at a time

For the current item:

1. State the exact question and its boundary.
2. Give only the context needed to decide it.
3. Compare the viable options and their concrete consequences.
4. Recommend one option and explain why. Do not offload technical judgment to the user.
5. Identify any behavior, compatibility, lifecycle, ownership, or API-semantic change that requires explicit confirmation.
6. Ask for confirmation before moving to the next dependent decision.

Keep each round compact. Do not preview detailed solutions for later items.

## Continue or exit

Apply the entry gate only when deciding whether to start the workflow. Once legitimately entered, continue while at least one mapped user-owned decision remains unresolved. Do not exit merely because the number of remaining decisions decreases.

Exit the workflow when any of these conditions is true:

- The user asks for autonomous decisions, a direct conclusion, or no further confirmations.
- The remaining choices are agent-owned, routine, reversible, or have a clear best option.
- New evidence removes the material uncertainty or dependency that justified stepwise discussion.

On exit, resolve remaining agent-owned choices autonomously and provide the requested conclusion or plan. If a concrete product or compatibility ambiguity still cannot safely be inferred, ask one focused question outside this workflow.

## Process user feedback

- Evaluate objections against current evidence; agree or disagree with reasons instead of conceding automatically.
- Record confirmed wording accurately and treat it as a constraint in later rounds.
- Add newly discovered decisions to the map and place them according to dependencies.
- Reopen a confirmed decision only when new evidence conflicts with it; explain the conflict first.
- Mark an item `deferred` when the user sets it aside, and avoid resolving or implementing it implicitly.
- When the user says to continue, advance to the next pending item without repeating the full history.

## Control implementation

- Do not modify code merely because a design is being discussed.
- Treat an initial request to design and implement as intent for eventual implementation, not as final approval after the decision phase.
- Never treat confirmation of an individual decision, including the last pending decision, as approval to begin implementation.
- After all decisions required for the intended scope are confirmed or explicitly excluded, set the phase to `awaiting_implementation_approval`.
- In that phase, summarize the final implementation scope and any deferred or excluded items, then explicitly ask whether to begin implementation. End the turn and wait for a new user response.
- Accept any unambiguous affirmative response such as “approved,” “start implementation,” or “implement this plan”; do not require a magic word.
- Start implementation only after that new affirmative response, then set the phase to `implementing`.
- Skip the separate final approval only when the user explicitly instructs Codex to implement automatically after the decisions are complete or otherwise says that no final confirmation is needed.
- Treat a new request to implement a clearly delimited confirmed subset as approval for that subset only; preserve deferred behavior unchanged.
- If the user requests changes instead of approving, return to `discussing` and update the decision map.
- Stop and surface any newly discovered choice that would alter visible behavior, state retention, API semantics, compatibility, or another confirmed boundary.
- After implementation, distinguish completed work from remaining deferred decisions.

## Summarize precisely

Summarize only when requested or when the decision phase is complete.

- Include confirmed conclusions and relevant constraints.
- List deferred or unresolved items separately.
- Exclude already implemented or previously summarized material when the user requests only the latest decision.
- Prefer a concise decision ledger over replaying the conversation.

## Avoid these failure modes

- Dumping every issue, recommendation, and code example into the first response.
- Discussing multiple independent decisions in one round.
- Treating a convenience abstraction as necessary without current evidence.
- Asking the user to choose between options without making a recommendation.
- Repeating all confirmed conclusions before every new question.
- Allowing a deferred decision to leak into implementation through an unstated assumption.
- Treating the answer to the final decision as approval of the whole implementation.
- Inferring final implementation approval from the initial request or announcing implementation before receiving a new affirmative response.
- Replacing an applicable project or formal workflow; use this skill only as its discussion protocol.
- Activating for an ordinary plan, review, refactor, naming discussion, or isolated implementation tradeoff.
- Treating the words “讨论”, “方案”, “设计”, or “过度设计” as sufficient activation signals by themselves.
- Continuing the workflow after the user asks for autonomous decisions or a direct conclusion.
- Turning a single repository-required confirmation into a multi-round decision process.
- Using the number of decisions as a proxy for whether the user must decide them.
- Exiting a valid workflow only because fewer decisions remain after confirmation.
