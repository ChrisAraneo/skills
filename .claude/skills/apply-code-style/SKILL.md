---
name: apply-code-style
description: >-
  Apply the house code style when writing new TypeScript/Angular or refactoring
  existing files in any repository. Use whenever you add or extract a function,
  touch an Angular component/service/pipe/directive, or are asked to "apply the
  style", "match the conventions", "refactor to the house style", or clean up a
  file. Two parts: (1) strict functional pure-TypeScript pipeline architecture
  (lodash-es chain + ts-pattern match, one function per file); (2) Angular rules
  layered on top — logic used by a single component/service stays as a private
  method (not its own file), display-only formatting becomes a Pipe, logic
  shared by multiple components becomes a service, types/interfaces/constants
  get their own files, method bodies prefer match/chaining over if/else and
  signals over plain mutable state, constructor/ngOnInit/ngOnChanges/
  ngOnDestroy are avoided in favor of field initializers/computed/effect where
  possible, and any never-reassigned field must be readonly.
---

# House code style

This skill has **two parts**:

- **Part 1 — Pure TypeScript.** The strict, functional, one-function-per-file
  pipeline style. It governs every plain `.ts` file that is not an Angular
  building block: helpers, transforms, guards, extracted logic.
- **Part 2 — Angular.** The rules for `.component.ts`, `.service.ts`,
  `.pipe.ts`, `.directive.ts` files. These files stay idiomatic Angular
  (decorated classes, DI, signals). Where a piece of logic lives is decided by
  who uses it — single-use logic stays as a private method, display formatting
  becomes a Pipe, cross-component logic becomes a service, and only logic with
  no natural Angular owner falls back to a Part 1 pure-function file. Method
  bodies that remain on the class follow Part 1's functional idioms.

Decide which part applies by the file: a decorated Angular class → Part 2 (see
its decision tree for where any given piece of logic should actually live).
Anything else → Part 1.

---

# Part 1 — Strict functional TypeScript

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

---

# Part 2 — Angular

Angular building blocks — `@Component`, `@Injectable`, `@Pipe`, `@Directive` —
**stay as idiomatic decorated classes**. You do not turn them into one-function
files, and — unlike Part 1 — you do not reflexively pull every non-trivial
method out into its own file either. Where a piece of logic *lives* is decided
by who uses it, not by how many lines it has. Method bodies that remain on the
class still follow the same functional idioms (match, chaining, signals).

## Where logic lives: a decision tree

Ask **who uses this logic**, in order:

1. **Only one component/service/pipe/directive uses it** → it stays as a
   **private method on that class**. Do not split it into a separate
   `*.function.ts` file just because it's non-trivial or "could" be reused
   someday. Extracting single-use logic adds an indirection nobody needs — wait
   for a second real caller before you generalize.
2. **Its only purpose is formatting/deriving a value for template display**
   (durations, labels, truncation, pluralization, currency, dates, ...) →
   extract it into an **Angular `Pipe`**, even if only one template uses it
   today. Pipes are the idiomatic display-formatting seam in Angular; write the
   logic directly in `transform()` (with `match`/chaining as usual) rather than
   delegating to a same-purpose helper file.
3. **Two or more components (or a component and a directive, etc.) need the
   same logic** → it graduates into an **Angular service** (`@Injectable`).
   Each consumer gets it via `inject(TheService)`. Do not duplicate the method
   across classes, and do not leave it as an unowned `*.function.ts` once a
   second Angular consumer needs it — a service is the correct home once
   logic is genuinely cross-cutting inside the Angular layer.
4. **Pure, non-Angular logic with no natural Angular owner** (a generic
   parsing/shaping utility that isn't display formatting and isn't tied to one
   class) → falls back to Part 1: its own `*.function.ts` file.

```ts
// (1) Single-component logic: stays as a private method, not its own file.
@Component({ selector: 'app-video-actions', /* ... */ })
export class VideoActionsComponent {
  private readonly apiService = inject(ApiService);
  private readonly toastService = inject(ToastService);

  addVideoToQueue(): void {
    const videoId = this.extractYouTubeVideoId(this.form.value.url?.trim());

    match(videoId)
      .with(P.string, (id) =>
        this.apiService.addVideoToQueue(`https://www.youtube.com/watch?v=${id}`),
      )
      .otherwise(() =>
        this.toastService.next({
          title: 'Invalid URL',
          message: 'Invalid YouTube URL',
          variant: 'danger',
        }),
      );
  }

  private extractYouTubeVideoId(url: string | undefined): string | null {
    try {
      const urlObj = new URL(url ?? '');

      return match(urlObj)
        .with({ hostname: P.string.includes('youtube.com') }, (value) =>
          value.searchParams.get('v'),
        )
        .with({ hostname: 'youtu.be' }, (value) => value.pathname.substring(1))
        .otherwise(() => null);
    } catch {
      return null;
    }
  }
}
```

```ts
// (2) Display-only formatting: an Angular Pipe, logic written inline.
@Pipe({ name: 'duration', standalone: true })
export class DurationPipe implements PipeTransform {
  transform(seconds: number | null | undefined): string {
    return match(seconds)
      .with(P.nullish, () => '0:00')
      .with(P.number.lt(1), () => '0:00')
      .otherwise(
        (value) =>
          `${Math.floor(value / 60)}:${Math.floor(value % 60)
            .toString()
            .padStart(2, '0')}`,
      );
  }
}
```

```ts
// (3) A second component now needs the same extraction as
// VideoActionsComponent above — it graduates out of the class into a service.
@Injectable({ providedIn: 'root' })
export class YouTubeUrlService {
  extractVideoId(url: string | undefined): string | null {
    try {
      const urlObj = new URL(url ?? '');

      return match(urlObj)
        .with({ hostname: P.string.includes('youtube.com') }, (value) =>
          value.searchParams.get('v'),
        )
        .with({ hostname: 'youtu.be' }, (value) => value.pathname.substring(1))
        .otherwise(() => null);
    } catch {
      return null;
    }
  }
}

// Every consumer injects it — the private method on VideoActionsComponent is
// deleted once the service exists.
private readonly youTubeUrl = inject(YouTubeUrlService);

addVideoToQueue(): void {
  const videoId = this.youTubeUrl.extractVideoId(this.form.value.url?.trim());
  // ...
}
```

Services created this way still follow Part 2's other rules internally:
`inject()` for their own dependencies, signals for any state they own, `match`
over `if`/`switch` in their methods.

## Types, interfaces, constants, config → their own files

Regardless of where logic lives, **never inline a type, interface, or constant
configuration object in a component/service/pipe/directive file.** Give each
its own file, named by what it holds:

- `*.types.ts` — type aliases.
- `*.interfaces.ts` — interfaces.
- `*.config.ts` — constant configuration values/objects (dialog configs,
  durations, thresholds, default options).

```ts
// username-dialog.config.ts
import { MatDialogConfig } from '@angular/material/dialog';

export const USERNAME_DIALOG_CONFIG: MatDialogConfig = {
  width: '320px',
  height: '200px',
  enterAnimationDuration: '150ms',
  exitAnimationDuration: '75ms',
};
```

```ts
// user-info.component.ts
import { USERNAME_DIALOG_CONFIG } from '../username-dialog/username-dialog.config';

openUsernameDialog(): void {
  this.dialog.open(UsernameDialogComponent, USERNAME_DIALOG_CONFIG);
}
```

If a repo already has an established suffix convention (e.g. `*.interface.ts`
singular, `*.consts.ts`), match it — the principle ("its own file, never
inline in a class file") is fixed, the exact suffix follows the project, same
as Part 1's directory-roles rule.

## Method bodies: match and chaining, not `if`/`else`

Inside whatever methods remain on the class — including the private methods
from rule (1) above — follow Part 1's branching rules:

- **No `if`/`else if`/`switch` chains.** Use `ts-pattern` `match(...)` for any
  branch that narrows a type or has more than one arm.
- **A single flat guard** may be an early-return `if` or a ternary — but as soon
  as there is a second branch, reach for `match`.
- **Compose with chaining/pipelines**, not stacks of intermediate mutable
  locals. Prefer lodash-es `chain().thru().value()`, array method chains
  (`.map().filter()`), and RxJS `pipe(...)` operator chains over imperative
  loops and reassignment.

RxJS streams are the pipeline for async: build them with `pipe()` and operators
(`map`, `filter`, `switchMap`, `combineLatest`), not by subscribing and mutating
fields inside the callback.

## Prefer signals wherever possible

Reach for **Angular signals** as the default for component and service state.

- **State:** `signal<T>(initial)` instead of a plain field you mutate.
- **Derived state:** `computed(() => ...)` instead of recomputing in a getter or
  in `ngOnChanges`. Never duplicate a value you can `computed()` from another
  signal.
- **Inputs / outputs:** use the signal-based `input()`, `input.required<T>()`,
  `model()`, and `output()` APIs rather than the `@Input()` / `@Output()`
  decorators in new code.
- **Reactions to signal changes:** use `effect(() => ...)` for side effects that
  follow state, instead of manual subscriptions where a signal fits.
- **Queries:** prefer `viewChild()` / `viewChildren()` / `contentChild()` signal
  queries over the decorator forms.
- **DI:** prefer `inject(Token)` over constructor-parameter injection, so fields
  can be initialized inline (including signal initializers derived from injected
  services).
- **Bridging RxJS:** convert with `toSignal(observable$)` for template
  consumption, and `toObservable(signal)` when a stream is genuinely needed.
  Keep long-lived async as RxJS; keep synchronous read state as signals.
- **Zoneless-friendly:** assume `provideZonelessChangeDetection()`. Do not rely
  on Zone.js side effects; signals and `markForCheck`-free updates are the model.

```ts
@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);
  private readonly themeSignal = signal<Theme>(this.resolveInitialTheme());

  readonly theme = computed(() => this.themeSignal());

  changeTheme(theme: Theme): void {
    this.themeSignal.set(theme);
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }

  private resolveInitialTheme(): Theme {
    // Only ThemeService needs this — stays a private method (rule 1),
    // not a separate *.function.ts file.
    // ...
  }
}
```

## Avoid `constructor`/`ngOnInit`/`ngOnChanges`/`ngOnDestroy` where signals suffice

Lifecycle hooks and the constructor exist to solve timing problems that
signals mostly already solve. **Default to no lifecycle hook at all** — reach
for one only when nothing signal-shaped covers the case.

- **`constructor()`** — avoid it. Field initializers run in the same
  injection context as the constructor, so `inject()`, `effect()`,
  `toSignal()`, and `.pipe(takeUntilDestroyed())` all work directly as field
  initializers. Keep a constructor only when you genuinely need imperative
  statements to run in a specific order before any field is readable — rare.
- **`ngOnInit`** — avoid it for setup that only reads injected services or
  static config; do that in a field initializer instead. If the setup depends
  on an input's value, express it as `computed()` (derived state) or
  `effect()` (a side effect) reacting to that input signal — both already run
  once inputs are available and again on every change, so there's no need for
  `ngOnInit` to single out "the first run."
- **`ngOnChanges`** — avoid it entirely once inputs are signal-based
  (`input()` / `model()`): a `computed()` or `effect()` reacting to the input
  signal re-runs on every change already, which is exactly what `ngOnChanges`
  exists for. `ngOnChanges` is only relevant to legacy `@Input()`-decorated
  fields.
- **`ngOnDestroy`** — avoid manual unsubscribe/cleanup. Use
  `.pipe(takeUntilDestroyed())` on an RxJS subscription (as a field
  initializer) or an `effect()`'s cleanup callback
  (`effect((onCleanup) => { ...; onCleanup(() => ...); })`). Keep `ngOnDestroy`
  only for teardown APIs that have no signal / `DestroyRef` equivalent.
- **Hooks that usually remain legitimate:** `ngAfterViewInit` /
  `ngAfterContentInit` (and their `...Checked` counterparts) fire at
  DOM/content-projection-ready timing that has no field-initializer or signal
  equivalent — keep them for work that genuinely needs the view or projected
  content to exist first (reading a `viewChild()` signal's `.nativeElement`,
  bootstrapping a third-party widget against a DOM node).

```ts
// Avoid: a constructor whose only job is DI plus a subscription.
export class ToastContainerComponent {
  readonly toasts = signal<Toast[]>([]);

  private readonly toastService = inject(ToastService);

  constructor() {
    this.toastService.get.pipe(takeUntilDestroyed()).subscribe((toast) => {
      this.toasts.update((current) => [...current, toast]);
    });
  }
}

// Prefer: the same subscription as a field initializer — no constructor,
// since field initializers already run in the injection context.
export class ToastContainerComponent {
  readonly toasts = signal<Toast[]>([]);

  private readonly toastService = inject(ToastService);

  private readonly toastSubscription = this.toastService.get
    .pipe(takeUntilDestroyed())
    .subscribe((toast) => {
      this.toasts.update((current) => [...current, toast]);
    });
}
```

## Readonly fields are mandatory when never reassigned

If a class property's *reference* is set once and never reassigned
afterward, it **must** be declared `readonly`. A field missing `readonly`
when nothing ever reassigns it is a bug to fix, not a style nit — the missing
modifier claims a mutability that doesn't exist and invites an accidental
future reassignment the compiler won't otherwise catch.

- Applies everywhere: injected services (`private readonly foo =
  inject(Foo)`), signals and computed signals (`readonly count = signal(0)`,
  `readonly doubled = computed(...)`), signal-based `input()` /
  `input.required()` / `model()` / `output()` fields, icon/constant fields,
  and any other field assigned once at declaration or in the constructor.
- **Signals stay `readonly` even though their value changes.** `readonly
  count = signal(0)` is correct: `count.set(5)` mutates what the signal
  *holds*; it does not reassign the `count` field itself — the field always
  points at the same `Signal` object.
- **Exception:** legacy `@Input()`-decorated fields are reassigned by
  Angular's change detection and cannot be `readonly`. That's one more reason
  to prefer signal-based `input()` — unlike `@Input()`, those fields can (and
  must) be `readonly`.
- A field the class itself reassigns in more than one place (e.g. `this.form
  = ...` set from two different methods) is correctly *not* `readonly` — this
  rule targets fields assigned once and never touched again, not fields in
  general.

## Keep the shell thin — what stays on the class

Belongs directly in the Angular class:

- Decorator metadata (`@Component`, `@Injectable`, selectors, templates, styles).
- Signal/observable **state fields** and DI via `inject()`.
- **Lifecycle hooks only where no field-initializer/signal equivalent
  exists** (see "Avoid `constructor`/`ngOnInit`/..." above) and event handlers.
- **Private methods used only by this class** (rule 1 above) — including
  non-trivial ones — written with `match`/chaining internally.
- Framework wiring that genuinely cannot be pure (subscribing a socket, setting a
  DOM/style property, navigating).

Moves out of the class:

- Display-only formatting logic → a **Pipe** (rule 2).
- Logic a second component/service/directive now needs too → a **service**
  (rule 3).
- Pure logic with no natural Angular owner → a Part 1 `*.function.ts` (rule 4).
- Types, interfaces, and constant/config objects → their own `*.types.ts` /
  `*.interfaces.ts` / `*.config.ts` files, always — regardless of how the logic
  itself is organized.

## Angular anti-patterns to remove on sight

- **Over-extraction:** a private method used by only one class pulled into its
  own `*.function.ts` file with no second caller — undo it, inline it back as a
  private method.
- **Duplication:** the same logic copy-pasted across two or more
  components/directives instead of centralized in a service.
- Display-formatting logic left inline in a component method (or duplicated
  across templates) instead of a `Pipe`.
- A type, interface, or constant/config object declared inline in a
  component/service/pipe/directive file instead of its own file.
- `if`/`else if`/`switch` in a method where a `ts-pattern` `match` fits.
- Imperative loops / reassigned locals where a `chain`, array-method chain, or
  RxJS `pipe` reads cleaner.
- A plain mutable field + manual change detection where a `signal` /
  `computed` / `effect` would express the same state reactively.
- `@Input()` / `@Output()` decorators, getter-based derived state, or
  constructor-injected fields in **new** code where `input()` / `output()` /
  `computed()` / `inject()` are available.
- A `constructor()`, `ngOnInit`, `ngOnChanges`, or `ngOnDestroy` doing work a
  field initializer, `computed()`, `effect()`, or `takeUntilDestroyed()` could
  do instead.
- A field that is assigned once and never reassigned again but is missing
  `readonly` — fix it in place, it's a defect, not a style choice.
