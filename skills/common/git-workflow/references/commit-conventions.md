# Commit Workflow and Conventions

## Inspect and Scope the Change

1. Run `git status --short --branch` and `git branch --show-current`.
2. Inspect staged and unstaged changes with `git diff --cached`, `git diff`, and focused file reads as needed.
3. Determine which files belong to the user's requested commit. If unrelated changes are present and the intended set cannot be inferred safely, ask the user to identify the scope.
4. Stage only intended files with explicit paths. Do not use `git add -A` when the worktree contains unrelated changes.
5. Inspect `git diff --cached --stat` and `git diff --cached`. Stop if the staged diff is empty or includes unrelated changes.

## Select the Repository Convention

Run `git remote get-url origin`.

- When the origin URL is exactly `https://git.duowan.com/voicetech/ios/drama-ios.git`, apply the drama-ios convention below.
- For another repository, read its `AGENTS.md` and repository commit documentation and follow those rules instead. Do not impose the drama-ios message format outside drama-ios.
- Treat Git-generated merge commits as part of the maintenance merge workflow; do not rewrite their messages into the normal drama-ios code-commit format.

## Build a drama-ios Commit Message

Use exactly this format:

```text
type: #requirement_id 中文说明
```

Allow only these types:

- `feat`: add or extend functionality.
- `fix`: correct a defect.
- `docs`: change documentation only.
- `style`: change formatting without changing behavior.
- `refactor`: restructure code without changing behavior.
- `perf`: improve performance.
- `test`: add or change tests only.
- `chore`: change tooling, configuration, generated maintenance data, or other non-product work.
- `revert`: revert an earlier commit.

Infer the type from the staged diff and the user's intent. If multiple types are reasonably valid, ask the user to choose before committing. Write a concise Chinese summary that accurately describes the staged change; retain necessary technical terms when useful.

## Resolve the Requirement ID

Resolve the ID conservatively in this order:

1. Inspect the current branch name. Extract distinct digit sequences containing at least five digits, using the conceptual boundary pattern `(?<![0-9])[0-9]{5,}(?![0-9])` so version components such as `2.25.0` are not candidates.
2. If the branch contains exactly one candidate, use it.
3. If the branch contains multiple candidates, ask the user to provide the intended requirement ID. Do not inspect history to break the tie.
4. If the branch contains no candidate, run `git log --no-merges -20 --pretty=format:%s`. Extract distinct IDs that appear as `#[0-9]{5,}`.
5. If history contains exactly one distinct candidate, use it.
6. If history contains no candidate or multiple candidates, ask the user to provide the requirement ID.

Do not run `git commit` until one unambiguous requirement ID is available. Do not guess from version numbers, file contents, unrelated branches, or issue-like numbers without the required evidence.

Before committing, verify that the complete subject matches:

```text
^(feat|fix|docs|style|refactor|perf|test|chore|revert): #[0-9]{5,} .+
```

## Validate and Commit

1. Read repository validation instructions and run the permitted checks relevant to the staged files.
2. In drama-ios, do not proactively run builds, compilers, or SDK discovery commands. Use checks such as `git diff --check` and targeted `plutil -lint` only when applicable.
3. Recheck `git diff --cached` after validation.
4. Run `git commit -m "<subject>"` without `--no-verify`. Do not create an empty commit. Do not use `--amend` unless the user explicitly requested it.
5. Verify the result with `git show --stat --oneline --decorate -1` and `git status --short --branch`.
6. Stop after the local commit when the user only asks to commit code. Push only when the user explicitly asks for a push.

Report the commit SHA and subject, files included, validation result, final branch, and whether the commit remains local or was pushed.
