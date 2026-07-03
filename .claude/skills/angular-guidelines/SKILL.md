---
name: angular-guidelines
description: "Angular coding guidelines for this workspace. USE WHEN creating or modifying any Angular component, directive, pipe, service, template, or model in apps/ or libs/. EXAMPLES: 'add a component', 'refactor this template', 'create a pipe', 'review Angular code'."
---

# Angular App Guidelines

Follow these rules for all Angular code in this workspace (`apps/browser` and `libs/*`).

## Templates

1. Use modern control flow ONLY: `@if`, `@for`, `@switch`, `@defer`, `@let`. Never use `*ngIf`, `*ngFor`, `*ngSwitch`, or `NgIf`/`NgFor` imports.
2. Every `@for` must have a `track` expression.
3. Keep logic out of templates. A function whose single responsibility is formatting/preparing data for display MUST be refactored into a pipe.

## Signals & reactivity

4. Use the signal-based APIs everywhere: `signal()`, `computed()`, `input()` / `input.required()`, `output()`, `model()`, and `inject()` for DI. Never use `@Input()`, `@Output()`, or constructor-parameter injection.
5. Avoid lifecycle methods (`ngOnInit`, `ngOnChanges`, `ngAfterViewInit`, ...) whenever possible. Prefer `effect()` (in the constructor or as a field), `computed()`, or signal `input()` transforms instead. Reach for a lifecycle hook only when there is no signal-based equivalent.
6. Do not write code that relies on zone.js.

## Components

7. Every component must set `changeDetection: ChangeDetectionStrategy.OnPush`.
8. Components are standalone (no NgModules); list dependencies in the component `imports` array.
9. Member visibility: members used only by the template are `protected`; injected services and internal state are `private`. Injected dependencies go last, as `private readonly x = inject(X)`.

## Immutability

10. Add the `readonly` modifier to EVERYTHING that can carry it: class fields (signals, injected services, subjects, icon references), constants, interface properties. If a member is never reassigned, it is `readonly`.

## Types, constants & configuration

11. Interfaces, types, enums, and consts live in separate files — never inline them in a component/service file. Use the established suffixes and locations:
    - `*.interface.ts`, `*.enum.ts` → `models/` directory (app) or the lib root
    - `*.consts.ts` → shared constant values (e.g. `app.consts.ts`)
    - `*.config.ts` → configuration objects
    - `*.token.ts` → `InjectionToken` definitions
    - `*.function.ts` → one standalone utility function per file (see `libs/utils`)
15. No magic numbers or magic strings: every literal that carries meaning must be a named `SCREAMING_SNAKE_CASE`.
16. Consts that "configure" a component go in a `<name>.config.ts` file next to that component. If a config is shared by multiple components, place it in the closest common ancestor directory of the components that use it.

## Control flow in TypeScript

17. Prefer `ts-pattern` `match()` over `if`/`else`/`switch` statements. Destructure the patterns you need (`const { nullish, number, when, union } = P;`) at the top of the file, and use `noop` from `lodash-es` for empty branches.
18. Prefer functional pipelines and `lodash-es` utilities (`attempt`, `isError`, `get`, `noop`, ...) over imperative loops and try/catch blocks.

## File layout & naming

19. One declaration per file, named by role: `*.component.ts`, `*.directive.ts`, `*.pipe.ts`, `*.service.ts` — each in its own directory together with its co-located `*.spec.ts` (e.g. `pipes/duration/duration.pipe.ts` + `duration.pipe.spec.ts`).
