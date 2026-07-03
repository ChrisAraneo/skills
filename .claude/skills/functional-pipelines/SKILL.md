---
name: functional-pipelines
description: >-
  Refactor imperative TypeScript into functional pipelines — and write new code
  the same way. Use whenever you are asked to "refactor to a pipeline", "remove
  the control flow", "make this functional", "use a chain", "replace the
  if/else", "replace the ternaries", "wrap this in tryCatch", or when you touch a
  function/method body that contains if/else, a ternary, switch, for/while,
  try/catch, throw, or reassigned locals. The single rule: every function and
  method body is ONE expression — a chain/pipeline that composes small named
  steps — with no statement-level control flow. Branch all if/else, ternaries,
  and switches — regardless of arm count — with ts-pattern match,
  compose with lodash-es chain().thru().value() and flow, thread absence as
  `X | undefined`, and capture anything that can throw with ramda tryCatch
  instead of try/catch. Primarily a refactoring skill; the target is existing
  code, but new code follows the same shape.
---

# Functional pipelines

The whole discipline is one rule:

> **A function or method body is a single expression — one pipeline that
> composes small named steps. There is no statement-level control flow in the
> body.**

No `if`/`else`, no ternary `?:`, no `switch`, no `for`/`while`, no `try`/`catch`,
no `throw`, no `let` you reassign, no stack of intermediate mutable locals. Those
are the symptoms this skill exists to remove. A body should read as one
`chain(...)` that flows a value from input to output.

This is **mainly a refactoring skill**. The usual starting point is an existing
imperative body; the job is to turn it into a pipeline without changing what it
does. New code is written in the same shape from the start.

The five tools, and what each replaces:

| Tool | Replaces | Use it for |
| --- | --- | --- |
| **ts-pattern** `match().with().otherwise()` | `if`/`else`, ternary `?:`, `switch`, `instanceof`/`typeof` ladders | every branch — two arms or more |
| **lodash-es** `chain().thru().value()` | intermediate locals, nested calls, hand-rolled loops/guards | the backbone pipeline; data-shaping helpers |
| **lodash-es** `flow` | glue between steps; naming an intermediate argument | composing existing functions point-free into one reusable step |
| **ramda** `tryCatch` | `try`/`catch`, `throw` | turning a throwing operation into a value with a fallback |

---

## Banned in a body — and its replacement

When you see the construct on the left inside a function/method body, replace it
with the construct on the right. This table is the checklist for a refactor.

| Imperative construct | Pipeline replacement |
| --- | --- |
| `if (x) … else …` (two outcomes) | `match(x).with(…).otherwise(…)` |
| `cond ? a : b` (ternary) | `match(x).with(…).otherwise(…)` |
| `if / else if / else`, `switch` (more than two outcomes) | `match(x).with(…).otherwise(…)` / `.exhaustive()` |
| `for` / `while` / `.forEach` accumulating | `map` / `filter` / `reduce` / `chain().thru()` |
| `try { … } catch (e) { … }` | `tryCatch(() => …, onError)` |
| `throw new Error(…)` | return a fallback value from the `tryCatch` catcher |
| `let acc = …; acc = …` | thread the value through `.thru()` / `flow` steps |
| a chain of `const a = …; const b = f(a);` | inline into `chain(a).thru(f).thru(g).value()` |
| manual `if (x == null) return` guards | thread `X \| undefined`; short-circuit with `?.` / lodash `get` |

---

## Tool 1 — ts-pattern `match` for all branches

Every branch — two arms or many, a plain `if`/`else`, a ternary `?:`, a `switch`,
or an `instanceof`/`typeof` ladder — is a `ts-pattern` `match`. There is no
threshold; `match` is the single branching tool. End with `.otherwise(...)` for
an open set or `.exhaustive()` when the cases are total. Use `P` for wildcard,
array, and refinement patterns.

Imperative — a two-arm `if`/`else`:

```ts
function toAccessLabel(user: User): string {
  if (user.isActive) {
    return 'Active';
  } else {
    return 'Suspended';
  }
}
```

Pipeline — one `match`:

```ts
import { match } from 'ts-pattern';

export const toAccessLabel = (user: User): string =>
  match(user)
    .with({ isActive: true }, () => 'Active')
    .otherwise(() => 'Suspended');
```

A ternary is the **same** replacement — `?:` never survives a refactor:

```ts
// Instead of: user.isActive ? 'Active' : 'Suspended'
match(user)
  .with({ isActive: true }, () => 'Active')
  .otherwise(() => 'Suspended');
```

As a chain step:

```ts
import { chain } from 'lodash-es';
import { match } from 'ts-pattern';

chain(user)
  .thru((u) =>
    match(u)
      .with({ isActive: true }, toActiveView)
      .otherwise(toSuspendedView),
  )
  .value();
```

Multi-arm branches and type narrowing follow the same pattern — just add more `.with()` calls:

```ts
import { match, P } from 'ts-pattern';

export const toStatusLabel = (state: RequestState): string =>
  match(state)
    .with({ kind: 'loading' }, () => 'Loading…')
    .with({ kind: 'error', code: P.number }, ({ code }) => `Failed (${code})`)
    .with({ kind: 'ready', items: P.array() }, ({ items }) => `${items.length} items`)
    .exhaustive();
```

This is also how you replace `instanceof`/`typeof` ladders.

---

## Tool 2 — lodash-es `chain().thru().value()` is the backbone

The default shape of a body is a lodash chain of small `.thru()` steps, each a
named function that takes the previous step's output. The top-level function does
almost no logic itself — it only names and orders the steps.

```ts
import { chain } from 'lodash-es';

import { getRecordField } from './transforms/get-record-field';
import { findActiveEntry } from './finds/find-active-entry';
import { toNormalized } from './transforms/to-normalized';

export const getActiveUsers = (
  input: RawPayload | undefined,
): NormalizedUser[] | undefined =>
  chain(input)
    .thru(getRecordField)
    .thru(findActiveEntry)
    .thru(toNormalized)
    .value();
```

That is the target shape for *every* refactor: read the input at the top, flow
it down through named steps, `.value()` out the result.

- Prefer lodash-es helpers over hand-written loops and guards: `chain`, `get`,
  `map`, `filter`, `compact`, `groupBy`, `sortBy`, `isUndefined`, `isEqual`,
  `keyBy`, `uniqBy`, `noop`.
- When a step needs to carry extra state forward, `.thru()` into an object
  literal and keep threading that object — never introduce a mutable `let`.
- Extract each meaningful step into its own named function so the chain reads as
  a sentence. Reuse existing steps before writing new ones.

---

## Tool 3 — lodash-es `flow` for point-free composition

`chain().thru()` shapes one concrete value you have in hand. When you instead
want to build a *reusable step* out of smaller functions — without naming an
intermediate argument — compose them point-free with lodash-es `flow`
(left-to-right).

```ts
import { flow } from 'lodash-es';

// flow: build a reusable step out of smaller ones, point-free.
export const normalizeName = flow(trim, toLowerCase, capitalize);
```

Rule of thumb: **`chain` when you have a value and want to flow it through steps;
`flow` when you want to name a new function that *is* the composition of existing
ones.** They coexist — a `.thru()` step can be a `flow(...)`, and a `flow` step
can be a `chain(...).value()`.

---

## Tool 4 — capture failure with ramda `tryCatch`, never `try`/`catch`

Anything that can throw is wrapped so the failure becomes a *value* — a fallback
the pipeline continues with. **`try`/`catch` and `throw` never appear in a
body.** Use ramda's `tryCatch`.

### The problem this solves

Incorrect — imperative `try`/`catch` with an `instanceof`/`typeof` ladder:

```ts
try {
  someOperation();
} catch (error) {
  if (error instanceof Error) {
    showToast(error.message);
  } else if (typeof error === 'string') {
    showToast(error);
  } else {
    console.log('Error', error);
    showToast('Unknown error occurred');
  }
}
```

### The refactor

Two named pieces — normalize the unknown error with `match`, then wrap the
operation in `tryCatch`.
`tryCatch(tryer, catcher)` returns a function that runs `tryer`; if it throws,
`catcher` receives the error and returns the fallback. There is no second channel
to fold — the catcher already produces the value the pipeline continues with.

```ts
import { tryCatch } from 'ramda';
import { match, P } from 'ts-pattern';

const toErrorMessage = (error: unknown): string =>
  match(error)
    .with(P.instanceOf(Error), (e) => e.message)
    .with(P.string, (s) => s)
    .otherwise(() => 'Unknown error occurred');

const runSafely = tryCatch(
  () => someOperation(),
  (error: unknown) => showToast(toErrorMessage(error)),
);

runSafely();
```

`tryCatch` swallows the `throw` and hands the error to `catcher` — no `try`,
no `catch`, no `if` ladder, one expression. When `tryer` returns a value, give
the catcher a fallback of the same type so the result is usable downstream:

```ts
const parseOrDefault = tryCatch(
  (raw: string) => JSON.parse(raw) as Config,
  () => DEFAULT_CONFIG,
);
```

### Async — fold the rejection on the promise

`tryCatch` is synchronous; it cannot catch a rejected promise. Keep the throw
out of an async body by folding both outcomes with the promise's own two-arm
`then` (success handler, failure handler):

```ts
export const loadUser = (id: string): Promise<User | undefined> =>
  fetchUser(id).then(normalizeUser, (error) => {
    showToast(toErrorMessage(error));
    return undefined;
  });
```

`then(onFulfilled, onRejected)` collapses success and failure without a `try`.
Do the side effect (toast, log) only in the failure arm, at the edge.

### Absence — thread `X | undefined`

Model "might be missing" by threading `X | undefined` through the chain and
letting later steps short-circuit with `?.` (or lodash `get`), never scattered
`if (x == null)` checks.

```ts
import { chain } from 'lodash-es';

export const getPrimaryEmail = (user: User | undefined): string | undefined =>
  chain(user)
    .thru((u) => u?.emails)
    .thru((emails) => emails?.[0])
    .value();
```

---

## Putting it together — one body, one pipeline

A refactored body composes these tools into a single expression: a `chain`
backbone, `match` for the branches, ramda `tryCatch` for failure,
threaded `| undefined` for absence.

```ts
import { chain } from 'lodash-es';
import { tryCatch } from 'ramda';
import { match, P } from 'ts-pattern';

const parseJson = tryCatch(
  (value: string) => JSON.parse(value) as Config,
  () => DEFAULT_CONFIG,
);

export const parseConfig = (raw: string | undefined): Config =>
  chain(raw ?? '{}')
    .thru(parseJson)
    .thru(withDefaults)
    .thru((config) =>
      match(config)
        .with({ mode: 'strict' }, applyStrictRules)
        .with({ mode: P.string }, applyLooseRules)
        .otherwise(() => DEFAULT_CONFIG),
    )
    .value();
```

No `let`, no `if`, no `?:`, no `try` — the value enters at `raw` and flows out as
`Config`.

---

## Small conventions

Three micro-rules that apply everywhere in the codebase, inside a pipeline or
not:

- **Named ramda imports only — never `R.tryCatch`.** Never reference ramda through
  the `R` namespace. Import `tryCatch` by name and call it bare — no
  `import * as R`, no `R.tryCatch`.

  ```ts
  // Instead of: import * as R from 'ramda';  … R.tryCatch(tryer, catcher)
  import { tryCatch } from 'ramda';

  const runSafely = tryCatch(tryer, catcher);
  ```

- **`() => undefined` → lodash `noop`.** A no-op thunk is always spelled with
  lodash-es `noop`, never a hand-written `() => undefined`. This covers empty
  callbacks, default handlers, and match/promise arms that intentionally do
  nothing.

  ```ts
  import { noop } from 'lodash-es';

  // Instead of: onDone={() => undefined}
  onDone={noop}
  ```

- **`P.nullish` → destructured `nullish`.** When you match on `nullish`,
  destructure it off `P` once at the top of the file and use the bare name in the
  pattern — never `P.nullish` inline.

  ```ts
  import { match, P } from 'ts-pattern';

  const { nullish } = P;

  export const toLabel = (value: string | null | undefined): string =>
    match(value)
      .with(nullish, () => 'None')
      .otherwise((v) => v);
  ```

---

## Refactoring workflow

Given an imperative function or method body:

1. **Name the steps.** Read the body top to bottom and identify each distinct
   transformation. Extract each into a small named function (a `const` arrow, or
   — in an Angular class — a `private` method).
2. **Replace branches.** Turn every `if`/`else`, ternary `?:`, `switch`, and
   `instanceof`/`typeof` ladder — regardless of arm count — into a `ts-pattern`
   `match`.
3. **Wrap throwers.** Turn every `try`/`catch` into ramda `tryCatch(tryer,
   catcher)`, where the catcher returns a fallback value; turn every `throw`
   into that fallback. For async, fold the rejection with `promise.then(onOk,
   onErr)`. Do the side effect only at the outermost edge.
4. **Thread absence.** Replace `null`/`undefined` guards by threading `X |
   undefined` and short-circuiting later steps with `?.` / lodash `get`.
5. **Kill the locals.** Collapse the chain of `const a = …; const b = f(a); …`
   and any reassigned `let` into one `chain(...).thru(...).value()` or a
   `flow(...)`.
6. **Annotate the return type** explicitly, including `| undefined` variants.
7. **Verify behavior is unchanged** — run the existing tests (or add them) before
   and after; a pipeline refactor must be behavior-preserving.

---

## Anti-patterns to remove on sight

- An `if`/`else`, ternary `?:`, or `switch` in a body not replaced with a
  `ts-pattern` `match`.
- `try`/`catch`/`throw` anywhere in a body — wrap in ramda `tryCatch`.
- `import * as R from 'ramda'` or an explicit `R.tryCatch` call — import
  `tryCatch` by name and call it bare.
- `instanceof`/`typeof` ladders — collapse into `match(...).with(P.instanceOf(...), …)`.
- `for`/`while`/`forEach` that accumulates — use `map`/`filter`/`reduce` or a
  lodash chain.
- A reassigned `let`, or a staircase of intermediate `const`s feeding the next —
  thread the value through one pipeline.
- Scattered `x == null` / `x === undefined` guards — thread `X | undefined` and
  short-circuit with `?.`.
- A side effect (toast, log, render) buried mid-pipeline instead of at the
  outermost handler — keep the chain pure and do effects only at the edge.
- A top-level function doing real logic itself instead of only composing named
  steps.
- A hand-written `() => undefined` no-op thunk — use lodash `noop`.
- `P.nullish` used inline — destructure `const { nullish } = P;` and match on the
  bare `nullish`.
