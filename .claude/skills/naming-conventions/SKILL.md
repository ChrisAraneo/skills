---
name: naming-conventions
description: Naming conventions for functions, variables, and modules. Use when creating or naming any function, variable, or file in new code, and when refactoring or renaming legacy code so it converges on these conventions (verb patterns get/from/to/filter/compute/create/with/is/can; full descriptive names, never abbreviations).
---

# Naming conventions

These conventions apply both to greenfield code (name things correctly at creation time) and to legacy code (use them as the rename target whenever you touch existing code).

## Variables and parameters

Always use full descriptive names. Never single-letter names, never abbreviations.

- Bad: `fa`, `ma`, `arr`, `idx`, `res`, `cfg`, `fn`, `e`
- Good: `optionValue`, `players`, `index`, `result`, `config`, `mapper`, `error`
- Collections are plural nouns: `players`, `battles` — not `playerList` or `playerArr`.
- Booleans follow guard naming: `isGameOver`, `canDispatch`.

## Function naming algorithm

Classify every function top-down — the first matching category wins — then apply that category's pattern:

1. Extracts a value from a complex object → **Extractor**
2. Maps one piece of data into another → **Mapping**
3. Filters data → **Filtering**
4. Makes a complex calculation and returns a simple result → **Computing**
5. Creates or initializes objects → **Constructor**
6. Adds to an object (e.g. new properties) → **Enhancer**
7. Returns a boolean → **Guard**
8. Otherwise → **Other**: name it `verb` + rest

| Category | Pattern | Meaning | Examples |
| --- | --- | --- | --- |
| Extractor | `get` + Thing | pull a value out of a complex object | `getLeft`, `getRight`, `getOrElse` |
| Mapping (into) | `from` + Type | conversion **into** this type from another | `fromEither`, `fromNullable`, `fromPredicate` |
| Mapping (out of) | `to` + Type | conversion **out of** this type | `toNullable`, `toUndefined`, `toArray` |
| Filtering | `filter` + Condition | keep the data matching a condition | `filter`, `filterNonEmpty` |
| Computing | `compute` + Thing | complex calculation, simple result | `computeBattleResult`, `computeTotalAlivePlayers` |
| Constructor | `create` + Thing | create or initialize a new object | `createGameState`, `createPlanet` |
| Enhancer | `with` + Thing | clone an object with added properties | `withTotal`, `withGameOver` |
| Guard (state) | `is` + Condition | boolean: is something the case | `isGameOver` |
| Guard (ability) | `can` + Condition | boolean: may an operation run | `canDispatch` |
| Other | verb + rest | any function not covered above | `dispatchAction`, `renderBoard` |

Do not invent synonyms for these verbs (`fetch`/`extract` for `get`, `make`/`build` for `create`, `calc` for `compute`, etc.) — the vocabulary is closed.

## Modules and files

- One module per file, **PascalCase singular noun**: `Array.ts`, `Option.ts`, `HashMap.ts`, `MutableHashSet.ts`.
- Private implementations live in `*/internal/` with **camelCase** filenames (`internal/hashMap.ts`); public modules re-export them (`export const succeed = internal.succeed`).

## Applying to new code

- Run every new function name through the algorithm above before writing it.
- Name variables at full length from the start; never introduce an abbreviation "temporarily".
- If a function fits two categories, it is probably doing two jobs — split it rather than picking a compromise name.

## Applying to legacy code

- When touching a function, classify it with the algorithm; if its current name doesn't match its category pattern, rename it (use IDE rename so all references update).
- Common legacy → convention renames:
  - `extract*`, `pluck*`, `fetch*` (from an object) → `get*`
  - `parse*`, `convert*`, `decode*` (into this type) → `from*`
  - `serialize*`, `encode*` (out of this type) → `to*`
  - `calc*`, `calculate*` → `compute*`
  - `make*`, `new*`, `build*`, `init*` → `create*`
  - `add*`, `set*` (when it clones with extra properties) → `with*`
  - `check*`, `has*`, `validate*` (returning boolean) → `is*` / `can*`
- Expand every abbreviation you encounter (`cfg` → `config`, `idx` → `index`, `res` → `result`), including in code you are only passing through.
- Keep renames in separate commits from behavior changes so reviews stay readable.
- Never rename an exported/public API in place if external consumers exist: add the new name, keep the old one as a deprecated alias (`/** @deprecated Use newName */ export const oldName = newName`), and remove it in the next major version.
- Converge module-by-module as files are touched — no drive-by mass renames across the whole codebase.
