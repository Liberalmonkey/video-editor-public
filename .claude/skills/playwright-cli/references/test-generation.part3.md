> `test-generation.md` devamı — parça 3/4. Bağlam: # Test generation (plan → generate → heal)

## 2. Generate

Goal: take a spec file and produce Playwright test files. Optionally update the spec if it has drifted.

### 2.1 Inputs

- **Spec file**, e.g. `specs/basic-operations.plan.md`.
- **Target**: either a single scenario (e.g. `1.2`), a whole group (`1`), or all.
- **Seed file**, read from the `**Seed:**` line of the scenario's group.

### 2.2 Generate one scenario

For each target scenario, in sequence (never in parallel — scenarios share the seed session):

```bash
PLAYWRIGHT_HTML_OPEN=never npx playwright test <seed-file> --debug=cli   # background
playwright-cli attach tw-XXXX
# resume
```

**Do not** just open the app url with playwright-cli, always go through the test to capture any custom setup done there.

Walk the scenario's `Steps:` one by one with `playwright-cli`, treating the spec as the plan and the live app as the source of truth. If a step is vague ("click the button" — which button?), references an element that no longer exists, or contradicts the app's actual behaviour, use your judgement: update the spec to match what the app really does, then keep going. Editing the spec mid-generation is expected.

Every action prints the equivalent Playwright TypeScript (see [How generation works](#0-how-generation-works)):

```bash
playwright-cli snapshot                         # find refs
playwright-cli fill e3 "John Doe"               # -> page.getByRole('textbox', {...}).fill(...)
playwright-cli press Enter
playwright-cli click e7
```

For each `- expect:` bullet, add an explicit assertion. See [How generation works](#0-how-generation-works) for details.

Collect the generated code and write the test file at the path given in the spec:

```ts
// spec: specs/basic-operations.plan.md
// seed: tests/seed.spec.ts
import { test, expect } from './fixtures';   // or '@playwright/test' if no fixtures file

test.describe('Signing in and out', () => {
  test('should sign in', async ({ page }) => {
    // 1. Navigate to the application
    // (handled by the seed fixture)

    // 2. Type 'John Doe' into the username field
    await page.getByRole('textbox', { name: 'username' }).fill('John Doe');

    // 3. Type password
    await page.getByRole('textbox', { name: 'password' }).fill('TestPassword');

    // 4. Press Enter to submit
    await page.getByRole('textbox', { name: 'password' }).press('Enter');

    await expect(page.getByRole('heading')).toContainText('Welcome, John Doe!');
  });
});
```

Rules:

- **One test per file.** File path, describe name, and test name come verbatim from the spec (minus the ordinal).
- Prefix each numbered step with a `// N. <step text>` comment before its actions.
- Use the describe group name verbatim from the spec (no `1.` ordinal).
- Import from `./fixtures` if the project has one; otherwise `@playwright/test`.
- **Important**: close the CLI session and stop the background test before moving to the next scenario.

### 2.3 Generate multiple scenarios

Loop 2.2 over the targeted scenarios one at a time, restarting the seed between each so every test starts from a clean page. Make sure each test run is stopped before starting the next one.

### 2.4 Run generated tests

After generation, run the new tests once:

```bash
PLAYWRIGHT_HTML_OPEN=never npx playwright test tests/<group>/<scenario>.spec.ts
```

Any failure goes to Section 3.

---

## 3. Heal

Goal: fix failing tests, and update the spec if the app's intended behaviour changed.

### 3.1 Find failing tests

```bash
PLAYWRIGHT_HTML_OPEN=never npx playwright test
```

Record the list of failing `<file>:<line>` entries and process them one at a time. Do not attempt parallel fixes — shared state and the single CLI session make that fragile.

### 3.2 Debug one failure

Run the single failing test in debug mode in the background, then attach:

```bash
PLAYWRIGHT_HTML_OPEN=never npx playwright test tests/<group>/<scenario>.spec.ts:<line> --debug=cli
# wait for "Debugging Instructions" and the tw-XXXX session name
playwright-cli attach tw-XXXX
```

The test is paused at the start. Step forward or run to until just before the failing action or assertion, then diagnose:

```bash
playwright-cli snapshot                # did the element change / move / rename?
playwright-cli console                 # app-side errors?
playwright-cli requests                # failed request? wrong payload?
playwright-cli show --annotate         # ask the user to point somewhere
```

Common causes: selector drift, new wrapper element, label/ARIA rename, timing (transition, async load), assertion text updated in the app, test data leaking between runs.

Rehearse the corrected interaction with `playwright-cli` — the generated code in the output is what you paste back into the test.

### 3.3 Apply the fix

Edit the test file: update the locator, assertion, step order, or inputs to match the corrected behaviour. Stop the background debug run. Rerun the single test to confirm green.

Never skip hooks or add sleeps as a fix. Never use `networkidle`.

### 3.4 Reconcile with the spec

Open the spec referenced by the `// spec:` header in the test file and locate the scenario that matches the test.

- **Fix was purely technical** (locator drift, better assertion shape) and the spec's user-level behaviour still matches the app → leave the spec alone.
- **Fix changed user-visible steps, inputs, order, or expected outcomes** that the spec describes → update the spec to match reality. Keep the scenario id and file path stable; only the step / expect lines change.
- **Unclear whether the app change is intentional** (spec is stale) **or a regression** (test was right, app is wrong) → **stop and ask the user**. Provide:
  - the scenario id (e.g. `2.3`),
  - the spec lines that no longer match,
  - the observed app behaviour (quote a snapshot excerpt or a concrete outcome).

Only after the user answers, either update the spec (intentional change) or file/flag the test as covering a bug (regression).

### 3.5 Iteration and giving up

- Fix failures one at a time; rerun after each.
- If after thorough investigation you are confident the test is correct but the app is wrong *and* the user has confirmed it's a bug: mark the test `test.fixme(...)` with a comment pointing at the user's decision or issue link. Never silently skip.

---

