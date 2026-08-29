---
name: angular-guidelines
description: "Angular coding guidelines for this workspace. USE WHEN creating or modifying any Angular component, directive, pipe, service, template, model, unit test (*.spec.ts) or e2e test in apps/ or libs/. EXAMPLES: 'add a component', 'refactor this template', 'create a pipe', 'review Angular code', 'write unit tests for this service', 'add an e2e test for the login flow', 'fix this flaky spec'."
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

## Testing

20. NEVER assume a test runner or e2e framework. Before writing a single test, detect what the workspace already uses and match it exactly — its APIs, its config, its folder layout, its file suffixes. Detect in this order:
    - **Unit runner**: the `test` target builder in `angular.json` / `project.json` (`@angular/build:unit-test`, `@angular-devkit/build-angular:karma`, `@angular-builders/jest`, `@nx/jest`, `@nx/vite`) → then `vitest.config.*` / `jest.config.*` / `karma.conf.*` → then `devDependencies` (`vitest`, `jest`, `jasmine-core`).
    - **E2E framework**: `playwright.config.*` / `cypress.config.*` → then the `e2e` target builder → then `devDependencies`.
    - Copy the conventions of the nearest existing spec file. If nothing exists and nothing is configured, ask which tools to add instead of introducing one.
21. Only the spy/mock/parameterisation API differs between runners — everything below applies to all of them. Translate at the call site:

    | Concept       | Jest                | Vitest             | Jasmine                       |
    | ------------- | ------------------- | ------------------ | ----------------------------- |
    | Stub function | `jest.fn()`         | `vi.fn()`          | `jasmine.createSpy()`         |
    | Spy on method | `jest.spyOn(o, 'm')`| `vi.spyOn(o, 'm')` | `spyOn(o, 'm')`               |
    | Object mock   | `jest.mocked(...)`  | `vi.mocked(...)`   | `jasmine.createSpyObj(...)`   |
    | Fake timers   | `jest.useFakeTimers()` | `vi.useFakeTimers()` | `jasmine.clock().install()` |

22. Test code is production code: rules 10–19 (readonly, one declaration per file, no magic literals, `ts-pattern` over `if`, kebab-case filenames) apply to specs, page objects, factories, and fixtures too.

## Unit tests

23. Co-locate `*.spec.ts` next to the file under test, in the same directory (rule 19). One spec file per declaration under test — never one spec covering several components.
24. Structure: a single top-level `describe` named exactly after the declaration under test, nested `describe`s per public member, and `it` titles that read as a sentence: `it('should <expected result> when <condition>')`. Never `it('works')`.
25. Every test body is Arrange → Act → Assert, in that order, separated by blank lines. One behaviour per `it`.
26. Test the public contract only. Never reach for `private` members, never assert on call counts of internal helpers, never cast to `any` to get access — if something is worth asserting, expose it or assert the observable effect instead.
27. Pure code (pipes, `*.function.ts`, `computed()` factories, guards without DI) is tested by calling it directly. Do NOT spin up `TestBed` for something that has no dependencies.
28. Components/services with DI use `TestBed.configureTestingModule({ imports: [TheComponent], providers: [...] })` — standalone components go in `imports`, never `declarations`.
29. The workspace is zoneless (rule 6): add `provideZonelessChangeDetection()` to the testing providers and await `fixture.whenStable()` after acting. Do NOT sprinkle `fixture.detectChanges()` calls to force a result, and never use `fakeAsync`/`tick` to paper over missing awaits.
30. Signal inputs are set with `fixture.componentRef.setInput('name', value)` — never assign to the input signal, never poke at the component field. Read signals and `computed()` values by calling them (`component.total()`).
31. Assert outputs by subscribing before acting: `component.saved.subscribe(spy)` (or `outputToObservable`), then assert the spy received the expected payload.
32. Replace dependencies at the DI boundary with `{ provide: SomeService, useValue: mock }`, and type the mock so it fails to compile when the real API changes. Do NOT mock the class under test, and do NOT mock plain data helpers — call the real ones.
33. HTTP is tested with `provideHttpClient()` + `provideHttpClientTesting()` and `HttpTestingController`; assert the request (method, url, body) and call `verify()` in `afterEach`. Never stub `fetch`/`XMLHttpRequest` directly.
34. Query the DOM through `fixture.debugElement.query(By.css('[data-testid="..."]'))`. Never select by CSS class, tag hierarchy, or index — those are styling details, not a contract.
35. No control flow in specs: no `if`, no `for`, no `try/catch`. Cover multiple cases with the runner's parameterised API (`it.each` / a `describe.each` table); each case must produce its own named test.
36. Tests must be deterministic and order-independent: no shared mutable module state, no real timers (use the runner's fake timers), no reliance on the system clock, locale, or network.
37. Build test data with a named factory (`create-user.mock.ts` exporting `createUserMock(overrides)`) rather than repeating object literals; each test overrides only the fields it actually asserts on.
38. Never commit `fdescribe`, `fit`, `.only`, or a disabled test without an adjacent comment explaining why and when it comes back.

## E2E tests

39. E2E specs live in the workspace's dedicated e2e project (`apps/<app>-e2e/` or `e2e/`), never beside unit specs, and use that framework's suffix (`*.e2e.spec.ts` for Playwright, `*.cy.ts` for Cypress).
40. E2E covers user journeys across real screens — sign in, complete the form, see the result. Anything provable at the component level belongs in a unit test. Keep the suite small and slow-moving on purpose.
41. Use the Page Object Model: one page object per route/screen, in its own file (`*.page.ts`) exporting one class, with locators as `readonly` fields and methods named for the user's intent (`submitLoginForm()`, not `clickButton()`). Specs contain no raw selectors.
42. Locator priority: accessible role/label first (`getByRole`, `getByLabel`), then `data-testid`, and nothing else. Never CSS classes, never XPath, never DOM structure or `nth-child`.
43. `data-testid` in a template is a public contract: kebab-case, descriptive, stable across refactors. Add one only when no accessible role/label works.
44. Use retrying, web-first assertions (`await expect(locator).toBeVisible()` / `cy.get(...).should(...)`). NEVER use a fixed sleep, and never assert on a value read once into a variable.
45. Every test sets up its own state and can run alone, in parallel, and in any order. No test depends on a previous test's leftovers.
46. Authenticate and seed programmatically (stored auth state, API calls, `page.route` / `cy.intercept` stubs) — not by driving the login UI in every spec. Reserve one real end-to-end login test for the auth journey itself.
47. Stub the network at the boundary for deterministic data; if a suite must hit a real backend, isolate it as a separate smoke/@smoke-tagged suite so the main suite stays hermetic.
48. No conditional logic or branching in an e2e spec. If a flow genuinely differs, write two named tests.
49. Fix flaky tests at the cause (missing await, racing request, shared state). Never "solve" flakiness with a retry, a sleep, or a `.skip`.
