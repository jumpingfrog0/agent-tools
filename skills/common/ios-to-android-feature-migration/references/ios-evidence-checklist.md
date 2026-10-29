# iOS Evidence Checklist

Use this checklist for targeted evidence checking after reading the final feature-discovery documents. This is not a full iOS rediscovery pass.

## Repository Setup

- Confirm the iOS repository path, defaulting to `../drama-ios`.
- Read the final feature-discovery documents from `<ios-repo>/.huangdonghong/docs`, not from the Android repository `.huangdonghong/docs`.
- Read applicable iOS repository instructions before inspecting code.
- Search from the feature names, classes, files, APIs, routes, config keys, analytics names, and resources listed in the feature-discovery documents.

## Required Evidence Areas

Check only the migration-critical parts of these areas:

- Entry points: screen, controller, view model, router, coordinator, command, handler, or user action.
- User path: trigger action, navigation, lifecycle, close/back behavior, and re-entry behavior.
- Business rules: eligibility, state transitions, sorting, filtering, thresholds, limits, and priority.
- API/RPC/model: request fields, response fields, enum values, default values, error handling, and nullability.
- Configuration: remote config, experiment, feature flag, server switch, local compile flag, and fallback value.
- Persistence: cache key, user-scoped storage, invalidation, migration, and default state.
- Resources: images, colors, dimensions, animations, and native strings.
- Analytics: event names, parameters, timing, exposure/click distinction, and failure reporting.
- Edge states: loading, empty, error, disabled, offline, permission denied, retry, compatibility, and degraded behavior.

## Conflict Handling

- If code confirms the documents, record the evidence path and symbol.
- If code conflicts with the documents, record both sides and mark whether the conflict blocks Android implementation.
- If evidence is not found, record "未发现" with the search terms or inspected locations.
- Do not silently drop unchecked config, analytics, resources, strings, persistence, or fallback behavior.

## Output Expectations

Feed these results into `Android迁移方案.md`:

- Inspected iOS evidence list.
- Confirmed migration-critical facts.
- Document/code conflicts.
- Missing evidence.
- Blocking questions.
