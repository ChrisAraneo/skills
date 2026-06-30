---
name: apply-code-style
description: >-
  Apply the house code style when writing new TypeScript or refactoring existing
  files in any repository. Use whenever you add or extract a function, or are
  asked to "apply the style", "match the conventions", "refactor to the house
  style", or clean up a file. Captures the strict, functional, one-function-per-
  file pipeline architecture (lodash-es chain + ts-pattern match), naming,
  imports, types, formatting, and test conventions.
---

# House code style — strict functional TypeScript

This is a **strict ESM, functional-pipeline TypeScript** style. It applies to any
repository that opts into it. Every file is small, pure, and single-purpose.
When writing new code or refactoring, reproduce the patterns below exactly —
consistency across files is the whole point.

The examples are illustrative, not tied to one project. Adapt the domain types,
but keep the structure, naming, and idioms identical.

## Core philosophy

1. **One named export per file.** Each file exports exactly one `const` arrow
   function. The only exceptions are barrel files (e.g. `index.ts`) that
   re-export, and a project's required entry/config files.
2. **Functions are pure transforms.** They take a value (often `X | undefined`),
   return a value (often `Y | undefined`), and short-circuit gracefully on
   `undefined`. Keep side effects (I/O, logging, framework callbacks) isolated in
   a small number of clearly-named files at the edge of the pipeline.
3. **Compose with pipelines, not control flow.** Wire small functions together
   with lodash-es `chain(...).thru(...).value()`. Branch with `ts-pattern`
   `match(...).with(...).otherwise(...)` — not `if`/`switch`.
4. **Files are kebab-case; the exported function is camelCase.**
   `get-active-users.ts` → `export const getActiveUsers = ...`.

## Directory roles

Group files by the *role* their function plays, not by feature. Place each helper
in the directory that matches what it does. Common roles (use the subset that
fits the project, add others by the same logic):

| Directory      | Responsibility                                              |
| -------------- | ----------------------------------------------------------- |
| `filters/`     | Narrow/guard a value, return it or `undefined` (`filterX`)  |
| `extracts/`    | Pull a value out of a structure (`getX` / `getXArray`)      |
| `extracts/finds/` | `Array.find` a member by key (`findXProperty`)           |
| `transforms/`  | Pure shape transforms (`toX`, `getX`), incl. curried DI     |
| `checks/`      | Decide a condition, return a result or `undefined` (`checkIfX`) |
| `effects/`     | The only side-effecting files (I/O, reporting) (`reportX`/`writeX`) |

The principle is fixed; the exact directory names follow the project. If a repo
already has a layout, match it.

## Pipelines: `chain().thru().value()`

Prefer a lodash-es chain of small `.thru()` steps over nested calls or
intermediate variables. Each step is a named function that accepts the previous
step's output:

```ts
import { chain } from 'lodash-es';

import { getRecordField } from './transforms/get-record-field.js';
import { findActiveEntry } from './finds/find-active-entry.js';
import { toNormalized } from './transforms/to-normalized.js';

export const getActiveUsers = (
  input: RawPayload | undefined,
): NormalizedUser[] | undefined =>
  chain(input)
    .thru(getRecordField)
    .thru(findActiveEntry)
    .thru(toNormalized)
    .value();
```

A top-level function should do almost no logic itself — it only composes named
helpers. When a step needs to accumulate state, `.thru()` into an object literal
and keep threading it.

## Branching: `ts-pattern` over `if`/`switch`

Narrow types and branch with `match`. Always end with `.otherwise(() =>
undefined)` (or a total fallback). Use `P` for array/wildcard patterns:

```ts
import { match, P } from 'ts-pattern';
import { get } from 'lodash-es';

export const getFirstObjectArg = (
  call: CallNode | undefined,
): ObjectNode | undefined =>
  match(call?.expression)
    .with(
      { type: 'CallExpression', arguments: [{ type: 'Object' }, ...P.array()] },
      (expression) => get(expression, 'arguments[0]') as ObjectNode,
    )
    .otherwise(() => undefined);
```

A short ternary is acceptable for a single, flat predicate; reach for `match` as
soon as you narrow types or have more than one branch.

## Prefer lodash-es helpers

Use lodash-es instead of hand-rolled loops/guards. Common idioms: `chain`, `get`,
`compact`, `isUndefined`, `isEqual`, `sortBy`, `groupBy`, `map`, `filter`.

```ts
import { compact, isUndefined } from 'lodash-es';

export const getNonNullItems = (
  items: (Item | null)[] | undefined,
): Item[] | undefined =>
  isUndefined(items) ? undefined : compact(items);
```

Extract reusable predicates/sorters into their own named helpers and reuse them —
do not reinvent a sort or filter inline. Case-insensitive alphabetical sort is
`sortBy(texts, (text) => text.toLocaleLowerCase())`.

## Currying for dependency injection

When a value (a context, config, client) must travel through a pipeline, inject
it with a curried function rather than a closure or class:

```ts
export const withConfig =
  (config: Config) =>
  (value: Payload | undefined) => ({ config, value });
```

## Types

- **Always annotate the return type** of an exported function, including the
  `| undefined` short-circuit variants.
- Model "might be absent" explicitly as `X | undefined` and thread it through;
  let later steps short-circuit. Avoid throwing.
- Name local shapes with a `type` alias (PascalCase) near the function that uses
  them.
- Honor strict `tsconfig` settings — assume `noUncheckedIndexedAccess` (index
  access is `T | undefined`; use `!` only where an invariant guarantees
  presence), `noImplicitReturns`, `noUnusedLocals`, `noUnusedParameters`,
  `strict`.

## Naming conventions

- **Files:** kebab-case, matching the export (`get-sorted-texts.ts`).
- **Functions / variables:** strict camelCase. Helper names read as verbs by
  role: `filterX`, `getX` / `getXArray`, `findXProperty`, `toX`, `checkIfX`,
  `reportX` / `writeX`, `withX`.
- **Types / interfaces:** PascalCase.
- **Booleans:** prefix with `is`/`has`/`are`/`can`/`should`/`did`/`will`/`with`.

## Formatting (Prettier)

Single quotes, semicolons, `printWidth` 80, 2-space indent, `trailingComma:
all`, `arrowParens: always`, `bracketSameLine: true`, `bracketSpacing: true`.
Keep object keys alphabetized. If the repo has a `.prettierrc`, that file wins —
match it.

## Tests

Colocate a `<name>.spec.ts` (or the project's convention) next to each unit.
Cover the happy path plus the boundary cases the function short-circuits on:
empty input, single element, `undefined`, and unrelated/no-op input. Mirror the
existing test files in the repo for runner and assertion style.

## Refactoring workflow

When refactoring an existing file or adding a feature:

1. **Decompose** any multi-step function into named single-purpose helpers, each
   in the directory matching its role; re-express the body as a
   `chain().thru()` pipeline.
2. **Replace** `if`/`switch`/imperative loops with `ts-pattern` `match` and
   lodash-es helpers.
3. **Thread `undefined`** instead of throwing; add the explicit return type.
4. **Fix imports**: regroup (external / relative), add `.js` extensions, use
   inline `type`.
5. **Reuse** existing helpers before writing new ones.
6. **Add/extend** the colocated test file.

## Anti-patterns to remove on sight

- Default exports outside barrels; multiple exports per file.
- `if`/`else`/`switch` chains where a `ts-pattern` `match` fits.
- Hand-written `for`/`while` loops or manual null guards where lodash-es
  (`compact`, `isUndefined`, `sortBy`, `chain`) reads cleaner.
- Missing return-type annotations; throwing instead of returning `undefined`.
- Relative imports without `.js`; type-only imports without the `type` modifier.
- Business logic buried inside an edge/side-effecting function instead of a named
  pure helper.
