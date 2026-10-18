import test from "node:test";
import assert from "node:assert/strict";
import { checkBrowserReport, EXPECTED_BROWSER_CASES } from "../scripts/gui-browser-tests.mjs";
const valid = () => ({ success: true, numTotalTests: 6, numPassedTests: 6,
  numFailedTests: 0, numPendingTests: 0,
  testResults: [{ status: "passed", assertionResults: EXPECTED_BROWSER_CASES.map((fullName) => ({
    fullName, status: "passed", failureMessages: [],
  })) }],
});

await test("bounded browser report accepts exactly the six executed passing cases", () => {
  assert.equal(checkBrowserReport(valid()), 6);
});
await test("aggregate pass cannot hide missing, extra or duplicate browser identities", () => {
  for (const mutate of [
    (cases) => cases.pop(),
    (cases) => cases.push({ ...cases[0], fullName: "unexpected" }),
    (cases) => { cases[1] = { ...cases[0] }; },
  ]) {
    const report = valid(); mutate(report.testResults[0].assertionResults);
    assert.throws(() => checkBrowserReport(report));
  }
});
await test("aggregate pass cannot hide skipped, todo or failed browser cases", () => {
  for (const status of ["pending", "skipped", "todo", "failed"]) {
    const report = valid(); report.testResults[0].assertionResults[0].status = status;
    assert.throws(() => checkBrowserReport(report));
  }
});
await test("browser report refuses inconsistent totals and failed file/runtime status", () => {
  for (const mutate of [
    (report) => { report.numTotalTests = 0; },
    (report) => { report.numPassedTests = 5; },
    (report) => { report.numFailedTests = 1; },
    (report) => { report.numPendingTests = 1; },
    (report) => { report.success = false; },
    (report) => { report.testResults[0].status = "failed"; },
    (report) => { report.testResults = []; },
  ]) {
    const report = valid(); mutate(report); assert.throws(() => checkBrowserReport(report));
  }
});
await test("even a passed browser case must carry no failure messages", () => {
  const report = valid(); report.testResults[0].assertionResults[0].failureMessages = ["unhandled failure"];
  assert.throws(() => checkBrowserReport(report));
});
