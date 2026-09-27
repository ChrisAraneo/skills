---
name: naming-conventions
description: Naming conventions for functions, variables, and modules. Use when creating or naming any function or variable in new code, and when refactoring or renaming legacy code so it converges on these conventions (verb patterns get/from/to/find/filter/create/with/is/can/has/have/should/handle/draw/compute; full descriptive names, never abbreviations; kebab-case for file names).
---

# Naming conventions

These conventions apply both to greenfield code (name things correctly at creation time) and to legacy code (use them as the rename target whenever you touch existing code).

## Variables and parameters

Always use full descriptive names. Never single-letter names, never abbreviations.

- Bad: `fa`, `ma`, `arr`, `idx`, `res`, `cfg`, `fn`, `e`
- Good: `optionValue`, `players`, `index`, `result`, `config`, `mapper`, `error`
- Collections are plural nouns: `players`, `battles` — not `playerList` or `playerArr`.
- Booleans follow guard naming: `isGameOver`, `canDispatch`, `hasBuilding`, `haveResources`, `shouldSkipTurn`.

## Function naming algorithm

Classify every function top-down — the first matching category wins — then apply that category's pattern:

1. Extracts a value from a complex object → **Extractor**
2. Maps one piece of data into another → **Mapping**
3. Locates a single item in a collection → **Finder**
4. Filters data → **Filtering**
5. Creates or initializes objects → **Constructor**
6. Adds to an object (e.g. new properties) → **Enhancer**
7. Returns a boolean → **Guard** (differentiated by state, ability, possession, or policy)
8. Handles an event or UI/system behavior → **Handler**
9. Renders or draws elements directly onto an HTML5 canvas context → **Drawer**
10. Makes a complex calculation and returns a simple result → **Computing**
11. Otherwise → **Other**: name it `verb` + rest

| Category | Pattern | Meaning | Examples |
| --- | --- | --- | --- |
| Extractor | `get` + Thing | pull a value out of a complex object | `getLeft`, `getRight`, `getOrElse` |
| Mapping (into) | `from` + Type | conversion **into** this type from another | `fromEither`, `fromNullable`, `fromPredicate` |
| Mapping (out of) | `to` + Type | conversion **out of** this type | `toNullable`, `toUndefined`, `toArray` |
| Finder | `find` + Target | return a single item from a collection or `undefined` | `findBoundary`, `findMarker`, `findTile` |
| Filtering | `filter` + Condition | keep the data matching a condition | `filter`, `filterNonEmpty` |
| Constructor | `create` + Thing | create or initialize a new object | `createGameState`, `createPlanet` |
| Enhancer | `with` + Thing | clone an object with added properties | `withTotal`, `withGameOver` |
| Guard (state) | `is` + Condition | boolean: is something the case | `isGameOver`, `isActive` |
| Guard (ability) | `can` + Action | boolean: may an operation run | `canDispatch`, `canAttack` |
| Guard (singular possession)| `has` + Thing | boolean: is a singular thing already defined/created on the object | `hasAction`, `hasBuilding` |
| Guard (plural possession) | `have` + Things | boolean: does the object possess a collection or meet a plural requirement | `haveResources`, `haveRequiredItems` |
| Guard (policy/requirement)| `should` + Action | boolean: is it recommended or required by business logic to perform an action | `shouldRender`, `shouldSkipTurn` |
| Handler | `handle` + Event | handle an event or interactive behavior | `handleKeyDown`, `handleStopEvent`, `handleResumeEvent` |
| Drawer | `draw` + Target | render visual elements onto an HTML5 canvas context | `drawPlayer`, `drawBoard`, `drawHealthBar` |
| Computing | `compute` + Thing | complex calculation, simple result | `computeBattleResult`, `computeTotalAlivePlayers` |
| Other | verb + rest | any function not covered above | `dispatchAction`, `saveState` |

Do not invent synonyms for these verbs (`fetch`/`extract` for `get`, `locate`/`search` for `find`, `make`/`build` for `create`, `paint`/`render` for `draw`, `calc` for `compute`, `needs`/`must` for `should`, `on`/`process` for `handle`, etc.) — the vocabulary is closed.

## Modules and files

Private implementations live in `*/internal/` with **kebab-case** filenames (`internal/hash-map.ts`); public modules re-export them (`export const succeed = internal.succeed`).

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
  - `locate*`, `search*`, `lookup*` (single element search) → `find*`
  - `make*`, `new*`, `build*`, `init*` → `create*`
  - `add*`, `set*` (when it clones with extra properties) → `with*`
  - `check*`, `validate*`, `contains*`, `exists*` (returning boolean) → `is*` / `can*` / `has*` / `have*`
  - `needs*`, `must*`, `requires*` (returning boolean) → `should*`
  - `on*`, `process*`, `listen*` (handling an event) → `handle*`
  - `paint*`, `renderCanvas*` (drawing to canvas context) → `draw*`
  - `calc*`, `calculate*` → `compute*`
- Expand every abbreviation you encounter (`cfg` → `config`, `idx` → `index`, `res` → `result`), including in code you are only passing through.
- Converge module-by-module as files are touched — no drive-by mass renames across the whole codebase.
