---
name: lodash-refactor
description: Refactor existing TypeScript to a strict lodash-first coding style — replacing native loops, array methods, object/string/number/date manipulation, cloning, type checks, and utilities with their lodash-es equivalents. Use when asked to "refactor with lodash", "convert to lodash", "apply the lodash style", or enforce lodash usage across a TypeScript file or module.
---

# Lodash Refactor

Rewrite existing **TypeScript** code so that all iteration, collection, object, string,
number, date, cloning, type-checking, and utility operations go through lodash instead of
native constructs. The goal is a consistent, uniform style where lodash is the single
vocabulary for these operations. This skill targets `.ts`/`.tsx` files — preserve type
annotations, generics, and type safety throughout the refactor.

## When to use

- The user asks to refactor a TypeScript file/module to use lodash.
- The user wants to enforce a "lodash-first" coding standard in a TypeScript codebase.
- New or reviewed TypeScript mixes native loops/methods with lodash and should be made consistent.

Do **not** apply blindly to code where a native construct is required for correctness,
type narrowing, or performance-critical hot paths (see [Cautions](#cautions)).

## Import convention

Always use **`lodash-es`** (the ES-module, tree-shakeable build), never the CommonJS
`lodash` package. **Never use the `_` namespace object in code.** Import each method by
name and call it directly:

```ts
import { forEach, map, filter, cloneDeep, isString } from 'lodash-es';

forEach(items, (item: Item) => doThing(item));
const names: string[] = map(users, 'name');
```

For types, ensure `@types/lodash-es` is installed as a dev dependency (lodash-es ships no
bundled types). If it is missing, add it — otherwise the named imports will not type-check.

Rules:

- Import every lodash method you use as a **named import** from `'lodash-es'` — one
  shared `import { ... } from 'lodash-es'` at the top of the file, kept in sync with the
  methods actually used.
- **Do not** write `import _ from 'lodash-es'`, `import * as _ from 'lodash-es'`,
  `_.map(...)`, or any `_.`-prefixed call. There must be no `_` identifier in the code.
- If the file currently imports from `'lodash'` (default or namespace) or uses
  `require('lodash')`, replace it entirely with named `'lodash-es'` imports. Leave nothing
  behind.

## Refactoring rules

Apply every rule below. Each shows the native pattern → the lodash replacement. All
replacements call methods directly by name (import them from `'lodash-es'`).

### 1. Loops and iteration → `forEach`

Convert `for`, `while`, `do...while`, `for...of`, and `Array.prototype.forEach`.

```ts
// before
for (let i = 0; i < items.length; i++) {
  doThing(items[i]);
}
for (const item of items) {
  doThing(item);
}
items.forEach((item) => doThing(item));

// after
forEach(items, (item) => doThing(item));
```

Note: `forEach` also iterates objects, so `for (const key in obj)` becomes
`forEach(obj, (value, key) => ...)`.

### 2. Array methods → lodash equivalents

`map`, `filter`, `reduce`, plus `find`, `some`, `every`, `includes`, `flatMap`,
`uniq`, `sortBy`, etc.

```ts
// before
const names = users.filter((u) => u.active).map((u) => u.name);

// after
const names = map(
  filter(users, (u) => u.active),
  (u) => u.name,
);
// or use chaining (rule 11)
```

### 3. Object manipulation → `get`, `set`, `has`, `omit`, `pick`, ...

```ts
// before
const city = user && user.address && user.address.city;
if (Object.prototype.hasOwnProperty.call(obj, 'id')) { ... }
const { password, ...safe } = user;

// after
const city = get(user, 'address.city');
if (has(obj, 'id')) { ... }
const safe = omit(user, ['password']);
```

### 4. `Object.keys` / `Object.values` / `Object.entries` → `keys` / `values` / `entries`

```ts
// before
Object.keys(obj);
Object.values(obj);
Object.entries(obj);

// after
keys(obj);
values(obj);
entries(obj); // toPairs is an alias for entries
```

### 5. String manipulation → `camelCase`, `kebabCase`, `snakeCase`, `startCase`, ...

Also `trim`, `upperFirst`, `lowerCase`, `capitalize`, `pad`, `truncate`, `repeat`.

```ts
// before
str.trim();
str.charAt(0).toUpperCase() + str.slice(1);

// after
trim(str);
upperFirst(str);
```

### 6. Number manipulation → `round`, `ceil`, `floor`, `random`, ...

```ts
// before
Math.round(x);
Math.floor(x);
Math.random();
Math.max(...nums);

// after
round(x);
floor(x);
random(0, 1, true);
max(nums);
// clamp, inRange also available
```

### 7. Date manipulation → `now`, ...

lodash has a limited date surface. Use `now()` for `Date.now()`. For add/subtract
style operations lodash does not provide dedicated date helpers — if the project relies
on `add`/`subtract` semantics, use `add`/`subtract` (arithmetic helpers) or flag that a
real date library is needed rather than forcing a wrong replacement.

```ts
// before
Date.now();

// after
now();
```

### 8. Deep clone / merge / assign → `cloneDeep`, `merge`, `assign`

Replace every `Object.assign` with lodash `assign` (same shallow-copy, mutate-first-arg
semantics).

```ts
// before
const copy = JSON.parse(JSON.stringify(obj));
const merged = { ...a, ...b }; // shallow
const updated = Object.assign({}, a, b);
Object.assign(target, source);

// after
const copy = cloneDeep(obj);
const merged = merge({}, a, b); // deep; use assign/defaults for shallow intent
const updated = assign({}, a, b);
assign(target, source);
```

### 9. Type checking → `isArray`, `isObject`, `isString`, `isNumber`, ...

Also `isNil`, `isEmpty`, `isFunction`, `isBoolean`, `isPlainObject`, `isEqual`.

```ts
// before
Array.isArray(x);
typeof x === 'string';
x === null || x === undefined;

// after
isArray(x);
isString(x);
isNil(x);
```

These helpers are typed as **type guards** in `@types/lodash-es` (e.g. `isString(x)`
narrows `x` to `string`, `isArray(x)` to `unknown[]`), so replacing a `typeof`/
`Array.isArray` check keeps the same narrowing in downstream branches. Confirm the
narrowed type still satisfies later usage after each swap.

### 10. Collection helpers → `groupBy`, `keyBy`, `countBy`, ...

```ts
// before
const byId = {};
for (const u of users) byId[u.id] = u;

// after
const byId = keyBy(users, 'id');
```

### 11. Chaining → `chain`

Collapse multi-step pipelines into an explicit lodash chain, ending with `.value()`.
Import `chain` by name like any other method.

```ts
// before
const result = map(
  filter(users, (u) => u.active),
  (u) => u.name,
);

// after
const result = chain(users)
  .filter((u) => u.active)
  .map('name')
  .value();
```

## Process

1. **Read the whole file first** and note the existing imports.
2. Work rule by rule (or top-to-bottom), converting one construct at a time.
3. Preserve behavior exactly — same inputs produce same outputs, same short-circuiting,
   same mutation vs. non-mutation semantics.
4. Maintain a single named `import { ... } from 'lodash-es'` at the top; add each method
   you introduce to it, and remove any `'lodash'` / `require('lodash')` import and every
   `_` reference. Confirm the identifier `_` no longer appears in the file.
5. Run the TypeScript compiler (`tsc --noEmit` or the project's typecheck script) plus
   lint and tests after refactoring to confirm no type errors or regressions.

## Cautions

- **Semantics differ.** `merge` is deep and mutates its first arg; `forEach` can't
  `break` (return `false` to stop early); `map` over an object iterates values. Verify
  each replacement preserves the original meaning, especially loop early-exit (`break`/
  `continue`/`return`) and async iteration (`for await`, awaiting inside loops — do **not**
  convert those to `forEach`, which ignores returned promises).
- **Types.** Keep the result strongly typed. Property-string shorthands like
  `map(users, 'name')` type-check via `@types/lodash-es` but infer more loosely than an
  arrow (`map(users, (u) => u.name)`); prefer the arrow form when it preserves a tighter
  type, and add explicit type arguments/annotations where inference degrades.
- **Dates** are weakly supported by lodash. Don't invent nonexistent lodash date methods;
  flag when a real date library (date-fns, dayjs) is the correct tool.
- **Hot paths.** Native `for` loops can be faster; if a comment or context marks code as
  performance-sensitive, leave it and note the exception.
- **Async/generators.** Leave `async`/`await` control flow and generator loops as native.
- Keep the diff focused: change style, not logic. Don't rename variables or restructure
  unrelated code.
