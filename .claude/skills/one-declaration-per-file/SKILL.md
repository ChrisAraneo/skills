---
name: one-declaration-per-file
description: File-organization rules for TypeScript/JavaScript. Use when writing new code or refactoring — every function, interface, type, and class must live in its own file; only const values (numbers, strings, config objects) may be grouped. Triggers on "split file", "one per file", "extract function/interface/class to its own file", "organize modules", "file structure".
---

# One Declaration Per File

## Core Rule

Each of these gets **its own file**, named after the declaration it exports.
**All filenames are kebab-case** regardless of the declaration's own casing:

| Declaration        | One per file? | Declaration name → file        |
| ------------------ | ------------- | ------------------------------ |
| Function           | Yes           | `computeScore` → `compute-score.ts` |
| Interface          | Yes           | `GameState` → `game-state.ts`  |
| Type alias         | Yes           | `InputState` → `input-state.ts` |
| Class              | Yes           | `LevelBuilder` → `level-builder.ts` |
| Enum               | Yes           | `TileKind` → `tile-kind.ts`    |
| Const values       | **No** — group freely | `constants.ts`, `config.ts` |

**Const values** (numbers, strings, booleans, config objects, lookup tables) are exempt:
multiple `const` declarations may share a file (e.g. `constants.ts`, `config.ts`).
A const holding an **arrow function** is a function, not a value — it follows the
function rule and goes in its own file.

## Filenames

- The filename is the export name **converted to kebab-case**:
  `createPlayer` → `create-player.ts`, `interface Player` → `player.ts`,
  `GameState` → `game-state.ts`.
- Acronyms lowercase together: `parseHTML` → `parse-html.ts`, `HttpClient` →
  `http-client.ts`.
- One exported declaration per file → **one default-shaped named export per file**.
  Do not mix a function and an interface in the same file.
- Small private helpers used only by the main declaration may stay in the same file
  **if they are not exported**. The moment a helper is exported or reused elsewhere,
  it gets its own file.

## Directory Layout

Group a declaration's file next to a barrel (`index.ts`) that re-exports it:

```
lib/
  reducer/
    reduce.ts            // export function reduce(...)
    tick.ts              // export function tick(...)          (if exported)
    is-intersecting.ts   // export function isIntersecting(...)
    index.ts             // export * from './reduce'; ...
  state/
    game-state.ts        // export interface GameState
    input-state.ts       // export interface InputState
    player.ts            // export interface Player
    constants.ts         // export const PLAYER_WIDTH = ...; PLAYER_HEIGHT = ...
    index.ts
```

- Consumers import from the barrel (`import { reduce } from './reducer'`),
  not from individual files.
- Keep one barrel per directory; the barrel contains only re-exports.

## Refactoring an Existing File

When you split a file that contains multiple declarations:

1. Move **each** function / interface / type / class into its own file named after it.
2. Collect the loose `const` values into a single `constants.ts` (or `config.ts`).
3. Create or update the directory's `index.ts` barrel to re-export everything the
   old file exported — so **import sites elsewhere keep working unchanged**.
4. Fix intra-directory imports to point at the new files (or the barrel).
5. Verify: no file declares more than one function/interface/type/class/enum.

Preserve public API: the set of names importable from the module must not change.

## Writing New Code

Create the file per declaration from the start — don't accumulate several
declarations in one file "for now." When you write a new function `computeScore`,
its file is `compute-score.ts`; a new interface `GameState` is `game-state.ts`;
add its line to the barrel.

## What NOT To Split

- Const values, config objects, and constant lookup tables — group these.
- Non-exported local helpers tightly bound to a single declaration.
- Framework files whose format is fixed by convention (e.g. a component's
  co-located `*.spec.ts`, `*.stories.ts`) — keep tests beside their subject.
