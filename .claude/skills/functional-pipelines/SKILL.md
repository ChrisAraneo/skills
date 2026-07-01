---
name: functional-pipelines
description: >-
  Refactor imperative TypeScript into functional pipelines — and write new code
  the same way. Use whenever you are asked to "refactor to a pipeline", "remove
  the control flow", "make this functional", "use a chain", "wrap this in
  Either", or when you touch a function/method body that contains if/else,
  switch, for/while, try/catch, throw, or reassigned locals. The single rule:
  every function and method body is ONE expression — a chain/pipeline that
  composes small named steps — with no statement-level control flow. Branch with
  ts-pattern match, compose with lodash-es chain().thru().value() and fp-ts
  pipe/flow, thread absence as Option / `X | undefined`, and capture anything
  that can throw as an fp-ts Either instead of try/catch. Primarily a
  refactoring skill; the target is existing code, but new code follows the same
  shape.
---

# Functional pipelines

The whole discipline is one rule:

> **A function or method body is a single expression — one pipeline that
> composes small named steps. There is no statement-level control flow in the
> body.**

No `if`/`else`, no `switch`, no `for`/`while`, no `try`/`catch`, no `throw`, no
`let` you reassign, no stack of intermediate mutable locals. Those are the
symptoms this skill exists to remove. A body should read as one `chain(...)` /
`pipe(...)` that flows a value from input to output.

This is **mainly a refactoring skill**. The usual starting point is an existing
imperative body; the job is to turn it into a pipeline without changing what it
does. New code is written in the same shape from the start.

The four tools, and what each replaces:

| Tool | Replaces | Use it for |
| --- | --- | --- |
| **lodash-es** `chain().thru().value()` | intermediate locals, nested calls, hand-rolled loops/guards | the backbone pipeline; data-shaping helpers |
| **ts-pattern** `match().with().otherwise()` | `if`/`else if`/`switch`, `instanceof`/`typeof` ladders | every branch that narrows a type or has >1 arm |
| **fp-ts** `pipe` / `flow` | glue between steps that aren't a lodash chain (esp. `Either`/`Option`) | composing effectful/absent-aware steps |
| **fp-ts** `Either` / `Option` (`E.tryCatch`, `TE.tryCatch`) | `try`/`catch`, `throw`, `null`/`undefined` checks | representing failure and absence as values |

---

## Banned in a body — and its replacement

When you see the construct on the left inside a function/method body, replace it
with the construct on the right. This table is the checklist for a refactor.

| Imperative construct | Pipeline replacement |
| --- | --- |
| `if (x) … else …` | `match(x).with(…, …).otherwise(…)` |
| `switch (x) { case … }` | `match(x).with(…).with(…).exhaustive()` |
| `for` / `while` / `.forEach` accumulating | `map` / `filter` / `reduce` / `chain().thru()` |
| `try { … } catch (e) { … }` | `E.tryCatch(() => …, toError)` then fold |
| `throw new Error(…)` | return `E.left(error)` (or `O.none`) |
| `let acc = …; acc = …` | thread the value through `.thru()` / `pipe` steps |
| a chain of `const a = …; const b = f(a);` | inline into `chain(a).thru(f).thru(g).value()` |
| manual `if (x == null) return` guards | `O.fromNullable` / thread `X \| undefined` |

A **single flat early-return guard** or a **single flat ternary** is tolerated —
`if (isEmpty(items)) return undefined;` or `cond ? a : b`. The moment there is a
second branch or a type narrowing, it becomes a `match`.

---

## Tool 1 — lodash-es `chain().thru().value()` is the backbone

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
  `keyBy`, `uniqBy`.
- When a step needs to carry extra state forward, `.thru()` into an object
  literal and keep threading that object — never introduce a mutable `let`.
- Extract each meaningful step into its own named function so the chain reads as
  a sentence. Reuse existing steps before writing new ones.

---

## Tool 2 — fp-ts `pipe` / `flow` for composition that isn't a data chain

`chain().thru()` is ideal for shaping one value. Reach for fp-ts `pipe` (apply a
value through functions) and `flow` (compose functions point-free) when the
steps are heterogeneous — especially once `Either`/`Option` enter the pipeline
and each step must be threaded with `E.map` / `E.chain` / `O.map`.

```ts
import { pipe, flow } from 'fp-ts/function';
import * as O from 'fp-ts/Option';

// pipe: run a concrete value through steps.
export const getDisplayName = (input: RawUser | undefined): string =>
  pipe(
    O.fromNullable(input),
    O.map(toFullName),
    O.map(capitalize),
    O.getOrElse(() => 'Anonymous'),
  );

// flow: build a reusable step out of smaller ones, point-free.
export const normalizeName = flow(trim, toLowerCase, capitalize);
```

Rule of thumb: **lodash `chain` for shaping data, fp-ts `pipe`/`flow` for
threading `Either`/`Option` and composing functions.** They coexist — a `.thru()`
step can itself be a `pipe(...)`, and a `pipe` step can be a `chain(...).value()`.

---

## Tool 3 — ts-pattern `match` over `if`/`switch`

Every branch that narrows a type or has more than one arm is a `match`. End with
`.otherwise(...)` for an open set or `.exhaustive()` when the cases are total.
Use `P` for wildcard, array, and refinement patterns.

```ts
import { match, P } from 'ts-pattern';

export const toStatusLabel = (state: RequestState): string =>
  match(state)
    .with({ kind: 'loading' }, () => 'Loading…')
    .with({ kind: 'error', code: P.number }, ({ code }) => `Failed (${code})`)
    .with({ kind: 'ready', items: P.array() }, ({ items }) => `${items.length} items`)
    .exhaustive();
```

This is also how you replace `instanceof`/`typeof` ladders — see the error
example below.

---

## Tool 4 — capture failure as an fp-ts `Either`, never `try`/`catch`

Anything that can throw is wrapped so the failure becomes a *value* on the `Left`
channel, and the pipeline continues functionally. **`try`/`catch` and `throw`
never appear in a body.**

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
operation in `E.tryCatch` and fold both channels:

```ts
import { pipe } from 'fp-ts/function';
import * as E from 'fp-ts/Either';
import { match, P } from 'ts-pattern';

const toErrorMessage = (error: unknown): string =>
  match(error)
    .with(P.instanceOf(Error), (e) => e.message)
    .with(P.string, (s) => s)
    .otherwise(() => 'Unknown error occurred');

pipe(
  E.tryCatch(() => someOperation(), toErrorMessage),
  E.fold(showToast, () => undefined),
);
```

`E.tryCatch(thunk, onThrow)` runs the throwing operation and yields
`Either<string, Result>`: `Left` holds the normalized message, `Right` holds the
success value. `E.fold(onLeft, onRight)` collapses both channels — here, toast on
failure, do nothing on success. No `try`, no `catch`, no `if` ladder, one
pipeline.

### Async — `TaskEither`

For promises, use `TE.tryCatch`; the result is a `Task<Either<…>>` you compose
the same way and run at the edge.

```ts
import { pipe } from 'fp-ts/function';
import * as E from 'fp-ts/Either';
import * as TE from 'fp-ts/TaskEither';

export const loadUser = (id: string): TE.TaskEither<string, User> =>
  pipe(
    TE.tryCatch(() => fetchUser(id), toErrorMessage),
    TE.map(normalizeUser),
  );

// at the edge (an event handler / effect), run the Task and fold:
pipe(await loadUser(id)(), E.fold(showToast, renderUser));
```

Keep the `Either`/`TaskEither` threaded through the whole pipeline; only fold it
into a side effect (toast, render, log) at the very edge — the outermost handler,
effect, or subscription.

### Absence — `Option`

Model "might be missing" as `Option` (or thread `X | undefined` and let later
steps short-circuit), never scattered `if (x == null)` checks.

```ts
import { pipe } from 'fp-ts/function';
import * as O from 'fp-ts/Option';

export const getPrimaryEmail = (user: User | undefined): string | undefined =>
  pipe(
    O.fromNullable(user),
    O.chain((u) => O.fromNullable(u.emails)),
    O.map((emails) => emails[0]),
    O.toUndefined,
  );
```

---

## Putting it together — one body, one pipeline

A refactored body composes all four tools into a single expression: a `chain`
backbone, `match` for the branches, `Either`/`Option` for failure and absence.

```ts
import { chain } from 'lodash-es';
import { pipe } from 'fp-ts/function';
import * as E from 'fp-ts/Either';
import { match, P } from 'ts-pattern';

export const parseConfig = (raw: string | undefined): Config =>
  chain(raw)
    .thru((value) => E.tryCatch(() => JSON.parse(value ?? '{}'), toErrorMessage))
    .thru(E.map(withDefaults))
    .thru(
      E.fold(
        () => DEFAULT_CONFIG,
        (config) =>
          match(config)
            .with({ mode: 'strict' }, applyStrictRules)
            .with({ mode: P.string }, applyLooseRules)
            .otherwise(() => DEFAULT_CONFIG),
      ),
    )
    .value();
```

No `let`, no `if`, no `try` — the value enters at `raw` and flows out as
`Config`.

---

## Refactoring workflow

Given an imperative function or method body:

1. **Name the steps.** Read the body top to bottom and identify each distinct
   transformation. Extract each into a small named function (a `const` arrow, or
   — in an Angular class — a `private` method).
2. **Replace branches.** Turn every `if`/`else`/`switch`/`instanceof`/`typeof`
   into a `ts-pattern` `match`.
3. **Wrap throwers.** Turn every `try`/`catch` into `E.tryCatch` (or
   `TE.tryCatch` for async); turn every `throw` into `E.left` / `O.none`. Push
   the fold to the outermost edge.
4. **Thread absence.** Replace `null`/`undefined` guards with `O.fromNullable`
   or a threaded `X | undefined` that later steps short-circuit on.
5. **Kill the locals.** Collapse the chain of `const a = …; const b = f(a); …`
   and any reassigned `let` into one `chain(...).thru(...).value()` or
   `pipe(...)`.
6. **Annotate the return type** explicitly, including `Either`/`Option`/
   `| undefined` variants.
7. **Verify behavior is unchanged** — run the existing tests (or add them) before
   and after; a pipeline refactor must be behavior-preserving.

---

## Anti-patterns to remove on sight

- `if`/`else if`/`switch` in a body where a `ts-pattern` `match` fits.
- `try`/`catch`/`throw` anywhere in a body — wrap in `Either`/`TaskEither`.
- `instanceof`/`typeof` ladders — collapse into `match(...).with(P.instanceOf(...), …)`.
- `for`/`while`/`forEach` that accumulates — use `map`/`filter`/`reduce` or a
  lodash chain.
- A reassigned `let`, or a staircase of intermediate `const`s feeding the next —
  thread the value through one pipeline.
- Scattered `x == null` / `x === undefined` guards — `O.fromNullable` or a
  threaded `X | undefined`.
- A folded `Either`/`Option` deep inside the pipeline instead of at the edge —
  keep it wrapped until the outermost handler.
- A top-level function doing real logic itself instead of only composing named
  steps.
