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

---
name: unit-tests
description: "Strict conventions for writing and reviewing Angular unit tests (*.spec.ts) — naming, structure, coverage checklist, and assertion rules for components, services, directives, pipes and pure functions. USE WHEN creating, reviewing, or fixing any unit test. EXAMPLES: 'write tests for this component', 'add a spec for this service', 'review my spec', 'why does this test not catch the bug', 'what should I assert here'."
---

# Angular App Tests Guidelines

## Before you write tests

Detect the workspace's conventions and match them exactly — runner, config, file suffix,
folder layout. Read the nearest existing spec first and copy its shape. Never introduce a
second runner or a second style.

Only the spy/mock API differs between runners; everything below applies to all of them:

| Concept | Vitest | Jest | Jasmine |
| --- | --- | --- | --- |
| Stub function | `vi.fn()` | `jest.fn()` | `jasmine.createSpy()` |
| Spy on method | `vi.spyOn(o, 'm')` | `jest.spyOn(o, 'm')` | `spyOn(o, 'm')` |
| Fake timers | `vi.useFakeTimers()` | `jest.useFakeTimers()` | `jasmine.clock().install()` |

Specs are co-located with their source, one spec per declaration under test. Test code is
production code — the project's lint, naming and immutability rules apply to it too.

If the app is zoneless, configure that once in the shared test setup (or add
`provideZonelessChangeDetection()` to the testing providers) rather than per spec.

## Naming

- Top-level `describe` = the **exact exported symbol**: `'UserCardComponent'`, `'AuthService'`, `'formatDuration'`. Never a prose title or a file path.
- Nested `describe` = the API surface. Use a fixed vocabulary:
  `'default inputs'` · `'<name> input'` · `'<name> output'` · `'content projection'` ·
  `'methodName()'` · `'with host'`. Add one named block per cross-cutting concern the
  subject has (e.g. `'internationalization'`, `'accessibility'`).
- `it` titles: `should [not] <verb> <object> [when/after <condition>]`.
  Verbs describe observable behaviour — render, display, emit, return, update, apply, pass,
  call, project, sort, group, include, exclude, trim, hide. **Never name a private method,
  a field, or an implementation detail.**
- First test: `it('should create')` for components and directives, `it('should be created')` for services.
- Loop-generated tests carry the parameter: `` it(`should render ${el} when element is "${el}"`) ``.

Bad: `'works'` · `'test the icon'` · `'should call formatParts()'` · `'should set this.active'` · `'handles edge cases'`

## Structure

File order: sorted imports → module-scope factories and constants → host components → `describe`.

Test body: arrange, act, **blank line**, assert. One behaviour per `it`. No conditionals,
loops or try/catch inside a test body — if you need a loop, generate the tests instead.

## Test data

Build domain objects through one override factory, so each test shows only the field it
cares about and a model change touches one line:

```ts
const createUser = (overrides: Partial<User> = {}): User => ({
  id: '1',
  name: 'Test user',
  createdAt: new Date('2025-06-15'),
  ...overrides,
});
```

Fixed values only. **Never `new Date()`, `Math.random()`, or `Date.now()` in a test** —
freeze the clock or pass a literal.

## Components

```ts
beforeEach(async () => {
  await TestBed.configureTestingModule({
    imports: [UserCardComponent],
    providers: [{ provide: UserService, useValue: userServiceMock }],
  }).compileComponents();

  fixture = TestBed.createComponent(UserCardComponent);
  component = fixture.componentInstance;
  fixture.detectChanges();
});
```

- Standalone components go in `imports`, never `declarations`.
- Signal inputs: `fixture.componentRef.setInput('name', value)`. Never assign to the input
  signal or poke the field. Read with `component.name()`.
- Signal outputs: subscribe before acting — `outputToObservable(component.saved).subscribe(spy)`.
  Legacy `@Output()`/`EventEmitter`: `spyOn(component.saved, 'emit')`.
- Add a **host fixture** for content projection, `ContentChildren`, and proving a parent's
  handler runs. After mutating a host field, mark it dirty
  (`hostFixture.changeDetectorRef.markForCheck()`) before flushing.
- Flush the way the app runs: `await fixture.whenStable()` in a zoneless app,
  `fixture.detectChanges()` in a zone-based one. Never mix both to force a result, and never
  reach for `fakeAsync`/`tick` to paper over a missing await.

**Coverage checklist** — cover in this order, skipping only what the component has no surface for:

1. `it('should create')`
2. `'default inputs'` — each default **value** *and* each default **DOM consequence**, as separate tests
3. `'<name> input'` — the applied value reaches the DOM, and a second value *replaces* the first
4. Conditional rendering — present on one side of the threshold, absent on the other, and the transition that removes it
5. Computed members — neutral result for empty input, one test per contributing field, one combined
6. Structural contract — element counts, and which container holds which child
7. `'content projection'` — initial, updated, cleared
8. Text fidelity — user content renders verbatim, including `& < > "` that HTML would escape
9. `'<name> output'` — correct payload, exactly once per interaction, never without interaction
10. `'methodName()'` — one test per branch, including the branch that does nothing

## Services

No `compileComponents()`, no fixture.

```ts
beforeEach(() => {
  repositoryMock = { load: vi.fn().mockReturnValue(of(items)) };

  TestBed.configureTestingModule({
    providers: [{ provide: Repository, useValue: repositoryMock }],
  });

  service = TestBed.inject(SearchService);
});
```

- Replace dependencies at the DI boundary with `{ provide: X, useValue: mock }`. Type the
  mock so it fails to compile when the real API changes.
- Mock only what the subject touches — the minimum surface, rebuilt in `beforeEach` so call
  history never leaks between tests.
- Never mock the class under test, and never mock pure data helpers — call the real ones.
- Unwrap observables with `await firstValueFrom(...)`. Never `subscribe` + `done`.
- Test HTTP with `provideHttpClient()` + `provideHttpClientTesting()`; assert method, URL and
  body, then `verify()` in `afterEach`. Never stub `fetch`/`XMLHttpRequest`.
- Stub browser APIs with `spyOn`. When the subject registers a listener, recover it from the
  spy's call record and invoke it directly rather than faking an event.
- Tear down persistent state in `afterEach` — databases, storage, timers, global spies.
- Every public method gets `describe('method()')` with the happy path plus its real edges:
  empty collection, unknown id, index 0 / last / out of bounds, empty and whitespace-only
  input, sort order, and the grouping or pagination boundary.

## Directives

Host-driven only — a directive has no fixture of its own. Declare a host that applies it and
collect the instances:

```ts
@Component({
  imports: [HighlightDirective],
  template: `<p appHighlight [color]="color">Text</p>`,
})
class TestHostComponent {
  @ViewChildren(HighlightDirective) directives!: QueryList<HighlightDirective>;
  color = 'yellow';
}
```

Split by cardinality:

- `describe('single instance')` — creates, defaults hold, each input binds from the host and
  updates when the host changes, injected refs are the expected type, callbacks come back
  **by identity** (`toBe`, not `toEqual`).
- `describe('multiple instances')` — one instance per usage, inputs set on one do not leak to
  the others, each instance holds its own injected refs.

## Pipes and pure functions

Call them directly. **No TestBed for anything without DI** — `new TruncatePipe().transform(…)`
or a plain import.

One `it` per mapped field and per boundary — zero, ±1, empty, the unit rollover (minute,
month, year), and time-of-day or timezone normalization where dates are involved.

A pipe with injected dependencies is tested like a service:
`TestBed.configureTestingModule({ providers })` + `TestBed.inject(MyPipe)`. Add one host test
confirming `{{ value | myPipe }}` transforms in a template, so the pipe `name` and its
registration are covered too.

## Assertion rules

- **Assert the observable effect, not the internal state.** A default value and its rendered
  consequence are two separate tests.
- **Prove the change.** Assert the new value *and* the absence of the old one — otherwise
  code that appends instead of replacing still passes.
- **Trigger through the DOM.** `button.click()` exercises the template wiring; calling
  `emit()` only exercises the emitter.
- **Query by stable selectors** — a test id, a role, or a semantic element. Never by styling
  class, tag hierarchy, or index; those are not a contract.
- **Derive formatted expectations from the production formatter** rather than hardcoding its
  output, so the test survives a library update and still proves the right locale, format and
  transformation were applied.
- **Test at the boundary, not a round number** — 7 items to prove rows of 3 give `3 / 3 / 1`.
- **Cover the branch that does nothing.** The no-op is the one that silently regresses.
- **Push each assertion to the lowest layer that can make it.** If you are building an
  elaborate fixture to reach a simple rule, the rule belongs in a lower layer.

## Never

- Cast to `any` or reach for a `private`/`protected` member — assert the observable effect instead.
- Assert on incidental whitespace or formatting the template controls.
- Leave a spec at `it('should create')` when the subject has branches, inputs or outputs.
- Call `emit()` to test an output.
- Use a non-deterministic value in an assertion.
- Write one spec covering several declarations.
