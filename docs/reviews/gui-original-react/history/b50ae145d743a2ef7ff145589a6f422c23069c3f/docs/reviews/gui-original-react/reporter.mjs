import { mkdirSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
const output = fileURLToPath(new URL("../../../.gate/gen/original/", import.meta.url));

// Assertion records arrive only from executed, awaited browser assertions. A
// declaration, skipped test, retry or missing attachment cannot produce a pass.
export default class OriginalReporter {
  fixtures = [];
  cases = [];
  onTestEnd(test, result) {
    const trace = result.attachments.find((item) => item.name === "executed-original-assertions");
    const fixture = trace?.body ? JSON.parse(trace.body.toString("utf8")) : null;
    const passed = result.status === "passed" && result.retry === 0 && test.expectedStatus === "passed";
    this.cases.push({ title: test.title, status: result.status, retry: result.retry, expectedStatus: test.expectedStatus, errors: result.errors });
    if (passed && fixture && fixture.assertions.length) this.fixtures.push(fixture);
  }
  onError(error) { process.stderr.write(`${error.message}\n`); }
  onEnd(result) {
    const status = result.status === "passed" && this.cases.length === this.fixtures.length &&
      this.cases.every((item) => item.status === "passed" && item.retry === 0) ? "pass" : "fail";
    mkdirSync(output, { recursive: true });
    writeFileSync(`${output}playwright.json`, JSON.stringify({
      schema: 1, status, cases: this.cases, fixtures: this.fixtures,
    }, null, 2) + "\n");
    process.stderr.write(`Original browser: ${this.fixtures.length}/${this.cases.length} fixtures ${status}\n`);
    for (const item of this.cases.filter((item) => item.status !== "passed")) {
      process.stderr.write(`${item.title}: ${JSON.stringify(item.errors)}\n`);
    }
  }
}
