# Android Analysis Checklist

Use this checklist before writing the Android migration plan.

## Repository Constraints

- Read the Android repository `AGENTS.md`.
- Respect module boundaries and validation limits.
- Do not modify Android code during analysis.
- Prefer existing local patterns over new abstractions.

## Module and Boundary Analysis

Identify the correct Android landing area:

- App shell versus business module versus feature module.
- Existing module with the closest semantic ownership.
- Existing `src/header` protocol interfaces when cross-module access is needed.
- Existing Hilt, Athena `@ServiceRegister`, or `Axis.getService` service patterns.
- Existing routing, Activity, Fragment, Dialog, View, or Compose entry points.

Do not add direct dependencies between business modules when the project pattern requires protocol/service boundaries.

## Implementation Surface

Inspect the Android side for:

- Existing screens, components, adapters, view models, repositories, managers, services, and protocol APIs.
- Existing network service patterns, RPC wrappers, request/response models, and serialization.
- Existing local storage patterns, especially `KvPreference` and `SpData`.
- Existing resource naming and resource ownership.
- Existing efox/configuration string handling.
- Existing analytics/logging helpers and event naming.
- Existing empty, loading, error, disabled, and fallback UI patterns.

## UI Rules

When Android UI is involved, check:

- Existing XML pages use ViewBinding.
- Existing Compose pages continue using Compose.
- Click handling uses `clickWithTrigger`.
- New constraints use `start/end` rather than `left/right`.
- Sizes use existing `dp2px`, `dp2pxInt`, `dimens.xml`, or project utilities.
- Dynamic backgrounds use project DSL such as `context.shape {}` or `context.selector {}`.
- Bold text uses existing typeface mechanisms such as `TypeCompatTextView` and `app:typeFont="PoppinsBold"` when appropriate.

## Plan Inputs

The analysis must produce:

- Chosen module and package.
- Existing Android pattern to follow.
- Exact production/resource/protocol areas expected to change.
- Android behavior gaps versus iOS.
- Validation constraints and manual acceptance scenarios.
